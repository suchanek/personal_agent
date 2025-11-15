# Personal AI Agent - Copilot Instructions

## Project Overview

Personal AI Agent is a sophisticated multi-agent AI system built on the **Agno framework** with comprehensive memory management, knowledge base integration, and local privacy. The system supports multiple users with isolated data storage, dual memory systems, and extensive tool integration.

## Core Architecture

### Manager-Based Architecture
The system uses a modular, manager-based pattern with **AgnoPersonalAgent** as the main coordinator:

- **AgentModelManager**: LLM provider management (Ollama/OpenAI/LM Studio)
- **AgentInstructionManager**: 4-tier instruction levels (MINIMAL/CONCISE/STANDARD/EXPLICIT)
- **AgentMemoryManager**: Dual memory orchestration (SQLite + LightRAG graph)
- **AgentKnowledgeManager**: Knowledge base lifecycle management
- **AgentToolManager**: Dynamic tool registration and introspection

### Key Initialization Pattern
```python
# CRITICAL: Initialization must follow this exact order
# 1. Create Agno storage → 2. Create combined knowledge → 3. Load knowledge
# 4. Create semantic memory → 5. Initialize managers → 6. Assemble tools
# 7. Build instructions → 8. Wire Agent fields
```

### Dual Knowledge + Memory Architecture
**Dual Knowledge System**:
- **LightRAG Knowledge Server** (port 9621): Graph-based KB for relational queries
- **Semantic Vector KB** (LanceDB): Local fast retrieval with vector similarity

**Dual Memory System**:
- **Local Memory**: SQLite + LanceDB for fast semantic search and deduplication
- **LightRAG Memory Server** (port 9622): Separate container for memory relationship graphs
- **Unified API**: Single interface through `AgentMemoryManager` for both systems

### Multi-User Support
**Dynamic User System**: Complete user isolation with runtime switching
- User registry: `~/.persagent/user_registry.json`
- Current user: `~/.persagent/current_user.json`
- User data: `$PERSAG_ROOT/agno/<user_id>/` + `~/.persagent/<user_id>/`
- Switch via `poe switch-user <user_id>` or `python switch-user.py <user_id>`

## Development Workflow

### Essential Commands (Poe Tasks)
```bash
# Core interfaces
poe serve-persag                 # Unified Streamlit web interface (defaults to team mode)
poe serve-persag --single        # Single-agent mode
poe cli                          # CLI interface
poe team                         # Team CLI interface

# Development
poe test-all                     # Comprehensive test suite
poe test-memory                  # Memory system tests
poe mcp-test                     # MCP server availability
poe restart-lightrag             # Restart LightRAG services
poe switch-user <user_id>        # Switch user contexts

# Memory management
poe store-fact "content"         # Store facts directly
poe memory-clean                 # Clean memory system
```

### Testing Strategy
- **Memory Tests**: 52 diverse memories across multiple categories with 13 search test cases
- **Tool Tests**: Runtime validation of all built-in and MCP tools
- **Integration Tests**: Cross-component communication validation
- Use `pytest` for unit tests, custom test suites for system-wide validation

## Critical Patterns

### Async Initialization
All agent initialization uses `asyncio.Lock` for thread safety:
```python
async def _ensure_initialized(self) -> bool:
    async with self._init_lock:
        if not self._initialized:
            return await self._do_initialization()
```

### Tool Architecture
Tools are managed through **AgentToolManager** with runtime registration/unregistration:
- **Built-in**: DuckDuckGo Search, YFinance, Python execution, Shell commands
- **Filesystem**: `PersonalAgentFilesystemTools` with security restrictions
- **Memory**: `AgnoMemoryTools` (personal info about user)
- **Knowledge**: `KnowledgeTools` (factual content, documents)
- **MCP**: External integrations (GitHub, Brave Search, Puppeteer, Filesystem)

### Memory vs. Knowledge Tool Rules
- **Memory tools**: Personal information ABOUT THE USER (`store_user_memory`, `query_memory`)  
- **Knowledge tools**: Factual content, documents, poems, articles (`ingest_knowledge_text`, `query_knowledge_base`)
- **Critical Distinction**: Memory = personal user data, Knowledge = general factual content

### Environment Variables
Key variables in `.env`:
```bash
PERSAG_ROOT=/path/to/data/directory    # Data root (defaults to /Users/Shared/personal_agent_data)
USER_ID=your_username                  # Current user (managed dynamically)
OLLAMA_URL=http://localhost:11434      # Ollama server
LIGHTRAG_URL=http://localhost:9621     # Knowledge server (LightRAG KB)
LIGHTRAG_MEMORY_URL=http://localhost:9622  # Memory server (LightRAG Memory)
PROVIDER=ollama                        # LLM provider (ollama/openai/lm-studio)
LLM_MODEL=qwen3:4b                     # Recommended model for balance of speed/capability
INSTRUCTION_LEVEL=CONCISE              # Instruction sophistication level
```

## Common Issues & Solutions

### LightRAG Services
- **Issue**: Knowledge/memory operations failing
- **Solution**: Run `./restart-lightrag.sh` to restart Docker services

### Ollama Connection
- **Issue**: Model loading failures
- **Solution**: Check `ollama list`, ensure models pulled (`ollama pull qwen3:8b`)

### User Switching
- **Issue**: Data isolation problems
- **Solution**: Use `poe switch-user <user_id>` instead of manual environment changes

### Memory Deduplication
- **Issue**: Duplicate memories
- **Solution**: System has built-in semantic + exact deduplication with 0.8 similarity threshold

### "Port Already Allocated" Docker Issues
- **Issue**: Docker containers fail to start after user switching
- **Solution**: Use `./restart-lightrag.sh` which prevents port conflicts with intelligent cleanup

## File Structure Patterns

### Core Components
- `src/personal_agent/core/`: Manager classes and main agent
- `src/personal_agent/tools/`: Tool implementations and wrappers
- `src/personal_agent/config/`: Settings and MCP server configurations
- `memory_tests/`: Comprehensive memory system validation
- `examples/`: Usage patterns and integration examples

### Testing Conventions
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Memory tests: `memory_tests/` (comprehensive system validation)
- Analysis: `analysis/` (performance and capability testing)

## Integration Points

### MCP Server Integration
MCP servers are defined in `src/personal_agent/config/mcp_servers.py` and dynamically loaded:
- Install: `poe mcp-install`
- Test: `poe mcp-test`
- Servers create on-demand sessions with function wrappers

### Docker Services
LightRAG services run in containers with user synchronization:
- Knowledge server: port 9621
- Memory server: port 9622
- Management: `./restart-lightrag.sh`

## Configuration Locations

### User-Specific Storage
```bash
# Primary user data (configurable via PERSAG_ROOT)
$PERSAG_ROOT/agno/<user_id>/
├── agent_memory.db          # SQLite semantic memory
├── agent_sessions.db        # Session storage
├── knowledge/               # Source files for semantic KB
└── lancedb/                 # Vector embeddings

# User registry and Docker configs
~/.persagent/
├── current_user.json        # Active user ID
├── user_registry.json       # All registered users
├── lightrag_server/         # Knowledge Docker config
└── lightrag_memory_server/  # Memory Docker config
```

### Critical Files
- `src/personal_agent/config/user_id_mgr.py`: User ID and path management
- `src/personal_agent/core/user_manager.py`: Multi-user orchestration
- `switch-user.py`: CLI user switching script
- `restart-lightrag.sh`: Docker service management

This architecture enables both single-agent and multi-agent team modes through a unified interface while maintaining data isolation and comprehensive memory capabilities.