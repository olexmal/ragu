# RAG System for Common Model Documentation

A local Retrieval-Augmented Generation (RAG) application that provides semantic search and context-aware responses for common model documentation using Ollama, Python, and ChromaDB.

> **Quick Start**: See [QUICKSTART.md](QUICKSTART.md) for a 5-minute setup guide.

## 🎯 Features

- **Semantic Search**: Natural language queries with semantic understanding
- **Incremental Updates**: Append documents to existing collections without overwriting
- **Version-Aware**: Support for version-specific documentation collections
- **Multi-Version Querying**: Query across multiple versions simultaneously
- **Query History & Favorites**: Track and favorite frequently asked questions
- **Query Caching**: Fast responses for frequently asked questions
- **Monitoring & Analytics**: Track query patterns and system performance
- **Local Processing**: All processing happens locally for privacy and security
- **RESTful API**: Easy integration via Flask API
- **CLI Tools**: Command-line interface for embedding and querying
- **Webhook Support**: Automatic updates via webhook notifications

## 📋 Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- Minimum 8GB RAM (16GB+ recommended)
- 10GB+ free disk space for models and vector database

## 🚀 Quick Start

### 1. Install Ollama

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### 2. Download Required Models

```bash
ollama pull mistral          # LLM for generation (~4GB)
ollama pull nomic-embed-text # Embedding model (lightweight)
```

### 3. Set Up Python Environment

```bash
# Clone or navigate to the project directory
cd ragu

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration (optional - defaults work for most cases)
```

### 5. Start the RAG Server

```bash
# Using the helper script
./scripts/start-rag-server.sh

# Or manually
python3 -c "from src.app import app; app.run(host='localhost', port=8080)"
```

The API will be available at `http://localhost:8080`

## 📖 Usage

### API Endpoints

#### Health Check
```bash
curl http://localhost:8080/health
```

#### Embed a File
```bash
curl -X POST http://localhost:8080/embed \
  -F "file=@documentation.pdf" \
  -F "version=1.2.3"
```

#### Query Documentation
```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I use the UserService class?"}'
```

#### List Collections
```bash
curl http://localhost:8080/collections
```

### CLI Usage

#### Embed a File
```bash
python3 src/cli.py embed path/to/documentation.pdf --version 1.2.3
```

#### Query Documentation
```bash
python3 src/cli.py query "How does UserService work?" --version 1.2.3
```

#### List Collections
```bash
python3 src/cli.py list-collections
```

#### Check System Status
```bash
python3 src/cli.py status
```

### Maven Integration

#### Automatic Documentation Update

To automatically check for version changes and update embedded documentation:

```bash
./scripts/update-docs.sh
```

This script will:
1. Check current common model version from Maven
2. Compare with last embedded version
3. Automatically embed new documentation if version changed
4. Update version tracking file

#### Manual Documentation Embedding

To manually embed Javadoc from your common model:

```bash
./scripts/embed-commonmodel-docs.sh
```

This script will:
1. Resolve the current common model version from Maven
2. Generate Javadoc if needed
3. Embed documentation into ChromaDB with version tagging

## 🏗️ Project Structure

```
ragu/
├── src/
│   ├── __init__.py
│   ├── app.py              # Flask API server
│   ├── cli.py              # Command-line interface
│   ├── embed.py            # Document embedding logic
│   ├── query.py            # Query processing
│   ├── get_vector_db.py    # Vector database management
│   └── utils.py            # Utility functions
├── scripts/
│   ├── embed-commonmodel-docs.sh  # Maven integration script
│   └── start-rag-server.sh        # Server startup script
├── docs/                   # Documentation storage
├── tests/                  # Test files
├── _temp/                  # Temporary file storage
├── chroma/                 # ChromaDB persistence
├── requirements.txt        # Python dependencies
├── .env.example           # Environment configuration example
└── README.md              # This file
```

## 🔧 Configuration

Environment variables (in `.env`):

```bash
# Vector Database
CHROMA_PATH=./chroma
COLLECTION_NAME=common-model-docs

# Models
LLM_MODEL=mistral
TEXT_EMBEDDING_MODEL=nomic-embed-text

# API Server
API_PORT=8080
API_HOST=localhost
FLASK_DEBUG=False

# Maven Integration
MAVEN_POM_PATH=../pom.xml
COMMON_MODEL_VERSION_PROPERTY=commonmodel.version

# Authentication (Optional)
AUTH_ENABLED=false
AUTH_REQUIRED_FOR=write  # Options: 'all', 'write', 'none'
API_KEY=  # Generate with: ./scripts/generate-api-key.sh
API_KEY_HEADER=X-API-Key
```

### Enabling Authentication

To enable API authentication:

1. Generate an API key:
```bash
./scripts/generate-api-key.sh
```

2. Add to `.env`:
```bash
AUTH_ENABLED=true
AUTH_REQUIRED_FOR=write  # or 'all' for all endpoints
API_KEY=your-generated-key-here
```

3. Use the API key in requests:
```bash
curl -X POST http://localhost:8080/embed \
  -H "X-API-Key: your-generated-key-here" \
  -F "file=@documentation.pdf"
```

**Authentication Modes:**
- `AUTH_REQUIRED_FOR=all`: All endpoints require authentication
- `AUTH_REQUIRED_FOR=write`: Only write operations (POST, PUT, DELETE) require authentication
- `AUTH_REQUIRED_FOR=none` or `AUTH_ENABLED=false`: No authentication required

## 🔒 Security Features

- **Path Traversal Protection**: File paths are sanitized and validated
- **Input Validation**: All API inputs are validated
- **Error Handling**: Comprehensive error handling with appropriate HTTP status codes
- **Local Processing**: All data stays on your machine
- **API Authentication** (Optional): API key-based authentication for production use
- **Write Protection**: Configurable authentication for write operations only

## 📚 API Documentation

### POST /embed
Embed a single file into the vector database.

**Parameters:**
- `file` (multipart/form-data): File to embed
- `version` (optional): Version string for collection naming
- `overwrite` (optional): Set to "true" to replace existing collection

### POST /query
Query the documentation using natural language.

**Request Body:**
```json
{
  "query": "Your question here",
  "version": "1.2.3",
  "k": 3,
  "simple": false
}
```

### GET /collections
List all available collections.

### GET /collections/<version>
Get information about a specific versioned collection.

### DELETE /collections/<version>
Delete a specific versioned collection.

### POST /query/multi-version
Query documentation across multiple versions simultaneously.

**Request Body:**
```json
{
  "query": "How does UserService work?",
  "versions": ["1.2.3", "1.3.0"],
  "k": 3
}
```

### POST /query/compare
Compare answers across different versions.

**Request Body:**
```json
{
  "query": "How do I create a user?",
  "versions": ["1.2.3", "1.3.0", "2.0.0"],
  "k": 3
}
```

### GET /history
Get query history.

**Query Parameters:**
- `limit` (optional): Number of entries (default: 50)
- `offset` (optional): Pagination offset (default: 0)

### GET /history/search?q=<term>
Search query history.

**Query Parameters:**
- `q`: Search term (required)
- `limit` (optional): Maximum results (default: 20)

### GET /history/export?format=json|csv
Export query history.

**Query Parameters:**
- `format`: Export format - 'json' or 'csv' (default: 'json')

### GET /favorites
Get list of favorite queries.

### POST /favorites
Add a query to favorites.

**Request Body:**
```json
{
  "query": "How does UserService work?"
}
```

### DELETE /favorites
Remove a query from favorites.

**Request Body:**
```json
{
  "query": "How does UserService work?"
}
```

### GET /stats
Get system statistics including query metrics, embedding stats, and cache statistics.

**Query Parameters:**
- `days` (optional): Number of days to analyze (default: 7)

### POST /extract-code
Extract code examples from text or documentation.

**Request Body:**
```json
{
  "text": "Documentation text with code examples...",
  "language": "java"
}
```

**Response:**
```json
{
  "total_blocks": 3,
  "languages": ["java", "text"],
  "blocks": [
    {
      "code": "public class UserService {...}",
      "language": "java",
      "type": "class",
      "length": 150,
      "highlighted": "..."
    }
  ]
}
```

### GET /auth/status
Get authentication configuration status.

**Response:**
```json
{
  "enabled": true,
  "required_for": "write",
  "api_key_configured": true,
  "header_name": "X-API-Key"
}
```

## 🧪 Testing

```bash
# Run unit tests
./scripts/run-tests.sh

# Run all tests including integration tests (requires Ollama)
RUN_INTEGRATION_TESTS=1 ./scripts/run-tests.sh --integration

# Or use pytest directly
pytest tests/                    # Run all tests
pytest tests/ -m unit            # Run only unit tests
pytest tests/ -m integration     # Run only integration tests
pytest tests/ --cov=src          # With coverage report
```

Test coverage report is generated in `htmlcov/index.html` after running tests with coverage.

## 🐛 Troubleshooting

### Ollama not found
- Ensure Ollama is installed and in your PATH
- Check that `ollama serve` is running

### Models not available
- Run `ollama pull mistral` and `ollama pull nomic-embed-text`
- Verify with `ollama list`

### Import errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`

### Port already in use
- Change `API_PORT` in `.env` file
- Or stop the process using port 8080

## 📝 Development

See [RAG_IMPLEMENTATION_PLAN.md](RAG_IMPLEMENTATION_PLAN.md) for detailed implementation plan and architecture.

## 📄 License

See LICENSE file for details.

## 🙏 Acknowledgments

- Based on the guide: [Build Your Own RAG App](https://dev.to/nassermaronie/build-your-own-rag-app-a-step-by-step-guide-to-setup-llm-locally-using-ollama-python-and-chromadb-b12)
- Uses [Ollama](https://ollama.ai/) for local LLM
- Uses [ChromaDB](https://www.trychroma.com/) for vector storage
- Uses [LangChain](https://www.langchain.com/) for RAG orchestration
