# Personal AI Agent

A sophisticated personal assistant powered by the **Agno Framework** with native MCP integration, async operations, and local SQLite + LanceDB storage. Built for modern AI workflows with local Ollama AI, zero external dependencies, and extensible Model Context Protocol (MCP) tools.

> **🎯 Quick Start**: Run `poetry run personal-agent` for the modern Agno-based Streamlit interface or `poetry run cli` for command-line interaction

## 🌟 Features

### Modern Architecture (Current Implementation)

- 🚀 **Agno Framework**: Built on modern agno framework with native async/await operations
- 🔧 **Native MCP Integration**: Direct Model Context Protocol support without bridges
- 🧠 **Local Storage**: SQLite + LanceDB for zero external dependencies
- 🤖 **Local AI**: Powered by Ollama (qwen2.5:7b-instruct model)
- 🌐 **Dual Interface**: Interactive Streamlit web UI + CLI with real-time streaming
- ⚡ **Enhanced Performance**: Async operations and optimized tool coordination
- 🔒 **Privacy-First**: All data stored locally, complete data sovereignty

### Core Capabilities

- 🔍 **Semantic Search**: Finds relevant context from past interactions using LanceDB vectors
- 📊 **Memory Management**: SQLite-based conversation and knowledge storage
- 🎯 **System Status**: Visual feedback for local storage connection status
- 🗑️ **Knowledge Management**: Clear and organize knowledge base functionality
- 📝 **Auto-Knowledge Creation**: Automatic creation of essential knowledge files
- 💭 **Real-time Thoughts**: Live streaming of agent reasoning process (Streamlit)
- 📁 **File-Based Storage**: Easy backup/restore by copying data directory
- 🌙 **Dark Mode**: Modern dark theme with user toggle

### MCP-Powered Tools (6 Servers)

- 📁 **File Operations**: Read, write, and list directory contents
- 🔎 **Intelligent File Search**: Combine file exploration with memory context
- 🐙 **GitHub Integration**: Search repositories, code, issues, and documentation
- 🌍 **Web Search**: Brave Search API integration for real-time research
- 💻 **Shell Commands**: Safe execution of terminal commands
- 🌐 **Web Fetching**: Retrieve content from URLs and APIs via Puppeteer

## 🏗️ Architecture

### Current System (SQLite + LanceDB)

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Streamlit Web UI│───▶│   Agno Agent    │───▶│   Ollama LLM    │
│  (Port 8502)    │    │  (Async/Await)  │    │  qwen2.5:7b     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                      │
         │                      ▼
         │          ┌─────────────────────────────────────────┐
         │          │         Native MCP Integration          │
         │          │                                         │
         │          │  ┌─────────────────┐  ┌───────────────┐ │
         │          │  │SQLite + LanceDB │  │ MCP Servers   │ │
         │          │  │  Local Storage  │  │ (6 servers)   │ │
         │          │  └─────────────────┘  └───────────────┘ │
         │          │                                         │
         │          │  📁 Filesystem     🐙 GitHub           │
         │          │  🌍 Brave Search   🌐 Puppeteer        │
         │          │  💻 Shell          🔧 System Tools     │
         │          └─────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│ CLI Interface   │
│ (poetry run cli)│
└─────────────────┘
```

### Available Interfaces

**Web Interface (Primary):**

- Streamlit app on `http://localhost:8502`
- Real-time streaming responses with agent thoughts
- Dark mode toggle and modern UI
- Memory status and system information

**CLI Interface:**

- Command-line interaction with streaming responses
- Same agno agent backend as web interface
- Direct terminal access for automation

## 🚀 Quick Start

### Current System (Recommended)

```bash
# 1. Clone and setup
git clone <repository-url>
cd personal_agent

# 2. Install dependencies and MCP servers
poetry install
poetry run install-mcp-servers

# 3. Setup Ollama (if not already installed)
brew install ollama
ollama serve
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text

# 4. Test everything works
poetry run test-tools

# 5. Run the Personal AI Agent
# Web interface (recommended)
poetry run personal-agent
# Opens Streamlit at http://localhost:8502

# CLI interface
poetry run cli
# Interactive command-line interface
```

**Available Commands:**

- `personal-agent` - Streamlit web interface (port 8502)
- `personal-agent-cli` - CLI interface with streaming
- `personal-agent-streamlit` - Direct Streamlit app launcher
- `cli` - Convenience alias for CLI interface

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

# Install project dependencies
poetry install
```

### 3. Install MCP Servers

Use our automated installation script to install all required MCP servers:

```bash
# Run the automated MCP server installation script
poetry run install-mcp-servers
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
   
   # MULTIMODAL AGENTS: API Keys for Media Generation
   # ModelsLab API Key (for GIF, music, and video generation)
   # Get from: https://modelslab.com/
   MODELS_LAB_API_KEY=your_modelslab_api_key_here
   
   # ElevenLabs API Key (for text-to-speech audio generation)
   # Get from: https://elevenlabs.io/
   ELEVEN_LABS_API_KEY=your_elevenlabs_api_key_here
   
   # Giphy API Key (for GIF search and retrieval)
   # Get from: https://developers.giphy.com/
   GIPHY_API_KEY=your_giphy_api_key_here
   ```

**Method 2: Export directly in terminal**

```bash
# Required filesystem paths
export ROOT_DIR="/Users/$(whoami)"

# Optional API keys
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
export BRAVE_API_KEY="your_api_key_here"

# Multimodal Agents API keys
export MODELS_LAB_API_KEY="your_modelslab_api_key_here"
export ELEVEN_LABS_API_KEY="your_elevenlabs_api_key_here"
export GIPHY_API_KEY="your_giphy_api_key_here"
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

### Starting the Personal AI Agent

```bash
# Web interface (recommended)
poetry run personal-agent
# Opens Streamlit at http://localhost:8502

# CLI interface with streaming
poetry run cli
# Interactive command-line interface
```

**Available Commands:**

- `personal-agent` - Launch Streamlit web interface
- `personal-agent-cli` - CLI interface with streaming responses  
- `cli` - Convenience alias for CLI interface
- `personal-agent-streamlit` - Direct Streamlit app launcher

### Web Interface Features

**Main Interface (<http://localhost:8502>):**

- Interactive chat interface with real-time streaming
- Agent thoughts display during processing
- Dark mode toggle in sidebar settings
- Memory status and system information
- MCP tool integration with visual feedback

**Key Features:**

- 🎯 **Interactive Chat**: Real-time conversation with the agent
- 💭 **Thought Streaming**: Live display of agent reasoning process
- 🔧 **Tool Integration**: Visual feedback on MCP tool usage
- 🧠 **Memory Status**: Display of knowledge base connection status
- 📊 **Session Management**: Automatic session handling
- 🌙 **Dark Mode**: Toggle between light and dark themes

### CLI Interface Features

- Real-time streaming responses
- Same agent backend as web interface
- Direct terminal access for automation
- Session continuity across interactions

### Testing the System

```bash
# Test all tool functionality
poetry run test-tools

# Test MCP server availability  
poetry run test-mcp-servers

# Install/verify MCP servers
poetry run install-mcp-servers
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

## 🛠️ Tool Reference

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

## 🚀 Advanced Features

### Async Architecture

The system provides true async operations throughout:

```python
# Native async/await throughout the stack
async def process_request(query: str) -> str:
    context = await query_knowledge_base(query)
    response = await agent.run(enhanced_prompt)
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
- **Web Interface**: Modern Streamlit interface displays all available tools and capabilities

## 🔧 Troubleshooting

### Common Issues

**1. Agent Won't Start**

```bash
# Check if all dependencies are installed
poetry install

# Verify MCP servers are available
poetry run test-mcp-servers

# Test system components
poetry run test-tools
```

**2. Streamlit Interface Issues**

```bash
# Check if Streamlit is properly installed
poetry show streamlit

# Verify agent backend works
poetry run cli

# Check console output for startup errors
```

**3. MCP Tools Not Available**

```bash
# Reinstall MCP servers
poetry run install-mcp-servers

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
echo $ROOT_DIR

# Verify .env file exists and has correct format
cat .env | grep -E "(GITHUB|BRAVE|MODELS_LAB|ELEVEN_LABS|GIPHY)"
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

# Optional: Multimodal agents API keys for media generation
export MODELS_LAB_API_KEY="your_modelslab_api_key_here"
export ELEVEN_LABS_API_KEY="your_elevenlabs_api_key_here"
export GIPHY_API_KEY="your_giphy_api_key_here"

# Optional: Override default service URLs
export OLLAMA_URL="http://localhost:11434"
```

## 📜 Available Commands

The system provides these Poetry scripts:

```bash
# Main interfaces
poetry run personal-agent         # Streamlit web interface (port 8502)
poetry run personal-agent-cli     # CLI interface with streaming
poetry run cli                    # Convenience alias for CLI

# System maintenance
poetry run install-mcp-servers
poetry run test-mcp-servers  
poetry run test-tools
poetry run store-fact "Your fact here" --topic "optional_topic"
```

## 📚 Migration from Weaviate (Completed)

### Migration Status: ✅ COMPLETE

The project has successfully migrated from Docker-based Weaviate vector database to a local SQLite + LanceDB architecture. This migration is **complete** and operational.

### Key Benefits of Current Architecture

- 🔒 **Privacy-First**: All data stored locally, no external database required
- 🚀 **Zero Setup**: No Docker containers or external services needed
- 📁 **Easy Backup**: Simple file-based storage in `data/` directory
- ⚡ **Faster Startup**: Instant initialization without waiting for containers
- 🔧 **Simplified Development**: No complex database management
- 🌐 **Dual Interface**: Both web and CLI interfaces available

### What Changed

- **REMOVED**: Docker-based Weaviate vector database
- **REMOVED**: External database dependencies  
- **ADDED**: SQLite + LanceDB local storage
- **ADDED**: CLI interface with streaming responses
- **ADDED**: Dark mode support in Streamlit interface
- **ENHANCED**: Session management and memory persistence

### Current System Commands

```bash
# NEW: Local storage system (current)
poetry run personal-agent      # Streamlit web interface
poetry run cli                 # CLI interface

# OLD: Docker-based Weaviate (no longer needed)
# docker-compose up -d weaviate  # DEPRECATED
```

### Data Storage

All data is now stored locally in the `data/` directory:

```
data/
├── agents.db              # Agent configurations
├── memory.db              # Conversation memory  
├── personal_agent_memory.db # User memory
├── knowledge/             # Knowledge files
└── lancedb/              # Vector embeddings
    └── personal_agent_knowledge.lance/
```

### Legacy Environment Variables (No Longer Needed)

These variables have been removed:

```bash
# REMOVED: No longer required
# DATA_DIR="/Users/your_username/data"  # Auto-managed now
# WEAVIATE_URL="http://localhost:8080"  # No external DB needed
```

## 📄 License

BSD 3-Clause License - See LICENSE file for details.

---

**Personal AI Agent** - A modern async AI assistant with native MCP integration, dual interfaces (Streamlit + CLI), and local SQLite + LanceDB storage. Zero external dependencies, complete data privacy. 🚀
