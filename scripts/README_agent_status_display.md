# Agent Status Display Script

This script properly initializes the Personal AI Agent and displays comprehensive system status information. It's designed to provide a quick overview of the agent's configuration, capabilities, and current state.

## Features

- **Proper Agent Initialization**: Uses the same initialization pattern as `agno_main.py`
- **Reduced Log Spam**: Sets logging level to WARNING to minimize verbose output
- **Comprehensive Status Display**: Shows detailed information about all system components
- **Memory System Status**: Displays memory statistics and topic distribution
- **Functionality Testing**: Tests basic agent operations to verify everything is working
- **Rich Console Output**: Uses Rich library for beautiful, formatted terminal output

## Usage

### Basic Usage
```bash
python scripts/agent_status_display.py
```

### With Options
```bash
# Use remote Ollama server
python scripts/agent_status_display.py --remote

# Recreate knowledge base from scratch
python scripts/agent_status_display.py --recreate

# Use custom user ID
python scripts/agent_status_display.py --user-id "john_doe"

# Combine options
python scripts/agent_status_display.py --remote --user-id "test_user"
```

### Make it executable (optional)
```bash
chmod +x scripts/agent_status_display.py
./scripts/agent_status_display.py
```

## Command Line Options

- `--remote`: Use the remote Ollama server instead of the local one
- `--recreate`: Recreate the knowledge base from scratch (useful for testing)
- `--user-id USER_ID`: Specify a custom user ID (defaults to configured USER_ID)
- `--help`: Show help message and exit

## What It Displays

### 1. Agent Configuration
- Framework type (Agno)
- Model provider and name
- Memory system status
- Knowledge base status
- MCP integration status
- Debug mode status
- User ID and storage paths

### 2. Tool Summary
- Total number of tools available
- Built-in tools count
- MCP tools count
- MCP servers count

### 3. Detailed Tool Lists
- Built-in tools with descriptions
- MCP server tools with descriptions
- MCP server details (command, args, environment variables)

### 4. System Status
- Agent framework status
- Memory system status and storage location
- Knowledge base status and location
- LightRAG knowledge system status
- MCP integration status and server count

### 5. Memory System Status (if enabled)
- Total memories stored
- Average memory length
- Recent memories (24 hours)
- Most common topic
- Topic distribution breakdown

### 6. Functionality Tests
- Agent response test (basic query)
- Memory storage test (if memory enabled)
- Tool availability check

## Log Level Configuration

The script automatically sets the logging level to WARNING for the following components to reduce output spam:

- `agno` - Agno framework logs
- `personal_agent` - Personal agent logs
- `lightrag` - LightRAG system logs
- `httpx` - HTTP client logs
- `urllib3` - URL library logs
- `asyncio` - Async operation logs
- `aiohttp` - Async HTTP logs
- `mcp` - MCP protocol logs
- `ollama` - Ollama client logs

## Example Output

The script produces beautifully formatted output including:

```
🤖 Personal AI Agent - System Status Display
Initializing agent and displaying comprehensive status...

🔧 Using Ollama server: http://localhost:11434
👤 User ID: egs
🧠 Model: qwen2.5:14b

🚀 Initializing Personal AI Agent...
✅ Agent initialized successfully!

[Detailed configuration tables follow...]
```

## Error Handling

The script includes comprehensive error handling:

- Graceful handling of initialization failures
- Detailed error messages for troubleshooting
- Proper cleanup on exit
- Keyboard interrupt handling (Ctrl+C)

## Integration with Existing Code

This script follows the same patterns used in:

- `agno_main.py` for proper agent initialization
- `agno_agent.py` for accessing agent functions and status
- Existing configuration system for settings and paths

## Use Cases

1. **System Health Check**: Verify that all components are working correctly
2. **Configuration Verification**: Check that settings are applied correctly
3. **Troubleshooting**: Identify issues with memory, knowledge base, or MCP integration
4. **Development**: Quick status check during development and testing
5. **Documentation**: Generate current system status for documentation purposes

## Dependencies

The script uses the same dependencies as the main Personal AI Agent:

- `agno` - Agent framework
- `rich` - Terminal formatting
- `asyncio` - Async operations
- All Personal AI Agent modules and configurations
