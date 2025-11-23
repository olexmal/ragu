"""
Multi-Version Query Module
Enables querying across multiple documentation versions simultaneously.
"""
import os
from typing import List, Dict, Any, Optional
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_classic.retrievers import EnsembleRetriever
from langchain_classic.retrievers.multi_query import MultiQueryRetriever
from dotenv import load_dotenv
from .get_vector_db import get_vector_db
from .utils import setup_logging
from .cache import get_cache
from .monitoring import get_query_monitor
import time

load_dotenv()

LLM_MODEL = os.getenv('LLM_MODEL', 'mistral')
logger = setup_logging()


def query_multiple_versions(question: str, versions: List[str], 
                           collection_name: str = None, k: int = 3) -> Dict[str, Any]:
    """
    Query documentation across multiple versions simultaneously.
    
    Args:
        question: Natural language question
        versions: List of version strings to query
        collection_name: Base collection name
        k: Number of documents to retrieve per version
        
    Returns:
        dict: Combined results from all versions with version attribution
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")
    
    if not versions:
        raise ValueError("At least one version must be specified")
    
    logger.info(f"Multi-version query: {question[:100]}... across {len(versions)} versions")
    start_time = time.time()
    
    # Check cache
    cache_key = f"{question}_{','.join(sorted(versions))}"
    cache = get_cache()
    cached_result = cache.get(question, cache_key, k)
    if cached_result:
        logger.info(f"Returning cached multi-version result")
        return cached_result
    
    # Initialize LLM
    llm = ChatOllama(model=LLM_MODEL, temperature=0)
    
    # Get retrievers for each version
    retrievers = []
    version_dbs = {}
    
    for version in versions:
        try:
            db = get_vector_db(collection_name=collection_name, version=version)
            retriever = db.as_retriever(search_kwargs={"k": k})
            retrievers.append(retriever)
            version_dbs[version] = db
            logger.debug(f"Added retriever for version {version}")
        except Exception as e:
            logger.warning(f"Failed to get retriever for version {version}: {e}")
            continue
    
    if not retrievers:
        raise ValueError("No valid versions found to query")
    
    # Create ensemble retriever to combine results from all versions
    ensemble_retriever = EnsembleRetriever(
        retrievers=retrievers,
        weights=[1.0 / len(retrievers)] * len(retrievers)  # Equal weights
    )
    
    # Create prompt that includes version information
    template = """Answer the question based on the following context from multiple documentation versions.
    The context may include information from different versions. When relevant, indicate which version
    the information comes from.
    
    Context from multiple versions:
    {context}
    
    Question: {question}
    
    Provide a comprehensive answer that synthesizes information from all available versions.
    If information differs between versions, mention the version-specific details."""
    
    prompt = PromptTemplate.from_template(template)
    
    # Create QA chain using LCEL pattern
    from langchain_core.runnables import RunnablePassthrough
    from langchain_core.output_parsers import StrOutputParser
    
    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)
    
    # Create QA chain using LCEL
    rag_chain = (
        {"context": ensemble_retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    try:
        # Get source documents - try different methods based on LangChain version
        source_docs = None
        try:
            # Try invoke() first (LangChain 1.0+)
            source_docs = ensemble_retriever.invoke(question)
        except (AttributeError, TypeError):
            try:
                # Try get_relevant_documents (older API)
                source_docs = ensemble_retriever.get_relevant_documents(question)
            except (AttributeError, TypeError):
                # Try calling directly
                try:
                    source_docs = ensemble_retriever(question)
                except Exception:
                    # Last resort: get from individual retrievers
                    source_docs = []
                    for ret in retrievers:
                        try:
                            docs = ret.invoke(question) if hasattr(ret, 'invoke') else ret.get_relevant_documents(question)
                            source_docs.extend(docs)
                        except:
                            pass
        
        answer = rag_chain.invoke(question)
        
        result = {
            "result": answer,
            "source_documents": source_docs
        }
        response_time = time.time() - start_time
        
        # Organize source documents by version and convert to dicts for JSON serialization
        sources_by_version = {}
        for doc in result.get('source_documents', []):
            if hasattr(doc, 'metadata'):
                version = doc.metadata.get('version', 'unknown')
            else:
                version = 'unknown'
            if version not in sources_by_version:
                sources_by_version[version] = []
            sources_by_version[version].append(doc)
        
        # Convert Document objects to dicts for JSON serialization (for caching and API response)
        sources_by_version_dict = {}
        for version, docs in sources_by_version.items():
            sources_by_version_dict[version] = [
                {
                    'content': doc.page_content[:500] if hasattr(doc, 'page_content') else str(doc)[:500],
                    'metadata': doc.metadata if hasattr(doc, 'metadata') else {}
                }
                for doc in docs
            ]
        
        query_result = {
            'result': answer,
            'query': question,
            'versions_queried': versions,
            'sources_by_version': sources_by_version_dict,  # Already in dict format
            'total_sources': len(result.get('source_documents', [])),
            'response_time': response_time
        }
        
        # Cache the result (already in dict format, so JSON-serializable)
        cache.set(question, query_result, cache_key, k)
        
        # Log to monitoring
        monitor = get_query_monitor()
        monitor.log_query(question, version=','.join(versions), 
                         response_time=response_time,
                         source_count=len(result.get('source_documents', [])),
                         cached=False)
        
        logger.info(f"Multi-version query completed in {response_time:.2f}s")
        return query_result
    
    except Exception as e:
        logger.error(f"Error in multi-version query: {e}")
        raise


def compare_versions(question: str, versions: List[str], 
                    collection_name: str = None, k: int = 3) -> Dict[str, Any]:
    """
    Compare answers across different versions to see how documentation changed.
    
    Args:
        question: Natural language question
        versions: List of version strings to compare
        collection_name: Base collection name
        k: Number of documents to retrieve per version
        
    Returns:
        dict: Version-specific answers for comparison
    """
    if not question or not question.strip():
        raise ValueError("Question cannot be empty")
    
    if len(versions) < 2:
        raise ValueError("At least 2 versions required for comparison")
    
    logger.info(f"Comparing versions for query: {question[:100]}...")
    
    results_by_version = {}
    
    for version in versions:
        try:
            from .query import query_docs
            result = query_docs(question, collection_name=collection_name, 
                             version=version, k=k, use_cache=True)
            results_by_version[version] = {
                'answer': result['result'],
                'source_count': len(result.get('source_documents', [])),
                'sources': [
                    {
                        'content': doc.page_content[:300],
                        'metadata': doc.metadata
                    }
                    for doc in result.get('source_documents', [])[:3]  # Top 3 per version
                ]
            }
        except Exception as e:
            logger.warning(f"Failed to query version {version}: {e}")
            results_by_version[version] = {
                'error': str(e),
                'answer': None
            }
    
    return {
        'query': question,
        'versions_compared': versions,
        'results_by_version': results_by_version
    }

