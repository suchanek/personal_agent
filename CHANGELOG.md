# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **Knowledge Coordinator Initialization**: Fixed a critical bug where the `KnowledgeCoordinator` was not being initialized with the local `agno_knowledge` base, preventing local and hybrid knowledge queries from functioning. The coordinator is now correctly instantiated in the `KnowledgeTools` constructor, ensuring reliable query routing. See [ADR-050](./refs/adr/050-knowledge-coordinator-initialization-fix.md) for details.

### Changed
- **Centralized Service Management**: Introduced a new `ServiceManager` to handle all Docker service operations, decoupling them from the `UserManager`. This improves modularity and simplifies the user switching process. A new `switch-user.py` script provides a unified CLI for managing user contexts. See [ADR-049](./refs/adr/049-centralized-service-management.md) for details.

### Changed
- **Decoupled User and Docker Configuration**: Refactored the entire configuration system to centralize all user-specific and Docker-related files into a `~/.persag` directory in the user's home directory. This decouples the agent's configuration from the project repository, establishes a single source of truth, and enables true multi-user isolation. The new `PersagManager` class handles automatic migration, validation, and provides a dynamic `get_userid()` function to ensure the correct user context is always used. See [ADR-048](./refs/adr/048-decoupled-user-docker-config.md) for details.

### Changed
- **Robust Docker User Synchronization**: The `DockerUserSync` class has been significantly refactored to improve stability and data integrity. The update introduces comprehensive input validation, robust error handling for file and subprocess operations, atomic file writes to prevent corruption, and more secure, reliable path detection. This ensures the user synchronization process is resilient and predictable. See [ADR-047](./refs/adr/047-robust-docker-user-synchronization.md) for details.

### Added
- **Non-Blocking Background Tool**: Introduced a new `run_in_background` tool to allow the agent to execute long-running shell commands without blocking the main execution thread. This enhances the agent's ability to manage background processes and improves overall responsiveness. See [ADR-046](./refs/adr/046-background-tool-execution.md) for details.

### Changed
- **Enhanced Ollama Reasoning Team**: The standalone Ollama Reasoning Team (`paga_team_cli`) has been significantly upgraded. It now integrates a full instance of the `AgnoPersonalAgent` as its memory and knowledge manager, providing feature parity with the main agent. The CLI has been rebuilt with `rich` and the `CommandParser` to support advanced memory commands (`!`, `?`, `@`) and deliver a more intuitive, consistent user experience. See [ADR-045](./refs/adr/045-enhanced-ollama-reasoning-team.md) for details.

### Added
- **Semantic Knowledge Ingestion Tools**: Introduced a new `SemanticKnowledgeIngestionTools` toolkit to provide a complete suite of ingestion tools (`ingest_semantic_file`, `ingest_semantic_text`, etc.) for the local LanceDB-based semantic knowledge base. This achieves feature parity with the LightRAG ingestion tools and allows users to easily populate the local vector store. See [ADR-044](./refs/adr/044-semantic-knowledge-ingestion-and-unified-querying.md) for details.

### Fixed
- **Unified Knowledge Querying**: Refactored the `query_knowledge_base` tool to use the central `KnowledgeCoordinator`. This resolves a bug where `mode="local"` failed to query the semantic knowledge base and ensures all knowledge queries are intelligently and reliably routed to the correct backend (local semantic or LightRAG). See [ADR-044](./refs/adr/044-semantic-knowledge-ingestion-and-unified-querying.md) for details.
- **Agno Role Mapping Bug**: Applied a workaround to fix a critical bug in the `agno` framework where the `system` role was incorrectly mapped to `developer`, causing errors with OpenAI-compatible APIs like LMStudio. The role mapping is now corrected at runtime for all model providers. See [ADR-030](./refs/adr/030-agno-role-mapping-bug-workaround.md) for details.


### Changed
- **Agent Initialization**: Refactored the `AgnoPersonalAgent` to use a lazy initialization pattern. The agent is now instantiated synchronously (`agent = AgnoPersonalAgent(...)`) and heavy initialization occurs automatically on first use. This simplifies agent creation, improves code clarity, and makes it easier to use agents within teams. The old `create_agno_agent()` factory is now deprecated but maintained for backward compatibility. See [ADR-043](./refs/adr/043-agno-agent-lazy-initialization.md) for details.

### Fixed
- **Team Memory Tools**: Resolved a validation issue in the `get_recent_memories` tool that occurred when the agent was used within a team context. The tool now correctly handles default parameter values.
- **Team Agent Responses**: Fixed a bug where the `AgnoPersonalAgent`, when used as a team member, would incorrectly return raw JSON tool calls instead of executing them and returning a natural language response. The agent's internal instructions have been improved to ensure proper tool execution.


### Added
- **Standalone Ollama Reasoning Team**: Introduced a new, lightweight, standalone multi-agent team that uses local Ollama models for reasoning tasks. This team is defined in `src/personal_agent/team/ollama_reasoning_multi_purpose_team.py` and can be run via the `paga_team_cli` command. It provides a flexible way to perform tasks like web search, financial analysis, and calculations without the full overhead of the `AgnoPersonalAgent`. See [ADR-042](./refs/adr/042-ollama-reasoning-team.md) for more details.
- **Direct Knowledge Query Tool**: Added a new `query_lightrag_knowledge_direct` tool to the `KnowledgeTools` toolkit. This tool allows for direct, unfiltered queries to the LightRAG knowledge base, providing more control for specific use cases like the new reasoning team.

### Fixed
- **Qwen3 Tool Calling**: Resolved a critical issue where the `qwen3` model failed to execute tool calls. The `AgentModelManager` has been reverted to use the standard `agno.models.ollama.Ollama` class instead of the unreliable `OllamaTools` wrapper, restoring reliable tool-calling functionality. See [ADR-041](./refs/adr/041-qwen3-tool-calling-fix.md) for details.


### Fixed
- **LightRAG URL Specificity**: Corrected an issue where tools could ambiguously target the wrong LightRAG server. All LightRAG-interacting methods now require an explicit `url` parameter, ensuring that requests for knowledge and memory are always sent to the correct server instance. See [ADR-040](./refs/adr/040-explicit-lightrag-url-parameterization.md) for details.

### Changed
- **Model Tuning**: Adjusted the default temperature and top-k parameters for the `qwen3` model to improve the quality and coherence of its responses.

### Added
- **Qwen3-8B Summary**: Added a new document summarizing the features and capabilities of the Qwen3-8B model.

### Chore
- **Project Organization**: Moved several markdown files and scripts into the `refs/` and `scripts/` directories to improve project structure and maintainability.


### Fixed
- **LightRAG URL Configuration**: Corrected the LightRAG URL configuration to ensure proper communication with the LightRAG server. The `query_lightrag_knowledge_direct` method in `agno_agent.py` now consistently uses `LIGHTRAG_URL` for knowledge queries. The `knowledge_coordinator.py` now correctly imports both `LIGHTRAG_URL` (for knowledge queries) and `LIGHTRAG_MEMORY_URL` (for memory queries) to ensure accurate routing between the knowledge and memory LightRAG instances. This resolves issues where the agent was attempting to query the wrong LightRAG instance.

### Changed
- **Topic Classification**: Enhanced the topic classification system by adding a comprehensive `relationships` category. This resolves a bug where statements about social connections were misclassified as `unknown` and improves the agent's ability to understand and organize memories about personal and professional relationships. See [ADR-039](./refs/adr/039-enhanced-topic-classification-for-relationships.md) for details.





### Fixed
- **Memory Clearing**: Resolved a critical bug where clearing memories via scripts did not consistently update the agent's state. The fix standardizes database connection handling and ensures all components are properly synchronized. See [ADR-038](./refs/adr/038-standardized-memory-clearing.md).

### Changed
- **Separation of Concerns**: Refactored the unified `MemoryAndKnowledgeTools` class into two distinct, focused toolkits: `KnowledgeTools` for factual data and `AgnoMemoryTools` for personal user information. This improves architectural clarity, enhances agent guidance through descriptive docstrings, and provides clearer boundaries between knowledge and memory operations. See [ADR-037](./refs/adr/037-knowledge-memory-tool-separation.md) for details.

### Changed
- **Decisive Tool Usage**: Overhauled the agent's instructions to be more decisive and accurate. The new prompts establish a clear distinction between "Memory" (user-specific info) and "Knowledge" (factual info), provide an explicit decision-making flowchart, and map common queries directly to specific tool calls (e.g., "what do you know about me" -> `get_all_memories()`). This resolves issues of tool hesitation and incorrect tool selection. See [ADR-036](./refs/adr/036-tool-use-hesitation-fix.md) for details.

### Fixed
- **Toolkit Initialization**: Corrected a bug in the `MemoryAndKnowledgeTools` `Toolkit` where `async` tools were not being registered correctly. All sync and async tools are now passed to the parent constructor at once, ensuring all tools are available to the agent.

### Changed
- **Unified Tool Architecture**: Refactored the agent's architecture by consolidating all memory and knowledge-related tools into a single, cohesive `MemoryAndKnowledgeTools` class. This simplifies agent initialization, improves modularity, and aligns with `agno` framework best practices. See [ADR-035](./refs/adr/035-unified-memory-and-knowledge-tools.md) for details.

### Fixed
- **Model Compatibility**: Resolved a startup failure with `deepseek-r1` models by documenting that they lack required tool-calling support and recommending compatible alternatives like `qwen3:8b`.


### Fixed
- **Instruction Override**: Removed a flawed optimization that replaced detailed instructions with a simplified version for prompts over 1000 characters. This ensures the agent always uses the full, intended instruction set, preserving its configured sophistication and performance. See [ADR-034](./refs/adr/034-smollm2-optimization-fix.md) for details.

### Changed
- **Agno Response Handling Simplification**: Refactored agent response processing to trust Agno's built-in parsing, eliminating redundant content extraction and simplifying streaming logic. This reduces code complexity and improves maintainability. See [ADR-033](./docs/adr/033-agno-response-handling-simplification.md) for details.

### Fixed
- **Tool Call Extraction**: Resolved an issue where tool calls were not consistently displayed in the Streamlit sidebar, despite successful execution. Implemented an event-based collection strategy to ensure reliable visibility of tool usage. See [ADR-033](./docs/adr/033-agno-response-handling-simplification.md) for details.
- **Memory Grammar Conversion**: Corrected an issue where memories stored in third-person were not consistently converted to second-person when presented to the user, improving conversational flow and identity consistency. See [ADR-032](./docs/adr/032-memory-grammar-conversion-fix.md) for details.

### Added
- **Formalized Agent Personality**: Embraced and formalized the agent's emergent "AI Friend" personality as a core feature. The agent is now explicitly guided to use memories creatively for building rapport and generating personalized content, while maintaining a strong distinction between its identity and the user's. See [ADR-031](./docs/adr/031-formalizing-emergent-agent-personality.md) for details.
- **Issue Tracking**: Added a new `ISSUES.md` file for internal tracking of running issues and todos.

## [dev/v0.11.0] - 2025-07-18

### Changed
- **Reaffirmed Ephemeral MCP Agent Architecture**: Reverted the MCP tool handling to the original, stable ephemeral agent pattern. This resolves critical stability and `asyncio` context issues discovered in the experimental `v0.10.1` and `v0.10.2` branches, which have now been abandoned. The ephemeral pattern, where a new client is created for each tool call, is now mandated as a core architectural requirement for all MCP interactions. See [ADR-028](./refs/adr/028-ephemeral-mcp-tool-agents.md) for details.

## [dev/v0.8.14] - 2025-07-17

### Changed
- **Environment Variable Consolidation**: The `.env` files have been cleaned up and reorganized to separate secrets, remove unused variables, and rely on sensible defaults. This improves security and maintainability. See [ADR-020](./refs/adr/020-environment-variable-consolidation.md) for details.

### Fixed
- **Deprecation Warnings**: Implemented a multi-layered strategy to suppress noisy `DeprecationWarning` messages from third-party libraries, providing a cleaner developer experience.

## [dev/v0.8.13] - 2025-07-16

### Changed
- **Major Agent Refactoring**: The monolithic `AgnoPersonalAgent` class (2,800+ lines) has been refactored into a modular architecture with specialized manager classes (`AgentModelManager`, `AgentInstructionManager`, `AgentMemoryManager`, `AgentKnowledgeManager`, `AgentToolManager`). This significantly improves maintainability, testability, and adherence to the Single Responsibility Principle. See [ADR-019](./refs/adr/019-modular-agent-architecture.md) for details.
- **CodeGPT Refactor Analysis**: A comprehensive analysis of the refactored codebase was performed by CodeGPT, validating the new modular architecture and its benefits. See the full analysis in [docs/CODEGPT_REFACTOR_ANALYSIS.md](./refs/CODEGPT_REFACTOR_ANALYSIS.md).

### Fixed
- **LightRAG Memory Port Fix**: Corrected a critical connection error where the agent was attempting to connect to the LightRAG Memory Server on the wrong port (`9623` instead of `9622`), which was preventing the dual-memory system from functioning correctly.
- **Deprecation Warnings**: Suppressed `DeprecationWarning` messages from `spacy` and `weasel` libraries to reduce console noise.

## [dev/v0.8.13] - 2025-07-16

### Changed
- **Major Agent Refactoring**: The monolithic `AgnoPersonalAgent` class (2,800+ lines) has been refactored into a modular architecture with specialized manager classes (`AgentModelManager`, `AgentInstructionManager`, `AgentMemoryManager`, `AgentKnowledgeManager`, `AgentToolManager`). This significantly improves maintainability, testability, and adherence to the Single Responsibility Principle. See [ADR-019](./refs/adr/019-modular-agent-architecture.md) for details.
- **CodeGPT Refactor Analysis**: A comprehensive analysis of the refactored codebase was performed by CodeGPT, validating the new modular architecture and its benefits. See the full analysis in [docs/CODEGPT_REFACTOR_ANALYSIS.md](./refs/CODEGPT_REFACTOR_ANALYSIS.md).

### Fixed
- **LightRAG Memory Port Fix**: Corrected a critical connection error where the agent was attempting to connect to the LightRAG Memory Server on the wrong port (`9623` instead of `9622`), which was preventing the dual-memory system from functioning correctly.

## [dev/v0.8.12] - 2025-07-15

### Fixed
- **Definitive Port Standardization**: Implemented a final, consistent port mapping standard to resolve all connection failures between the application and the LightRAG services. The Knowledge Base server now correctly runs on host port `9621` and the Memory server on `9622`. See [ADR-017](./refs/adr/017-definitive-port-standardization.md) for details.
- **Service Reliability**: Enhanced Docker health checks and optimized PDF processing settings (timeouts, chunk sizes) to improve the stability and reliability of the LightRAG services.

## [dev/v0.8.12] - 2025-07-15

### Fixed
- **Critical Port Configuration Fix**: Resolved a widespread connection failure issue where the application was incorrectly configured to use internal Docker container ports instead of the exposed host ports. The Knowledge Base server now correctly runs on host port `9621` and the Memory server on `9622`. See [ADR-016](./refs/adr/016-consistent-port-mapping.md) for details.

## [dev/v0.8.11] - 2025-07-14

### Added
- **Persistent User Context**: Implemented a new system where the `env.userid` file acts as the single source of truth for the current user. This ensures that the user context is persistent across application restarts. See [ADR-015](./refs/adr/015-persistent-user-context.md) for details.
- New test suite (`test_persistent_user_context.py`) to validate the new persistent user context logic.

### Changed
- **`AgnoPersonalAgent` Initialization**: The agent's initialization logic is now more robust. If the agent is initialized with a user ID that differs from the one in `env.userid`, it will automatically trigger a formal user switch, ensuring the change is persisted.
- **`UserManager`**: The `switch_user` method now writes the new user ID to the `env.userid` file, making the change persistent.
- **Configuration Loading**: The application now reads `env.userid` at startup to set the initial user context.

### Fixed
- **Dedicated Service Ports**: Resolved a critical issue where both LightRAG services were configured to use the same `PORT` environment variable. They now use dedicated `LIGHTRAG_SERVER_PORT` and `LIGHTRAG_MEMORY_PORT` variables to prevent port conflicts. See [ADR-014](./refs/adr/014-dedicated-service-ports.md) for details.
- **Test Script Safety**: The `test_persistent_user_context.py` script now uses a `.test` suffixed file to avoid interfering with the actual `env.userid` file.

## [dev/0.9.0] - 2025-07-13

### Added
- **Dynamic Multi-User Management System**: Implemented a comprehensive, full-stack multi-user system. This allows for dynamic user switching at runtime without requiring an application restart. See [ADR-013](./refs/adr/013-dynamic-multi-user-management.md) for details.
- **UserRegistry**: A new JSON-based registry (`src/personal_agent/core/user_registry.py`) to persistently manage user profiles.
- **UserManager**: A central orchestrator (`src/personal_agent/core/user_manager.py`) for all user-related operations, including creation, switching, and deletion.
- **LightRAGManager**: A Python-native manager (`src/personal_agent/core/lightrag_manager.py`) to control LightRAG Docker services and inject the current `USER_ID` dynamically.
- **Smart Docker Restart**: A robust shell script (`smart-restart-lightrag.sh`) and Python module (`SmartDockerRestart`) to prevent port conflicts and ensure service stability during restarts.
- **Full-Featured Streamlit UI**: The Streamlit dashboard now includes a complete user management interface, allowing for creating, switching, and managing users, as well as viewing real-time, user-specific data.
- **Dynamic Configuration**: The system now uses `get_current_user_id()` and `refresh_user_dependent_settings()` to dynamically update the user context across the application.
- New test suite (`test_user_id_propagation.py`) to validate the multi-user implementation.

### Changed
- **`SemanticMemoryManager`**: Refactored to be fully user-aware by dynamically resolving the `USER_ID` for all memory operations.
- **Docker Configuration**: `docker-compose.yml` files for LightRAG services were updated to accept a `USER_ID` environment variable, ensuring containers run in the correct user context.
- **Streamlit UI**: Replaced all placeholder data with live, user-specific data from the new management modules.


## [dev/0.8.9] - 2025-07-12

### Added
- **Enum-Based Memory Storage Status**: Implemented a new enum-based system (`MemoryStorageStatus`) and a structured result dataclass (`MemoryStorageResult`) for memory storage operations. This replaces ambiguous `None` returns with a clear, type-safe, and extensible status system, providing detailed metadata on storage outcomes, including duplicate detection with similarity scores and dual-storage success status. See [ADR-011](./refs/adr/011-enum-based-memory-status.md) for details.
- New test suites (`test_enum_memory_status.py`, `test_dual_storage_enum_status.py`) to validate the new memory status system.

### Changed
- The `store_user_memory` tool and underlying `SemanticMemoryManager.add_memory` method were refactored to return a `MemoryStorageResult` object instead of a simple string or tuple. This provides a structured, detailed, and machine-readable outcome for every memory storage attempt.
- The tool's user-facing output for memory storage is now more informative, using emojis to clearly indicate success (✅), partial success (⚠️), duplicates (🔄), and failures (❌).

### Fixed
- Refined agent instructions to prevent the agent from incorrectly storing its own creative writing and other actions as user memories. The new instructions are more precise and less aggressive, leading to higher quality and more relevant memory storage.
- Updated the CLI entry point to use the refined `CONCISE` instruction level, ensuring consistent behavior across all interfaces.

## [0.11.0] - 2024-07-19

### Added
- New documentation: `docs/MEMORY_COMMAND_SUMMARY.md` providing a comprehensive overview of all memory-related commands.

### Changed
- **Docker Smart Restart and Module Refactoring**: Implemented a smart restart capability to allow forced restarts of Docker containers even when USER_IDs are consistent. Refactored the Docker synchronization logic by moving the `DockerUserSync` class from `scripts` to a new `src/personal_agent/core/docker` module, eliminating circular dependencies and improving architectural clarity. See [ADR-012](./refs/adr/012-docker-smart-restart.md) for details.
- **AntiDuplicateMemory Refactor for Polymorphism**: Refactored the `AntiDuplicateMemory` class to align its method signatures with the parent `Memory` class. This change ensures polymorphic compatibility, allowing `AntiDuplicateMemory` to be used as a drop-in replacement for `Memory`, which improves code robustness and maintainability. See [ADR-010](./refs/adr/010-anti-duplicate-memory-refactor.md) for details.
- **CLI Refactor for Maintainability**: The `agno_main.py` file was refactored to improve maintainability and organization. Memory-related CLI commands and initialization logic were extracted into new modules (`src/personal_agent/cli/` and `src/personal_agent/core/agno_initialization.py`). This significantly reduced the size and complexity of the main CLI file, enhancing modularity, testability, and extensibility while maintaining full backward compatibility. See [ADR-008](./refs/adr/008-cli-refactor.md) for details.
- **Comprehensive Memory System Technical Summary**: Updated `COMPREHENSIVE_MEMORY_SYSTEM_TECHNICAL_SUMMARY.md` to reflect the CLI refactor, enhanced memory tool CLI, and new testing infrastructure.

### Fixed
- **Agent Initialization Docker Consistency**: The agent initialization process now forces a restart of Docker containers, ensuring a clean and consistent state at every startup and preventing issues with stale containers or port conflicts.
- **Critical Port Mapping in Memory Server**: Corrected a port mismatch in the `lightrag_memory_server` Docker configuration. The internal container port was incorrectly set to `9621` while the exposed port was `9622`, causing connection failures. Both are now correctly configured to `9622`, restoring access to the memory server.
- **Recreate Flag Memory Safety Fix**: Resolved a critical memory safety vulnerability where the `--recreate` flag could lead to accidental data loss. The fix ensures that user memories are preserved by default and are only cleared when explicitly requested via the `--recreate` flag, with proper synchronization across both local SQLite and LightRAG graph memory systems. See [ADR-009](./refs/adr/009-recreate-flag-memory-safety-fix.md) for details.

## [0.8.8] - 2025-07-10

## [0.8.7] - 2025-07-16

### Fixed
- **Memory Clearing**: Resolved a critical bug where clearing memories via scripts did not consistently update the agent's state. The fix standardizes database connection handling and ensures all components are properly synchronized. See [ADR-016](./refs/adr/016-standardized-memory-clearing.md).
- **Memory Restatement**: Ensured all user memories are stored in a consistent third-person format to improve knowledge graph accuracy and entity recognition.

### Added
- **Scripts Cheatsheet**: Added `SCRIPTS_CHEATSHEET.md` to provide a quick reference for common project scripts and tools.
- **Memory Clearing Test**: Added `test_memory_clearing_fix.py` to verify the memory clearing fix.

### Removed
- **Legacy Script**: Removed the unused `scripts/clear_lightrag_data.py` script.



### Added
- **Enriched Graph Ingestion Pipeline**: The `store_graph_memory` tool now uses a sophisticated, hybrid approach to build the knowledge graph. The agent performs local NLP (coreference resolution, entity/relationship extraction) to generate rich metadata, which is then embedded in a text file and uploaded to LightRAG. This guides the server's native ingestion pipeline, resulting in a more accurate and detailed graph. See [ADR-007](./refs/adr/007-direct-knowledge-graph-construction.md) for details.
- New `nlp_extractor.py` module for NLP tasks.
- New test suites (`test_knowledge_graph_relationships.py`, `run_kg_relationship_test.py`) to validate the new memory system.
- New `inject_eric_facts_v2.py` script to leverage the new memory system.

### Changed
- The `store_graph_memory` tool was completely overhauled to use the new Enriched Graph Ingestion Pipeline, replacing the previous direct text upload.

## [0.8.6] - 2025-07-10

### Added
- The `docmgr` tool now supports a `--json` flag for machine-readable output.

### Changed
- Project version bumped to `0.8.6`.

## [0.8.52] - 2025-07-09

### Added
- Implemented an intelligent Memory Restatement System to improve knowledge graph mapping. User facts are now converted to the third person for graph storage while remaining in the first person for local semantic memory. For more details, see [ADR-004: Memory Restatement System](./refs/adr/004-memory-restatement-system.md).
- Added a comprehensive test suite for the Memory Restatement System (`tests/test_fact_restatement.py`).

### Changed
- The `store_graph_memory()` method now uses restated content for file uploads to ensure proper entity mapping in the knowledge graph.
- The core agent's `_restate_user_fact()` method was enhanced with more robust pronoun and possessive conversion using regex with word boundaries.

## [0.8.51] - 2025-07-09

### Added
- New `show-config` tool with color-coded output and a `--json` option for viewing system configuration.
- Healthcheck for the `lightrag_memory_server` to monitor its operational status.

### Fixed
- Increased service timeouts and added TCP keepalive settings in the `lightrag_memory_server` to prevent connection drops during long-running operations.

### Chore
- Updated Python dependencies, including `lightrag-hku`, `googlesearch-python`, `pycountry`, and `pyyaml`.

## [0.8.50] - 2025-01-09

### Added
- **Unified Memory Management System** to clear semantic (local) and graph (LightRAG) memories simultaneously. Includes a core `MemoryClearingManager` and a `clear_all_memories.py` CLI tool with safety features like dry-run and verification. See [ADR-005](./refs/adr/005-unified-memory-and-doc-management.md) for details.
- **Enhanced LightRAG Document Manager** (`docmgr.py`) using modern, API-based operations, eliminating the need for server restarts. Includes features like batch deletion, pattern matching, and a retry mechanism. See [ADR-005](./refs/adr/005-unified-memory-and-doc-management.md) for details.

### Removed
- Removed legacy and outdated scripts: `scripts/fix_lightrag_data.py` and `scripts/fix_lightrag_persistent_storage.py`.

## [0.8.3] - 2025-07-05

### Added
- **Knowledge Graph Memory System** and a **Unified Knowledge Architecture**. This introduces a dual memory paradigm combining local semantic search with a graph-based (LightRAG) memory system. See [ADR-003](./refs/adr/003-knowledge-graph-memory-system.md) for the full architecture.
- **Knowledge Coordinator** to intelligently route queries between the local semantic and LightRAG graph systems.
- A dedicated, containerized **LightRAG Memory Server** for memory-specific operations with user isolation.

### Changed
- The `store_user_memory` tool now persists memories to both the local and graph systems simultaneously.
- The `query_knowledge_base` tool now uses the Knowledge Coordinator for intelligent routing.
- The topic classifier was enhanced with whole-word matching and an expanded keyword dictionary for greater accuracy.

### Fixed
- Resolved a Pydantic validation issue (`"file_path": null`) by switching to a file-upload-based approach for storing memories in the LightRAG graph.

## [0.8.1] - 2025-07-04

### Added
- The LightRAG service is now a **decoupled, standalone service** with its own Docker configuration, managed independently of the main application. For more details, see [ADR-001](./refs/adr/001-decoupled-lightrag-service.md).
- A `LIGHTRAG_URL` environment variable now acts as the single source of truth for the LightRAG server's address.
- The `switch-ollama.sh` script was enhanced to also switch the `LIGHTRAG_URL` between local and remote environments.

### Fixed
- **Critical Multi-User Path Configuration:** Fixed a critical bug where all users were sharing the same data directories. The system now correctly generates user-specific paths for storage and knowledge, ensuring proper data isolation. See [ADR-002](./refs/adr/002-multi-user-path-fix.md) for details.

## [0.7.10] - 2025-07-03

### Added
- **LightRAG Document Manager V2** (`lightrag_docmgr_v2.py`), a rewritten document management tool that uses the core LightRAG library for more stable and reliable operations.
- The `send_to_lightrag.py` script was enhanced with SCP support for transferring files to remote LightRAG deployments.
- Foundational design for a **Multi-User Architecture** was created in `docs/MULTI_USER_DESIGN.md`.

## [0.7.9] - 2025-07-01

### Added
- A `--recreate` flag for the `paga_cli` command-line interface to enable on-demand recreation of the knowledge base.
- **Instruction-Level Performance Analysis System**, allowing the agent's instruction sophistication to be tuned for different models. Includes a four-tier `InstructionLevel` (MINIMAL, CONCISE, STANDARD, EXPLICIT).
- A comprehensive performance testing framework (`tests/test_instruction_level_performance.py`) for scientific-grade performance measurement.
- **Google Search** tool (`GoogleSearchTools`) was integrated into the agent.
- **Structured JSON Response System** using Ollama's JSON schema validation for more reliable tool call detection and response parsing.

### Fixed
- **Critical LightRAG Timeout Fix:** Resolved an `httpx.ReadTimeout` error that occurred during large document ingestion by correcting the timeout value in the `lightrag` service's `config.ini`. See [ADR-006](./refs/adr/006-lightrag-timeout-fix.md) for details.