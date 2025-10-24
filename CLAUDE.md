# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Personal AI Agent is a sophisticated multi-agent AI system built on the Agno framework with comprehensive memory management, knowledge base integration, and local privacy. The system supports multiple users with isolated data storage, dual memory systems (local SQLite + LightRAG graph), and extensive tool integration including Google Search, Python execution, and MCP servers.

## Core Architecture

The system uses a modular, manager-based architecture:

- **AgnoPersonalAgent**: Main production agent with lazy initialization and async operations
- **Manager Classes**: Specialized components for models, memory, knowledge, tools, and users
- **Dual Storage**: Combined local (SQLite/LanceDB) and remote (LightRAG) systems
- **Multi-Interface**: Streamlit web UI, CLI, and REST API endpoints
- **Multi-User**: Dynamic user switching with complete data isolation

## Common Development Commands

### Installation and Setup
```bash
# Install dependencies
poetry install

# Install MCP servers
poe mcp-install

# Start LightRAG services (required for knowledge base)
./smart-restart-lightrag.sh

# Switch users
poe switch-user <user_id>
```

### Main Application Commands
```bash
# Start unified Streamlit interface (team mode default)
poe serve-persag

# Start in single-agent mode
poe serve-persag --single

# CLI interface (single agent)
poe cli

# Team CLI interface
poe team

# System management dashboard
poe dashboard
```

### Testing and Validation
```bash
# Run comprehensive tests
poe test-all

# Test specific components
poe test-tools          # Tool functionality
poe test-memory         # Memory system
poe mcp-test           # MCP server availability
poe test-unit          # Unit tests
poe test-integration   # Integration tests

# Run specific test files
pytest tests/test_agent_memory_manager.py -v
pytest memory_tests/test_comprehensive_memory_search.py -v
```

### Memory and Knowledge Management
```bash
# Store facts directly
poe store-fact "I work as a software engineer at Google"

# Clean memory system
poe memory-clean

# Restart LightRAG services
poe restart-lightrag

# Run memory system demo
poe demo-memory
```

### Development Utilities
```bash
# Display current configuration
poe config

# Generate documentation
poe docs

# Clean temporary files
poe clean

# Switch Ollama configuration
poe switch-ollama
```

## Key File Locations

### Core Agent Implementation
- `src/personal_agent/core/agno_agent.py` - Main agent class with manager-based architecture
- `src/personal_agent/core/agent_*_manager.py` - Specialized manager classes
- `src/personal_agent/core/semantic_memory_manager.py` - Dual memory system
- `src/personal_agent/core/knowledge_coordinator.py` - Unified knowledge querying

### Tool System
- `src/personal_agent/tools/memory_functions.py` - Standalone memory operations
- `src/personal_agent/tools/knowledge_tools.py` - Knowledge base operations
- `src/personal_agent/tools/personal_agent_tools.py` - System integration tools

### Configuration and User Management
- `src/personal_agent/config/settings.py` - Environment and configuration management
- `src/personal_agent/config/runtime_config.py` - Global configuration manager (centralized, thread-safe)
- `src/personal_agent/core/user_manager.py` - Multi-user support and switching
- `src/personal_agent/core/user_registry.py` - User profile registry with extended fields (gender, NPC status)
- `src/personal_agent/core/user_model.py` - User dataclass with validation
- `src/personal_agent/config/user_id_mgr.py` - User ID management

### Interfaces
- `src/personal_agent/streamlit/dashboard.py` - System management dashboard
- `src/personal_agent/tools/paga_streamlit_agno.py` - Main Streamlit interface
- `src/personal_agent/tools/rest_api.py` - REST API endpoints

## Development Patterns

### Memory System
The system uses dual storage:
- **Local Memory**: SQLite + LanceDB for fast semantic search and deduplication
- **Graph Memory**: LightRAG server for relationship mapping and complex reasoning
- Access through `AgentMemoryManager` or standalone functions in `memory_functions.py`

### Tool Integration
Tools are managed through `AgentToolManager`:
- Runtime registration/unregistration
- Parameter validation and introspection
- LLM-compatible formatting
- Categorization and discovery

### User Management
Multi-user support with complete isolation:
- User data stored under `$PERSAG_ROOT/agno/<user_id>/`
- Rich user profiles with extended fields (gender, NPC status for bot users, cognitive state)
- UserRegistry now uses global configuration manager instead of direct environment variables
- Dynamic path resolution and service coordination
- Use `poe switch-user <user_id>` to switch between users
- Web dashboard provides full user profile management with field validation

### Model Configuration
Supports multiple LLM providers:
- **Ollama**: Local models (qwen3:8b, llama3.1:8b recommended)
- **OpenAI**: API-based models
- **LM Studio**: Local server with OpenAI-compatible API
- Configuration through `AgentModelManager`

### Async Patterns
The system uses extensive async/await patterns:
- Agent initialization with `asyncio.Lock` for thread safety
- Async tool execution and response streaming
- Non-blocking memory and knowledge operations

## Environment Variables

Key environment variables in `.env`:
```bash
PERSAG_ROOT=/path/to/data/directory    # Data root directory
USER_ID=your_username                  # Current user ID
OLLAMA_URL=http://localhost:11434      # Ollama server URL
LIGHTRAG_URL=http://localhost:9621     # Knowledge server URL
LIGHTRAG_MEMORY_URL=http://localhost:9622  # Memory server URL
```

## Testing Strategy

The project includes comprehensive testing:
- Unit tests for individual components
- Integration tests for system interactions
- Memory system tests with 52 diverse memories and 13 search test cases
- Tool functionality validation
- MCP server availability testing

Use `poe test-all` to run the complete test suite, or run specific test categories as needed.

## Docker Services

LightRAG services run in Docker containers:
- Use `./smart-restart-lightrag.sh` for coordinated restart
- Services include knowledge server (port 9621) and memory server (port 9622)
- User synchronization ensures consistent state across containers

## Common Troubleshooting

1. **Ollama issues**: Check with `ollama list` and ensure models are pulled
2. **LightRAG services**: Restart with `./smart-restart-lightrag.sh`
3. **User switching**: Use `poe switch-user --status` to check current user
4. **Memory issues**: Run memory tests with `poe test-memory`
5. **MCP servers**: Test availability with `poe mcp-test`