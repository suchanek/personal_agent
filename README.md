# Personal AI Agent

A sophisticated personal assistant that learns about you and provides context-aware responses using Ollama, Weaviate vector database, LangChain, and Model Context Protocol (MCP) integration.

## 🌟 Features

### Core Capabilities

- 🧠 **Persistent Memory**: Uses Weaviate vector database for semantic memory storage
- 🤖 **Local AI**: Powered by Ollama (qwen2.5:7b-instruct model)
- 🔍 **Semantic Search**: Finds relevant context from past interactions
- 🌐 **Web Interface**: Clean Flask-based web UI with knowledge base management
- 📊 **Topic Organization**: Categorize memories by topic
- 🎯 **ReAct Agent**: Uses LangChain's ReAct framework for intelligent tool usage
- 🗑️ **Memory Management**: Clear knowledge base functionality

### MCP-Powered Tools (12 Total)

- 📁 **File Operations**: Read, write, and list directory contents
- 🔎 **Intelligent File Search**: Combine file exploration with memory context
- 🐙 **GitHub Integration**: Search repositories, code, issues, and documentation
- 🌍 **Web Search**: Brave Search API integration for real-time research
- 💻 **Shell Commands**: Safe execution of terminal commands
- 🌐 **Web Fetching**: Retrieve content from URLs and APIs
- 🔬 **Comprehensive Research**: Multi-source research combining memory, web, GitHub, and files

### Enhanced Architecture

- 🔧 **MCP Integration**: Model Context Protocol for extensible tool ecosystem  
- 🚀 **Multi-Server Architecture**: 6 MCP servers (filesystem, github, brave-search, puppeteer)
- 🔗 **Hybrid Intelligence**: Combines persistent memory with external data sources
- 📡 **Real-time Capabilities**: Live web search and GitHub integration

## 🏗️ Architecture

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask Web UI  │───▶│  Personal Agent │───▶│   Ollama LLM    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                   ┌─────────────────────────────────────────┐
                   │         Enhanced Capabilities           │
                   │                                         │
                   │  ┌─────────────────┐  ┌───────────────┐ │
                   │  │ Weaviate Vector │  │ MCP Servers   │ │
                   │  │    Database     │  │ (6 total)     │ │
                   │  └─────────────────┘  └───────────────┘ │
                   │                                         │
                   │  📁 File System    🐙 GitHub            │
                   │  🌍 Web Search     🌐 Puppeteer         │
                   │  💻 Shell Commands 🔬 Research          │
                   │  🔍 Smart Search                        │
                   └─────────────────────────────────────────┘
```

## 🚀 Quick Start

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

# 6. Run the agent
poetry run personal-agent
```

Then open `http://127.0.0.1:5001` in your browser and start chatting!

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

# Install project dependencies
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

**Method 2: Export environment variables**

```bash
# REQUIRED: Filesystem path configuration
# ROOT_DIR: Your home directory (used by filesystem MCP server)
export ROOT_DIR="/Users/your_username"

# DATA_DIR: Directory for vector database storage
export DATA_DIR="/Users/your_username/data"

# OPTIONAL: API keys for enhanced functionality
# GitHub Personal Access Token (for repository search)
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"

# Brave Search API Key (for web search)  
export BRAVE_API_KEY="your_api_key_here"
```

**Getting API Keys:**

- **GitHub Personal Access Token**:
  1. Go to GitHub → Settings → Developer settings → Personal access tokens
  2. Generate a token with 'repo' and 'read:org' permissions

- **Brave Search API Key**:
  1. Visit <https://api.search.brave.com/app/keys>
  2. Create an account and generate an API key

**Directory Configuration (REQUIRED):**

- **ROOT_DIR**: **REQUIRED** - Set this to your home directory (e.g., `/Users/your_username` on macOS, `/home/your_username` on Linux). This is where the filesystem MCP server will have access. The personal agent will not function properly without this configuration.
- **DATA_DIR**: **REQUIRED** - Set this to where you want the vector database data stored (e.g., `/Users/your_username/data`). This directory will be created automatically if it doesn't exist.

### 6. Start Weaviate Database

```bash
# Start Weaviate using Docker Compose
docker-compose up -d

# Verify Weaviate is running
curl http://localhost:8080/v1/.well-known/ready
```

## 💻 Usage

### 1. Start the Personal Agent

You can run the agent using Poetry scripts:

```bash
# Run the main agent
poetry run personal-agent

# Alternative: Run directly with Python
poetry run python personal_agent.py
```

### 2. Test Tool Functionality

Verify all 12 tools are working correctly:

```bash
# Test all tool imports and descriptions
poetry run test-tools

# Test MCP server availability (optional)
poetry run test-mcp-servers

# Test comprehensive research functionality
poetry run python tests/test_comprehensive_research.py

# Test cleanup and resource management
poetry run python tests/test_cleanup_improved.py
```

## 🧪 Comprehensive Testing Suite

The project includes a comprehensive test suite in the `tests/` directory:

### Available Tests

- **`test_tools.py`**: Validates all 12 tool imports and descriptions
- **`test_mcp_availability.py`**: Tests MCP server availability and connectivity
- **`test_comprehensive_research.py`**: Validates research functionality with real results
- **`test_cleanup_improved.py`**: Tests enhanced resource management and cleanup
- **`test_cleanup.py`**: Basic cleanup functionality validation
- **`test_mcp.py`**: Low-level MCP communication testing
- **`test_github.py`**: Comprehensive GitHub MCP tool functionality testing (7 test functions)

### Debug Scripts (moved to tests/)

- **`debug_github_direct.py`**: Direct GitHub API testing and validation
- **`debug_github_tools.py`**: GitHub MCP server tool discovery (26 available tools)
- **`debug_tool_call.py`**: General MCP tool call debugging

### Running Individual Tests

```bash
# Test specific functionality
source .venv/bin/activate && python tests/test_comprehensive_research.py
source .venv/bin/activate && python tests/test_mcp_availability.py
source .venv/bin/activate && python tests/test_cleanup_improved.py

# Test GitHub tool functionality (comprehensive)
source .venv/bin/activate && python tests/test_github.py

# Run all tool validations
poetry run test-tools

# Run debug scripts for troubleshooting
source .venv/bin/activate && python tests/debug_github_tools.py
source .venv/bin/activate && python tests/debug_github_direct.py
```

### Test Results Overview

All tests provide detailed output including:

- ✅ Success indicators with result details
- ❌ Failure indicators with error explanations  
- 📊 Performance metrics (character counts, timing)
- 🔧 Configuration validation
- 🐙 GitHub authentication and tool availability testing
- 🌍 Web search and external service integration validation

### 3. Access Web Interface

Open your browser and navigate to: `http://127.0.0.1:5001`

### 3. Interact with Your Agent

- **Ask questions**: "What do you know about me?"
- **Share information**: "I like Python programming and 3D visualization"
- **Get help**: "Write a PyVista script to display a cube"
- **Categorize topics**: Use the topic field to organize memories

## 🎯 Example Interactions

### Basic Memory Operations

```text
User: My name is Eric and I enjoy Python programming
Agent: Nice to meet you, Eric! I've noted that you enjoy Python programming. 
       I'll remember this for future conversations.

User: What programming languages do I like?
Agent: Based on our previous conversation, you enjoy Python programming!
```

### File Operations

```text
User: Create a Python script at ~/test.py that prints "Hello World"
Agent: I'll create that file for you...
[Agent uses mcp_write_file to create the script]

User: What files are in my home directory?
Agent: Let me list the contents of your home directory...
[Agent uses mcp_list_directory to show files]
```

### Research & Web Search

```text
User: Research the latest developments in Python 3.12
Agent: I'll conduct comprehensive research for you...
[Agent combines memory search, web search, GitHub search, and local files]

User: Find Python tutorials on GitHub
Agent: Searching GitHub repositories for Python tutorials...
[Agent uses mcp_github_search to find relevant repositories]
```

### Shell Commands

```text
User: Check the current system time and date
Agent: I'll run the date command for you...
[Agent uses mcp_shell_command to execute system commands]
```

## 🔧 Advanced Features

### Multi-Modal Tool Integration

The agent seamlessly combines multiple data sources:

- **Memory + Files**: "What Python scripts have I created before?" combines memory search with file system exploration
- **Web + GitHub**: "Find the latest Flask documentation and examples" searches both web and GitHub repositories
- **Local + Remote**: "Compare my local Python scripts with popular GitHub examples" analyzes local files and searches GitHub

### Intelligent Context Switching

- **Automatic Tool Selection**: Agent chooses appropriate tools based on query type
- **Progressive Enhancement**: Starts with memory, adds web search, includes file operations as needed
- **Cross-Reference Validation**: Compares information across multiple sources for accuracy

### Persistent Learning Loop

- **Auto-Storage**: Important operations automatically stored in vector database
- **Context Enrichment**: Each interaction enhances future responses
- **Topic Categorization**: Organizes knowledge by subject area for better retrieval

### Safe Execution Environment

- **Sandboxed Shell**: MCP shell server provides controlled command execution
- **Path Restrictions**: File operations limited to user directory for security
- **Error Handling**: Graceful degradation when services are unavailable

### Real-Time Research Capabilities

The `comprehensive_research` tool provides multi-source intelligence:

1. **Memory Search**: Checks existing knowledge base
2. **Web Search**: Gets current information via Brave Search
3. **GitHub Search**: Finds code examples and documentation
4. **File Analysis**: Searches local files for relevant content
5. **Synthesis**: Combines all sources into coherent response

## 🛠️ Complete Tool Reference

### Memory & Knowledge Management

1. **`store_interaction`**: Store conversations and interactions in vector database
2. **`query_knowledge_base`**: Semantic search through stored memories
3. **`clear_knowledge_base`**: Reset all stored knowledge (admin function)

### File System Operations  

4. **`mcp_read_file`**: Read content from any file in accessible directories
5. **`mcp_write_file`**: Create or update files with new content
6. **`mcp_list_directory`**: Browse directory contents and file structure
7. **`intelligent_file_search`**: Smart file discovery with memory integration

### External Data Sources

8. **`mcp_github_search`**: Search GitHub repositories, code, issues, documentation
9. **`mcp_brave_search`**: Web search using Brave Search API for real-time information
10. **`mcp_fetch_url`**: Retrieve content from web URLs and APIs
11. **`mcp_shell_command`**: Execute system commands safely within controlled environment

### Advanced Research

12. **`comprehensive_research`**: Multi-source research combining all available tools

Each tool integrates with the memory system to provide context-aware results and automatically stores important operations for future reference.

## ⚙️ Configuration

### Required Environment Variables

```bash
# REQUIRED: Filesystem paths - must be configured in .env file
ROOT_DIR="/Users/your_username"        # Your home directory
DATA_DIR="/Users/your_username/data"   # Vector database storage
```

### Optional Environment Variables

```bash
# Optional: Override default service URLs
export WEAVIATE_URL="http://localhost:8080"
export OLLAMA_URL="http://localhost:11434"

# Optional: API keys for enhanced functionality  
export GITHUB_PERSONAL_ACCESS_TOKEN="your_token_here"
export BRAVE_API_KEY="your_api_key_here"
```

### Memory Management

The agent automatically:

- Stores all interactions in Weaviate
- Searches for relevant context before responding
- Organizes memories by timestamp and topic
- Uses semantic similarity for context retrieval

### Model Context Protocol (MCP)

Included MCP configuration for filesystem access:

```bash
# Use with MCP-compatible tools
mcphost -m ollama:qwen2.5 --config mcp.json
```

## 📁 Project Structure

```text
personal_agent/
├── personal_agent.py         # Main application with 12 integrated tools
├── tests/                    # Comprehensive test suite
│   ├── __init__.py          # Test package initializer
│   ├── test_tools.py        # Tool verification script  
│   ├── test_mcp_availability.py # MCP server testing script
│   ├── test_comprehensive_research.py # Research functionality tests
│   ├── test_cleanup_improved.py # Enhanced cleanup tests
│   ├── test_cleanup.py      # Basic cleanup tests
│   ├── test_mcp.py          # MCP communication tests
│   ├── test_github.py       # GitHub MCP tool functionality tests (7 tests)
│   ├── debug_github_direct.py # Direct GitHub API testing
│   ├── debug_github_tools.py # GitHub MCP server tool discovery
│   └── debug_tool_call.py   # General MCP tool call debugging
├── pyproject.toml           # Poetry dependencies & scripts
├── docker-compose.yml       # Weaviate setup
├── mcp.json                # MCP server configurations (with env vars)
├── mcp.json.template       # Template without sensitive data
├── .env.example            # Example environment variables
├── .env                    # Your actual API keys (excluded from git)
├── README.md               # This documentation
├── FIX_SUMMARY.md          # Comprehensive fix documentation
├── scripts/                # Installation and utility scripts
│   ├── __init__.py        
│   └── install_mcp.py     # Automated MCP server installation
└── .venv/                 # Virtual environment
```

### Security Notes

- `mcp.json` contains environment variable placeholders (e.g., `${GITHUB_PERSONAL_ACCESS_TOKEN}`)
- `mcp.json.template` is the safe template version for sharing
- `.env` contains your actual API keys and is excluded from git
- `.env.example` shows what environment variables are needed

## 📦 Dependencies

### Core Dependencies

- **langchain**: Framework for LLM applications
- **langchain-ollama**: Ollama integration
- **langchain-weaviate**: Weaviate vector store
- **weaviate-client**: Weaviate database client
- **flask**: Web framework
- **requests**: HTTP client
- **rich**: Enhanced logging

### AI Models

- **qwen2.5:7b-instruct**: Main conversation model
- **nomic-embed-text**: Text embedding model

## 🔍 Features in Detail

### Memory System

- **Vector Storage**: All interactions stored as embeddings
- **Semantic Search**: Find related memories using similarity
- **Metadata**: Track timestamps and topics
- **Persistence**: Memories survive between sessions

### Agent Capabilities

- **Tool Usage**: Can store and retrieve information
- **Context Awareness**: Uses relevant past interactions
- **ReAct Framework**: Thought-Action-Observation loops
- **Error Handling**: Graceful fallbacks when services unavailable

### Web Interface

- **Clean UI**: Simple, responsive design
- **Context Display**: Shows retrieved memories
- **Topic Organization**: Categorize conversations
- **Real-time**: Immediate responses

## 🔧 Troubleshooting

### Common Issues

1. **Weaviate Connection Failed**

   ```bash
   # Restart Weaviate
   docker-compose down
   docker-compose up -d
   ```

2. **Ollama Model Not Found**

   ```bash
   # Pull required models
   ollama pull qwen2.5:7b-instruct
   ollama pull nomic-embed-text
   ```

3. **Port Already in Use**

   ```bash
   # Check what's using port 5001
   lsof -i :5001
   # Kill the process or change port in personal_agent.py
   ```

4. **MCP Server Issues**

   ```bash
   # Test MCP servers
   source .venv/bin/activate && python tests/test_mcp_availability.py
   
   # Verify all tools are loaded
   poetry run test-tools
   
   # Test comprehensive research
   source .venv/bin/activate && python tests/test_comprehensive_research.py
   
   # Test GitHub functionality specifically
   source .venv/bin/activate && python tests/test_github.py
   
   # Discover available GitHub tools
   source .venv/bin/activate && python tests/debug_github_tools.py
   
   # Reinstall MCP servers if needed
   poetry run python scripts/install_mcp.py
   ```

5. **GitHub Authentication Issues**

   ```bash
   # Check if GitHub Personal Access Token is set
   echo $GITHUB_PERSONAL_ACCESS_TOKEN
   
   # Test GitHub tool availability and authentication
   source .venv/bin/activate && python tests/test_github.py
   
   # For debugging, check GitHub tools directly
   source .venv/bin/activate && python tests/debug_github_direct.py
   ```

6. **Poetry Script Issues**

   ```bash
   # If Poetry scripts don't work, run directly
   python personal_agent.py
   python test_tools.py
   
   # Ensure Poetry is properly installed
   poetry install
   ```

7. **GitHub Tool Testing**

   ```bash
   # Full GitHub test suite (7 comprehensive tests)
   source .venv/bin/activate && python tests/test_github.py
   
   # Check environment variables
   echo "GitHub Token: ${GITHUB_PERSONAL_ACCESS_TOKEN:0:10}..."
   
   # List all 26 available GitHub MCP tools
   source .venv/bin/activate && python tests/debug_github_tools.py
   ```

### Logs and Debugging

- **Agent Logs**: Check terminal output for detailed logs
- **Weaviate Logs**: `docker-compose logs weaviate`
- **Debug Mode**: Flask runs in debug mode by default
- **MCP Server Logs**: Check stderr output in terminal

## 🔨 Development

### Adding New Tools

```python
@tool
def my_custom_tool(param: str) -> str:
    """Description of what the tool does."""
    # Tool implementation
    return "Tool result"

# Add to tools list in personal_agent.py
tools = [
    store_interaction, 
    query_knowledge_base, 
    my_custom_tool,  # Add your new tool here
    # ...existing tools...
]
```

### Customizing Prompts

Edit the `system_prompt` in `personal_agent.py` to modify agent behavior.

### Database Schema

Weaviate collection structure:

- **text**: Interaction content
- **timestamp**: When stored (RFC3339)
- **topic**: Category/topic

### Adding New MCP Servers

1. Install the MCP server: `npm install -g @modelcontextprotocol/server-<name>`
2. Add configuration to `mcp.json`
3. Create corresponding `@tool` function in `personal_agent.py`
4. Add tool to the tools list

## 📄 License

BSD 3-Clause License

Copyright (c) 2025, Eric G. Suchanek, Ph.D.

See LICENSE file for full details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd personal_agent

# Install dependencies
poetry install

# Install MCP servers
poetry run python scripts/install_mcp.py

# Test the setup
source .venv/bin/activate && poetry run test-tools
source .venv/bin/activate && python tests/test_mcp_availability.py

# Test GitHub functionality specifically
source .venv/bin/activate && python tests/test_github.py

# Run debug scripts for troubleshooting
source .venv/bin/activate && python tests/debug_github_tools.py
source .venv/bin/activate && python tests/debug_github_direct.py
source .venv/bin/activate && python tests/debug_tool_call.py
```

### Debug Scripts (in tests/ directory)

- **`debug_github_tools.py`**: Discover all available GitHub MCP tools (26 total)
- **`debug_github_direct.py`**: Test GitHub API connectivity and authentication
- **`debug_tool_call.py`**: General MCP tool call debugging and validation

---

## 🌟 What Makes This Special

### Comprehensive Integration

Unlike basic chatbots, this personal agent combines:

- **Persistent Memory**: Never forgets your preferences and past interactions
- **Real-time Web Access**: Always has current information via Brave Search
- **Code Intelligence**: GitHub integration for technical questions and examples
- **File System Awareness**: Can read, write, and analyze your local files
- **Shell Access**: Execute commands safely within controlled environment

### Production Ready

- **Robust Error Handling**: Graceful degradation when services are unavailable
- **Extensible Architecture**: Easy to add new MCP servers and capabilities
- **Security Conscious**: Sandboxed execution and path restrictions
- **Performance Optimized**: Efficient vector search and caching
- **Comprehensive Testing**: Full test suite including GitHub authentication and tool validation
- **Debug Infrastructure**: Organized debug scripts for troubleshooting and development

### Current Status: ✅ Fully Operational

- All 12 tools verified and working
- MCP integration stable and tested
- Web interface responsive and user-friendly
- Memory system storing and retrieving context effectively
- GitHub authentication and tool integration fully functional
- Comprehensive test suite with 100% success rate
- Debug infrastructure properly organized
- Ready for daily use with optional API key enhancement

**Personal AI Agent** - A comprehensive, MCP-powered personal assistant that learns, remembers, and grows with you. 🚀
