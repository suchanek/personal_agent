# Personal AI Agent

A sophisticated personal assistant powered by the **Agno Framework** with native MCP integration, async operations, and persistent memory. Built for modern AI workflows with local Ollama AI, Weaviate vector database, and extensible Model Context Protocol (MCP) tools.

> **🎯 Quick Start**: Run `poetry run personal-agent-agno` or `paga` for the modern Agno implementation

## 🌟 Features

### Agno Framework (Primary Implementation)

- 🚀 **Modern Async Architecture**: Built on agno framework with native async/await operations
- 🔧 **Native MCP Integration**: Direct Model Context Protocol support without bridges
- 🧠 **Persistent Memory**: Weaviate vector database for semantic memory storage
- 🤖 **Local AI**: Powered by Ollama (qwen2.5:7b-instruct model)
- 🌐 **Modern Web Interface**: Real-time thought streaming and session management
- ⚡ **Enhanced Performance**: Async operations and optimized tool coordination

### Core Capabilities

- 🔍 **Semantic Search**: Finds relevant context from past interactions
- 📊 **Topic Organization**: Categorize memories by topic
- 🎯 **Brain Status Indicator**: Visual feedback for Weaviate connection status
- 🗑️ **Memory Management**: Clear knowledge base functionality
- 📝 **Fact Storage Utility**: Command-line tool for storing facts directly in the knowledge base
- 💭 **Real-time Thoughts**: Live streaming of agent reasoning process

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

## 🏗️ Architecture

### Agno Framework (Primary)

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask Web UI  │───▶│   Agno Agent    │───▶│   Ollama LLM    │
│  (Port 5002)    │    │  (Async/Await)  │    │  qwen2.5:7b     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                   ┌─────────────────────────────────────────┐
                   │         Native MCP Integration          │
                   │                                         │
                   │  ┌─────────────────┐  ┌───────────────┐ │
                   │  │ Weaviate Vector │  │ MCP Servers   │ │
                   │  │    Database     │  │ (6 servers)   │ │
                   │  └─────────────────┘  └───────────────┘ │
                   │                                         │
                   │  📁 Filesystem     🐙 GitHub           │
                   │  🌍 Brave Search   🌐 Puppeteer        │
                   │  💻 Shell          🔧 System Tools     │
                   └─────────────────────────────────────────┘
```

### API Endpoints

**Main Interface:**

- `GET/POST /` - Main chat interface with real-time thought streaming
- `GET /stream_thoughts?session_id={id}` - Server-Sent Events for live thoughts
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

# 4. Start Weaviate database
docker-compose up -d

# 5. Test everything works
poetry run test-tools

# 6. Run the Agno agent (recommended)
poetry run personal-agent-agno
# OR use the short alias:
paga
```

**Commands Available:**

- `personal-agent-agno` or `paga` - Web interface (port 5002)
- `personal-agent-agno-cli` or `pagc` - CLI interface

### Alternative Implementations

```bash
# LangChain version (legacy, stable)
poetry run personal-agent  # port 5001

# Smolagents version (experimental)
poetry run personal-agent-smolagent  # port 5003
```

Then open `http://127.0.0.1:5002` in your browser and start chatting with the Agno-powered agent!

## 📋 Prerequisites

- **Python**: 3.11 or higher
- **Poetry**: For dependency management
- **Docker**: For Weaviate database
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
   
   # DATA_DIR: Directory for vector database storage
   DATA_DIR=/Users/your_username/data
   
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
export DATA_DIR="/Users/$(whoami)/data"

# Optional API keys
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
export BRAVE_API_KEY="your_api_key_here"
```

### 6. Start Weaviate Database

```bash
# Start the vector database
docker-compose up -d

# Verify it's running
docker-compose ps
```

### 7. Test Installation

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

**Web Interface**: Open `http://127.0.0.1:5002` in your browser

**Features:**

- 🔄 **Real-time Thoughts**: Live streaming of agent reasoning
- 🧠 **Memory Integration**: Persistent knowledge with Weaviate
- ⚡ **Async Operations**: Modern async/await architecture  
- 🔧 **Native MCP**: Direct Model Context Protocol integration
- 💭 **Session Management**: Unique sessions for each interaction

### API Endpoints (Agno)

**Main Interface:**

- `GET/POST /` - Chat interface with thought streaming
- `GET /stream_thoughts?session_id={id}` - Real-time thought stream (SSE)
- `GET /agent_info` - Agent capabilities and server status
- `GET /clear` - Memory management (clear knowledge base)

**Mogli Usage Example:**

```python
import requests

# Chat with the agent
response = requests.post('http://localhost:5002/', data={
    'query': 'What is the current status of Python 3.12?',
    'topic': 'programming',
    'session_id': 'api_session_001'
})

# Get agent information
info = requests.get('http://localhost:5002/agent_info')
print(info.text)  # Shows MCP servers, tools, capabilities

# Clear memory
clear_result = requests.get('http://localhost:5002/clear')
```

**Server-Sent Events (Thoughts):**

```javascript
// Subscribe to real-time agent thoughts
const eventSource = new EventSource('/stream_thoughts?session_id=my_session');
eventSource.onmessage = function(event) {
    const thought = JSON.parse(event.data);
    console.log('Agent thinking:', thought.thought);
};
```

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

### Research with Real-time Thoughts

```text
💭 "🤔 Thinking about your request..."
💭 "🔍 Searching memory for context..."
💭 "✅ Found relevant context in memory"
💭 "🧠 Analyzing request with agno reasoning"
💭 "🔧 Preparing MCP tools and capabilities"

User: Research the latest developments in async Python
Agent: I'll research the latest async Python developments using multiple sources...

[Agent uses MCP tools: brave_search, github_search, filesystem]
[Results combined with memory context for comprehensive response]
```

### File Operations with Memory

```text
User: Create a FastAPI app that uses async/await patterns
Agent: I'll create a modern FastAPI application for you...

💭 "📁 Creating new Python file..."
💭 "🔧 Using MCP filesystem tools..."
💭 "💾 Storing interaction in memory..."

[Agent creates file using mcp_write_file and stores the interaction]
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

- Memory management (Weaviate integration)
- Session and state management
- Error handling and recovery

### Memory Integration

All tools integrate with the persistent memory system:

- **Automatic Storage**: Important interactions saved to Weaviate
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

### Real-time Thought Streaming

Monitor agent reasoning in real-time:

- **Session-based**: Each interaction gets unique session ID
- **Live Updates**: Server-Sent Events for instant thought delivery
- **Progress Tracking**: Visual feedback on processing stages
- **Error Recovery**: Graceful handling of failed operations

### Enhanced Memory System

Intelligent memory management with Weaviate:

- **Vector Storage**: Semantic similarity search
- **Context Retrieval**: Relevant past interactions surface automatically
- **Knowledge Building**: Each interaction improves future responses
- **Topic Categorization**: Organized knowledge domains

### MCP Native Integration

Direct Model Context Protocol support:

- **No Bridges**: Native MCP tool execution
- **Multi-Server**: Coordinate across 6 different MCP servers
- **Tool Discovery**: Automatic detection of available capabilities  
- **Error Handling**: Robust fallbacks for server unavailability
- **Web Interface**: Custom Flask interface displays all available tools and capabilities

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

**2. Real-time Thoughts Not Streaming**

```bash
# Check browser developer console for SSE errors
# Verify session ID is being passed correctly
# Test endpoint directly: curl http://localhost:5002/stream_thoughts?session_id=test
```

**3. MCP Tools Not Available**

```bash
# Reinstall MCP servers
poetry run python scripts/install_mcp.py

# Check agent info endpoint
curl http://localhost:5002/agent_info
```

**4. Memory/Weaviate Issues**

```bash
# Restart Weaviate
docker-compose down && docker-compose up -d

# Clear and rebuild memory
curl http://localhost:5002/clear
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
DATA_DIR="/Users/your_username/data"   # Vector database storage
```

### Optional Environment Variables

```bash
# Optional: API keys for enhanced functionality  
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
export BRAVE_API_KEY="your_api_key_here"

# Optional: Override default service URLs
export WEAVIATE_URL="http://localhost:8080"
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

## 📄 License

BSD 3-Clause License - See LICENSE file for details.

---

**Personal AI Agent (Agno)** - A modern async AI assistant with native MCP integration, real-time thought streaming, and persistent memory. 🚀
