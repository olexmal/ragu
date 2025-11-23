"""
Query Module
Processes natural language queries and retrieves relevant documentation.
"""
import os
import time
from langchain_ollama import ChatOllama
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
        dict: Query result with answer and source documents
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")
    
    # Check cache if enabled
    cached = False
    if use_cache is None:
        use_cache = USE_CACHE
    
    if use_cache:
        cache = get_cache()
        cached_result = cache.get(question, version, k)
        if cached_result:
            logger.info(f"Returning cached result for: {question[:100]}...")
            cached = True
            # Log to monitoring
            monitor = get_query_monitor()
            monitor.log_query(question, version, response_time=0.0, 
                            source_count=len(cached_result.get('source_documents', [])), 
                            cached=True)
            return cached_result
    
    logger.info(f"Processing query: {question[:100]}...")
    start_time = time.time()
    
    # Initialize the language model
    llm = ChatOllama(model=LLM_MODEL, temperature=0)
    
    # Get the vector database instance
    db = get_vector_db(collection_name=collection_name, version=version)
    
    # Get the prompt templates
    QUERY_PROMPT, prompt = get_prompt()
    
    # Set up the retriever with multi-query support
    base_retriever = db.as_retriever(search_kwargs={"k": k})
    retriever = MultiQueryRetriever.from_llm(
        retriever=base_retriever,
        llm=llm,
        prompt=QUERY_PROMPT
    )
    
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
        try:
            source_docs = retriever.invoke(question)
        except (AttributeError, TypeError) as e:
            # Fallback: use the underlying base retriever
            logger.warning(f"MultiQueryRetriever.invoke failed, using base retriever: {e}")
            source_docs = base_retriever.invoke(question)
        
        # Get answer from the chain
        answer = rag_chain.invoke(question)
        response_time = time.time() - start_time
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
        
        query_result = {
            'result': answer,
            'source_documents': source_docs,  # Keep original for return value
            'query': question
        }
        
        # Cache the result if enabled (use serializable version)
        if use_cache:
            cache = get_cache()
            cacheable_result = {
                'result': answer,
                'source_documents': source_docs_dict,  # Use dict version for caching
                'query': question
            }
            cache.set(question, cacheable_result, version, k)
        
        # Log to monitoring
        monitor = get_query_monitor()
        monitor.log_query(question, version, response_time=response_time,
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
        dict: Query result with answer and source documents
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")
    
    logger.info(f"Processing simple query: {question[:100]}...")
    
    # Initialize the language model
    llm = ChatOllama(model=LLM_MODEL, temperature=0)
    
    # Get the vector database instance
    db = get_vector_db(collection_name=collection_name, version=version)
    
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
        try:
            source_docs = retriever.invoke(question)
        except (AttributeError, TypeError):
            try:
                source_docs = retriever.get_relevant_documents(question)
            except (AttributeError, TypeError):
                source_docs = []
        answer = rag_chain.invoke(question)
        
        logger.info(f"Query processed successfully. Retrieved {len(source_docs)} documents")
        
        # Note: source_documents are kept as Document objects for consistency
        # They will be converted to dicts in app.py for JSON serialization
        return {
            'result': answer,
            'source_documents': source_docs,
            'query': question
        }
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise

