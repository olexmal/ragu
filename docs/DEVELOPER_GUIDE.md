# RAG System Developer Guide

## Architecture Overview

The RAG system is built with a modular architecture that separates concerns into distinct components:

```
┌─────────────────────────────────────────────────────────────┐
│                      API Layer (app.py)                     │
│  - RESTful endpoints                                        │
│  - Request validation                                       │
│  - Security controls                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
┌───────▼────────┐          ┌─────────▼─────────┐
│  Query Module  │          │  Embed Module     │
│  (query.py)    │          │  (embed.py)       │
│                │          │                   │
│  - RAG chain   │          │  - Document load  │
│  - Caching     │          │  - Chunking       │
│  - Monitoring  │          │  - Embedding      │
└───────┬────────┘          └─────────┬─────────┘
        │                             │
        └──────────────┬──────────────┘
                       │
            ┌──────────▼──────────┐
            │  Vector Database    │
            │  (get_vector_db.py) │
            │  - ChromaDB         │
            │  - Collections      │
            └─────────────────────┘
```

## Core Components

### 1. Vector Database (`get_vector_db.py`)

**Purpose**: Manages ChromaDB connections and collections.

**Key Functions**:
- `get_vector_db()`: Get or create a ChromaDB instance
- `get_or_create_collection()`: Check if collection exists before creating

**Usage**:
```python
from src.get_vector_db import get_vector_db

# Get default collection
db = get_vector_db()

# Get version-specific collection
db = get_vector_db(version="1.2.3")
```

### 2. Embedding Module (`embed.py`)

**Purpose**: Processes documents and embeds them into the vector database.

**Key Features**:
- Supports multiple formats (PDF, HTML, TXT, Markdown)
- Incremental updates (appends to existing collections)
- Version-aware collection naming
- Automatic chunking with overlap

**Usage**:
```python
from src.embed import embed_file, embed_directory

# Embed single file
db = embed_file("documentation.pdf", version="1.2.3")

# Embed directory
results = embed_directory("./docs", version="1.2.3")
```

### 3. Query Module (`query.py`)

**Purpose**: Processes natural language queries using RAG.

**Key Features**:
- Multi-query retrieval (generates alternative queries)
- Caching support
- Monitoring integration
- Version-aware querying

**Usage**:
```python
from src.query import query_docs, query_simple

# Full RAG query with multi-query
result = query_docs("How does UserService work?", version="1.2.3")

# Simple query (faster)
result = query_simple("What is UserService?", version="1.2.3")
```

### 4. Caching Module (`cache.py`)

**Purpose**: Caches query results to improve performance.

**Features**:
- File-based caching
- TTL (Time To Live) support
- Automatic cache size management
- Cache statistics

**Configuration**:
```bash
# .env
USE_CACHE=true
CACHE_TTL=3600  # 1 hour
CACHE_MAX_SIZE=100
CACHE_DIR=./.rag_cache
```

### 5. Monitoring Module (`monitoring.py`)

**Purpose**: Tracks query patterns and embedding operations.

**Features**:
- Query logging
- Embedding operation tracking
- Statistics generation
- Performance metrics

**Usage**:
```python
from src.monitoring import get_query_monitor, get_embedding_monitor

# Get query statistics
monitor = get_query_monitor()
stats = monitor.get_query_stats(days=7)

# Get embedding statistics
embed_monitor = get_embedding_monitor()
embed_stats = embed_monitor.get_embedding_stats(days=7)
```

## Extension Points

### Adding New Document Loaders

To support additional document formats:

1. Add loader import in `embed.py`:
```python
from langchain_community.document_loaders import YourCustomLoader
```

2. Update format detection in `utils.py`:
```python
def detect_document_format(file_path):
    # ... existing code ...
    format_map = {
        # ... existing formats ...
        '.yourformat': 'yourformat'
    }
```

3. Add loader logic in `embed_file()`:
```python
elif doc_format == 'yourformat':
    loader = YourCustomLoader(str(file_path))
```

### Adding Custom Retrievers

To customize retrieval behavior:

```python
from src.query import query_docs
from langchain.retrievers import YourCustomRetriever

# Modify query.py to accept custom retriever
def query_docs(question, retriever=None, ...):
    if retriever is None:
        # Use default retriever
    else:
        # Use custom retriever
```

### Adding New API Endpoints

1. Add endpoint in `app.py`:
```python
@app.route('/your-endpoint', methods=['POST'])
def your_endpoint():
    # Implementation
    return jsonify({"result": "..."}), 200
```

2. Update API documentation in README.md

### Customizing Prompts

Modify prompt templates in `query.py`:

```python
def get_prompt():
    template = """Your custom prompt template here:
    {context}
    Question: {question}
    """
    prompt = PromptTemplate.from_template(template)
    return QUERY_PROMPT, prompt
```

## Performance Tuning

### Chunk Size Optimization

Adjust chunk size based on your documents:

```python
# In embed.py
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1500,  # Increase for longer context
    chunk_overlap=300  # Increase for better context continuity
)
```

### Retrieval Parameters

Adjust retrieval parameters:

```python
# In query.py
retriever = db.as_retriever(
    search_kwargs={
        "k": 5,  # More documents for comprehensive answers
        "score_threshold": 0.7  # Minimum similarity score
    }
)
```

### Caching Strategy

Optimize cache settings:

```bash
# .env
CACHE_TTL=7200  # 2 hours for stable documentation
CACHE_MAX_SIZE=200  # More entries for larger teams
```

## Testing

### Running Tests

```bash
# Unit tests only
pytest tests/ -m unit

# Integration tests (requires Ollama)
RUN_INTEGRATION_TESTS=1 pytest tests/ -m integration

# With coverage
pytest tests/ --cov=src --cov-report=html
```

### Writing New Tests

1. Create test file in `tests/`:
```python
# tests/test_your_feature.py
import pytest
from src.your_module import your_function

def test_your_function():
    result = your_function()
    assert result is not None
```

2. Add appropriate markers:
```python
@pytest.mark.unit
def test_unit_feature():
    ...

@pytest.mark.integration
def test_integration_feature():
    ...
```

## Debugging

### Enable Debug Logging

```python
# In utils.py or your module
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check System Status

```bash
# CLI
python3 src/cli.py status

# API
curl http://localhost:8080/health
```

### View Monitoring Data

```bash
# Query statistics
curl http://localhost:8080/stats?days=7

# Cache statistics
python3 -c "from src.cache import get_cache; print(get_cache().stats())"
```

## Best Practices

### 1. Version Management
- Always use version-specific collections for production
- Track versions in `.rag-versions.json`
- Clean up old versions periodically

### 2. Error Handling
- Always wrap external calls in try-except
- Log errors with context
- Return meaningful error messages to users

### 3. Performance
- Use caching for frequently asked queries
- Monitor query patterns to optimize
- Batch embedding operations when possible

### 4. Security
- Always validate and sanitize file paths
- Validate all API inputs
- Use environment variables for sensitive config

### 5. Testing
- Write unit tests for all new features
- Test edge cases and error conditions
- Maintain test coverage above 80%

## Troubleshooting

### Common Issues

**Issue**: Collection not found
- **Solution**: Check collection name and version
- **Debug**: `python3 src/cli.py list-collections`

**Issue**: Slow queries
- **Solution**: Enable caching, check Ollama performance
- **Debug**: Check monitoring stats for response times

**Issue**: Embedding fails
- **Solution**: Check file format support, verify Ollama models
- **Debug**: Check logs in `ragu.log`

**Issue**: Cache not working
- **Solution**: Verify `USE_CACHE=true` in `.env`
- **Debug**: Check cache directory permissions

## Contributing

When adding new features:

1. Update relevant documentation
2. Add tests for new functionality
3. Update `.env.example` if adding new config
4. Follow existing code style
5. Update CHANGELOG if applicable

## Resources

- [LangChain Documentation](https://python.langchain.com/)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [Ollama Documentation](https://ollama.ai/docs)
- [RAG Implementation Plan](./RAG_IMPLEMENTATION_PLAN.md)

