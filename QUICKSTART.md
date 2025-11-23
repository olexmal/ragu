# Quick Start Guide

Get your RAG system up and running in 5 minutes!

## 🚀 5-Minute Setup

### Step 1: Install Ollama (2 minutes)

```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Step 2: Download Models (2 minutes)

```bash
ollama pull mistral          # ~4GB download
ollama pull nomic-embed-text # Lightweight
```

### Step 3: Setup Python Environment (1 minute)

```bash
cd ragu
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 4: Start Server

```bash
./scripts/start-rag-server.sh
```

### Step 5: Test It!

```bash
# Health check
curl http://localhost:8080/health

# Embed a test file
echo "UserService provides methods for managing users." > test.txt
curl -X POST http://localhost:8080/embed -F "file=@test.txt"

# Query it
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is UserService?"}'
```

## 📝 Common Workflows

### Embed Your First Documentation

```bash
# Via API
curl -X POST http://localhost:8080/embed \
  -F "file=@your-docs.pdf" \
  -F "version=1.0.0"

# Via CLI
python3 src/cli.py embed your-docs.pdf --version 1.0.0
```

### Query Documentation

```bash
# Via API
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{"query": "How do I use UserService?"}'

# Via CLI
python3 src/cli.py query "How do I use UserService?"
```

### Check System Status

```bash
python3 src/cli.py status
```

### List Collections

```bash
python3 src/cli.py list-collections
```

## 🔧 Configuration (Optional)

The system works with defaults, but you can customize:

```bash
cp .env.example .env
# Edit .env to customize settings
```

## 🎯 Next Steps

1. **Embed Your Documentation**: Use `/embed` endpoint or CLI
2. **Start Querying**: Ask questions about your docs
3. **Enable Authentication**: For production use
4. **Set Up Automation**: Use scheduled updates for version changes

## 📚 Learn More

- **Full Documentation**: See [README.md](README.md)
- **Developer Guide**: See [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md)
- **Implementation Details**: See [RAG_IMPLEMENTATION_PLAN.md](RAG_IMPLEMENTATION_PLAN.md)

## 🆘 Troubleshooting

**Server won't start?**
- Check Ollama is running: `ollama list`
- Check port 8080 is available

**No results from queries?**
- Verify documentation is embedded: `python3 src/cli.py list-collections`
- Check collection has documents

**Import errors?**
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

---

**That's it!** You're ready to use your RAG system. 🎉

