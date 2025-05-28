# Personal AI Agent

A sophisticated personal assistant that learns about you and provides context-aware responses using Ollama, Weaviate vector database, LangChain, and Model Context Protocol (MCP) integration.

## Features

- 🧠 **Persistent Memory**: Uses Weaviate vector database for semantic memory storage
- 🤖 **Local AI**: Powered by Ollama (qwen2.5:7b-instruct model)
- 🔍 **Semantic Search**: Finds relevant context from past interactions
- 🌐 **Web Interface**: Clean Flask-based web UI with knowledge base management
- 📊 **Topic Organization**: Categorize memories by topic
- 📁 **File Operations**: MCP filesystem integration for reading, writing, and analyzing files
- 🔧 **MCP Integration**: Model Context Protocol for extensible tool ecosystem
- 🎯 **ReAct Agent**: Uses LangChain's ReAct framework for intelligent tool usage
- 🚀 **Hybrid Architecture**: Combines persistent memory with file system operations
- 🗑️ **Memory Management**: Clear knowledge base functionality

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Flask Web UI  │───▶│  Personal Agent │───▶│   Ollama LLM    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                               │
                               ▼
                   ┌─────────────────────────────┐
                   │     Enhanced Capabilities   │
                   │                             │
                   │  ┌─────────────────┐        │
                   │  │ Weaviate Vector │        │
                   │  │    Database     │        │
                   │  └─────────────────┘        │
                   │                             │
                   │  ┌─────────────────┐        │
                   │  │  MCP Filesystem │        │
                   │  │     Server      │        │
                   │  └─────────────────┘        │
                   └─────────────────────────────┘
```

## Prerequisites

- **Python**: 3.11 or higher
- **Poetry**: For dependency management
- **Docker**: For Weaviate database
- **Ollama**: For local LLM inference
- **Node.js**: For MCP filesystem server

## Installation

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

### 4. Start Weaviate Database

```bash
# Start Weaviate using Docker Compose
docker-compose up -d

# Verify Weaviate is running
curl http://localhost:8080/v1/.well-known/ready
```

## Usage

### 1. Start the Personal Agent

```bash
# Run the agent
python3 personal_agent.py

# Or using Poetry
poetry run python personal_agent.py
```

### 2. Access Web Interface

Open your browser and navigate to: `http://127.0.0.1:5000`

### 3. Basic Interactions

#### Memory and Learning

```
User: My name is Eric and I enjoy Python programming
Agent: Nice to meet you, Eric! I've noted that you enjoy Python programming. 
       I'll remember this for future conversations.

User: What programming languages do I like?
Agent: Based on our previous conversation, you enjoy Python programming!

User: I prefer :param: style docstrings in Python
Agent: Noted! I'll remember that you prefer :param: style docstrings for Python code.
```

#### File Operations

```
User: Read the contents of /Users/egs/repos/personal_agent/README.md
Agent: [Uses mcp_read_file tool to read and display file contents]

User: List the files in my repos directory
Agent: [Uses mcp_list_directory to show directory contents]

User: Create a new Python file with a simple hello world script
Agent: [Uses mcp_write_file to create the file with appropriate content]
```

#### Intelligent File Search

```
User: Find Python files related to data science in my repos
Agent: [Uses intelligent_file_search to combine memory context with file system exploration]
```

## Available Tools

The agent has access to the following tools:

### Memory Tools

- **`store_interaction`**: Store important conversations in memory
- **`query_knowledge_base`**: Search past interactions for relevant context
- **`clear_knowledge_base`**: Reset all stored memories (via web UI button)

### File System Tools (via MCP)

- **`mcp_read_file`**: Read file contents
- **`mcp_write_file`**: Write content to files
- **`mcp_list_directory`**: List directory contents
- **`intelligent_file_search`**: Search files with memory-enhanced context

### Tool Usage Examples

#### Reading Files

```
User: "Show me the contents of my Python config file"
Agent uses: mcp_read_file("/path/to/config.py")
```

#### Writing Files

```
User: "Create a Python script that prints hello world"
Agent uses: mcp_write_file("/path/to/hello.py", "print('Hello, World!')")
```

#### Directory Exploration

```
User: "What files are in my project directory?"
Agent uses: mcp_list_directory("/Users/egs/repos/personal_agent")
```

#### Smart File Search

```
User: "Find files related to machine learning in my repos"
Agent uses: intelligent_file_search("machine learning", "/Users/egs/repos")
```

## Configuration

### Environment Variables

```bash
# Optional: Override default configurations
export WEAVIATE_URL="http://localhost:8080"
export OLLAMA_URL="http://localhost:11434"
export USE_WEAVIATE="true"
export USE_MCP="true"
```

### MCP Server Configuration

The agent is configured to use MCP filesystem server for file operations:

```python
MCP_SERVERS = {
    "filesystem": {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-filesystem", "/Users/egs/repos"],
        "description": "Access filesystem operations"
    }
}
```

### Memory Management

The agent automatically:

- Stores all interactions in Weaviate with timestamps and topics
- Searches for relevant context before responding
- Organizes memories by semantic similarity
- Stores file operations for future context
- Provides a "Reset Knowledge Base" button in the web interface

## Advanced Features

### Hybrid Intelligence

The agent combines:

1. **Persistent Memory**: Long-term learning from interactions
2. **File System Access**: Real-time file operations
3. **Context Integration**: Merges memory and file data for enhanced responses

### Example Advanced Workflow

```
1. User: "I'm working on a data science project with pandas"
   → Stored in memory with topic "data_science"

2. User: "Show me my pandas utilities file"
   → Agent searches memory for "pandas" context
   → Uses MCP to find and read relevant files
   → Combines both for enhanced response

3. User: "Add a new function to calculate correlation matrix"
   → Agent recalls pandas preference from memory
   → Reads existing utilities file
   → Writes enhanced file with new function
   → Stores the operation in memory for future reference
```

## Web Interface Features

- **Query Input**: Natural language interaction
- **Topic Classification**: Organize conversations by topic
- **Context Display**: Shows retrieved memories used in responses
- **Reset Knowledge Base**: Clear all stored memories with confirmation
- **Responsive Design**: Clean, modern interface

## Project Structure

```
personal_agent/
├── personal_agent.py      # Main application with MCP integration
├── pyproject.toml        # Poetry dependencies
├── docker-compose.yml    # Weaviate setup
├── mcp.json             # MCP configuration (legacy)
├── README.md            # This documentation
└── .venv/               # Virtual environment
```

## Dependencies

### Core Dependencies

- **langchain**: Framework for LLM applications
- **langchain-ollama**: Ollama integration
- **langchain-weaviate**: Weaviate vector store
- **weaviate-client**: Weaviate database client
- **flask**: Web framework
- **requests**: HTTP client
- **rich**: Enhanced logging

### MCP Dependencies

- **@modelcontextprotocol/server-filesystem**: File operations server

### AI Models

- **qwen2.5:7b-instruct**: Main conversation model
- **nomic-embed-text**: Text embedding model

## Features in Detail

### Memory System

- **Vector Storage**: All interactions stored as embeddings
- **Semantic Search**: Find related memories using similarity
- **Metadata**: Track timestamps and topics
- **Persistence**: Memories survive between sessions
- **Contextual Enhancement**: File operations stored for future reference

### MCP Integration

- **Filesystem Access**: Read, write, and list files
- **Async Processing**: Non-blocking file operations
- **Error Handling**: Graceful fallbacks when MCP unavailable
- **Memory Integration**: File operations stored in knowledge base

### Agent Capabilities

- **Tool Selection**: Intelligently chooses appropriate tools
- **Context Synthesis**: Combines memory and file system data
- **ReAct Framework**: Thought-Action-Observation loops
- **Multi-step Operations**: Can chain multiple tools together

## Troubleshooting

### Common Issues

1. **Weaviate Connection Failed**

   ```bash
   # Restart Weaviate
   docker-compose down && docker-compose up -d
   ```

2. **MCP Filesystem Server Not Found**

   ```bash
   # Install MCP filesystem server
   npm install -g @modelcontextprotocol/server-filesystem
   ```

3. **Ollama Model Not Found**

   ```bash
   # Pull required models
   ollama pull qwen2.5:7b-instruct
   ollama pull nomic-embed-text
   ```

4. **Permission Denied on File Operations**

   ```bash
   # Check file permissions and update MCP server path
   # Edit MCP_SERVERS configuration in personal_agent.py
   ```

### Logs and Debugging

- **Agent Logs**: Check terminal output for detailed logs
- **Weaviate Logs**: `docker-compose logs weaviate`
- **MCP Logs**: Check stderr output in agent logs
- **Debug Mode**: Flask runs in debug mode by default

## Development

### Adding New Tools

```python
@tool
def my_custom_tool(param: str) -> str:
    """Description of what the tool does."""
    # Tool implementation
    # Optionally store operation in memory
    if USE_WEAVIATE and vector_store is not None:
        store_interaction.invoke({
            "text": f"Custom operation: {param}", 
            "topic": "custom_tools"
        })
    return "Tool result"

# Add to tools list
tools = [
    store_interaction, 
    query_knowledge_base, 
    clear_knowledge_base,
    mcp_read_file,
    mcp_write_file,
    mcp_list_directory,
    intelligent_file_search,
    my_custom_tool
]
```

### Adding New MCP Servers

```python
# Add to MCP_SERVERS configuration
MCP_SERVERS = {
    "filesystem": {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-filesystem", "/Users/egs/repos"],
        "description": "Access filesystem operations"
    },
    "github": {
        "command": "npx",
        "args": ["@modelcontextprotocol/server-github"],
        "description": "GitHub repository access"
    }
}
```

### Customizing Prompts

Edit the `system_prompt` in `personal_agent.py` to modify agent behavior:

```python
system_prompt = PromptTemplate(
    template="""You are a helpful personal assistant...
    
    NEW CAPABILITIES:
    - Add your custom instructions here
    - Define new interaction patterns
    - Specify tool usage preferences
    
    {agent_scratchpad}""",
    input_variables=["input", "context", "tool_names", "tools", "agent_scratchpad"]
)
```

### Database Schema

Weaviate collection structure:

- **text**: Interaction content (includes file operations)
- **timestamp**: When stored (RFC3339 format)
- **topic**: Category/topic (e.g., "file_operations", "data_science")

## Security Considerations

- **File Access**: MCP filesystem server has access to specified directories only
- **Memory Storage**: All interactions are stored locally in Weaviate
- **No External Calls**: All processing happens locally
- **Permission Checks**: File operations respect system permissions

## Performance Tips

- **Memory Limit**: Large file operations are summarized before storage
- **Search Efficiency**: Use specific topics for better memory retrieval
- **Resource Management**: MCP servers are started on-demand
- **Cleanup**: Proper resource cleanup on shutdown

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions:

1. Check the troubleshooting section
2. Review logs for specific error messages
3. Ensure all dependencies are properly installed
4. Verify Weaviate and Ollama are running
