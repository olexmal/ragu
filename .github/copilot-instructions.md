# Common Model Documentation via RAG

This project uses a local RAG (Retrieval-Augmented Generation) system to provide semantic search and context-aware responses about the common model package (`com.company.commonmodel.*`).

## When Working with Common Model Classes

### 1. Check Current Version

Always check the current common model version before implementing interfaces:

```bash
mvn help:evaluate -Dexpression=commonmodel.version -q -DforceStdout
```

### 2. Query the RAG System

The RAG system provides natural language querying of common model documentation.

#### Via API (if server is running):

```bash
# Start the RAG server (if not already running)
./scripts/start-rag-server.sh

# Query via API
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How does UserService work?", "version": "1.2.3"}'
```

#### Via CLI:

```bash
# Query from command line
python3 src/cli.py query "How does UserService work?" --version 1.2.3

# Or without version (uses default collection)
python3 src/cli.py query "What methods does UserService have?"
```

### 3. Benefits of RAG System

- **Semantic Understanding**: Finds relevant context even with partial class names or imprecise queries
- **Context-Aware Responses**: Provides answers with surrounding context and class relationships
- **Privacy**: All processing happens locally - no data leaves your machine
- **Offline Capable**: Works without internet once documentation is embedded
- **Version-Aware**: Can query specific versions of documentation

### 4. Update Documentation

When the common model version changes, update the embedded documentation:

```bash
# Automatic update (checks for version changes)
./scripts/update-docs.sh

# Manual update for specific version
./scripts/embed-commonmodel-docs.sh
```

### 5. Example Queries

Here are some example queries you can use:

```bash
# Query about a specific class
python3 src/cli.py query "What is the UserService class and how do I use it?"

# Query about methods
python3 src/cli.py query "What methods are available in UserService?"

# Query about relationships
python3 src/cli.py query "What classes does UserService depend on?"

# Query about specific version
python3 src/cli.py query "How do I create a user?" --version 1.2.3
```

### 6. Integration with Development Workflow

#### Before Implementing Common Model Interfaces:

1. **Check Version**: Verify you're using the correct version
   ```bash
   mvn help:evaluate -Dexpression=commonmodel.version -q -DforceStdout
   ```

2. **Query Documentation**: Ask the RAG system about the class/interface
   ```bash
   python3 src/cli.py query "How do I implement UserService interface?"
   ```

3. **Review Source Citations**: Check the source documents in the response for code examples

4. **Implement**: Use the context from RAG responses to implement correctly

#### When Common Model Updates:

1. **Detect Version Change**: The `update-docs.sh` script automatically detects changes
2. **Re-embed Documentation**: Run `./scripts/update-docs.sh` to update embeddings
3. **Verify**: Query the new version to ensure documentation is current

### 7. Troubleshooting

#### RAG Server Not Running
```bash
# Check if server is running
curl http://localhost:8080/health

# Start server if needed
./scripts/start-rag-server.sh
```

#### No Results Found
- Check if documentation is embedded: `python3 src/cli.py list-collections`
- Verify version matches: Use `--version` parameter if querying specific version
- Re-embed documentation if needed: `./scripts/embed-commonmodel-docs.sh`

#### Ollama Not Available
- Ensure Ollama is installed: `ollama --version`
- Check models are available: `ollama list`
- Pull required models: `ollama pull mistral && ollama pull nomic-embed-text`

## Best Practices

1. **Always Check Version**: Common model updates 3+ times daily - always verify version
2. **Use Version-Specific Queries**: When working with specific versions, use `--version` flag
3. **Update Regularly**: Run `update-docs.sh` regularly or set up automated updates
4. **Review Sources**: Always check source citations in RAG responses for accuracy
5. **Combine with IDE**: Use RAG responses alongside IDE autocomplete and documentation

## System Status

Check system status anytime:

```bash
python3 src/cli.py status
```

This shows:
- Ollama availability
- ChromaDB status
- Available collections
- Current common model version

