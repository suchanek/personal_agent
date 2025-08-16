## Agent Operating Instructions

### AI Persona
- Give concise responses.
- Minimize excess summaries.
- Do not use flowery language.
- Avoid excessive praise; be objective.

- You MUST answer concisely with fewer than 4 lines.
- IMPORTANT: You should minimize output tokens as much as possible.
- Only address the specific query or task at hand, avoiding tangential information.
- If you can answer in 1-3 sentences or a short paragraph, please do.
- You should NOT answer with unnecessary preamble or postamble.
- Assist with defensive security tasks only. Refuse to create, modify, or improve code that may be used maliciously.
- IMPORTANT: You must NEVER generate or guess URLs.
- Never introduce code that exposes or logs secrets and keys.
- When making changes to files, first understand the file's code conventions.
- Mimic code style, use existing libraries and utilities, and follow existing patterns.
- NEVER assume that a given library is available.
- IMPORTANT: DO NOT ADD ANY COMMENTS unless asked.
- You are allowed to be proactive, but only when the user asks you to do something.
- NEVER commit changes unless the user explicitly asks you to.
- Only use emojis if the user explicitly requests it. Avoid using emojis in all communication unless asked.

# Gemini Workspace Context

This document provides context for the Gemini agent to understand and effectively work with this project.

## Project Overview

## Project Overview

This project is a sophisticated personal AI assistant powered by the **Agno Framework**. It features a **dual knowledge base system**, integrating a remote **LightRAG** graph-based KB for complex, relational data and a local **semantic vector KB** (using LanceDB) for fast, direct retrieval. This hybrid approach, combined with native MCP integration, semantic memory management, and local Ollama AI, creates a powerful and versatile locally-run AI assistant.

## Dynamic Multi-User System

The agent now features a full-stack, dynamic multi-user system that allows for seamless user switching at runtime. This ensures strong data isolation and stable service management. The single source of truth for the current user is the `env.userid` file located in the `~/.persag` directory in the user's home directory. All user-specific configurations, data, and Docker service files are also stored in this centralized location, decoupling them from the project's source code. See [ADR-048](./refs/adr/048-decoupled-user-docker-config.md) and [ADR-058](./refs/adr/058-modular-user-id-management.md) for details.

### Key Components:
*   **`UserManager`**: The central orchestrator for all user-related operations (creation, switching, deletion).
*   **`user_id_mgr.py`**: A dedicated module that handles all user ID and user-specific path management, including the automatic creation of the `~/.persag` environment.
*   **`UserRegistry`**: A JSON-based registry to persistently manage user profiles.
*   **`LightRAGManager`**: A Python-native manager to control LightRAG Docker services and inject the current `USER_ID` dynamically.
*   **`smart-restart-lightrag.sh`**: A robust shell script to prevent port conflicts and ensure service stability during user switches. It now operates on the Docker configurations located in `~/.persag`.
*   **`switch-user.py`**: A CLI script for creating and switching between users.

## Personal Files

Files specific to the user, such as `eric_facts.json` and `eric_structured_facts.txt`, are now located in the `eric/` directory at the project root.

## Prerequisites

*   **Python**: 3.11 or higher
*   **Poetry**: For dependency management
*   **Docker**: For optional Weaviate database (if using vector storage) and LightRAG server
*   **Ollama**: For local LLM inference
*   **LMStudio**: For running MLX and other local models.
*   **Node.js**: For MCP servers

### LightRAG Server

The LightRAG server must be running for the agent to function correctly. It is managed via Docker Compose. To start or restart the LightRAG services with proper user context and port handling, use the new smart restart script:

```bash
./smart-restart-lightrag.sh
```

This script intelligently stops, cleans up, and restarts the containers, preventing common "port already allocated" errors.

## Installation and Dependencies

This is a Python project managed with `Poetry`.

1.  **Clone and Setup**

    ```bash
    git clone <repository-url> # Replace with actual repository URL
    cd personal_agent
    poetry install
    ```

2.  **First Run & Environment Setup**

    On the first run of any agent command (e.g., `poetry run paga_cli`), the system will automatically create a `.persag` directory in your home directory (`~/.persag`). This directory will be populated with the necessary default configurations, including the Docker configurations for the LightRAG services. You do not need to configure this manually.

3.  **Start LightRAG Server**

    Use the smart restart script to ensure a clean start. This script now automatically finds the Docker configurations in your `~/.persag` directory.
    ```bash
    ./smart-restart-lightrag.sh
    ```

4.  **Manage Users (CLI)**
    
    Use the `switch-user.py` script to create or switch between user contexts. This will automatically update configurations and restart services.
    ```bash
    # Create and switch to a new user named 'alice'
    python switch-user.py alice
    
    # Switch back to the 'eric' user
    python switch-user.py eric
    ```

5.  **Manage MCP & Ollama Servers**

    Use the provided scripts to manage your MCP and Ollama servers:

    ```bash
    # Switch to local Ollama server
    ./switch-ollama.sh local

    # Switch to remote Ollama server
    ./switch-ollama.sh remote

    # Check server status
    ./switch-ollama.sh status
    ```

6.  **Setup Ollama**

    ```bash
    # Install Ollama (macOS example)
    brew install ollama

    # Start Ollama service
    ollama serve -d

    # Pull recommended models
    ollama pull qwen2.5:7b-instruct
    ollama pull qwen3:1.7B
    ollama pull qwen3:8b
    ollama pull llama3.1:8b
    ollama pull nomic-embed-text
    ```

7.  **Configure Environment (`.env` file)**

    You can create a `.env` file in the project root for optional settings. The core user-specific paths are now managed automatically.

    ```bash
    # Optional: Filesystem paths for MCP server if you need to override defaults
    ROOT_DIR=/Users/your_username
    HOME_DIR=/Users/your_username

    # Optional: Override default data root. 
    # User-specific data will be stored in PERSAG_ROOT/agno/USER_ID/
    PERSAG_ROOT=/path/to/your/custom/data/location

    # Required: Ollama Configuration
    OLLAMA_URL=http://localhost:11434
    OLLAMA_DOCKER_URL=http://host.docker.internal:11434
    LMSTUDIO_URL="http://localhost:1234/v1" # LMStudio server

    # Optional: API keys for enhanced functionality
    GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here
    BRAVE_API_KEY=your_api_key_here
    ```

## Running the Agent

The project includes several entry points for running different agent configurations:

### Legacy - do not worry about these

*   **LangChain Agent**: `poetry run personal-agent-langchain`
*   **Smol-Agent**: `poetry run personal-agent-smolagent`

### Current

*   **Agno-Interface (Streamlit Web UI)**: `poetry run paga_streamlit` or `poetry run paga`. The UI is now a full-featured user management dashboard.
*   **Agno-Cli**: The CLI has been refactored for improved maintainability and organization. The main entry point remains `poetry run paga_cli`, but its internal structure has been modularized. See [ADR-008](./docs/adr/008-cli-refactor.md) for details.
    *   **Usage**: The CLI usage remains identical to before the refactor.
        ```bash
        # CLI usage remains identical
        poetry run paga_cli
        poetry run paga_cli --remote
        poetry run paga_cli --recreate
        ```

### Agent Initialization

The `AgnoPersonalAgent` now uses a **lazy initialization** pattern. This means the agent is created instantly without waiting for heavy components like models and memory systems to load. The actual initialization happens automatically and transparently the first time the agent is used (e.g., when `run()` is called).

- **Simplified Creation**: You no longer need to call an `async initialize()` method. Just instantiate the class directly: `agent = AgnoPersonalAgent(...)`.
- **Backward Compatibility**: The old `create_agno_agent()` factory function is still available but is now deprecated.
- **`--recreate` flag**: When the `--recreate` flag is used, the agent will clear all existing memories from both the local SQLite database and the LightRAG graph memory server upon its first use. This ensures a clean slate for the knowledge base and memory system.

## Testing

The project uses a custom testing setup.

*   **Run validation tests**:

    ```bash
    python3 tests/run_validation_test.py
    ```

    This will run the tests located in `tests/test_pydantic_validation_fix.py`.

*   **Run debug tests**:

    ```bash
    python3 tests/run_debug_test.py
    ```

*   **Run fact recall tests**:

    ```bash
    python3 tests/run_fact_recall_tests.py
    ```

*   **Test all functionality**: `poetry run test-tools`
*   **Test instruction level performance**: `python tests/test_instruction_level_performance.py`
*   **Test MCP servers**: `poetry run test-mcp-servers`
*   **Test memory system**: `python memory_tests/test_comprehensive_memory_search.py`
*   **Test tool call detection**: `python tests/test_tool_call_detection.py`
*   **Test memory synchronization**: `python test_memory_sync_fix.py`
*   **Test multi-user system**: `python test_user_id_propagation.py`

## Key Technologies

## Key Technologies

*   **agno**: Core framework for building the agent.
*   **Ollama**: For running local language models.
*   **LMStudio**: For running local MLX and other OpenAI-compatible models.
*   **Dual Knowledge Base**:
    *   **LightRAG**: For the remote, graph-based knowledge base, enabling relational and hybrid search.
    *   **LanceDB & SQLite**: For the local, semantic vector knowledge base and conversational memory.
*   **Poetry**: For dependency management.
*   **Streamlit**: For the agent's user interface.
*   **MCP (Model Context Protocol)**: For integrated servers and tools.

## Configuration

The agent's configuration has been significantly simplified. Core user-specific and Docker-related files are now managed automatically within the `~/.persag` directory in your home directory. 

### Environment Variables

For most use cases, you will not need to set any environment variables manually. The system uses sensible defaults and manages user-specific paths automatically. However, you can override certain settings by creating a `.env` file in the project root.

```bash
# Optional: Override the default location for all user data.
# Default is /Users/Shared/personal_agent_data
PERSAG_ROOT=/path/to/your/custom/data/location

# Optional: Override for MCP server if needed
ROOT_DIR="/Users/your_username"      
HOME_DIR="/Users/your_username"

# Optional API Keys
GITHUB_PERSONAL_ACCESS_TOKEN="token"   # GitHub integration
BRAVE_API_KEY="key"                   # Brave search (if using)

# Service URLs (optional overrides)
OLLAMA_URL="http://localhost:11434"   # Ollama server
# With Tailscale, the Ollama server on `tesla` is accessible at: http://tesla.tail19187e.ts.net:11434
WEAVIATE_URL="http://localhost:8080"  # Weaviate (if using)
```

### Model Configuration

The agent supports dynamic model switching through the web interface:

*   **qwen3-4b-mlx** (recommended, via LMStudio)
*   **qwen3:8b** (via Ollama)
*   **llama3.1:8b** (via Ollama)
*   **Any Ollama or LMStudio compatible model**

## Troubleshooting

### Common Issues

**1. Instruction Level Performance**

If you are experiencing slow response times, try changing the instruction level. You can do this by editing the `instruction_level` parameter in `src/personal_agent/core/agno_agent.py`.

**2. Ollama Connection Issues**

```bash
# Check if Ollama is running
ollama list

# Start Ollama service
ollama serve

# Test connection
curl http://localhost:11434/api/tags
```

**3. MCP Server Issues**

```bash
# Reinstall MCP servers
poetry run python scripts/install_mcp.py

# Test server availability
poetry run test-mcp-servers
```

**4. Docker Restart Issues ("Port already allocated")**

This issue is now largely prevented by the new multi-user system. Use the `smart-restart-lightrag.sh` script to ensure services are restarted cleanly.
```bash
./smart-restart-lightrag.sh
```

**5. Memory System Issues**

If you encounter issues with the memory system, consider the following:

*   **Clear all memories**: Use the `clear_all_memories.py` script for a unified approach to clear both local and graph memories.
    ```bash
    python3 scripts/clear_all_memories.py --no-confirm
    ```
*   **Wait for pipeline idle**: If clearing memories after ingestion, use `clear_memory_when_ready.py` to ensure the LightRAG pipeline is idle.
    ```bash
    python3 clear_memory_when_ready.py
    ```
*   **Test memory functionality**:
    ```bash
    python memory_tests/test_comprehensive_memory_search.py
    ```
*   **Check memory sync status**: In the Streamlit UI, use the "Memory Sync Status" section to check for inconsistencies between local and graph memories and sync them if needed.

**6. Tool Call Visibility**

If tools are being called but not visible in debug panels:

*   Check that you're using the latest version of the agent
*   Verify tool call detection is working: `python tests/test_tool_call_detection.py`
*   Review debug information in the Streamlit interface

## Issue Tracking

When requested to add an issue, add it to the `ISSUES.md` file. Each issue should be on a new line and must include the current git branch, the current date, and a timestamp.

## Project Structure

```
personal_agent/
├── src/personal_agent/
│   ├── cli/                  # CLI commands and parsing
│   ├── core/                 # Core agent, memory, user management, and initialization
│   ├── tools/               # Tool implementations
│   ├── config/              # Configuration management
│   └── web/                 # Web interface (Streamlit)
│       ├── components/      # Streamlit UI components
│       └── utils/           # Streamlit utility functions
├── tools/                   # Standalone tools and utilities
├── scripts/                 # Installation and utility scripts
├── memory_tests/           # Memory system tests
├── examples/               # Usage examples
├── docs/                   # Documentation
├── eric/                   # Personal files (e.g., eric_facts.json)
├── old/                    # Legacy or deprecated files
└── tests/                  # Test scripts and test files
```

## LightRAG API Endpoints

Here's a summary of the LightRAG API endpoints for reference:

### documents

*   `POST /documents/scan` - Scan For New Documents
*   `POST /documents/upload` - Upload To Input Dir
*   `POST /documents/text` - Insert Text
*   `POST /documents/texts` - Insert Texts
*   `DELETE /documents` - Clear Documents
*   `GET /documents` - Documents
*   `GET /documents/pipeline_status` - Get Pipeline Status
*   `DELETE /documents/delete_document` - Delete a document and all its associated data by its ID.
*   `POST /documents/clear_cache` - Clear Cache
*   `DELETE /documents/delete_entity` - Delete Entity
*   `DELETE /documents/delete_relation` - Delete Relation

### query

*   `POST /query` - Query Text
*   `POST /query/stream` - Query Text Stream

### graph

*   `GET /graph/label/list` - Get Graph Labels
*   `GET /graphs` - Get Knowledge Graph
*   `GET /graph/entity/exists` - Check Entity Exists
*   `POST /graph/entity/edit` - Update Entity
*   `POST /graph/relation/edit` - Update Relation

### ollama

*   `GET /api/version` - Get Version
*   `GET /api/tags` - Get Tags
*   `GET /api/ps` - Get Running Models
*   `POST /api/generate` - Generate
*   `POST /api/chat` - Chat

### default

*   `GET /` - Redirect To Webui
*   `GET /auth-status` - Get Auth Status
*   `POST /login` - Login
*   `GET /health` - Get Status

### Schemas

*   `Body_login_login_post`
*   `Body_upload_to_input_dir_documents_upload_post`
*   `ClearCacheRequest`
*   `ClearCacheResponse`
*   `ClearDocumentsResponse`
*   `DeleteDocByIdResponse`
*   `DeleteDocRequest`
*   `DeleteEntityRequest`
*   `DeleteRelationRequest`
*   `DeletionResult`
*   `DocStatus`
*   `DocStatusResponse`
*   `DocsStatusesResponse`
*   `EntityUpdateRequest`
*   `HTTPValidationError`
*   `InsertResponse`
*   `InsertTextRequest`
*   `InsertTextsRequest`
*   `PipelineStatusResponse`
*   `QueryRequest`
*   `QueryResponse`
*   `RelationUpdateRequest`
*   `ScanResponse`
*   `ValidationError`

### QueryParam Class

The `QueryParam` class defines the configuration for querying the LightRAG knowledge base.

```python
class QueryParam:
    """Configuration parameters for query execution in LightRAG."""

    mode: Literal["local", "global", "hybrid", "naive", "mix", "bypass"] = "global"
    """Specifies the retrieval mode:
    - "local": Focuses on context-dependent information.
    - "global": Utilizes global knowledge.
    - "hybrid": Combines local and global retrieval methods.
    - "naive": Performs a basic search without advanced techniques.
    - "mix": Integrates knowledge graph and vector retrieval.
    """

    only_need_context: bool = False
    """If True, only returns the retrieved context without generating a response."""

    only_need_prompt: bool = False
    """If True, only returns the generated prompt without producing a response."""

    response_type: str = "Multiple Paragraphs"
    """Defines the response format. Examples: 'Multiple Paragraphs', 'Single Paragraph', 'Bullet Points'."""

    stream: bool = False
    """If True, enables streaming output for real-time responses."""

    top_k: int = int(os.getenv("TOP_K", "60"))
    """Number of top items to retrieve. Represents entities in 'local' mode and relationships in 'global' mode."""

    max_token_for_text_unit: int = int(os.getenv("MAX_TOKEN_TEXT_CHUNK", "4000"))
    """Maximum number of tokens allowed for each retrieved text chunk."""

    max_token_for_global_context: int = int(
        os.getenv("MAX_TOKEN_RELATION_DESC", "4000")
    )
    """Maximum number of tokens allocated for relationship descriptions in global retrieval."""

    max_token_for_local_context: int = int(os.getenv("MAX_TOKEN_ENTITY_DESC", "4000"))
    """Maximum number of tokens allocated for entity descriptions in local retrieval."""

    conversation_history: list[dict[str, str]] = field(default_factory=list)
    """Stores past conversation history to maintain context.
    Format: [{"role": "user/assistant", "content": "message"}].
    """

    history_turns: int = 3
    """Number of complete conversation turns (user-assistant pairs) to consider in the response context."""

    ids: list[str] | None = None
    """List of ids to filter the results."""

    model_func: Callable[..., object] | None = None
    """Optional override for the LLM model function to use for this specific query.
    If provided, this will be used instead of the global model function.
    This allows using different models for different query modes.
    """

    user_prompt: str | None = None
    """User-provided prompt for the query.
    If proivded, this will be use instead of the default vaulue from prompt template.
    """
```