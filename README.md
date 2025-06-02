# Personal AI Agent

A sophisticated personal assistant that learns about you and provides context-aware responses. Features two implementations: **LangChain** (default, production-ready) and **Smolagents** (experimental), both with local Ollama AI, persistent Weaviate memory, and extensible Model Context Protocol (MCP) tools.

> **🎯 Quick Start**: Run `poetry run personal-agent` for the recommended LangChain version

## 🌟 Features

### Two Powerful Versions Available

- 🎯 **LangChain Version** (Default): Production-ready, stable, feature-complete
- 🧪 **Smolagents Version**: Experimental HuggingFace multi-agent framework

### Core Capabilities

- 🧠 **Persistent Memory**: Uses Weaviate vector database for semantic memory storage
- 🤖 **Local AI**: Powered by Ollama (qwen2.5:7b-instruct model)
- 🔍 **Semantic Search**: Finds relevant context from past interactions
- 🌐 **Web Interface**: Clean Flask-based web UI with live status indicators
- 📊 **Topic Organization**: Categorize memories by topic
- 🎯 **Brain Status Indicator**: Visual feedback for Weaviate connection status
- 🗑️ **Memory Management**: Clear knowledge base functionality

### MCP-Powered Tools (13 Total)

- 📁 **File Operations**: Read, write, and list directory contents
- 🔎 **Intelligent File Search**: Combine file exploration with memory context
- 🐙 **GitHub Integration**: Search repositories, code, issues, and documentation (with OUTPUT_PARSING_FAILURE fix)
- 🌍 **Web Search**: Brave Search API integration for real-time research
- 💻 **Shell Commands**: Safe execution of terminal commands
- 🌐 **Web Fetching**: Retrieve content from URLs and APIs
- 🔬 **Comprehensive Research**: Multi-source research combining memory, web, GitHub, and files

### Enhanced Architecture

- 🔧 **MCP Integration**: Model Context Protocol for extensible tool ecosystem  
- 🚀 **Multi-Server Architecture**: 6 MCP servers (filesystem, github, brave-search, puppeteer)
- 🤖 **Smolagents Framework**: HuggingFace multi-agent system with custom MCP bridge
- 🔗 **Hybrid Intelligence**: Combines persistent memory with external data sources
- 📡 **Real-time Capabilities**: Live web search and GitHub integration

## 🏗️ Architecture

### LangChain Version (Default - More Functional)

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask Web UI  │───▶│ LangChain Agent │───▶│   Ollama LLM    │
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

### Smolagents Version (Experimental)

```text
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask Web UI  │───▶│ Smolagents Agent│───▶│   Ollama LLM    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                   ┌─────────────────────────────────────────┐
                   │      Multi-Agent Framework              │
                   │                                         │
                   │  ┌─────────────────┐  ┌───────────────┐ │
                   │  │ Weaviate Vector │  │ MCP Bridge    │ │
                   │  │    Database     │  │ Tools         │ │
                   │  └─────────────────┘  └───────────────┘ │
                   └─────────────────────────────────────────┘
```

## 🔄 Version Comparison

### LangChain Version (Default - Recommended)

**Command**: `poetry run personal-agent`

**Features**:

- ✅ More stable and mature
- ✅ Better error handling and debugging
- ✅ Enhanced web interface with brain status indicator
- ✅ Comprehensive tool integration
- ✅ Real-time thought streaming
- ✅ Better memory integration with Weaviate
- ✅ Production-ready

**Best For**: Daily use, production environments, reliable performance

### Smolagents Version (Experimental)

**Command**: `poetry run personal-agent-smolagent`

**Features**:

- 🧪 Experimental multi-agent framework
- 🧪 HuggingFace smolagents integration
- 🧪 Custom MCP bridge implementation
- ⚠️ Less stable, occasional tool discovery issues
- ⚠️ Limited error recovery

**Best For**: Research, experimentation, contributing to smolagents ecosystem

## 🚀 Quick Start

### LangChain Version (Default - Recommended)

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

# 6. Run the LangChain agent (default)
poetry run personal-agent
```

### Smolagents Version (Experimental)

```bash
# Follow steps 1-5 above, then:

# 6. Run the Smolagents agent
poetry run personal-agent-smolagent
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

**Note**: Weaviate will store its data in the `~/weaviate_data/` directory in your home folder. This directory will be created automatically when Weaviate starts.

**Cleanup**: If you have an old `./weaviate_data/` directory in your project root from a previous setup, you can safely remove it:

```bash
rm -rf ./weaviate_data/
```

## 💻 Usage

### 1. Start the Personal Agent

Launch the agent using the Poetry endpoint:

```bash
# Launch the agent
poetry run personal-agent
```

### 2. Test Tool Functionality

Verify all 13 tools are working correctly:

```bash
# Test all tool imports and descriptions
poetry run test-tools

# Test the system
poetry run personal-agent --help

# Test MCP server availability (optional)
poetry run test-mcp-servers

# Test comprehensive research functionality
python tests/test_comprehensive_research.py

# Test cleanup and resource management
python tests/test_cleanup_improved.py

# Run the complete test suite
python tests/run_tests.py --category all
```

## 🧪 Comprehensive Testing Suite

The project includes a comprehensive test suite in the `tests/` directory with organized categories:

### Test Categories

- **Config Tests**: `test_config_extraction.py`, `test_env_vars.py` - Configuration and environment setup
- **Core Tests**: `test_agent_init.py`, `test_refactored_system.py`, `test_main_fix.py` - System initialization
- **Tool Tests**: `test_tools.py`, `test_github.py`, `test_logger_injection.py` - Individual tool functionality  
- **Web Tests**: `test_web_interface.py`, `test_web_detailed.py` - Web interface validation
- **Integration Tests**: `test_comprehensive_research.py`, `test_cleanup_improved.py` - Full system testing
- **Debug Scripts**: `debug_github_tools.py`, `debug_globals.py` - Troubleshooting utilities

### Running Tests

```bash
# Run all tests
python tests/run_tests.py --category all

# Run specific category
python tests/run_tests.py --category core
python tests/run_tests.py --category tools

# Run individual test
python tests/run_tests.py --test test_agent_init

# List all available tests
python tests/run_tests.py --list

# Legacy poetry commands (still work for some tests)
poetry run test-tools
poetry run test-mcp-servers
```

### 3. Access Web Interface

After launching the agent, open your browser to:

**🌐 <http://127.0.0.1:5001>**

The web interface provides:

- 💬 **Interactive Chat**: Direct conversation with the AI agent
- 🧠 **Memory Display**: Shows retrieved context from past interactions  
- 🏷️ **Topic Organization**: Categorized memory storage for better organization
- 🗑️ **Knowledge Management**: Clear/reset knowledge base functionality
- 📊 **System Status**: Real-time indication of MCP server status and tool availability
- 🔧 **Agent Info**: View detailed information about all 13 integrated tools and capabilities
- 🛠️ **Debugging Info**: Tool call logs and response details for troubleshooting

### 4. Example Usage

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
13. **Additional MCP Tools**: Various other tools discovered from MCP servers

Each tool integrates with the memory system to provide context-aware results and automatically stores important operations for future reference.

## 🤖 Smolagents Integration

### Multi-Agent Framework

This Personal AI Agent is built on **HuggingFace smolagents**, a powerful multi-agent framework that provides:

- **CodeAgent**: Advanced agent with tool integration capabilities
- **Tool Management**: Automatic discovery and registration of tools
- **Multi-Agent Architecture**: Extensible framework for complex agent interactions
- **Custom LLM Backend**: Integrated with Ollama for local AI processing

### MCP-Smolagents Bridge

A custom integration layer connects Model Context Protocol (MCP) servers to the smolagents framework:

```python
# smolagents tools are automatically discovered from MCP servers
smolagents_agent = CodeAgent(
    tools=mcp_tools,  # 13 tools from 6 MCP servers
    llm_engine=ollama_engine,
    max_iterations=10
)
```

### Tool Architecture

- **SimpleTool Objects**: Each MCP tool is wrapped as a smolagents SimpleTool
- **Dictionary Storage**: Tools stored as `{tool_name: SimpleTool}` for efficient access
- **Automatic Discovery**: MCP servers are scanned and tools registered automatically
- **Web Interface**: Custom Flask interface displays all available tools and capabilities

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
# MCP servers are configured internally in src/personal_agent/config/mcp_servers.py
# Configure API keys in .env file for enhanced functionality
```

## 📁 Project Structure

```text
personal_agent/
├── src/                      # Source code directory
│   └── personal_agent/       # Main package
│       ├── __init__.py
│       ├── main.py          # Application entry point
│       ├── smol_main.py     # Smolagents system initialization
│       ├── config/          # Configuration modules
│       │   ├── __init__.py
│       │   ├── mcp_servers.py # MCP server configurations
│       │   └── settings.py   # Application settings
│       ├── core/            # Core functionality
│       │   ├── __init__.py
│       │   ├── agent.py     # Smolagents agent setup
│       │   ├── mcp_client.py # MCP client implementation
│       │   └── memory.py    # Weaviate memory management
│       ├── tools/           # Tool implementations
│       │   ├── __init__.py
│       │   ├── filesystem.py # File system operations
│       │   ├── memory_tools.py # Knowledge base tools
│       │   ├── research.py  # Comprehensive research tool
│       │   ├── system.py    # Shell command execution
│       │   └── web.py       # Web search and GitHub tools
│       ├── utils/           # Utility modules
│       │   ├── __init__.py
│       │   └── cleanup.py   # Resource cleanup and logging
│       └── web/             # Web interface
│           ├── __init__.py
│           └── smol_interface.py # Smolagents web interface
│           ├── __init__.py
│           └── interface.py # Flask web application
├── tests/                   # Comprehensive test suite (20+ files)
│   ├── __init__.py
│   ├── run_tests.py         # Test runner with categories
│   ├── test_tools.py        # Tool verification script  
│   ├── test_mcp_availability.py # MCP server testing
│   ├── test_github.py       # GitHub integration tests (7 tests)
│   ├── test_comprehensive_research.py # Research functionality
│   ├── test_agent_init.py   # System initialization tests
│   ├── test_refactored_system.py # Modular architecture tests
│   ├── debug_github_tools.py # GitHub MCP tool discovery
│   ├── debug_github_direct.py # Direct GitHub API testing
│   └── debug_tool_call.py   # General MCP debugging
├── scripts/                 # Installation and utility scripts
│   ├── __init__.py        
│   └── install_mcp.py      # Automated MCP server installation
├── old/                     # Legacy code (archived)
│   ├── personal_agent.py   # Original monolithic version
│   ├── mcp.json            # Legacy MCP configuration
│   └── mcp.json.template   # Legacy MCP template
├── pyproject.toml          # Poetry dependencies & scripts
├── docker-compose.yml      # Weaviate database setup
├── .env.example           # Example environment variables
├── .env                   # Your actual API keys (excluded from git)
├── README.md              # This documentation
├── PROJECT_SUMMARY.md     # Project overview and status
├── FIX_SUMMARY.md         # Comprehensive fix documentation
└── .venv/                 # Virtual environment
```

### Configuration Notes

- MCP servers are configured internally in `src/personal_agent/config/mcp_servers.py`
- Environment variables (API keys) are loaded from `.env` file
- `.env.example` shows what environment variables are needed
- Legacy `mcp.json` files are archived in `old/` directory

## 📦 Dependencies

### Core Dependencies

- **smolagents**: HuggingFace multi-agent framework
- **ollama**: Ollama integration for local LLM
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

- **Smolagents Framework**: Multi-agent system with tool integration
- **Tool Usage**: Can store and retrieve information across 13 integrated tools
- **Context Awareness**: Uses relevant past interactions from vector memory
- **MCP Integration**: Custom bridge connecting Model Context Protocol to smolagents
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

3. **Agent Won't Start**

   ```bash
   # Use the Poetry endpoint (recommended)
   poetry run personal-agent
   
   # If that fails, check if dependencies are installed
   poetry install
   
   # For manual testing, activate environment first
   source .venv/bin/activate
   # Then run any commands or tests
   ```

4. **Port Already in Use**

   ```bash
   # Check what's using port 5001
   lsof -i :5001
   # Kill the process or change port in main.py
   ```

5. **MCP Server Issues**

   ```bash
   # Test MCP servers
   python tests/test_mcp_availability.py
   
   # Verify all tools are loaded
   poetry run test-tools
   
   # Test system initialization
   python tests/test_agent_init.py
   
   # Run complete test suite
   python tests/run_tests.py --category all
   
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
   # If Poetry scripts don't work, run directly using Python module
   cd /Users/egs/repos/personal_agent && source .venv/bin/activate
   python -m src.personal_agent.main
   
   # Or run test tools directly
   python tests/test_tools.py
   
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

# Add to the appropriate tools module in src/personal_agent/tools/
# For example, in src/personal_agent/tools/web.py for web-related tools
# Then update src/personal_agent/tools/__init__.py to include it
```

### Customizing Prompts

Edit the `system_prompt` in `src/personal_agent/core/agent.py` to modify agent behavior.

### Database Schema

Weaviate collection structure:

- **text**: Interaction content
- **timestamp**: When stored (RFC3339)
- **topic**: Category/topic

### Adding New MCP Servers

1. Install the MCP server: `npm install -g @modelcontextprotocol/server-<name>`
2. Add configuration to `src/personal_agent/config/mcp_servers.py` in the `MCP_SERVERS` dictionary
3. Create corresponding `@tool` function in the appropriate module under `src/personal_agent/tools/`
4. Update `src/personal_agent/tools/__init__.py` to include the new tool

## 📜 Available Commands

The project provides several convenient Poetry scripts:

```bash
# Run LangChain version (default, recommended)
poetry run personal-agent-langchain

# Run Smolagents version (experimental)
poetry run personal-agent

# Install MCP servers automatically
poetry run install-mcp-servers

# Test MCP server availability
poetry run test-mcp-servers

# Test all tools functionality
poetry run test-tools
```

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

- All 13 tools verified and working
- MCP integration stable and tested
- Web interface responsive and user-friendly
- Memory system storing and retrieving context effectively
- GitHub authentication and tool integration fully functional
- Comprehensive test suite with 100% success rate
- Debug infrastructure properly organized
- Ready for daily use with optional API key enhancement

---

## 🚀 Latest Updates & Changes

### Recent Major Improvements (December 2024)

#### ✅ Web Interface Fixes (Latest)

- **Problem**: Agent Info button in web interface resulted in 'not found' error, then "'str' object has no attribute 'name'" error when accessing agent info page
- **Root Cause**: URL mismatch (`/info` vs `/agent_info`) and smolagents tools stored as dictionary instead of list
- **Solution**:
  - Fixed button URL from `/info` to `/agent_info` in web template
  - Updated tool name extraction to use `list(smolagents_agent.tools.keys())` instead of `[tool.name for tool in tools]`
  - Added defensive handling for both dictionary and list tool formats
- **Impact**: Agent info page now displays correctly showing all 13 tools (filesystem.mcp_read_file, research.web_search, etc.)

#### ✅ Smolagents Framework Migration

- **Migration**: Successfully migrated from LangChain ReAct to HuggingFace smolagents multi-agent framework
- **Custom Integration**: Created MCP-smolagents bridge connecting Model Context Protocol servers to smolagents tools
- **Tool Discovery**: Automatic registration of all 13 MCP tools as smolagents SimpleTool objects
- **Impact**: More robust agent framework with better tool integration and multi-agent capabilities

#### ✅ GitHub Tool Integration Resolution

- **Problem**: GitHub search was experiencing parsing errors with large JSON responses
- **Solution**: Added `_sanitize_github_output()` function that parses GitHub responses and creates concise, formatted summaries
- **Impact**: GitHub search now works reliably without parsing errors

#### ✅ Modular Architecture Migration  

- **Before**: Monolithic `personal_agent.py` file with 1000+ lines
- **After**: Organized modular structure under `src/personal_agent/` with clear separation of concerns
- **Benefits**: Better maintainability, testing, and development experience

#### ✅ Enhanced Launch Instructions

- **Current Method**: `poetry run personal-agent`
- **Why**: Uses the Poetry endpoint for the latest refactored codebase with all recent fixes
- **Note**: Clean and simple launch method via Poetry script configuration

#### ✅ Comprehensive Testing Infrastructure

- **Added**: 20+ test files organized by category in `tests/` directory
- **Features**: Test runner with categories, debug scripts, system validation
- **Coverage**: All components from core initialization to GitHub integration

### System Architecture Updates

The agent now features:

- **Smolagents Framework**: HuggingFace multi-agent system as the core architecture
- **MCP Integration**: Custom bridge connecting Model Context Protocol to smolagents
- **Modular Design**: Clean separation between config, core, tools, web, and utils
- **Tool Discovery**: Automatic registration of MCP tools as smolagents SimpleTool objects
- **Dependency Injection**: Proper logger and component injection throughout
- **Resource Management**: Enhanced cleanup and error handling
- **Test Organization**: Categorized test suite with dedicated runner

---

**Personal AI Agent** - A comprehensive, smolagents-powered personal assistant with 13 integrated MCP tools that learns, remembers, and grows with you. 🚀
