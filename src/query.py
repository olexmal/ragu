"""
Query Module
Processes natural language queries and retrieves relevant documentation.
"""
import os
import time
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from dotenv import load_dotenv
from .get_vector_db import get_vector_db
from .utils import setup_logging
from .cache import get_cache
from .monitoring import get_query_monitor
from .query_history import get_query_history
from .llm_providers import LLMProviderFactory
from .settings import get_active_llm_provider

load_dotenv()

LLM_MODEL = os.getenv('LLM_MODEL', 'mistral')
TEXT_EMBEDDING_MODEL = os.getenv('TEXT_EMBEDDING_MODEL', 'nomic-embed-text')
USE_CACHE = os.getenv('USE_CACHE', 'true').lower() == 'true'

logger = setup_logging()


def get_prompt():
    """
    Get prompt templates for query processing.
    
    Returns:
        tuple: (QUERY_PROMPT for multi-query, prompt template for QA)
    """
    QUERY_PROMPT = PromptTemplate(
        input_variables=["question"],
        template="""You are an AI language model assistant. Your task is to generate 3 
        different versions of the given user question to retrieve relevant documents from a 
        vector database. By generating multiple perspectives on the user question, your goal 
        is to help the user overcome some of the limitations of distance-based similarity search. 
        Provide these alternative questions separated by newlines.
        Original question: {question}""",
    )

    template = """Answer the question based ONLY on the following context:
    {context}
    
    Question: {question}
    
    If the context does not contain enough information to answer the question, 
    say "I don't have enough information in the documentation to answer this question."
    
    Provide a clear, concise answer with relevant details from the context."""
    
    prompt = PromptTemplate.from_template(template)

    return QUERY_PROMPT, prompt


def query_docs(question, collection_name=None, version=None, k=3, use_cache=None):
    """
    Query documentation using RAG with optional caching.
    
    Args:
        question: Natural language question
        collection_name: Name of the collection to query
        version: Optional version string for version-specific collections
        k: Number of documents to retrieve (default: 3)
        use_cache: Override cache setting (default: from USE_CACHE env var)
        
    Returns:
        dict: Query result with answer, source documents, and timing statistics
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")
    
    # Initialize timing statistics
    stats = {
        'total_time': 0.0,
        'cache_lookup_time': 0.0,
        'llm_init_time': 0.0,
        'vector_db_init_time': 0.0,
        'multi_query_generation_time': 0.0,
        'document_retrieval_time': 0.0,
        'answer_generation_time': 0.0,
        'cache_store_time': 0.0
    }
    overall_start = time.time()
    
    # Check cache if enabled
    cached = False
    if use_cache is None:
        use_cache = USE_CACHE
    
    if use_cache:
        cache_start = time.time()
        cache = get_cache()
        cached_result = cache.get(question, version, k)
        stats['cache_lookup_time'] = time.time() - cache_start
        
        if cached_result:
            logger.info(f"Returning cached result for: {question[:100]}...")
            cached = True
            stats['total_time'] = time.time() - overall_start
            cached_result['stats'] = stats
            # Log to monitoring
            monitor = get_query_monitor()
            monitor.log_query(question, version, response_time=stats['total_time'], 
                            source_count=len(cached_result.get('source_documents', [])), 
                            cached=True)
            return cached_result
    
    logger.info(f"Processing query: {question[:100]}...")
    start_time = time.time()
    
    # Initialize the language model
    llm_start = time.time()
    provider_config = get_active_llm_provider()
    llm = LLMProviderFactory.get_llm(provider_config['type'], provider_config)
    stats['llm_init_time'] = time.time() - llm_start
    
    # Get the vector database instance
    db_start = time.time()
    db = get_vector_db(collection_name=collection_name, version=version)
    stats['vector_db_init_time'] = time.time() - db_start
    
    # Get the prompt templates
    QUERY_PROMPT, prompt = get_prompt()
    
    # Set up the retriever with multi-query support
    base_retriever = db.as_retriever(search_kwargs={"k": k})
    
    # Multi-query generation timing
    multi_query_start = time.time()
    retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm,
        prompt=QUERY_PROMPT
    )
    stats['multi_query_generation_time'] = time.time() - multi_query_start
    
    # Create the QA chain using LCEL
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # Execute query
    try:
        # Get source documents - MultiQueryRetriever wraps the base retriever
        # In LangChain 1.0+, retrievers are Runnable and support invoke()
        retrieval_start = time.time()
        try:
            source_docs = retriever.invoke(question)
        except (AttributeError, TypeError) as e:
            # Fallback: use the underlying base retriever
            logger.warning(f"MultiQueryRetriever.invoke failed, using base retriever: {e}")
            source_docs = base_retriever.invoke(question)
        stats['document_retrieval_time'] = time.time() - retrieval_start
        
        # Get answer from the chain
        answer_start = time.time()
        answer = rag_chain.invoke(question)
        stats['answer_generation_time'] = time.time() - answer_start
        
        response_time = time.time() - start_time
        stats['total_time'] = time.time() - overall_start
        logger.info(f"Query processed successfully. Retrieved {len(source_docs)} documents in {response_time:.2f}s")
        
        # Convert Document objects to dicts for JSON serialization
        source_docs_dict = []
        for doc in source_docs:
            if hasattr(doc, 'page_content'):
                source_docs_dict.append({
                    'page_content': doc.page_content,
                    'metadata': doc.metadata if hasattr(doc, 'metadata') else {}
                })
            elif isinstance(doc, dict):
                source_docs_dict.append(doc)
            else:
                source_docs_dict.append({
                    'page_content': str(doc),
                    'metadata': {}
                })
        
        # Cache the result if enabled (use serializable version)
        cache_store_start = time.time()
        if use_cache:
            cache = get_cache()
            cacheable_result = {
                'result': answer,
                'source_documents': source_docs_dict,  # Use dict version for caching
                'query': question
            }
            cache.set(question, cacheable_result, version, k)
        stats['cache_store_time'] = time.time() - cache_store_start
        
        query_result = {
            'result': answer,
            'source_documents': source_docs,  # Keep original for return value
            'query': question,
            'stats': stats
        }
        
        # Log to monitoring
        monitor = get_query_monitor()
        monitor.log_query(question, version, response_time=stats['total_time'],
                         source_count=len(query_result.get('source_documents', [])),
                         cached=False)
        
        return query_result
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise


def query_simple(question, collection_name=None, version=None, k=3):
    """
    Simple query without multi-query retrieval (faster but less comprehensive).
    
    Args:
        question: Natural language question
        collection_name: Name of the collection to query
        version: Optional version string
        k: Number of documents to retrieve
        
    Returns:
        dict: Query result with answer, source documents, and timing statistics
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")
    
    # Initialize timing statistics
    stats = {
        'total_time': 0.0,
        'cache_lookup_time': 0.0,
        'llm_init_time': 0.0,
        'vector_db_init_time': 0.0,
        'document_retrieval_time': 0.0,
        'answer_generation_time': 0.0,
        'cache_store_time': 0.0
    }
    overall_start = time.time()
    
    logger.info(f"Processing simple query: {question[:100]}...")
    
    # Initialize the language model
    llm_start = time.time()
    provider_config = get_active_llm_provider()
    llm = LLMProviderFactory.get_llm(provider_config['type'], provider_config)
    stats['llm_init_time'] = time.time() - llm_start
    
    # Get the vector database instance
    db_start = time.time()
    db = get_vector_db(collection_name=collection_name, version=version)
    stats['vector_db_init_time'] = time.time() - db_start
    
    # Get prompt template
    _, prompt = get_prompt()
    
    # Create simple retriever
    retriever = db.as_retriever(search_kwargs={"k": k})
    
    # Create the QA chain using LCEL
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # Execute query
    try:
        # Get source documents - try different methods based on LangChain version
        retrieval_start = time.time()
        try:
            source_docs = retriever.invoke(question)
        except (AttributeError, TypeError):
            try:
                source_docs = retriever.get_relevant_documents(question)
            except (AttributeError, TypeError):
                source_docs = []
        stats['document_retrieval_time'] = time.time() - retrieval_start
        
        # Get answer from the chain
        answer_start = time.time()
        answer = rag_chain.invoke(question)
        stats['answer_generation_time'] = time.time() - answer_start
        
        stats['total_time'] = time.time() - overall_start
        logger.info(f"Query processed successfully. Retrieved {len(source_docs)} documents in {stats['total_time']:.2f}s")
        
        # Note: source_documents are kept as Document objects for consistency
        # They will be converted to dicts in app.py for JSON serialization
        return {
            'result': answer,
            'source_documents': source_docs,
            'query': question,
            'stats': stats
        }
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise

