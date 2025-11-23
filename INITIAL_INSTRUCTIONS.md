# Summary: Using Docs MCP Server for Dynamic Common Model Integration

## 🎯 Problem Statement
- **Goal**: Use `docs-mcp-server` to provide GitHub Copilot with context about generated Java code from a common model package (`com.company.commonmodel.*`)
- **Challenge**: Common model updates 3+ times daily, all components use same version via Maven property
- **Constraint**: Cannot trigger CI/CD cascades that would cause unnecessary compilations

## ✅ Primary Solution: MCP Server Integration

### Configuration
```json
// .vscode/mcp.json
{
  "mcpServers": {
    "docs-mcp": {
      "command": "uvx",
      "args": ["docs-mcp-server"]
    }
  }
}
```

### Dynamic Version Handling
- **Real-time version resolution** using Maven command:
  ```bash
  mvn help:evaluate -Dexpression=commonmodel.version -q -DforceStdout
  ```
- **No CI/CD triggers** - version resolved locally at query time

### Copilot Instructions
```markdown
# .github/copilot-instructions.md
When using `com.company.commonmodel.*` classes:
1. Check current version: `mvn help:evaluate -Dexpression=commonmodel.version -q -DforceStdout`
2. Query docs-mcp-server: "Search [ClassName] - version $(current_version)"
3. All components use same version via `${commonmodel.version}` property
```

## 🔄 Alternative Solutions (When MCP Not Available)

### Option 1: Documentation Pre-generation
```bash
# Generate current documentation
mvn javadoc:javadoc
# Copy to consistent location
cp -r target/site/apidocs ./docs/current-common-model/
```

**Instructions for Copilot**:
```markdown
# Common Model Reference
- Generated documentation available at: `./docs/current-common-model/`
- Current version: $(mvn help:evaluate -Dexpression=commonmodel.version -q -DforceStdout)
- Always check version before implementing common model interfaces
```

### Option 2: Git Submodule with Documentation
```bash
# Add common model as submodule
git submodule add https://github.com/company/common-model.git
# Generate docs locally
cd common-model && mvn javadoc:javadoc
```

**Instructions**:
```markdown
# Common Model Access
- Source available in: `./common-model/`
- Documentation: `./common-model/target/site/apidocs/`
- Version tracked via git submodule reference
```

### Option 3: Local Maven Repository with Documentation
```bash
# Install common model with sources
mvn install:install-file -Dfile=common-model.jar \
  -Dsources=common-model-sources.jar \
  -Djavadoc=common-model-javadoc.jar
```

**Instructions**:
```markdown
# Common Model Usage
- Available via Maven: `com.company:common-model:${commonmodel.version}`
- Sources and Javadoc attached in local repository
- Use IDE's "Download Sources" feature for inspection
```

### Option 4: Custom Documentation Server
```bash
# Run simple HTTP server with docs
python -m http.server 8000 --directory ./docs/current-common-model/
```

**Instructions**:
```markdown
# Common Model Documentation
- Available at: http://localhost:8000
- Update docs: `./scripts/update-commonmodel-docs.sh`
- Version: $(cat .commonmodel-version)
```

### Option 5: IDE-specific Solutions

**VS Code Workspace Settings**:
```json
{
  "files.watcherExclude": {
    "**/common-model/**": true
  },
  "java.configuration.updateBuildConfiguration": "disabled"
}
```

**Project-specific Instructions**:
```markdown
# Project Setup
- Common model version: ${commonmodel.version}
- Documentation: Internal network share //docs/commonmodel/current/
- Update: Run `./scripts/sync-commonmodel.sh` when version changes
```

### Option 6: Local RAG Application with Ollama and ChromaDB

A **Retrieval-Augmented Generation (RAG)** application provides semantic search and context-aware responses from your documentation. This approach embeds documentation into a vector database and uses a local LLM to answer questions about the common model.

#### What is RAG?

RAG combines information retrieval with text generation:
- **Retrieval**: Searches relevant documentation snippets from a vector store based on semantic similarity
- **Generation**: Uses a local language model to generate contextually relevant answers
- **Benefits**: Enhanced accuracy, contextual relevance, and complete privacy (all processing happens locally)

#### Setup Requirements

**Prerequisites**:
- Python 3.x
- [Ollama](https://ollama.ai/) installed locally
- ChromaDB for vector storage
- Required Python packages: `langchain`, `langchain-community`, `chromadb`, `ollama`

**Installation**:
```bash
# Install Ollama (if not already installed)
curl -fsSL https://ollama.ai/install.sh | sh

# Pull required models
ollama pull mistral          # For LLM generation
ollama pull nomic-embed-text # For text embeddings

# Install Python dependencies
pip install langchain langchain-community langchain-core chromadb ollama flask werkzeug python-dotenv
```

#### Implementation Structure

**1. Embed Documentation** (`embed.py`):
```python
import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OllamaEmbeddings
from langchain_community.vectorstores.chroma import Chroma

CHROMA_PATH = os.getenv('CHROMA_PATH', 'chroma')
COLLECTION_NAME = os.getenv('COLLECTION_NAME', 'common-model-docs')
TEXT_EMBEDDING_MODEL = os.getenv('TEXT_EMBEDDING_MODEL', 'nomic-embed-text')

def get_or_create_collection(collection_name, embedding_function):
    """Get existing collection or create new one if it doesn't exist."""
    try:
        # Try to load existing collection
        db = Chroma(
            collection_name=collection_name,
            persist_directory=CHROMA_PATH,
            embedding_function=embedding_function
        )
        # Verify collection exists by checking if it has any documents
        # This will raise an error if collection doesn't exist
        _ = db._collection.count()
        return db, True  # Collection exists
    except Exception:
        # Collection doesn't exist, will be created when adding documents
        return None, False

def embed_file(file_path, collection_name=None, version=None, overwrite=False):
    """
    Embed a file into ChromaDB with support for incremental updates.
    
    Args:
        file_path: Path to the file to embed
        collection_name: Name of the collection (defaults to COLLECTION_NAME)
        version: Optional version string for version-specific collections
        overwrite: If True, delete existing collection before embedding
    """
    # Determine collection name
    if version:
        final_collection_name = f"{collection_name or COLLECTION_NAME}-v{version}"
    else:
        final_collection_name = collection_name or COLLECTION_NAME
    
    # Load document (supports PDF, TXT, etc.)
    if file_path.endswith('.pdf'):
        loader = PyPDFLoader(file_path)
    else:
        loader = TextLoader(file_path)
    
    documents = loader.load()
    
    # Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200
    )
    chunks = text_splitter.split_documents(documents)
    
    # Add metadata to chunks
    for chunk in chunks:
        chunk.metadata = chunk.metadata or {}
        chunk.metadata['source_file'] = file_path
        if version:
            chunk.metadata['version'] = version
    
    # Create embeddings
    embedding = OllamaEmbeddings(model=TEXT_EMBEDDING_MODEL)
    
    # Handle collection creation or update
    if overwrite:
        # Delete existing collection if it exists
        try:
            existing_db = Chroma(
                collection_name=final_collection_name,
                persist_directory=CHROMA_PATH,
                embedding_function=embedding
            )
            existing_db.delete_collection()
        except Exception:
            pass  # Collection doesn't exist, continue
        # After deletion, always create new collection
        db = Chroma.from_documents(
            chunks,
            embedding,
            collection_name=final_collection_name,
            persist_directory=CHROMA_PATH
        )
    else:
        # Check if collection exists for incremental update
        db, collection_exists = get_or_create_collection(final_collection_name, embedding)
        
        if collection_exists:
            # Incremental update: add documents to existing collection
            # This preserves all existing documents and appends new ones
            db.add_documents(chunks)
        else:
            # Create new collection with documents
            db = Chroma.from_documents(
                chunks,
                embedding,
                collection_name=final_collection_name,
                persist_directory=CHROMA_PATH
            )
    
    return db
```

**2. Query Documentation** (`query.py`):
```python
from langchain_community.llms import Ollama
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from get_vector_db import get_vector_db

LLM_MODEL = os.getenv('LLM_MODEL', 'mistral')

def query_docs(question):
    llm = Ollama(model=LLM_MODEL)
    db = get_vector_db()
    
    # Create retrieval chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=db.as_retriever(search_kwargs={"k": 3}),
        return_source_documents=True
    )
    
    result = qa_chain({"query": question})
    return result
```

**3. Web API Server** (`app.py`):
```python
from flask import Flask, request, jsonify
from embed import embed_file
from query import query_docs
import os
from pathlib import Path
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Ensure temp directory exists
TEMP_DIR = Path(os.getenv('TEMP_FOLDER', './_temp'))
TEMP_DIR.mkdir(parents=True, exist_ok=True)

@app.route('/embed', methods=['POST'])
def embed():
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    version = request.form.get('version')  # Optional version parameter
    overwrite = request.form.get('overwrite', 'false').lower() == 'true'
    
    # SECURITY: Sanitize filename to prevent path traversal attacks
    # secure_filename removes directory separators and dangerous characters
    safe_filename = secure_filename(file.filename)
    if not safe_filename:
        return jsonify({"error": "Invalid filename"}), 400
    
    # Use absolute path to ensure we stay within TEMP_DIR
    file_path = TEMP_DIR / safe_filename
    
    # Additional security: Ensure resolved path is still within TEMP_DIR
    try:
        file_path = file_path.resolve()
        if not str(file_path).startswith(str(TEMP_DIR.resolve())):
            return jsonify({"error": "Invalid file path"}), 400
    except (OSError, ValueError):
        return jsonify({"error": "Invalid file path"}), 400
    
    # Save file
    file.save(str(file_path))
    
    try:
        # Embed with version support and incremental update capability
        embed_file(str(file_path), version=version, overwrite=overwrite)
        return jsonify({
            "message": "File embedded successfully",
            "version": version,
            "mode": "overwrite" if overwrite else "incremental"
        })
    except Exception as e:
        return jsonify({"error": f"Embedding failed: {str(e)}"}), 500

@app.route('/query', methods=['POST'])
def query():
    # SECURITY: Check if request has JSON body
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.json
    if data is None:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    
    question = data.get('query')
    if not question:
        return jsonify({"error": "Missing 'query' field in request body"}), 400
    
    try:
        result = query_docs(question)
        return jsonify({
            "answer": result['result'],
            "sources": [doc.page_content[:200] for doc in result['source_documents']]
        })
    except Exception as e:
        return jsonify({"error": f"Query failed: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(port=8080)
```

**Security Features**:
- **Path Traversal Protection**: Uses `secure_filename()` and path resolution checks to prevent directory traversal attacks
- **Input Validation**: Validates JSON body existence and required fields before processing
- **Error Handling**: Proper error responses with appropriate HTTP status codes
- **File Validation**: Checks for file existence and validates file paths stay within intended directory

#### Integration with Common Model Workflow

**Automated Documentation Embedding**:
```bash
#!/bin/bash
# scripts/embed-commonmodel-docs.sh

VERSION=$(mvn help:evaluate -Dexpression=commonmodel.version -q -DforceStdout)
DOC_DIR="./docs/common-model-${VERSION}"

# Generate Javadoc
mvn javadoc:javadoc -Dcommonmodel.version=${VERSION}

# Convert HTML to text or extract from Javadoc
# Then embed into ChromaDB with version-specific collection
# Note: This will incrementally add to existing collection if it exists
python3 -c "
from embed import embed_file
import os
import glob

# Find all documentation files
doc_files = glob.glob('${DOC_DIR}/**/*.html', recursive=True) + \
            glob.glob('${DOC_DIR}/**/*.txt', recursive=True)

for doc_file in doc_files:
    embed_file(doc_file, version='${VERSION}', overwrite=False)
"
```

**Environment Configuration** (`.env`):
```bash
TEMP_FOLDER=./_temp
CHROMA_PATH=chroma
COLLECTION_NAME=common-model-docs
LLM_MODEL=mistral
TEXT_EMBEDDING_MODEL=nomic-embed-text
```

**Usage Example**:
```bash
# Start the RAG server
python3 app.py

# Embed new documentation version (incremental update - appends to existing collection)
curl -X POST http://localhost:8080/embed \
  -F "file=@./docs/common-model-1.2.3/javadoc.pdf" \
  -F "version=1.2.3"

# Embed with overwrite mode (replaces existing collection)
curl -X POST http://localhost:8080/embed \
  -F "file=@./docs/common-model-1.2.3/javadoc.pdf" \
  -F "version=1.2.3" \
  -F "overwrite=true"

# Query the documentation
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I use the UserService class?"}'
```

**⚠️ Important**: By default, `embed_file()` performs incremental updates - it appends documents to existing collections rather than overwriting them. Use `overwrite=True` only when you want to replace the entire collection.

#### Copilot Instructions for RAG Integration

```markdown
# .github/copilot-instructions.md

## Common Model Documentation via RAG

When working with `com.company.commonmodel.*` classes:

1. **Check current version**:
   ```bash
   mvn help:evaluate -Dexpression=commonmodel.version -q -DforceStdout
   ```

2. **Query local RAG system**:
   - Start RAG server: `python3 app.py`
   - Query via API: `POST /query` with question about class/interface
   - Or use CLI: `python3 query.py "How does UserService work?"`

3. **Benefits**:
   - Semantic search finds relevant context even with partial class names
   - Context-aware responses include code examples and relationships
   - All processing happens locally - no data leaves your machine
   - Works offline once documentation is embedded

4. **Update documentation**:
   - When common model version changes, re-embed docs:
     ```bash
     ./scripts/embed-commonmodel-docs.sh
     ```
```

#### Advantages of RAG Approach

- **Semantic Understanding**: Finds relevant documentation even with imprecise queries
- **Context-Aware**: Provides answers with surrounding context and relationships
- **Privacy**: All processing happens locally - no external API calls
- **Offline Capable**: Works without internet once documentation is embedded
- **Version-Aware**: Can maintain separate collections per version
- **Natural Language**: Ask questions in plain English, not just class names

#### GPU Considerations

- **CPU Mode**: Works but slower for large documentation sets
- **GPU Recommended**: Significantly faster embeddings and generation
- **Memory**: Mistral model requires ~4GB RAM; nomic-embed-text is lightweight
- **Performance**: GPU can reduce query time from seconds to milliseconds

**Reference**: [Build Your Own RAG App Guide](https://dev.to/nassermaronie/build-your-own-rag-app-a-step-by-step-guide-to-setup-llm-locally-using-ollama-python-and-chromadb-b12)

## 🎯 Recommended Alternatives Based on Priority

1. **Best**: Local documentation generation with version file tracking
2. **Excellent**: Local RAG application (Ollama + ChromaDB) for semantic search and context-aware responses
3. **Good**: Git submodule with isolated documentation builds  
4. **Adequate**: Maven repository with attached sources/javadoc

## 🔧 Key Success Factors

- **Version Awareness**: Always reference exact version from `pom.xml`
- **Zero Cascade**: Solutions avoid triggering dependent component builds
- **Team Consistency**: All developers use same documentation source
- **Automation**: Minimal manual steps for documentation updates
- **Semantic Understanding**: RAG solutions provide context-aware responses beyond simple keyword matching
- **Privacy & Security**: Local solutions (RAG, MCP, pre-generated docs) ensure sensitive code stays private

The primary MCP solution remains ideal, but these alternatives provide viable fallbacks while maintaining the dynamic version awareness critical for your rapid development cycle. The RAG approach is particularly powerful for teams needing natural language querying and semantic understanding of documentation.