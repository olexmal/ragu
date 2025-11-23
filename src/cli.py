#!/usr/bin/env python3
"""
Command-Line Interface for RAG System
"""
import argparse
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from embed import embed_file, embed_directory
from query import query_docs, query_simple
from get_vector_db import get_vector_db
from utils import get_maven_version, setup_logging, generate_collection_name

logger = setup_logging()


def cmd_embed(args):
    """Embed a file or directory."""
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"Error: File or directory not found: {file_path}")
        return 1
    
    try:
        if file_path.is_file():
            embed_file(
                str(file_path),
                version=args.version,
                overwrite=args.overwrite
            )
            print(f"Successfully embedded: {file_path}")
        elif file_path.is_dir():
            results = embed_directory(
                str(file_path),
                version=args.version,
                overwrite=args.overwrite
            )
            print(f"Embedding complete: {results['success']} succeeded, {results['failed']} failed")
            if results['errors']:
                print("\nErrors:")
                for error in results['errors']:
                    print(f"  - {error['file']}: {error['error']}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Embedding failed: {e}", exc_info=True)
        return 1


def cmd_query(args):
    """Query the documentation."""
    try:
        if args.simple:
            result = query_simple(
                args.question,
                version=args.version,
                k=args.k
            )
        else:
            result = query_docs(
                args.question,
                version=args.version,
                k=args.k
            )
        
        print("\n" + "="*80)
        print("ANSWER:")
        print("="*80)
        print(result['result'])
        print("\n" + "="*80)
        print(f"SOURCES ({len(result['source_documents'])} documents):")
        print("="*80)
        for i, doc in enumerate(result['source_documents'], 1):
            print(f"\n[{i}] {doc.metadata.get('source_file', 'Unknown')}")
            print("-" * 80)
            print(doc.page_content[:300] + "..." if len(doc.page_content) > 300 else doc.page_content)
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        logger.error(f"Query failed: {e}", exc_info=True)
        return 1


def cmd_update_docs(args):
    """Update documentation from Maven."""
    version = args.version or get_maven_version()
    
    if not version:
        print("Error: Could not determine version. Specify with --version")
        return 1
    
    print(f"Updating documentation for version: {version}")
    
    # This would call the embed-commonmodel-docs.sh script logic
    # For now, just print instructions
    print(f"Run: ./scripts/embed-commonmodel-docs.sh")
    return 0


def cmd_list_collections(args):
    """List all collections."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=os.getenv('CHROMA_PATH', 'chroma'))
        collections = client.list_collections()
        
        if not collections:
            print("No collections found.")
            return 0
        
        print(f"\nFound {len(collections)} collection(s):\n")
        for collection in collections:
            print(f"  - {collection.name} ({collection.count()} documents)")
        
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def cmd_status(args):
    """Show system status."""
    print("RAG System Status")
    print("=" * 80)
    
    # Check Ollama
    try:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model=os.getenv('LLM_MODEL', 'mistral'))
        print("✓ Ollama: Available")
    except Exception as e:
        print(f"✗ Ollama: Not available ({e})")
    
    # Check ChromaDB
    try:
        import chromadb
        client = chromadb.PersistentClient(path=os.getenv('CHROMA_PATH', 'chroma'))
        collections = client.list_collections()
        print(f"✓ ChromaDB: Available ({len(collections)} collections)")
        
        # Show collection details
        if collections:
            print("\nCollections:")
            for collection in collections:
                print(f"  - {collection.name}: {collection.count()} documents")
    except Exception as e:
        print(f"✗ ChromaDB: Not available ({e})")
    
    # Check version
    version = get_maven_version()
    if version:
        print(f"\n✓ Common Model Version: {version}")
    else:
        print("\n✗ Common Model Version: Could not determine")
    
    # Check cache
    try:
        from cache import get_cache
        cache = get_cache()
        stats = cache.stats()
        print(f"\n✓ Cache: {stats['entries']} entries ({stats['total_size_mb']} MB)")
    except Exception as e:
        print(f"\n✗ Cache: Not available ({e})")
    
    # Check monitoring
    try:
        from monitoring import get_query_monitor, get_embedding_monitor
        query_monitor = get_query_monitor()
        query_stats = query_monitor.get_query_stats(days=7)
        print(f"\n✓ Monitoring: {query_stats.get('total_queries', 0)} queries tracked (7 days)")
    except Exception as e:
        print(f"\n✗ Monitoring: Not available ({e})")
    
    return 0


def cmd_delete_collection(args):
    """Delete a collection by version."""
    try:
        import chromadb
        from utils import generate_collection_name
        
        client = chromadb.PersistentClient(path=os.getenv('CHROMA_PATH', 'chroma'))
        collection_name = generate_collection_name(
            os.getenv('COLLECTION_NAME', 'common-model-docs'),
            args.version
        )
        
        client.delete_collection(name=collection_name)
        print(f"✓ Deleted collection: {collection_name}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


def main():
    parser = argparse.ArgumentParser(description='RAG System CLI')
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Embed command
    embed_parser = subparsers.add_parser('embed', help='Embed a file or directory')
    embed_parser.add_argument('file', help='File or directory to embed')
    embed_parser.add_argument('--version', help='Version string for collection')
    embed_parser.add_argument('--overwrite', action='store_true', help='Overwrite existing collection')
    
    # Embed directory command (alias)
    embed_dir_parser = subparsers.add_parser('embed-dir', help='Embed all files in a directory')
    embed_dir_parser.add_argument('directory', help='Directory to embed')
    embed_dir_parser.add_argument('--version', help='Version string for collection')
    embed_dir_parser.add_argument('--overwrite', action='store_true', help='Overwrite existing collection')
    
    # Query command
    query_parser = subparsers.add_parser('query', help='Query the documentation')
    query_parser.add_argument('question', help='Question to ask')
    query_parser.add_argument('--version', help='Version to query')
    query_parser.add_argument('--k', type=int, default=3, help='Number of documents to retrieve')
    query_parser.add_argument('--simple', action='store_true', help='Use simple query (faster)')
    
    # Update docs command
    update_parser = subparsers.add_parser('update-docs', help='Update documentation from Maven')
    update_parser.add_argument('--version', help='Version to embed (default: from Maven)')
    
    # List collections command
    list_parser = subparsers.add_parser('list-collections', help='List all collections')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show system status')
    
    # Delete collection command
    delete_parser = subparsers.add_parser('delete-collection', help='Delete a collection')
    delete_parser.add_argument('version', help='Version of collection to delete')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    commands = {
        'embed': cmd_embed,
        'embed-dir': lambda a: cmd_embed(type('args', (), {'file': a.directory, 'version': a.version, 'overwrite': a.overwrite})()),
        'query': cmd_query,
        'update-docs': cmd_update_docs,
        'list-collections': cmd_list_collections,
        'status': cmd_status,
        'delete-collection': lambda a: cmd_delete_collection(a)
    }
    
    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())

