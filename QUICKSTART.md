# 🚀 Quick Start Guide

Get RAGU (Retrieval-Augmented Generation Universal) up and running in 5 minutes!

---

## 🐳 Docker Quick Start (Fastest - 2 minutes)

**Prerequisites:** Docker and Docker Compose installed

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd ragu

# Start all services in development mode
./scripts/docker-start.sh dev

# Or start in production mode
./scripts/docker-start.sh prod
```

**Access the application:**
- Frontend: http://localhost:4200 (dev) or http://localhost:80 (prod)
- Backend API: http://localhost:8080

**With containerized Ollama:**
```bash
./scripts/docker-start.sh dev container
```

**Stop services:**
```bash
./scripts/docker-stop.sh
```

**View logs:**
```bash
./scripts/docker-logs.sh
```

For detailed Docker instructions, see [docs/DOCKER_GUIDE.md](docs/DOCKER_GUIDE.md).

### WSL2/Docker Configuration (If Ollama is in WSL)

If you're running Ollama in WSL2 and Docker containers in WSL2, you need to configure Ollama to listen on all interfaces so containers can access it:

```bash
# Run the configuration script (requires sudo)
sudo ./scripts/configure-ollama-wsl.sh
```

This script will:
- Configure Ollama systemd service to listen on `0.0.0.0:11434` (all interfaces)
- Restart Ollama service
- Verify the configuration

**After running the script:**

1. Get your WSL IP address:
   ```bash
   ip addr show eth0 | grep 'inet ' | awk '{print $2}' | cut -d/ -f1
   ```

2. Update your `.env` file or set environment variable:
   ```bash
   # Create/update .env file
   echo "OLLAMA_BASE_URL=http://<WSL_IP>:11434" > .env
   # Replace <WSL_IP> with the IP from step 1
   ```

3. Restart Docker containers:
   ```bash
   docker compose restart backend celery-worker
   ```

**Alternative: Use Windows Ollama**

If you prefer to use Ollama running on Windows (outside WSL), configure it to listen on `0.0.0.0:11434` and use the Windows host IP:
```bash
# Get Windows host IP from WSL
cat /etc/resolv.conf | grep nameserver | awk '{print $2}'
# Then set OLLAMA_BASE_URL=http://<WINDOWS_IP>:11434
```

---

## ⚡ Manual Setup (5-Minute Setup)

### Step 1: Install Ollama (2 minutes)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Verify installation
ollama --version
```

### Step 2: Download Models (2 minutes)

```bash
# Pull LLM model (~4GB download)
ollama pull mistral

# Pull embedding model (lightweight)
ollama pull nomic-embed-text

# Verify models
ollama list
```

### Step 3: Setup Python Environment (1 minute)

```bash
# Navigate to project
cd ragu

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Start Backend Server

```bash
# Using helper script
./scripts/start-rag-server.sh

# Or manually
python3 -c "from src.app import app; app.run(host='localhost', port=8080)"
```

### Step 5: (Optional) Start Web UI

```bash
# In a new terminal
cd web-ui
npm install
npm start
# Access at http://localhost:4200
```

### Step 6: Test It!

**Via Web UI:**
1. Open `http://localhost:4200` in your browser
2. Go to "Upload & Import"
3. Upload a test document
4. Go to "Chat Playground" and ask a question

**Via API:**
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

---

## 📝 Common Workflows

### Upload Your First Document

**Via Web UI:**
1. Navigate to "Upload & Import" → "Upload Documents" tab
2. Click "Choose File" and select your document
3. Optionally set a version (e.g., "1.0.0")
4. Click "Upload & Embed"

**Via API:**
```bash
curl -X POST http://localhost:8080/embed \
  -F "file=@your-docs.pdf" \
  -F "version=1.0.0"
```

**Via CLI:**
```bash
python3 src/cli.py embed your-docs.pdf --version 1.0.0
```

### Import from Confluence

**Via Web UI:**
1. First, configure Confluence settings in "Settings" → "Confluence Integration"
2. Navigate to "Upload & Import" → "Confluence Import" tab
3. Enter the Confluence page ID or URL
4. Optionally set a version
5. Click "Import Page"

**Via API:**
```bash
curl -X POST http://localhost:8080/confluence/import \
  -H "Content-Type: application/json" \
  -d '{
    "page_id": "123456",
    "version": "1.0.0"
  }'
```

### Query Documentation

**Via Web UI:**
1. Navigate to "Chat Playground" page
2. Type your question in the chat input area
3. Optionally select a version from the dropdown
4. Adjust "Documents to retrieve" (k value) in the settings panel
5. Press Enter or click the send button to submit your query
6. View sources in the Sources panel (toggle button in toolbar)

**Via API:**
```bash
curl -X POST http://localhost:8080/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I use UserService?",
    "version": "1.0.0",
    "k": 3
  }'
```

**Via CLI:**
```bash
python3 src/cli.py query "How do I use UserService?" --version 1.0.0
```

### Check System Status

**Via Web UI:**
- Navigate to "Dashboard" for system overview
- Check "Monitoring" for detailed statistics

**Via CLI:**
```bash
python3 src/cli.py status
```

**Via API:**
```bash
curl http://localhost:8080/health
curl http://localhost:8080/stats
```

### List Collections

**Via Web UI:**
- Navigate to "Collections" page

**Via API:**
```bash
curl http://localhost:8080/collections
```

**Via CLI:**
```bash
python3 src/cli.py list-collections
```

---

## 🔧 Configuration (Optional)

The system works with defaults, but you can customize:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env to customize:
# - API port (default: 8080)
# - Model names
# - Authentication settings
# - Vector database path
```

### Web UI Configuration

Edit `web-ui/src/environments/environment.ts` to change API URL:

```typescript
export const environment = {
  apiUrl: 'http://localhost:8080'  // Change if backend runs on different port
};
```

---

## 🎯 Next Steps

1. **📤 Upload Documentation**: Use the web UI or API to upload your documents
2. **🔗 Import from Confluence**: Configure Confluence settings and import pages
3. **🔍 Start Querying**: Ask questions about your documentation
4. **⚙️ Configure Settings**: Set up LLM providers, embedding models, and system preferences
5. **📊 Monitor Usage**: Check the Monitoring page for statistics and analytics

---

## 📚 Learn More

- **📖 Full Documentation**: See [README.md](README.md) for complete user guide
- **🔌 API Reference**: See [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for all endpoints
- **👨‍💻 Developer Guide**: See [docs/DEVELOPER_GUIDE.md](docs/DEVELOPER_GUIDE.md) for architecture details
- **📝 Changelog**: See [CHANGELOG.md](CHANGELOG.md) for version history

---

## 🆘 Troubleshooting

**Server won't start?**
- Check Ollama is running: `ollama list`
- Check port 8080 is available: `lsof -i :8080` (Linux/Mac) or `netstat -ano | findstr :8080` (Windows)
- Verify Python version: `python3 --version` (requires 3.8+)

**No results from queries?**
- Verify documentation is embedded: Check "Collections" page or `python3 src/cli.py list-collections`
- Ensure collection has documents (count > 0)
- Try a simpler query or increase k value

**Import errors?**
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`
- Check Python version compatibility

**Web UI not loading?**
- Ensure backend is running on port 8080
- Check browser console for errors
- Verify API URL in environment configuration
- Check CORS settings if accessing from different origin

**Confluence import fails?**
- Verify Confluence settings are configured in Settings page
- Check that `confluence-markdown-exporter` is installed: `pip show confluence-markdown-exporter`
- Ensure API token has read permissions for the page
- Try with a different page ID to rule out page-specific issues

**Docker containers can't connect to Ollama?**
- If Ollama is in WSL: Run `sudo ./scripts/configure-ollama-wsl.sh` to configure it for Docker access
- Verify Ollama is listening on all interfaces: `netstat -tuln | grep 11434` (should show `0.0.0.0:11434`)
- Check OLLAMA_BASE_URL is set correctly in `.env` or docker-compose.yml
- Test connectivity from container: `docker compose exec backend curl http://<OLLAMA_IP>:11434/api/tags`
- For WSL2: Use WSL IP address, not `host.docker.internal` (which may not work in WSL2)

---

**That's it!** You're ready to use your RAG system. 🎉

For more detailed information, see the [full documentation](README.md).
