# Local-AI-RAG

A complete local LLM application with web frontend featuring an **AI Firewall**, **Intelligent Search Scout**, and **RAG (Retrieval Augmented Generation)** using a local vector database. All data stays on your machine.

![Local-AI-RAG](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

- 🛡️ **AI Firewall**: Intelligent content filtering with pattern-based and LLM-powered safety checks
- 🔍 **Search Scout**: Automatic uncertainty detection with web search (works without API keys!)
- 📚 **RAG Pipeline**: Document ingestion, embedding, and retrieval for knowledge-enhanced responses
- 💾 **Local-First**: All data stored locally - SQLite + ChromaDB
- 🎨 **Modern UI**: Beautiful Tailwind CSS interface with real-time chat
- ⚡ **Fast**: Powered by Ollama for local inference
- 🔒 **Private**: No data leaves your machine (except optional web searches)

## 🏗️ Architecture

### Backend
- **FastAPI** - High-performance async API server
- **Ollama** - Local LLM inference (llama3.2:3b main, llama3.2:1b scout)
- **ChromaDB** - Vector database for embeddings
- **SQLite** - Relational data storage
- **Sentence-Transformers** - Optional embedding model

### Frontend
- **HTML5 + Tailwind CSS** - Modern responsive UI
- **Vanilla JavaScript** - No framework dependencies
- **Real-time updates** - Instant chat interface

## 📋 Prerequisites

- **Python 3.10+** (for local installation)
- **Docker & Docker Compose** (for Docker installation) - [Install Docker](https://docs.docker.com/get-docker/)
- **Ollama** - [Install from ollama.ai](https://ollama.ai)
- **8GB+ RAM** recommended
- **Optional**: Google Custom Search API key for Scout feature

## 📚 Documentation

- **[DOCKER.md](DOCKER.md)** - Complete Docker deployment guide
- **[DOCKER-QUICKREF.md](DOCKER-QUICKREF.md)** - Quick reference for Docker commands
- **[SCOUT-SEARCH.md](SCOUT-SEARCH.md)** - Complete guide to web search configuration
- **README.md** (this file) - Main documentation
- **[Makefile](Makefile)** - Automation commands

## 🚀 Quick Start

### Option 1: Docker (Recommended) 🐳

**Prerequisites:**
- Docker and Docker Compose installed
- Ollama running on host machine (`ollama serve`)
- Required models pulled (`ollama pull llama3.2:3b llama3.2:1b nomic-embed-text`)

```bash
# Make build script executable
chmod +x docker-build.sh

# Build and run with Docker
./docker-build.sh
```

Or manually:
```bash
# Build image
docker build -t local-ai-rag:latest .

# Run with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Access:** http://localhost:8000

### Option 2: Local Python Installation

**Prerequisites:**
- Python 3.10+
- Ollama installed and running

```bash
# Run installation script
chmod +x install.sh
./install.sh

# Start Ollama (in separate terminal)
ollama serve

# Activate virtual environment
source venv/bin/activate

# Start server
python backend/main.py
```

**Access:** http://localhost:8000

### Configuration

Edit `.env` file with your settings:

```bash
# Essential settings
OLLAMA_BASE_URL=http://localhost:11434  # or http://host.docker.internal:11434 for Docker
EMBEDDING_PROVIDER=ollama  # or "sentence-transformers"
VECTOR_DB_TYPE=chromadb    # or "sqlite"

# Optional: Google Search API (for Scout feature)
GOOGLE_API_KEY=your_api_key_here
GOOGLE_CSE_ID=your_cse_id_here
```

## 📚 Usage Guide

### Chat Interface

1. **Basic Chat**: Type messages and get AI responses
2. **AI Firewall**: Toggle to enable/disable content filtering
3. **Search Scout**: Toggle to enable automatic web search for uncertain queries
4. **RAG Mode**: Toggle to use document knowledge base for responses

### Document Management

1. Click **"Manage Documents"** in sidebar
2. Add documents with title and content
3. Documents are automatically chunked and embedded
4. Toggle **"Use RAG"** in chat to query your documents

### API Endpoints

#### Chat
```bash
POST /api/chat
{
  "message": "Your question",
  "session_id": "optional-session-id",
  "use_rag": false,
  "temperature": 0.7
}
```

#### Ingest Document
```bash
POST /api/rag/ingest
{
  "title": "Document Title",
  "content": "Document content...",
  "source": "optional-source",
  "url": "optional-url"
}
```

#### Query RAG
```bash
POST /api/rag/query
{
  "query": "Your question",
  "top_k": 5
}
```

#### Health Check
```bash
GET /health
```

#### Statistics
```bash
GET /api/stats
```

## 🏗️ Project Structure

```
local-llm-app/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── config.py            # Configuration management
│   ├── database.py          # SQLite operations
│   ├── vector_db.py         # Vector storage (ChromaDB/SQLite)
│   ├── llm_client.py        # Ollama integration
│   ├── embeddings_client.py # Embedding generation
│   ├── search_client.py     # Google Search API
│   ├── firewall.py          # AI firewall logic
│   ├── scout.py             # Uncertainty detection & search
│   └── rag_pipeline.py      # RAG implementation
├── frontend/
│   ├── index.html           # Main UI
│   ├── app.js               # Frontend logic
│   └── style.css            # Custom styles
├── data/
│   ├── app.db              # SQLite database (auto-created)
│   └── chroma/             # ChromaDB storage (auto-created)
├── requirements.txt         # Python dependencies
├── .env.example            # Example configuration
├── .env                    # Your configuration (git-ignored)
├── install.sh              # Setup script
├── README.md               # This file
└── .gitignore
```

## 🔧 Configuration Options

### Embedding Providers

**Ollama (Recommended)**
```bash
EMBEDDING_PROVIDER=ollama
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

**Sentence-Transformers**
```bash
EMBEDDING_PROVIDER=sentence-transformers
SENTENCE_TRANSFORMER_MODEL=all-MiniLM-L6-v2
```

### Vector Database

**ChromaDB (Recommended)**
```bash
VECTOR_DB_TYPE=chromadb
CHROMA_PERSIST_DIRECTORY=./data/chroma
```

**SQLite with NumPy**
```bash
VECTOR_DB_TYPE=sqlite
```

### RAG Parameters

```bash
RAG_TOP_K=5                      # Number of documents to retrieve
RAG_SIMILARITY_THRESHOLD=0.5     # Minimum similarity score
CHUNK_SIZE=500                   # Document chunk size
CHUNK_OVERLAP=50                 # Overlap between chunks
```

### Scout Parameters

```bash
SCOUT_ENABLED=true
SCOUT_UNCERTAINTY_THRESHOLD=0.6  # Trigger search if confidence < 0.6
```

## 🛡️ AI Firewall

The AI Firewall provides multi-layer content protection:

1. **Pattern Matching**: Fast regex-based filtering for known harmful patterns
2. **Keyword Detection**: Identifies sensitive topics requiring review
3. **LLM Review**: Uses smaller model for nuanced safety judgment
4. **Input & Output Filtering**: Checks both user messages and AI responses

Configure blocked categories in `.env`:
```bash
FIREWALL_ENABLED=true
```

## 🔍 Search Scout

Scout automatically detects when the AI needs current information:

- Identifies uncertainty phrases ("I don't know", "I'm not sure")
- Detects time-sensitive queries (current events, prices, weather)
- Triggers web search when confidence is low
- Augments response with search results

### Search Methods

**1. Google Custom Search API (Recommended)**
- Most accurate and reliable
- Requires API key setup
- Best for production use

**2. Public Web Scraping (Automatic Fallback)**
- Uses DuckDuckGo and public search engines
- No API key required - works out of the box!
- Automatically activated when Google API not configured
- Great for development and testing

**Setup Google Custom Search (Optional):**
1. Get API key: [Google Cloud Console](https://console.cloud.google.com)
2. Create Custom Search Engine: [Programmable Search](https://programmablesearchengine.google.com)
3. Add credentials to `.env`:
   ```bash
   GOOGLE_API_KEY=your_api_key
   GOOGLE_CSE_ID=your_cse_id
   ```

**Using Web Scraping (No Setup Needed):**
- Just start the application!
- Scout will automatically use DuckDuckGo search
- No configuration required
- Perfect for getting started quickly

## 📊 Database Schema

### Chat Messages
- Session management
- Message history with metadata
- Firewall and Scout flags
- RAG usage tracking

### Documents
- Document metadata
- Content storage
- Source attribution

### Vector Embeddings
- Document chunks
- Embedding vectors
- Similarity search

## 🔒 Security & Privacy

- ✅ All data stored locally
- ✅ No external API calls (except optional Google Search)
- ✅ AI Firewall content protection
- ✅ SQLite database with ACID compliance
- ✅ Session-based isolation

## � Docker Commands

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Restart services
docker-compose restart

# Shell access
docker exec -it local-ai-rag bash

# View stats
docker stats local-ai-rag

# Rebuild single service
docker-compose up -d --build local-ai-rag
```

## �🚧 Troubleshooting

### Ollama Not Connecting (Docker)
```bash
# Check Ollama on host
curl http://localhost:11434/api/tags

# Ensure Ollama is accessible
ollama serve

# Check container can reach host
docker exec -it local-ai-rag curl http://host.docker.internal:11434/api/tags
```

### Ollama Not Connecting (Local)
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama
ollama serve
```

### Models Not Found
```bash
# Pull required models
ollama pull llama3.2:3b
ollama pull llama3.2:1b
ollama pull nomic-embed-text
```

### Port Already in Use
```bash
# Change port in .env or docker-compose.yml
PORT=8001

# Or stop conflicting service
lsof -ti:8000 | xargs kill -9
```

### Docker Container Won't Start
```bash
# Check logs
docker-compose logs local-ai-rag

# Rebuild from scratch
docker-compose down -v
docker-compose up -d --build

# Check disk space
docker system df
docker system prune -a
```

### Import Errors (Local)
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Permission Issues (Docker)
```bash
# Fix data directory permissions
sudo chown -R $USER:$USER data/
chmod -R 755 data/
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) - Local LLM inference
- [ChromaDB](https://www.trychroma.com) - Vector database
- [FastAPI](https://fastapi.tiangolo.com) - Modern Python API framework
- [Tailwind CSS](https://tailwindcss.com) - Utility-first CSS framework

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review documentation in `/docs`

---

**Built with ❤️ for local-first AI applications**
