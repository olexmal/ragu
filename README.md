# 🚀 RAGU - Retrieval-Augmented Generation Universal

<div align="center">

**RAGU (Retrieval-Augmented Generation Universal) - A modern, local RAG application with a beautiful web interface**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Angular](https://img.shields.io/badge/Angular-19+-red.svg)](https://angular.io/)
[![Ollama](https://img.shields.io/badge/Ollama-Required-orange.svg)](https://ollama.ai/)
[![License](https://img.shields.io/badge/License-See%20LICENSE-green.svg)](LICENSE)

[Quick Start](#-quick-start) • [Features](#-features) • [Documentation](#-documentation) • [API Reference](docs/API_REFERENCE.md) • [Task Tracking](.github/TASK_TRACKING.md)

</div>

---

## ✨ Overview

RAGU (Retrieval-Augmented Generation Universal) is a powerful, privacy-focused documentation search and query platform that enables semantic search across your documentation using local AI models. With a modern Angular web interface, you can upload documents, import from Confluence, query your knowledge base, and manage collections—all while keeping your data completely local.

### 🎯 Key Highlights

- 🌐 **Modern Web UI** - Beautiful, intuitive interface built with Angular
- 📄 **Document Upload** - Support for PDF, HTML, TXT, Markdown, and more
- 🔗 **Confluence Integration** - Import pages directly from Confluence
- 🔍 **Semantic Search** - Natural language queries with context-aware responses
- 📊 **Version Management** - Track and query multiple documentation versions
- 🔒 **Privacy First** - All processing happens locally on your machine
- ⚡ **Fast & Efficient** - Query caching and optimized retrieval

---

## 📸 Screenshots

<div align="center">

![Chat Playground](docs/images/start_page.png)

*Chat Playground - Interactive chat interface for querying your documentation with natural language*

![Admin Dashboard](docs/images/admin_dashboard.png)

*Admin Dashboard - System overview and quick actions*

![System Monitoring](docs/images/system_monitoring.png)

*System Monitoring - Query analytics and performance metrics*

</div>

---

## 🎯 Features

### Core Capabilities

- **📤 Document Upload & Import**
  - Upload multiple file formats (PDF, HTML, TXT, Markdown)
  - Import Confluence pages via page ID or URL
  - **Web Scraping**: Crawl and embed entire documentation sites
  - Batch processing for multiple files
  - Incremental updates without data loss

- **🔍 Intelligent Querying**
  - Natural language question answering
  - Multi-version querying across documentation versions
  - Version comparison for tracking changes
  - Query history and favorites management
  - Source citations with document references

- **📊 Management & Monitoring**
  - Collection management with version tracking
  - Query analytics and statistics
  - Performance monitoring
  - Export query history (JSON/CSV)

- **⚙️ Configuration & Integration**
  - Multiple LLM provider support (Ollama, OpenAI, Anthropic, Azure, Google, OpenRouter)
  - Configurable embedding providers (Ollama, OpenRouter, OpenAI, Azure, Google)
  - OpenRouter support for both LLM and embeddings (OpenAI-compatible API)
  - Confluence integration settings
  - System settings management
  - Optional API authentication

### Web Interface Features

- **🎨 Modern UI/UX**
  - Clean, responsive design
  - Intuitive navigation
  - Real-time feedback
  - Helpful tooltips and icons
  - Error handling with clear messages

- **📱 Pages**
  - **Chat Playground** - Interactive chat interface for querying documentation
  - **History** - View and rerun previous queries
  - **Dashboard** - System overview and quick actions
  - **Upload & Import** - Document upload and Confluence import
  - **Collections** - Manage your document collections
  - **Monitoring** - System statistics and analytics
  - **Settings** - Configure LLM providers, Confluence, and system settings

---

## 📋 Prerequisites

Before you begin, ensure you have:

- **Python 3.8+** installed
- **Node.js 18+** and **npm** (for web UI)
- **[Ollama](https://ollama.ai/)** installed and running
- **Minimum 8GB RAM** (16GB+ recommended)
- **10GB+ free disk space** for models and vector database

---

## 🚀 Quick Start

### 1. Install Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
```

### 2. Download Required Models

```bash
# Download LLM for generation (~4GB)
ollama pull mistral

# Download embedding model (lightweight)
ollama pull nomic-embed-text

# Verify models
ollama list
```

### 3. Set Up Backend

```bash
# Navigate to project directory
cd ragu

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Set Up Web UI

```bash
# Navigate to web UI directory
cd web-ui

# Install Node.js dependencies
npm install

# Build the application
npm run build

# Or run in development mode
npm start
```

### 5. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration (optional - defaults work for most cases)
```

### 6. Start the System

**Option A: Start Backend Only (API)**
```bash
# Using helper script
./scripts/start-rag-server.sh

# Or manually
python3 -c "from src.app import app; app.run(host='localhost', port=8080)"
```

**Option B: Start with Web UI**
```bash
# Terminal 1: Start backend API
./scripts/start-rag-server.sh

# Terminal 2: Start web UI (development)
cd web-ui
npm start
```

The API will be available at `http://localhost:8080`  
The web UI will be available at `http://localhost:4200` (development) or served from the backend (production)

---

## 📖 Usage

### Web Interface

1. **Access the Web UI**: Open `http://localhost:4200` in your browser
2. **Upload Documents**: Navigate to "Upload & Import" → "Upload Documents" tab
3. **Import from Confluence**: Use "Confluence Import" tab (configure Confluence settings first)
4. **Query Documentation**: Go to "Query" page and ask questions
5. **Manage Collections**: View and manage collections in "Collections" page

### API Usage

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

#### Import from Confluence
```bash
curl -X POST http://localhost:8080/confluence/import \
  -H "Content-Type: application/json" \
  -d '{
    "page_id": "123456",
    "version": "1.2.3",
    "overwrite": false
  }'
```

#### Query Documentation
```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I use the UserService class?",
    "version": "1.2.3",
    "k": 3
  }'
```

### CLI Usage

```bash
# Embed a file
python3 src/cli.py embed path/to/documentation.pdf --version 1.2.3

# Query documentation
python3 src/cli.py query "How does UserService work?" --version 1.2.3

# List collections
python3 src/cli.py list-collections

# Check system status
python3 src/cli.py status
```

---

## 🏗️ Project Structure

```
ragu/
├── src/                          # Backend Python code
│   ├── app.py                   # Flask API server
│   ├── cli.py                   # Command-line interface
│   ├── embed.py                 # Document embedding logic
│   ├── query.py                 # Query processing
│   ├── get_vector_db.py         # Vector database management
│   ├── settings.py              # Settings management
│   ├── llm_providers.py         # LLM provider abstraction
│   ├── confluence.py            # Confluence integration
│   └── ...
├── web-ui/                      # Frontend Angular application
│   ├── src/
│   │   ├── app/
│   │   │   ├── features/        # Feature modules
│   │   │   │   ├── admin/       # Admin features (dashboard, upload, collections, etc.)
│   │   │   │   ├── query/       # Query interface
│   │   │   │   └── auth/        # Authentication
│   │   │   ├── core/            # Core services and state
│   │   │   ├── layout/          # Layout components
│   │   │   └── shared/          # Shared components
│   │   └── ...
│   └── ...
├── scripts/                     # Utility scripts
│   ├── start-rag-server.sh      # Server startup
│   ├── embed-commonmodel-docs.sh # Maven integration
│   └── ...
├── docs/                        # Documentation
│   ├── API_REFERENCE.md         # Complete API documentation
│   └── DEVELOPER_GUIDE.md      # Developer guide
├── tests/                       # Test files
├── chroma/                      # ChromaDB persistence
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment configuration example
└── README.md                    # This file
```

---

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

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

# Authentication (Optional)
AUTH_ENABLED=false
AUTH_REQUIRED_FOR=write  # Options: 'all', 'write', 'none'
API_KEY=
API_KEY_HEADER=X-API-Key

# Session Security
SECRET_KEY=your-secret-key-here
SESSION_SECURE=false  # Set to true for HTTPS
```

### Web UI Configuration

The web UI connects to the backend API. Configure the API URL in `web-ui/src/environments/environment.ts`:

```typescript
export const environment = {
  apiUrl: 'http://localhost:8080'
};
```

### Confluence Integration

Configure Confluence settings via the web UI (Settings → Confluence Integration) or via API:

```bash
curl -X POST http://localhost:8080/settings/confluence \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-domain.atlassian.net",
    "username": "your-email@example.com",
    "api_token": "your-api-token"
  }'
```

---

## 🔒 Security Features

- **Path Traversal Protection** - File paths are sanitized and validated
- **Input Validation** - All API inputs are validated before processing
- **Error Handling** - Comprehensive error handling with appropriate HTTP status codes
- **Local Processing** - All data stays on your machine
- **API Authentication** (Optional) - API key-based authentication for production use
- **Write Protection** - Configurable authentication for write operations only
- **Session Security** - Secure session management for web UI

---

## 📚 Documentation

### Quick Links

- **[Quick Start Guide](QUICKSTART.md)** - Get up and running in 5 minutes
- **[API Reference](docs/API_REFERENCE.md)** - Complete API endpoint documentation
- **[Developer Guide](docs/DEVELOPER_GUIDE.md)** - Architecture and extension guide
- **[Changelog](CHANGELOG.md)** - Version history and changes

### Key Endpoints

- `POST /embed` - Embed a single file
- `POST /embed-batch` - Embed multiple files
- `POST /confluence/import` - Import Confluence page
- `POST /query` - Query documentation
- `POST /query/multi-version` - Query across multiple versions
- `GET /collections` - List all collections
- `GET /stats` - System statistics
- `GET /history` - Query history

For complete API documentation, see [API_REFERENCE.md](docs/API_REFERENCE.md).

---

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

---

## 🐛 Troubleshooting

### Common Issues

**Ollama not found**
- Ensure Ollama is installed and in your PATH
- Check that `ollama serve` is running
- Verify with `ollama list`

**Models not available**
- Run `ollama pull mistral` and `ollama pull nomic-embed-text`
- Verify with `ollama list`

**Import errors**
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt`
- Check Python version: `python3 --version` (requires 3.8+)

**Port already in use**
- Change `API_PORT` in `.env` file
- Or stop the process using port 8080

**Web UI not connecting to backend**
- Verify backend is running on the configured port
- Check CORS settings if accessing from different origin
- Verify API URL in environment configuration

**Confluence import fails**
- Verify Confluence settings are configured correctly
- Check that `confluence-markdown-exporter` is installed: `pip install confluence-markdown-exporter==1.0.4`
- Ensure API token has read permissions for the page

---

## 🛠️ Development

### Running in Development Mode

**Backend:**
```bash
# Activate virtual environment
source venv/bin/activate

# Run with auto-reload
FLASK_DEBUG=True python3 -c "from src.app import app; app.run(host='localhost', port=8080, debug=True)"
```

**Frontend:**
```bash
cd web-ui
npm start
# Access at http://localhost:4200
```

### Building for Production

**Backend:**
```bash
# No build step needed - Python runs directly
# Use production WSGI server like gunicorn:
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8080 "src.app:app"
```

**Frontend:**
```bash
cd web-ui
npm run build
# Output in web-ui/dist/
```

---

## 📄 License

See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Based on the guide: [Build Your Own RAG App](https://dev.to/nassermaronie/build-your-own-rag-app-a-step-by-step-guide-to-setup-llm-locally-using-ollama-python-and-chromadb-b12)
- Uses [Ollama](https://ollama.ai/) for local LLM
- Uses [ChromaDB](https://www.trychroma.com/) for vector storage
- Uses [LangChain](https://www.langchain.com/) for RAG orchestration
- Uses [Angular](https://angular.io/) for the web interface

---

<div align="center">

**Made with ❤️ for developers who value privacy and local processing**

[Report Bug](https://github.com/your-org/ragu/issues) • [Request Feature](https://github.com/your-org/ragu/issues) • [Documentation](docs/)

</div>
