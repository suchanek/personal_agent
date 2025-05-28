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
# Activate virtual environment and run
poetry run personal_agent.py
```

### 2. Access Web Interface

Open your browser and navigate to: `http://127.0.0.1:5000`

### 3. Interact with Your Agent

- **Ask questions**: "What do you know about me?"
- **Share information**: "I like Python programming and 3D visualization"
- **Get help**: "Write a PyVista script to display a cube"
- **Categorize topics**: Use the topic field to organize memories

### Example Interactions

```
User: My name is Eric and I enjoy Python programming
Agent: Nice to meet you, Eric! I've noted that you enjoy Python programming. 
       I'll remember this for future conversations.

User: What programming languages do I like?
Agent: Based on our previous conversation, you enjoy Python programming!

User: Write a Python script for 3D visualization
Agent: I remember you like Python! Here's a PyVista script for 3D visualization...
```

## Configuration

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

## Project Structure

```
personal_agent/
├── personal_agent.py      # Main application
├── pyproject.toml        # Poetry dependencies
├── docker-compose.yml    # Weaviate setup
├── mcp.json             # MCP configuration
├── README.md            # This file
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

### AI Models

- **qwen2.5:7b-instruct**: Main conversation model
- **nomic-embed-text**: Text embedding model

## Features in Detail

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

## Troubleshooting

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
   # Check what's using port 5000
   lsof -i :5000
   # Kill the process or change port in personal_agent.py
   ```

### Logs and Debugging

- **Agent Logs**: Check terminal output for detailed logs
- **Weaviate Logs**: `docker-compose logs weaviate`
- **Debug Mode**: Flask runs in debug mode by default

## Development

### Adding New Tools

```python
@tool
def my_custom_tool(param: str) -> str:
    """Description of what the tool does."""
    # Tool implementation
    return "Tool result"

# Add to tools list
tools = [store_interaction, query_knowledge_base, my_custom_tool]
```

### Customizing Prompts

Edit the `system_prompt` in `personal_agent.py` to modify agent behavior.

### Database Schema

Weaviate collection structure:

- **text**: Interaction content
- **timestamp**: When stored (RFC3339)
- **topic**: Category/topic

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
