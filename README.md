# Personal AI Agent

A sophisticated personal assistant powered by the **Agno Framework** with native MCP integration, async operations, and persistent local storage. Built for modern AI workflows with local Ollama AI, SQLite + LanceDB vector database, and extensible Model Context Protocol (MCP) tools.

> **🎯 Quick Start**: Run `poetry run personal-agent-agno` or `paga` for the modern Agno implementation

## 🌟 Features

### Agno Framework (Primary Implementation)

- 🚀 **Modern Async Architecture**: Built on agno framework with native async/await operations
- 🔧 **Native MCP Integration**: Direct Model Context Protocol support without bridges
- 🧠 **Local Persistent Storage**: SQLite + LanceDB for zero external dependencies
- 🤖 **Local AI**: Powered by Ollama (qwen2.5:7b-instruct model)
- 🌐 **Modern Streamlit Interface**: Interactive web UI with real-time updates
- ⚡ **Enhanced Performance**: Async operations and optimized tool coordination
- 🔒 **Privacy-First**: All data stored locally, no external database dependencies

### Core Capabilities

- 🔍 **Semantic Search**: Finds relevant context from past interactions using LanceDB
- 📊 **Topic Organization**: Categorize memories by topic in local SQLite database
- 🎯 **System Status Indicator**: Visual feedback for local storage connection status
- 🗑️ **Memory Management**: Clear knowledge base functionality
- 📝 **Knowledge Auto-Creation**: Automatic creation of essential knowledge files
- 💭 **Real-time Thoughts**: Live streaming of agent reasoning process
- 📁 **File-Based Storage**: Easy backup/restore by copying data directory

### MCP-Powered Tools (6 Servers)

- 📁 **File Operations**: Read, write, and list directory contents
- 🔎 **Intelligent File Search**: Combine file exploration with memory context
- 🐙 **GitHub Integration**: Search repositories, code, issues, and documentation
- 🌍 **Web Search**: Brave Search API integration for real-time research
- 💻 **Shell Commands**: Safe execution of terminal commands
- 🌐 **Web Fetching**: Retrieve content from URLs and APIs via Puppeteer

### Alternative Implementations (Legacy)

- 🔧 **LangChain Version**: Traditional agent executor (stable but being phased out)
- 🧪 **Smolagents Version**: HuggingFace experimental framework (research only)
- 📦 **Weaviate Version**: Original Docker-based vector storage (migrated to SQLite + LanceDB)

## 🏗️ Architecture

### Agno Framework (Primary)

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Streamlit Web UI│───▶│   Agno Agent    │───▶│   Ollama LLM    │
│  (Port 8501)    │    │  (Async/Await)  │    │  qwen2.5:7b     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                   ┌─────────────────────────────────────────┐
                   │         Native MCP Integration          │
                   │                                         │
                   │  ┌─────────────────┐  ┌───────────────┐ │
                   │  │SQLite + LanceDB │  │ MCP Servers   │ │
                   │  │  Local Storage  │  │ (6 servers)   │ │
                   │  └─────────────────┘  └───────────────┘ │
                   │                                         │
                   │  📁 Filesystem     🐙 GitHub           │
                   │  🌍 Brave Search   🌐 Puppeteer        │
                   │  💻 Shell          🔧 System Tools     │
                   └─────────────────────────────────────────┘
```

### API Endpoints

**Main Interface:**

- `GET/POST /` - Main chat interface with real-time thought streaming (Streamlit on port 8501)
- `GET /agent_info` - Agent capabilities and MCP server status
- `GET /clear` - Clear knowledge base/memory

**Alternative Implementations:**

- **LangChain**: Port 5001 (`poetry run personal-agent`)
- **Smolagents**: Port 5003 (`poetry run personal-agent-smolagent`)

## 🚀 Quick Start

### Agno Framework (Recommended)

```bash
# 1. Clone and setup
git clone <repository-url>
cd personal_agent

# 2. Install dependencies and MCP servers
poetry install
poetry run python scripts/install_mcp.py

# 3. Setup Ollama (if not already installed)
brew install ollama
ollama serve
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text

# 4. Test everything works
poetry run test-tools

# 5. Run the Agno agent (recommended)
poetry run personal-agent-agno
# OR use the short alias:
paga
```

**Commands Available:**

- `personal-agent-agno` or `paga` - Streamlit web interface (port 8501)
- `personal-agent-agno-cli` or `pagc` - CLI interface

### Alternative Implementations

```bash
# LangChain version (legacy, stable)
poetry run personal-agent  # port 5001

# Smolagents version (experimental)
poetry run personal-agent-smolagent  # port 5003
```

Then open `http://localhost:8501` in your browser and start chatting with the Agno-powered agent!

## 📋 Prerequisites

- **Python**: 3.11 or higher
- **Poetry**: For dependency management
- **Ollama**: For local LLM inference
- **Node.js**: For MCP servers (filesystem, github, brave-search, puppeteer)

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd personal_agent
```

### 2. Install Dependencies

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Install project dependencies (includes smolagents)
poetry install
```

### 3. Install MCP Servers

Use our automated installation script to install all required MCP servers:

```bash
# Run the automated MCP server installation script
poetry run python scripts/install_mcp.py
```

This script will automatically install:

- **@modelcontextprotocol/server-filesystem**: File operations (read, write, list directories)
- **@modelcontextprotocol/server-github**: GitHub repository search and code analysis
- **@modelcontextprotocol/server-brave-search**: Web search for real-time information
- **@modelcontextprotocol/server-puppeteer**: Browser automation and web content fetching

### 4. Install and Setup Ollama

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
ollama serve

# Pull required models
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
```

### 5. Configure Environment Variables (Required)

For proper operation, you **must** configure filesystem paths and optionally set up API keys for enhanced functionality:

**Method 1: Using .env file (Recommended)**

1. Copy the example environment file:

   ```bash
   cp .env.example .env
   ```

2. Edit `.env` file and configure your settings:

      ```bash
   # REQUIRED: Filesystem path configuration
   # ROOT_DIR: Your home directory (used by filesystem MCP server)
   ROOT_DIR=/Users/your_username
   
   # OPTIONAL: API keys for enhanced functionality
   # GitHub Personal Access Token
   # Get from: https://github.com/settings/tokens
   GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here
   
   # Brave Search API Key  
   # Get from: https://api.search.brave.com/app/keys
   BRAVE_API_KEY=your_brave_api_key_here
   ```

**Method 2: Export directly in terminal**

```bash
# Required filesystem paths
export ROOT_DIR="/Users/$(whoami)"

# Optional API keys
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
export BRAVE_API_KEY="your_api_key_here"
```

### 6. Test Installation

```bash
# Test all components are working
poetry run test-tools
poetry run test-mcp-servers

# Test the agno system specifically
poetry run personal-agent-agno-cli --help
```

## 💻 Usage

### Starting the Agno Agent

```bash
# Launch the Agno framework agent (recommended)
poetry run personal-agent-agno
# OR use the short alias:
paga

# Alternative CLI interface
poetry run personal-agent-agno-cli
pagc
```

**Web Interface**: Open `http://localhost:8501` in your browser

**Features:**

- 🔄 **Real-time Thoughts**: Live streaming of agent reasoning
- 🧠 **Memory Integration**: Persistent knowledge with SQLite + LanceDB
- ⚡ **Async Operations**: Modern async/await architecture  
- 🔧 **Native MCP**: Direct Model Context Protocol integration
- 💭 **Session Management**: Unique sessions for each interaction

### Streamlit Interface (Agno)

**Main Interface:**

- Streamlit web app on `http://localhost:8501`
- Interactive chat interface with thought streaming
- Agent capabilities and MCP server status displayed
- Memory management controls integrated in UI

**Streamlit Interface Features:**

- 🎯 **Interactive Chat**: Real-time conversation with the agent
- 💭 **Thought Streaming**: Live display of agent reasoning process
- 🔧 **Tool Integration**: Visual feedback on MCP tool usage
- 🧠 **Memory Status**: Display of knowledge base connection
- 📊 **Session Management**: Automatic session handling

### Testing the System

```bash
# Test all tool functionality
poetry run test-tools

# Test MCP server availability
poetry run test-mcp-servers

# Install/check MCP servers
poetry run python scripts/install_mcp.py
```

## 🎯 Example Interactions

### Research with Streamlit Interface

```text
[Streamlit Interface]
User Input: "Research the latest developments in async Python"

💭 Agent Thoughts (Live Display):
- 🤔 Thinking about your request...
- 🔍 Searching memory for context...
- ✅ Found relevant context in memory
- 🧠 Analyzing request with agno reasoning
- 🔧 Preparing MCP tools and capabilities

Agent Response:
I'll research the latest async Python developments using multiple sources...

[MCP Tools Used: brave_search, github_search, filesystem]
[Results displayed with memory context integration]
```

### File Operations with Memory

```text
[Streamlit Interface]
User Input: "Create a FastAPI app that uses async/await patterns"

💭 Agent Thoughts (Live Display):
- 📁 Creating new Python file...
- 🔧 Using MCP filesystem tools...
- 💾 Storing interaction in memory...

[Agent creates file using mcp_write_file and stores the interaction]
[File content displayed in Streamlit with syntax highlighting]
```

## 🛠️ Tool Reference (Agno MCP Integration)

### Native MCP Tools (6 Servers)

**Filesystem Server:**

- File read/write operations
- Directory listing and navigation
- Intelligent file search with memory integration

**GitHub Server:**

- Repository search and code analysis
- Issue and documentation retrieval
- Developer resource discovery

**Brave Search Server:**

- Real-time web information retrieval
- Current event and technology research
- Multi-source fact verification

**Puppeteer Server:**

- Web content extraction and analysis
- Dynamic page interaction
- Rich content retrieval

**Shell Server:**

- Safe system command execution
- Environment information gathering
- Development tool integration

**System Tools:**

- Memory management (SQLite + LanceDB integration)
- Session and state management
- Error handling and recovery

### Memory Integration

All tools integrate with the persistent memory system:

- **Automatic Storage**: Important interactions saved to SQLite + LanceDB
- **Context Enhancement**: Past knowledge enriches current responses
- **Semantic Search**: Vector-based retrieval of relevant information
- **Topic Organization**: Categorized storage for better organization

## 🗂️ Legacy Implementations

The project includes alternative implementations that are being phased out in favor of the Agno framework:

### LangChain Version (Port 5001)

```bash
poetry run personal-agent
# OR short alias:
pagl
```

- **Status**: Stable but deprecated
- **Use Case**: Fallback option if agno version has issues

### Smolagents Version (Port 5003)  

```bash
poetry run personal-agent-smolagent
# OR short alias:
pags
```

- **Status**: Experimental research platform
- **Use Case**: Multi-agent research and development

> **⚠️ Note**: These implementations are maintained for compatibility but new features are developed in the Agno framework only.

## 🚀 Advanced Features

### Async Architecture

The Agno framework provides true async operations:

```python
# Native async/await throughout the stack
async def process_request(query: str) -> str:
    context = await query_knowledge_base(query)
    response = await agno_agent.run(enhanced_prompt)
    await store_interaction(query, response)
    return response
```

### Streamlit Integration

Monitor agent reasoning through the interactive interface:

- **Session-based**: Each conversation gets unique session management
- **Live Updates**: Real-time display of agent thoughts and tool usage
- **Progress Tracking**: Visual feedback on processing stages
- **Error Recovery**: Graceful handling of failed operations
- **Interactive Controls**: Memory management and tool configuration

### Enhanced Memory System

Intelligent memory management with SQLite + LanceDB:

- **Vector Storage**: Semantic similarity search using LanceDB
- **Context Retrieval**: Relevant past interactions surface automatically
- **Knowledge Building**: Each interaction improves future responses
- **Topic Categorization**: Organized knowledge domains in SQLite
- **Local Files**: Easy backup/restore by copying data directory

### MCP Native Integration

Direct Model Context Protocol support:

- **No Bridges**: Native MCP tool execution
- **Multi-Server**: Coordinate across 6 different MCP servers
- **Tool Discovery**: Automatic detection of available capabilities  
- **Error Handling**: Robust fallbacks for server unavailability
- **Streamlit Interface**: Modern web interface displays all available tools and capabilities

## 🔧 Troubleshooting (Agno)

### Common Issues

**1. Agno Agent Won't Start**

```bash
# Check if all dependencies are installed
poetry install

# Verify MCP servers are available
poetry run test-mcp-servers

# Test agno specifically
poetry run personal-agent-agno-cli --help
```

**2. Streamlit Interface Issues**

```bash
# Check if Streamlit is properly installed
poetry show streamlit

# Verify the agno agent starts without errors
poetry run personal-agent-agno-cli --help

# Check console output for any startup errors
```

**3. MCP Tools Not Available**

```bash
# Reinstall MCP servers
poetry run python scripts/install_mcp.py

# Test MCP server availability
poetry run test-mcp-servers
```

**4. Memory/Storage Issues**

```bash
# Check if data directory exists and is writable
ls -la data/

# Verify SQLite database files
ls -la data/*.db

# Test memory functionality
poetry run test-tools
```

**5. API Key Configuration**

```bash
# Check environment variables are loaded
poetry run personal-agent-agno-cli --help

# Verify .env file exists and has correct format
cat .env | grep -E "(GITHUB|BRAVE)"
```

## ⚙️ Configuration

### Required Environment Variables

```bash
# REQUIRED: Filesystem paths - must be configured in .env file
ROOT_DIR="/Users/your_username"        # Your home directory
```

### Optional Environment Variables

```bash
# Optional: API keys for enhanced functionality  
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
export BRAVE_API_KEY="your_api_key_here"

# Optional: Override default service URLs
export OLLAMA_URL="http://localhost:11434"
```

## 📜 Available Commands (Agno)

The agno implementation provides these Poetry scripts:

```bash
# Run Agno web interface (recommended)
poetry run personal-agent-agno   # or paga

# Run Agno CLI interface  
poetry run personal-agent-agno-cli   # or pagc

# System maintenance
poetry run install-mcp-servers
poetry run test-mcp-servers
poetry run test-tools
poetry run store-fact "Your fact here" --topic "optional_topic"
```

## 📚 Migration from Weaviate (Legacy)

### What Changed

The project has migrated from Docker-based Weaviate vector database to a local SQLite + LanceDB architecture for improved privacy and zero external dependencies.

### Key Benefits of New Architecture

- 🔒 **Privacy-First**: All data stored locally, no external database
- 🚀 **Zero Setup**: No Docker containers or external services required
- 📁 **Easy Backup**: Simple file-based storage in `data/` directory
- ⚡ **Faster Startup**: Instant initialization without waiting for containers
- 🔧 **Simplified Development**: No complex database management

### Legacy Weaviate Setup (Deprecated)

If you need to reference the old Weaviate setup:

```bash
# OLD: Docker-based Weaviate (no longer needed)
docker-compose up -d weaviate

# NEW: Automatic local storage initialization
poetry run personal-agent-agno  # Automatically creates SQLite + LanceDB
```

### Migration Path

Data from existing Weaviate installations should be migrated using the built-in migration tools:

```bash
# Run migration script (if available)
poetry run python migration_plan_sqlite.py

# Or start fresh with knowledge auto-creation
poetry run personal-agent-agno  # Creates essential knowledge files automatically
```

### Legacy Environment Variables

These variables are no longer needed:

```bash
# REMOVED: No longer required
# DATA_DIR="/Users/your_username/data"  # Auto-managed now
# WEAVIATE_URL="http://localhost:8080"  # No external DB needed
```

## 📄 License

BSD 3-Clause License - See LICENSE file for details.

---

**Personal AI Agent (Agno)** - A modern async agentic AI assistant with native MCP integration, Streamlit interface, and local persistent memory. 🚀
