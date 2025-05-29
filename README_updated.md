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
- 🚀 **Multi-Server Architecture**: 7 MCP servers (filesystem, GitHub, web, shell, fetch)
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
                   │  │    Database     │  │ (7 total)     │ │
                   │  └─────────────────┘  └───────────────┘ │
                   │                                         │
                   │  📁 File System    🐙 GitHub            │
                   │  🌍 Web Search     💻 Shell             │
                   │  🌐 URL Fetch      🔬 Research          │
                   │  🔍 Smart Search                        │
                   └─────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Python**: 3.11 or higher
- **Poetry**: For dependency management
- **Docker**: For Weaviate database
- **Ollama**: For local LLM inference
- **Node.js**: For MCP filesystem server

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

# Install MCP filesystem server
npm install -g @modelcontextprotocol/server-filesystem
```

### 3. Install and Setup Ollama

```bash
# Install Ollama (macOS)
brew install ollama

# Start Ollama service
ollama serve

# Pull required models
ollama pull qwen2.5:7b-instruct
ollama pull nomic-embed-text
```

### 4. Install Additional MCP Servers

```bash
# Install additional MCP servers for enhanced capabilities
npm install -g @modelcontextprotocol/server-github
npm install -g @modelcontextprotocol/server-brave-search
npm install -g @modelcontextprotocol/server-shell
npm install -g @modelcontextprotocol/server-fetch
```

### 5. Configure API Keys (Optional but Recommended)

For full functionality, add your API keys to `mcp.json`:

**GitHub Personal Access Token** (for repository search):

1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate a token with 'repo' and 'read:org' permissions
3. Add to `mcp.json` under `github.env.GITHUB_PERSONAL_ACCESS_TOKEN`

**Brave Search API Key** (for web search):

1. Visit <https://api.search.brave.com/app/keys>
2. Create an account and generate an API key
3. Add to `mcp.json` under `brave-search.env.BRAVE_API_KEY`

### 6. Start Weaviate Database

```bash
# Start Weaviate using Docker Compose
docker-compose up -d

# Verify Weaviate is running
curl http://localhost:8080/v1/.well-known/ready
```

## 💻 Usage

### 1. Start the Personal Agent

```bash
# Activate virtual environment and run
poetry run python personal_agent.py
```

### 2. Access Web Interface

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

### Environment Variables

```bash
# Optional: Override default configurations
export WEAVIATE_URL="http://localhost:8080"
export OLLAMA_URL="http://localhost:11434"
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
├── personal_agent.py      # Main application with 12 integrated tools
├── test_tools.py         # Tool verification script
├── test_mcp.py          # MCP server testing script
├── pyproject.toml       # Poetry dependencies
├── docker-compose.yml   # Weaviate setup
├── mcp.json            # MCP server configurations (7 servers)
├── README.md           # This documentation
└── .venv/              # Virtual environment
```

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
   python test_mcp.py
   
   # Verify all tools are loaded
   python test_tools.py
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

BSD 3-Clause License - see LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

### Development Setup

```bash
# Clone and setup
git clone <repository-url>
cd personal_agent
poetry install

# Test the setup
python test_tools.py
python test_mcp.py
```

---

**Personal AI Agent** - A comprehensive, MCP-powered personal assistant that learns, remembers, and grows with you. 🚀
