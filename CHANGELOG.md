# Changelog

## [v0.8.77.dev] - 2025-11-18

### Fixed
- **UI Provider State**: Fixed a state desynchronization bug in the Streamlit UI where switching LLM providers (e.g., from Ollama to LM Studio) would not reliably update the application's backend. The system now uses a dedicated session state variable (`SESSION_KEY_CURRENT_PROVIDER`) as the single source of truth for the active provider, ensuring that model lists and agent initializations are always in sync with the user's selection. See [ADR-100](./refs/adr/100-streamlit-provider-state-management.md) for details.
- **Auto-Scanning Models**: Enhanced the provider switching mechanism to automatically scan and update the available models list when a new provider is selected. This eliminates the need for manual refreshes and ensures the model dropdown is always populated with the latest available models for the current provider, improving user experience and reducing configuration errors.

### Added
- **External Query Classification Config**: Moved query classification patterns from hard-coded lists into a new, external `query_classification.yaml` file. This allows for easier tuning and maintenance of the memory query "fast path" logic without requiring code changes.

## [v0.8.77.dev] - 2025-11-18

### Fixed
- **Query Classifier Pattern Matching**: Fixed critical bug where natural language variations of memory list queries (e.g., "list my memories", "show my memories") were not matching classifier patterns and falling back to full team inference (~40s) instead of using the fast path (~1s). Root cause was overly strict regex patterns that expected specific word order. Added flexible patterns with optional modifiers (`r"^list\s+(my\s+)?memories"`, `r"^show\s+(my\s+)?memories"`) to support natural variations. Updated `query_classification.yaml` to maintain configuration parity with code patterns. Added test coverage for new variations. All 19 unit tests passing. This fix completes the query handling refactoring that was preventing the 40x performance improvement from reaching production.

## [v0.8.76.dev] - 2025-11-17

### Fixed
- **UI State Consistency**: Implemented an atomic transaction system for all configuration changes made in the Streamlit UI. When switching models or providers, the application configuration and UI session state are now snapshotted before re-initialization. If the new agent or team fails to initialize for any reason, the entire transaction is rolled back, restoring the application to its previous stable state. This prevents the UI and backend from becoming desynchronized and entering a broken state, significantly improving the reliability and user experience of the model management interface. See [ATOMIC_CONFIG_TRANSACTIONS_FOR_UI_STABILITY.md](./refs/ATOMIC_CONFIG_TRANSACTIONS_FOR_UI_STABILITY.md) for technical details.
- **Knowledge Base Semantic Ingestion**: Fixed critical issue where knowledge ingestion via Streamlit UI and REST API was not triggering semantic KB recreation. Streamlit was calling individual LightRAG-only methods (`ingest_knowledge_file`, `ingest_knowledge_text`, `ingest_knowledge_from_url`) that uploaded to LightRAG but never reloaded semantic KB indices. Solution: Updated Streamlit UI (3 call sites in `streamlit_tabs.py` lines 2240, 2337, 2418) and REST API (2 call sites in `rest_api.py` lines 633, 685) to use unified ingestion methods (`ingest_file`, `ingest_text`, `ingest_url`) that properly coordinate both LightRAG and semantic KB ingestion with automatic index recreation. Individual methods are now internal implementation details called by unified methods, not exposed as tools.
- **Streamlit Import Handling**: Removed defensive `sys.path` manipulation from `paga_streamlit_agno.py` that was checking for and manually adding the `src` directory. This import test was unnecessary since the file is now a proper package module with correct Python import handling.

### Changed
- **Knowledge Management Package Refactoring**: Consolidated and refactored the knowledge management subsystem for improved clarity and maintainability. Unified naming conventions across knowledge ingestion functions (`ingest_knowledge_file`, `ingest_knowledge_text`, `ingest_knowledge_from_url`), simplified logic by removing redundant path handling, and reduced code duplication across `knowledge_tools.py`. The refactoring establishes clear responsibility boundaries: `KnowledgeTools` handles unified ingestion coordination, individual methods handle LightRAG-specific operations internally, and file lifecycle is now explicit and predictable.

## [v0.8.76.dev] - 2025-11-15

### Changed
- **Granite 3.1 LLM Standardization for LightRAG Servers**: Migrated LightRAG servers to use IBM Granite 3.1 models with full Apache 2.0 licensing across all sizes. Knowledge server now uses `granite3.1-dense:8b` (5.0GB) for robust document processing, while memory server uses `granite3.1-dense:2b` (1.6GB) for lightweight memory relationship extraction. Reduced context windows from 128K to 32K (32,768 tokens) to support concurrent multi-instance deployment on 24GB RAM systems. Personal agent inference continues using proven `qwen3:4b` for tool-calling capabilities. This hybrid strategy provides licensing compliance for RAG workloads while maintaining established inference performance. Updated installer to pull both Granite models (for RAG) and Qwen3 models (for inference/team mode). Total RAG infrastructure footprint: ~9-11GB, leaving ~13-15GB available for agent operations on 24GB systems. See [GRANITE_LLM_STANDARDIZATION_SUMMARY.md](./refs/GRANITE_LLM_STANDARDIZATION_SUMMARY.md) for complete licensing analysis, performance considerations, and deployment strategy.

### Added
- **First-Run User Profile Setup**: Created comprehensive `first-run-setup.sh` script for interactive user profile creation after fresh installation. The script provides guided prompts for full name, user_id (with automatic normalization), birth year, and gender. Includes intelligent user_id validation (lowercase alphanumeric, dots, hyphens, underscores) and automatic normalization from display names (e.g., "John Smith" → "john.smith"). Activates virtual environment, calls `switch-user.py --create-if-missing`, and restarts LightRAG services automatically. Added `poe setup` task for convenient access. Implemented dual-approach initialization: interactive setup script (preferred) + lazy fallback in Streamlit UI (automatic default user creation with warning to run proper setup). Updated installer final instructions to prominently feature first-run setup as step 1.

### Fixed
- **LightRAG Docker Service Startup**: Fixed critical "too many colons" error that prevented LightRAG containers from starting. Removed `build:` sections from docker-compose files that were triggering package installations during startup, producing output that corrupted volume mount parsing. Updated both knowledge server (port 9621) and memory server (port 9622) to use pre-built images from Docker Hub (`egsuchanek/lightrag_pagent:latest`). Corrected healthcheck port for memory server to use exposed port 9622 instead of internal port 9621. See [INSTALLER_IDEMPOTENCY_AND_DOCKER_FIXES.md](./refs/INSTALLER_IDEMPOTENCY_AND_DOCKER_FIXES.md) for complete technical details.
- **Installer Sudo Requirement Eliminated**: Completely refactored `install-personal-agent.sh` to run as normal user without requiring root/sudo upfront. Removed all `sudo -u` wrapper commands that were dropping privileges from root back to user - an unnecessarily complex pattern. Script now runs directly as the current user, with all files and directories automatically owned correctly since they're created by the user. Sudo is only requested conditionally when needed: (1) if `/usr/local/bin` doesn't exist and `/usr/local` is root-owned, it will be created with proper user ownership; (2) cleanup of old system LaunchDaemons in `/Library/LaunchDaemons/` if present from previous installations. Removed all `chown` commands (files are already owned by the creating user), removed root privilege check, and updated all documentation to show `./install-personal-agent.sh` instead of `sudo ./install-personal-agent.sh`. This simplifies installation, eliminates permission issues, and follows the principle of least privilege - requesting sudo only when actually needed.
- **Installer Idempotency**: Completely overhauled `install-personal-agent.sh` to achieve true idempotency with accurate dry-run reporting. Enhanced all setup functions (`setup_lightrag_directories()`, `setup_ollama_service()`, `setup_ollama_management()`, `setup_repository()`) to check for existing resources before attempting creation. Dry-run mode now accurately reports `[EXISTS]`, `[SKIP]`, or `[WOULD CREATE]` for each resource instead of misleadingly showing "WOULD CREATE" for existing items. The installer can now be safely run multiple times without errors or unintended side effects.
- **Non-Interactive Installation**: Eliminated all interactive prompts during installation to enable automated deployments and CI/CD pipelines. Added `.venv` existence checking in `setup_repository()` to prevent `uv venv` from prompting about overwriting existing virtual environments. The installer now completes fully non-interactively, suitable for automation tools and testing workflows.
- **Offline Ollama Model Detection**: Fixed model checking to work without requiring the Ollama service to be running. Implemented `check_model_in_directory()` function that inspects the Ollama manifest directory structure (`$OLLAMA_MODELS_DIR/manifests/registry.ollama.ai/library/`) directly, enabling reliable model detection during fresh installations or when the service is stopped. Replaced API-dependent `ollama list` calls with filesystem-based validation.
- **Docker Image Pull Handling**: Made Docker image pulling non-fatal with graceful degradation. The `pull_lightrag_images()` function now continues installation even if pre-pulling fails due to authentication issues, displaying informative warnings that images will be automatically pulled when containers start via `docker-compose up`. This prevents installation failures when Docker Hub CLI authentication is not configured.
- **Dashboard User Switching and Sidebar Refresh**: Fixed critical issue where switching users in the dashboard did not update the current user display in the sidebar. Removed phantom `current_user.json` reference and unnecessary fallback methods, simplifying user detection to directly use `~/.persagent/env.userid` via `get_userid()` - the actual single source of truth. Added session state tracking to detect user changes and automatically clear caches. The sidebar now correctly shows the new user with a green success indicator after switching.
- **Simplified User Detection**: Eliminated unnecessary 4-tier fallback system that included a non-existent `current_user.json` file. Dashboard now directly reads from `~/.persagent/env.userid` through the `get_userid()` function, which is the actual single source of truth that gets updated during user switching.
- **Dashboard Refresh Button Placement**: Added "🔄 Refresh Dashboard" button to the System Control section above the Power Off button, allowing users to manually refresh the current user display and system status at any time.
- **Version Consistency**: Updated all version strings across the project to `0.8.76` for consistency. Updated `pyproject.toml` from `v0.8.73` to `v0.8.76`, `src/__init__.py` from `v0.8.73` to `v0.8.76`, and `src/personal_agent/__init__.py` from `0.8.74dev` to `0.8.76dev` to match the current development branch.
- **User Registry Architecture**: Resolved critical multi-user system issues by refactoring `UserRegistry` to use the shared data location (`PERSAG_ROOT`) instead of user-specific directories. This fix eliminates multiple conflicting registry files, ensures dashboard and CLI see the same user list, and provides a single source of truth at `/Users/Shared/personal_agent_data/users_registry.json`. The refactoring includes case-insensitive user lookup, user ID normalization (lowercase, dot-separated), and proper separation between `user_id` (normalized identifier) and `user_name` (display name). See [USER_REGISTRY_ARCHITECTURE_FIX.md](./refs/USER_REGISTRY_ARCHITECTURE_FIX.md) for complete details.
- **Docker Service Hanging**: Fixed critical issue where Docker containers would hang indefinitely during user switching by removing the `--wait` flag from `docker-compose up` commands. The startup process now completes reliably with a simple 2-second initialization delay instead of blocking on health checks. Reduced timeout from 120s to 60s for better responsiveness.
- **Redundant Consistency Checks**: Eliminated triple consistency checking during user switching operations by removing redundant `check_docker_consistency()` call in `ensure_docker_consistency()`. Docker validation now runs once instead of three times, significantly improving user switching performance.
- **Dashboard Directory Creation**: Fixed inconsistency where dashboard user creation didn't create required directory structure. The `create_new_user()` function now creates all 6 user directories (knowledge, rag_storage, inputs, memory_rag_storage, memory_inputs, lancedb) matching the CLI behavior.
- **User Switching Config Singleton Bug**: Fixed critical bug where switching users created directories with incorrect names (e.g., "charlie" instead of "charlie.brown"). The issue occurred because `create_user_directories()` in `user_switcher.py` was creating an `AgnoPersonalAgent` instance while the `PersonalAgentConfig` singleton still had the OLD user_id cached. Since `AgnoPersonalAgent` gets storage paths from the config singleton (not from the passed `user_id` parameter), directories were created using paths based on the old user. Fixed by calling `config.set_user_id(user_id, persist=False)` BEFORE creating the agent, ensuring the config singleton is synchronized with the target user_id. The original user_id is restored in the finally block to prevent side effects.

### Changed
- **Case-Insensitive User Management**: User IDs are now case-insensitive throughout the system, preventing duplicate users like "Paula" and "paula". The `get_user()` and `remove_user()` methods now perform lowercase comparison while preserving the original `user_name` for display purposes.
- **User ID Normalization**: Implemented automatic user ID normalization that converts to lowercase and replaces spaces with dots (e.g., "Paula Smith" → user_id: "paula.smith", user_name: "Paula Smith"). Added regex validation to ensure user IDs only contain alphanumeric characters, dots, hyphens, and underscores.
- **Default Cognitive State**: Changed default `cognitive_state` from 50 to 100 across `UserRegistry` and `UserManager` for better initial user experience.
- **Simplified User Manager**: Refactored `UserManager` to no longer pass user-specific paths to `UserRegistry()`, allowing the registry to use its own defaults from global configuration. This improves separation of concerns and eliminates path confusion.

### Added
- **Dual Storage Memory Restatement System**: Implemented a sophisticated dual storage strategy for user memories that balances natural language retrieval with accurate knowledge graph entity mapping. Memories are now stored in different formats optimized for each system: second-person ("you have") in local SQLite/LanceDB for natural conversational retrieval, and third-person with user_id ("{user_id} has") in LightRAG graph for accurate entity identification. This eliminates the need for constant presentation conversion in agent instructions while preserving relationship extraction accuracy. Added `restate_to_second_person()` method with 13 comprehensive regex patterns covering contractions, possessives, and reflexive pronouns. Updated `store_user_memory()` to generate both `local_content` and `graph_content` versions. Benefits include more natural agent responses, simpler instructions, user-agnostic local storage, and maintained entity mapping in knowledge graphs. See [DUAL_STORAGE_MEMORY_RESTATEMENT.md](./refs/DUAL_STORAGE_MEMORY_RESTATEMENT.md) for complete implementation details and examples.
- **Intelligent Verb Conjugation for Third-Person Restatement**: Implemented a comprehensive verb conjugation system that properly handles conversion of first-person statements to grammatically correct third-person form for knowledge graph storage. The new `_conjugate_verb_third_person()` method intelligently handles present tense verbs (love→loves, go→goes, study→studies), irregular verbs (am→is, have→has, do→does), and correctly preserves past tense verbs unchanged (did, had, was). This fixes the grammatically incorrect restatements that previously occurred (e.g., "I love hiking" now correctly becomes "alice loves hiking" instead of "alice love hiking"). The system includes 20+ irregular and past tense verbs, proper handling of verb ending rules (-s, -es, -ies), and comprehensive test coverage with 19 conjugation test cases.
- **Enhanced Dashboard User Management**: Improved the Streamlit dashboard user management interface with better tab organization and field ordering. Removed the User Settings tab and moved Profile Management before Create User for more intuitive workflow. Added a new "Basic Info" tab within Profile Management showing user_name (editable) and user_id (read-only) fields. Reordered fields in User Overview and Create User tabs to display User Name before User ID, aligning with user-centric design principles.
- **Functional Dashboard User Switching**: Implemented fully functional Switch User tab in the dashboard using the enhanced REST API `/api/v1/users/switch` endpoint. Users can now switch between existing users directly from the dashboard UI with automatic Docker service restart, system reinitialization, and automatic page refresh after successful switch. The interface includes user details preview, confirmation warnings, and comprehensive error handling with user feedback.

### Changed
- **Enhanced Memory Statistics with Confidence Analytics**: Significantly upgraded the `get_memory_stats()` method to provide comprehensive analytics including average confidence scores with visual indicators (🟢🟡🟠🔴), confidence distribution breakdown (high/medium/low), user vs proxy memory attribution counts, and detailed proxy agent contribution tracking. The statistics output now uses emoji-enhanced formatting for better readability and provides actionable insights into memory quality, source attribution, and topic distribution. This enables users to monitor memory system health, track confidence trends over time, and identify which agents are contributing memories.
- **Enhanced Memory Display with Full Field Support**: Comprehensively updated all memory display interfaces across both the main Streamlit application (`paga_streamlit_agno.py`) and the management dashboard (`dashboard.py`) to display the complete set of enhanced memory fields from the `EnhancedUserMemory` model. All memory views (Explorer, Search, Browse) now consistently show `confidence` scores with color-coded visual indicators (🟢 green for high, 🟡 yellow for medium, 🟠 orange for low, 🔴 red for very low), `is_proxy` flags distinguishing user memories (👤) from proxy agent memories (🤖), and `proxy_agent` names for attribution. Export/import functionality has been updated to preserve all enhanced fields in both JSON and CSV formats, ensuring data integrity across backup and restore operations. This provides users with complete transparency into memory provenance, quality, and source, supporting the multi-agent architecture where different agents can contribute memories with varying confidence levels.
- **Configuration Directory Rebranding**: Renamed the user configuration directory from `~/.persag` to `~/.persagent` for better brand alignment with "Personal Agent". This change affects all configuration and Docker management files, providing clearer naming that reflects the application's identity. All code references, scripts, documentation, and installation procedures have been updated to use the new `.persagent` directory name consistently.
- **Ollama Memory Optimization for 24GB Systems**: Optimized Ollama configuration for production deployment on memory-constrained systems by switching from f16 to q8_0 KV cache type, reducing per-model memory usage from ~7GB to ~3.5GB (50% savings). This enables safe operation of 3 concurrent models on 24GB RAM systems (10.5GB vs 21GB with f16). Updated `OLLAMA_MAX_LOADED_MODELS` from 2 to 3 to improve concurrency. Added comprehensive documentation comments across all configuration files explaining the optimization rationale and deployment considerations. See [OLLAMA_MEMORY_OPTIMIZATION_24GB.md](./refs/OLLAMA_MEMORY_OPTIMIZATION_24GB.md) for details.
- **Enhanced REST API User Switching**: Completely rebuilt the `/api/v1/users/switch` endpoint to use the robust `user_switcher` module functions for comprehensive user switching. The endpoint now performs validation, user creation if needed, directory setup, LightRAG service management, and system restart. Added new parameters including `user_name`, `user_type`, `auto_confirm`, and `restart_containers`/`restart_system` flags. Returns detailed response with normalized user_id, creation status, and actions performed. Creates restart marker file for automatic Streamlit UI refresh.
- **Dynamic User ID Display in Main UI**: Removed static `USER_ID` module-level variable in `paga_streamlit_agno.py` and replaced with dynamic `get_current_user_id()` calls in the main function. Sidebar now displays user display name from UserManager instead of user_id, updating correctly after user switches without requiring application restart.
- **Improved REST API Documentation**: Updated `rest_api.py` and `paga_streamlit_agno.py` module docstrings to comprehensively document all REST API endpoints including the new `/api/v1/users/switch` with detailed parameter descriptions, response schemas, and usage examples. Added documentation for the custom `/api/v1/paga/restart` endpoint.

### Fixed
- **Dynamic Path Resolution in Runtime Operations**: Fixed critical path resolution issue where static imports of storage directory constants from `settings.py` caused stale or incorrect paths when environment variables were loaded after module import. Affected dashboard delete all memories operation and other file operations. Replaced static imports with dynamic `get_user_storage_paths()` calls in `agent_memory_manager.py`, `memory_cleaner.py`, `lightrag_document_manager.py`, and `knowledge_tools.py`. This ensures paths are always calculated using current environment variables, resolving failures in Docker environments where `.env.docker` is loaded after initial module imports. See [DYNAMIC_PATH_RESOLUTION_FIX_SUMMARY.md](./refs/DYNAMIC_PATH_RESOLUTION_FIX_SUMMARY.md) for details.
- **LightRAG Memory Server Docker Configuration**: Corrected the `docker-compose.yml` environment file reference for the memory server to properly point to `env.memory_server` instead of the generic `env.server`, ensuring correct configuration loading during container startup.

### Removed
- **Unused Ollama Template Files**: Removed obsolete `setup/start_ollama.sh` template file that was not referenced by the installation process, eliminating configuration confusion. The install script generates the startup script directly via heredoc as the single source of truth.

## [v0.8.74] - 2025-10-20

### Added
- **Enhanced User Profile Model**: Extended the `User` dataclass with `gender` (validated against "Male", "Female", "N/A") and `npc` (boolean) fields, enabling richer user profiles and support for bot users. These fields are fully integrated across the entire stack including serialization, persistence, and UI components.

### Changed
- **Centralized Configuration in User Registry**: Refactored `user_registry.py` to use the global `PersonalAgentConfig` singleton (`get_config()`) instead of scattered environment variables, improving maintainability and consistency with the rest of the codebase.
- **Enhanced Dashboard User Management**: Updated the Streamlit dashboard's user management interface to include gender selection (selectbox) and NPC designation (checkbox) in the Personal Info tab, with proper session state management for UI persistence across user selections and tab changes.
- **Improved UI Persistence**: Implemented comprehensive session state management in the dashboard to maintain selected tabs and user selections across reruns, preventing the frustrating behavior of resetting to the main pane when managing users.

### Fixed
- **User Model Validation**: Added robust validation for the new gender field with clear error messages for invalid values, ensuring data integrity throughout the system.
- **Documentation Accuracy**: Corrected and expanded `architecture.md` to accurately document previously undocumented features including REST API endpoints, macOS/iOS Shortcuts integration, Tailscale secure networking, and the centralized Ollama LaunchAgent service.

### Documentation
- **Comprehensive Module Attribution**: Updated module docstrings across the user management stack with proper author attribution (Eric G. Suchanek, PhD), current revision dates, and Apache 2.0 license information.
- **Architecture Documentation Updates**: Extensively updated `architecture.md`, `CLAUDE.md`, and `GEMINI.md` to reflect the enhanced user management capabilities, configuration patterns, and network access features.

## [v0.8.74] - 2025-10-17

### Changed
- **Decoupled Dashboard from Docker Management**: To improve stability and user experience, the dashboard has been decoupled from direct Docker management. The "Docker Services" tab has been removed, and the UI now provides clear guidance and fallback instructions if the Docker daemon is not accessible, preventing crashes and permission errors. See [ADR-097](./refs/adr/097-decouple-dashboard-from-direct-docker-management.md) for details.
- **Robust Ollama Service Management**: The installation script (`install-personal-agent.sh`) has been overhauled to configure Ollama as a persistent `launchd` background service on macOS. This prevents conflicts with the GUI app, ensures Ollama starts automatically on login, and provides a more stable and reliable experience. See [ADR-098](./refs/adr/098-robust-ollama-service-management.md) for details.

## [v0.8.73] - 2025-10-13

### Changed
- **Centralized Configuration Management**: Majorly refactored the configuration system, replacing scattered environment variables with a centralized, thread-safe `PersonalAgentConfig` singleton. This eliminates race conditions, provides a single source of truth, and enables reliable, dynamic switching of model providers at runtime. See [ADR-096](./refs/adr/096-centralized-configuration-management.md) for details.

## [v0.8.72] - 2025-10-12

### Changed
- **Simplified CLI Memory Architecture**: The CLI for memory operations (`src/personal_agent/cli/memory_commands.py`) has been refactored into a thin presentation layer. It now directly delegates all calls to the agent's public memory interface, removing complex tool-finding and fallback logic. This improves separation of concerns and aligns with the unified agent interface. See [ADR-095](./refs/adr/095-simplified-cli-memory-architecture.md) for details.

## [v0.8.7dev] - 2025-10-01

### Added
- **Dynamic Memory Timestamps**: Both the main agent UI and the management dashboard now display memories with dynamic, human-readable timestamps (e.g., '3 days ago,' 'at age 25'), providing a more intuitive and chronological view of memories. See [ADR-094](./refs/adr/094-unified-memory-display-and-dashboard.md) for details.

### Fixed
- **User Switching**: Resolved an issue in the user management system to ensure stable and reliable switching between user contexts.

## [v0.8.7dev] - 2025-09-30

### Changed
- **Robust User Switching**: The `switch-user.py` script now explicitly shuts down all LightRAG Docker services *before* switching the user context and then restarts them. This prevents potential race conditions and ensures a clean, reliable transition between users. See [ADR-093](./refs/adr/093-robust-docker-shutdown-for-user-switching.md) for details.

## [v0.8.7dev] - 2025-09-25

### Added
- **Enhanced REST API Health Checks**: The `/api/v1/health` endpoint now performs a comprehensive check on all critical system components (Agent, Team, Memory, Knowledge) and provides a detailed status report, ensuring the API only reports as healthy when the entire system is operational. See [ADR-092](./refs/adr/092-enhanced-rest-api-health-checks.md) for details.

### Changed
- **Dynamic Docker Storage Paths**: The `smart-restart-lightrag.sh` script now dynamically retrieves the `AGNO_STORAGE_DIR` from the application's settings, making the Docker startup process more robust and less reliant on manual environment configuration.
- **Theme-Aware UI Charts**: The response time chart in the Streamlit UI is now theme-aware, with styles that adapt to both light and dark modes for improved visibility.

### Fixed
- **Agent Response Handling**: Resolved a bug that could cause the agent to crash when receiving a non-streaming response from a language model. The response handling logic is now more robust and can gracefully handle both streaming and single responses.
- **Streamlit Dark Theme**: Corrected several CSS issues in the Streamlit dark theme, particularly for select boxes and dropdown menus, to ensure a consistent and usable interface.

### Removed
- **Obsolete Test Files**: Removed several outdated and unused test scripts related to LM Studio and Llama32 to clean up the codebase.

## [v0.2.6dev0] - 2025-09-24

### Fixed
- **Ollama Docker Connectivity**: Resolved a critical bug that prevented LightRAG Docker containers from connecting to the Ollama server on the host machine. The `OLLAMA_URL` has been corrected to `http://host.docker.internal:11434` to ensure reliable communication from within the container environment. See [ADR-091](./refs/adr/091-ollama-docker-connectivity-and-configuration-standardization.md) for details.

### Changed
- **Docker Configuration Standardization**: Migrated Docker Compose configurations to use visible and documented `env.server` and `env.memory_server` files instead of hidden `.env` files. This improves configuration transparency and maintainability. See [ADR-091](./refs/adr/091-ollama-docker-connectivity-and-configuration-standardization.md) for details.

### Added
- **REST API for Memory and Knowledge**: Introduced a RESTful API to provide programmatic access to the agent's memory and knowledge management capabilities. The API, which runs alongside the Streamlit application, exposes endpoints for storing, searching, and managing memories and knowledge, enabling integration with external systems and automation of data ingestion. The architecture uses a global state manager to safely share the agent instance between the Streamlit and API server threads. See [ADR-090](./refs/adr/090-rest-api-for-memory-and-knowledge.md) for details.

### Changed
- **Standardized Agent and Team Interfaces**: Introduced `BaseAgent` and `BaseTeam` abstract base classes to create a unified interface for all agents and teams. This refactoring promotes polymorphism, simplifies the architecture, and improves modularity by ensuring that all agentic components share a consistent `run` and `arun` method signature. See [ADR-089](./refs/adr/089-standardized-agent-and-team-interfaces.md) for details.

## [v0.2.6dev0] - 2025-09-22

### Changed
- **Streamlined Streamlit UI and Default Team Mode**: The Streamlit application now defaults to the more capable team-based mode, with a `--single` flag to run in a single-agent configuration. The runtime mode-switching UI has been removed to simplify the user experience. This change is documented in [ADR-072](./refs/adr/072-streamlit-ui-simplification.md).
- **Team Delegation and Reasoning**: Switched the `personal_agent_team` from `route` to `coordinate` mode and integrated `ReasoningTools` to significantly improve the coordinator's ability to delegate tasks to the correct specialized agents.

### Fixed
- **Tool Call Extraction and Response Handling**: Overhauled the response handling logic to correctly parse and display tool calls and their results. This resolves a critical bug where the Streamlit UI would show raw tool call syntax instead of the executed content from the writer agent. The new `extract_tool_calls_and_metrics` function now robustly handles various tool call formats from different models and agents.
- **Streamlit `arun` Compatibility**: Fixed a bug that caused the Streamlit app to crash when using `agent.arun()` with asynchronous tools in single-agent mode.
- **File Tools Path Handling**: Corrected a recurring issue where file-related tools (`FileTools`, `ShellTools`, `PythonTools`) were failing due to being initialized with string paths instead of the required `pathlib.Path` objects. All tools now correctly use `Path` objects and consistently point to the user's home directory, resolving multiple `'str' object has no attribute 'iterdir'` and `'str' object has no attribute 'joinpath'` errors. This is documented in [ADR-073](./refs/adr/073-file-tools-path-fix.md).

## [v0.2.6dev0] - 2025-09-21

### Added
- **Native LM Studio Provider**: Integrated a dedicated `lm-studio` model provider, allowing seamless use of models served from LM Studio for both local and remote setups. See [ADR-088](./refs/adr/088-native-lm-studio-provider-and-unified-agent-mode.md) for details.
- **Explicit Standalone Agent Mode**: Introduced a `--single` command-line flag to explicitly run the agent in a standalone mode with its full suite of tools. This removes ambiguity and provides clear control over the agent's capabilities.
- **Unified Knowledge Ingestion Tools**: The `KnowledgeTools` toolkit now features unified `ingest_file`, `ingest_text`, and `ingest_url` methods that ingest data into both the LightRAG (graph) and local (semantic) knowledge bases simultaneously, streamlining the data ingestion process.
- **Comprehensive Tooling Tests**: Added new test scripts (`test_alltools_fix.py`, `test_remote_alltools_toggle.py`) to validate the new agent mode logic and prevent regressions.

### Changed
- **Simplified Agent Mode Configuration**: The agent's operational mode (standalone vs. team) is now exclusively controlled by the `--single` flag, decoupling it from the `--remote` flag. This simplifies configuration and makes agent behavior more predictable.
- **Refactored Knowledge Ingestion**: Overhauled the `KnowledgeTools` and `batch_ingest_directory` to use the new unified ingestion methods, improving code clarity and maintainability.

### Fixed
- **Agent Tool Loading**: Corrected a critical bug where the `alltools` parameter in `AgnoPersonalAgent` was not correctly loading the full suite of tools. The agent now reliably loads the appropriate toolset based on the `--single` flag.

## [v0.2.6dev0] - 2025-09-18

### Fixed
- **Streamlit Memory Storage in Team Mode**: Resolved a critical bug where storing memories from the Streamlit UI would fail in team mode. The architecture has been simplified to have the UI interact directly with the dedicated Knowledge Agent, removing a complex and faulty wrapper layer.
- **`delta_year` Timestamping**: Fixed a bug that prevented the `delta_year` feature from working. The memory storage pipeline now correctly converts user data into a `User` object, ensuring that age-perspective timestamps are calculated and applied as intended. See [ADR-087](./refs/adr/087-robust-ui-memory-storage-and-context-handling.md) for details on both fixes.

## [v0.2.6dev0] - 2025-09-17

### Added
- **Age-Perspective Memory Creation**: Introduced a `delta_year` attribute to the `User` model, allowing memories to be created from the perspective of the user at a specific age. The system adjusts the memory's timestamp to `user.birth_year + delta_year` for chronological consistency. See [ADR-086](./refs/adr/086-age-perspective-memory-creation.md) for details.
- **Qwen Model Configurations**: Added new model configurations for `Qwen3-4B-Instruct-2507-GGUF`.

### Changed
- **Memory Timestamp Handling**: Updated `AgentMemoryManager` and `SemanticMemoryManager` to support custom timestamps, enabling the `delta_year` feature.
- The `store_user_memory` tool now passes the user's context to the memory managers to enable age-specific timestamp adjustments.

## [v0.2.6dev0] - 2025-09-16

### Added
- **Standalone Dockerized Dashboard**: Introduced a new, standalone, containerized Streamlit dashboard for managing the personal agent system. The dashboard can be deployed and run independently, providing a flexible and scalable solution for system management. See [ADR-085](./refs/adr/085-standalone-dockerized-dashboard.md) for details.

### Changed
- **Refactored Memory Management**: Overhauled the memory management system to improve modularity and reduce code duplication. All memory operations are now centralized in a new `src/personal_agent/tools/memory_functions.py` module, which serves as a single source of truth for memory-related logic. See [ADR-084](./refs/adr/084-standalone-memory-functions.md) for details.
- **Deprecated `PersagMemoryTools`**: The `PersagMemoryTools` class has been deprecated and now simply re-exports the new standalone memory functions for backward compatibility.

### Removed
- **Unused Dependencies**: Removed `pathlib` and `langfuse` from project dependencies to streamline the environment.

## [v0.2.6] - 2025-09-08

### Fixed
- **Memory Verbosity**: Resolved a major behavioral issue where the agent provided overly detailed and verbose responses when asked to list memories. It now correctly uses a new, concise summary tool (`list_all_memories`) for general listing requests, improving user experience and reducing token usage. See [ADR-083](./refs/adr/083-differentiated-memory-retrieval.md) for details.

### Changed
- **Differentiated Memory Retrieval**: Overhauled the agent's instructions and tools to create a clear distinction between summary (`list_all_memories`) and detailed (`get_all_memories`) memory retrieval. The agent now defaults to concise summaries for general queries.
- **Optimized Memory Listing**: The `list_all_memories` tool (formerly `list_memories`) has been optimized to return a clean, performance-optimized summary list of memories without extra metadata or topics.
- **Enhanced CLI**: The command-line interface has been improved with a `brief` command for concise memory lists, a comprehensive `help` command, `examples` for user guidance, and a safer `wipe` command that now requires confirmation.

### Added
- **Comprehensive Memory Fix Tests**: Added an extensive suite of new tests (e.g., `test_memory_agent_complete_fix.py`, `test_list_memories_fix.py`) to validate the new differentiated memory retrieval logic from the unit to the integration level and prevent future regressions.
- **Behavioral Analysis**: Added `memory_agent_behavior_analysis.md` to document the root cause analysis of the memory verbosity issue.

## [v0.2.6dev0] - 2025-09-05

### Added
- **Multi-Provider Model Support**: The agent now supports multiple language model providers, starting with OpenAI and Ollama. This allows for greater flexibility, enabling the use of models like GPT-4o alongside local models. See [ADR-082](./refs/adr/082-multi-provider-model-support.md) for details.
- **Configuration for Model Providers**: Added new environment variables (`MODEL_PROVIDER`, `OPENAI_API_KEY`) to manage the selection and authentication of model providers.
- **OpenAI Dependency**: Added the `openai` library to the project dependencies to support the new provider.

### Changed
- **Refactored Model Management**: The `AgentModelManager` has been significantly refactored to dynamically load and manage models based on the selected provider, making the system more modular and extensible.
- **UI Provider Display**: The Streamlit UI now displays the active model provider and model name for better transparency.

### Fixed
- **Ollama Tool-Calling Stability**: Replaced the unstable, custom `OllamaTools` wrapper with the standard `agno.models.ollama.Ollama` class. This resolves previous reliability issues and improves the stability of tool-calling when using Ollama models.


_Reminder: All new entries should include a date/timestamp._

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.2.5dev0] - 2025-09-03

### Added
- **Unified Agent Memory Interface**: The `AgnoPersonalAgent` now exposes a complete and robust set of public methods for all memory operations (list, query, update, delete, stats, etc.), serving as a single, authoritative interface for memory management. See [ADR-081](./refs/adr/081-unified-agent-memory-interface.md) for details.
- **Live Graph Memory Count**: The `AgentMemoryManager` can now directly query the LightRAG server for a live count of graph entities, enabling accurate UI reporting of memory synchronization status.
- **Workflow-Based Coordination Examples**: Added new examples (`workflow_memory_writer_example.py`) demonstrating the use of `agno.Workflow` for robust, stateful, and sequential agent coordination, offering a better architectural pattern for tasks like memory-based writing.
- **Comprehensive Test Suite**: Added a full suite of integration tests to verify the new memory interfaces, the refactored Streamlit helpers, and the team coordination logic, ensuring all components work correctly across single-agent and team modes.

### Changed
- **Major UI Refactoring**: The `StreamlitMemoryHelper` has been completely refactored to be a thin client for the new agent-level memory interface. This decouples the UI from the agent's internal state, simplifies the code, and improves robustness.
- **Team Coordinator Logic**: The `PersonalAgentTeam` coordinator's instructions have been updated to enforce a correct memory-based writing workflow, ensuring memories are first retrieved and then explicitly passed to the writer agent.
- **Model Context Sizes**: Corrected and standardized the context sizes for many Llama and Qwen models in `model_contexts.py` to a more realistic `32768` tokens.
- **Reduced Log Verbosity**: Changed numerous `logger.info` calls to `logger.debug` across the agent core to reduce console noise during standard operation.

### Fixed
- **Streamlit Async Bugs**: Resolved critical `RuntimeError` issues in the Streamlit UI by implementing a safe `asyncio` runner (`_run_async_safely`) that correctly handles the event loop, making memory operations from the UI reliable.
- **Memory-Based Content Generation**: Fixed a major logical flaw in the `PersonalAgentTeam` where retrieved memories were not being passed to the writer agent. Content generation based on user memories now works as intended.
- **Inaccurate Memory Sync Status**: The memory sync status in the UI is now accurate, as it uses the new live graph entity count instead of assuming the local and graph counts are identical.

## [v0.2.4dev0] - 2025-09-01

### Added
- **Journaling and Safety Topics**: Introduced new `journal` and `self_harm_risk` topics to the topic classifier. The `journal` topic helps categorize personal reflections, while the `self_harm_risk` topic is a critical safety feature to identify users in distress. See [ADR-080](./refs/adr/080-journaling-and-safety-topics.md) for details.
- **Topic Analysis Script**: Added a new script `scripts/analyze_topic.py` for analyzing the topic of a given string.
- **Age-Perspective Memory Writing**: Introduced `birth_date` and `delta_year` fields to the `User` model, enabling users to write memories from the perspective of a specific age. This includes a delta-year-aware timestamp system that adjusts the year of `last_seen` to reflect the chosen age, ensuring temporal consistency. See [ADR-079](./refs/adr/079-user-profile-birth-date-delta-year.md) for details.
- **Comprehensive User Model Validation**: Implemented robust validation for the new `birth_date` and `delta_year` fields, including format checks, range limits, and cross-field validation to ensure the calculated "memory year" is not in the future.
- **New Test Suite**: Added `test_birth_date_integration.py` to provide comprehensive testing for the new age-perspective memory writing functionality, including validation and timestamp logic.

### Changed
- **Topic Classifier Accuracy**: Improved the `TopicClassifier` by using the original lowercase text for phrase matching, enhancing accuracy for phrases containing stopwords.
- **Streamlit UI**: Updated the Streamlit UI to use `st.toast` for notifications and added the `journal` topic to the memory management section.
- **User Management Integration**: The new `birth_date` and `delta_year` fields have been fully integrated into the user management stack, including `UserManager`, `UserRegistry`, and Streamlit UI components and utilities.
- **Profile Completeness**: The user profile completeness calculation now includes the `birth_date` and `delta_year` fields.

## [v0.2.3dev0 - 2025-08-26

### Added
- **One-off Query Execution**: The reasoning team CLI (`rteam-cli`) now supports a `--query` argument to execute a single query and exit, streamlining non-interactive use cases.
- **System Shutdown Control**: Added a "Power Off" button to the Streamlit dashboard, allowing for a graceful shutdown of the application directly from the UI.
- **Formalized Memory Schemas**: Introduced a comprehensive `MEMORY_SUBSYSTEM_SCHEMAS.md` document to serve as the single source of truth for all memory-related data structures, clarifying the distinction between legacy (`id`) and current (`memory_id`) schemas. See [ADR-076](./refs/adr/076-formalize-memory-schemas-and-diagnostics.md) for details.
- **Unified Diagnostics Script**: Implemented a new, unified diagnostic script at `scripts/run_diagnostics.py` to provide a centralized and structured way to test the health of all major subsystems.

### Changed
- **Developer Setup Overhaul**: The project setup has been significantly streamlined. It now standardizes on Python 3.12, uses `uv` for faster virtual environment management, and includes a completely revamped `README` with detailed, step-by-step instructions for installation, Docker, and Ollama configuration. See [ADR-077](./refs/adr/077-developer-environment-and-setup-overhaul.md) for details.
- **Task Runner Cleanup**: Renamed the `poe` task `rteam` to `rteam-cli` for improved clarity and consistency.
- **Robust Service Restarts**: Refactored the `switch-user.py` script to use the more robust and centralized `ensure_docker_user_consistency` function for restarting Docker services, improving separation of concerns.
- **Legacy File Rename for Clarity**: Renamed `src/personal_agent/tools/memory_tools.py` to `weaviate_memory_tools.py` to clearly indicate its Weaviate-specific legacy status and avoid confusion with current memory functionality. The file is no longer actively used since the system evolved to use the agno framework without Weaviate. See [ADR-078](./refs/adr/078-memory-tools-rename-for-clarity.md) for details.

### Fixed
- **Streamlit Application Path**: Corrected the file path for the Streamlit application in the `serve-persag` poe task.
- **Memory Schema Consistency**: The new diagnostic script correctly uses the documented `memory_id` attribute for `UserMemory` objects, resolving a class of bugs caused by schema confusion between legacy and current memory models.

### Removed
- **Redundant Agno Workaround**: Removed the obsolete `agno` role-mapping workaround from the reasoning team's model creation, as the underlying framework issue has been resolved.
- **Obsolete UI File**: Deleted the old and unused `tools/paga_streamlit_team_orig.py` file.


## [responsefix/v0.2.4] - 2025-08-25

### Changed
- **Unambiguous Data Directory Configuration**: Refactored data directory management to remove ambiguous and direct `DATA_DIR` usage. The application now consistently uses specific, user-aware environment variables (`USER_DATA_DIR`, `AGNO_KNOWLEDGE_DIR`, etc.) to ensure proper multi-user data isolation and improve security and maintainability. See [ADR-075](./refs/adr/075-unambiguous-data-dir-configuration.md) for details.


## [responsefix/v0.2.3] - 2025-08-24

### Added
- **Streamlit Management Dashboard**: Introduced a new, full-featured Streamlit dashboard (`src/personal_agent/streamlit/dashboard.py`) for comprehensive system management. The dashboard includes tabs for System Status, User Management, Memory Management, and Docker Services, along with a dark mode theme for improved usability. See [ADR-074](./refs/adr/074-reasoning-team-cli-and-ui-updates.md) for details.
- **Response Parsing Guide**: Created a new `runresponse_parsing_guide.md` to provide a clear and comprehensive guide for parsing `RunResponse` and `TeamRunResponse` objects from the `agno` framework, standardizing UI and tool development.

### Changed
- **Enhanced Reasoning Team CLI**: The standalone Ollama Reasoning Team (`src/personal_agent/team/reasoning_team.py`) has been significantly upgraded. It now integrates a full `AgnoPersonalAgent` instance as its memory and knowledge manager, providing feature parity with the main agent's CLI, including all advanced memory commands (`!`, `?`, `@`). The CLI has been rebuilt with `rich` for an improved user experience. See [ADR-074](./refs/adr/074-reasoning-team-cli-and-ui-updates.md) for details.

### Fixed
- **Streamlit User Display**: Corrected a bug in the new Streamlit dashboard where the current user ID was not being displayed reliably. The dashboard now uses a fallback mechanism to ensure the user is always shown.


## [responsefix/v0.23] - 2025-08-23

### Added
- **Qwen Model Settings**: Implemented specific, environment-configurable settings for the Qwen model, including parameters for temperature, `min_p`, `top_p`, and `top_k`. These settings are now applied during model initialization and are displayed in the Streamlit UI for transparency. This is documented in [QWEN_MODEL_SETTINGS_IMPLEMENTATION.md](./refs/QWEN_MODEL_SETTINGS_IMPLEMENTATION.md).
- Added a new `server-persag` task to `pyproject.toml` for starting the Streamlit interface.
- **Robust User Deletion**: Implemented a comprehensive and safe user deletion system. The `UserManager` now supports full data directory cleanup, pre-deletion data backups, and a dry-run mode to preview changes. This functionality is exposed through a new, intuitive "Delete User" interface in the Streamlit dashboard, which includes explicit confirmation checks to prevent accidental data loss. See [ADR-056](./refs/adr/056-robust-user-deletion-with-data-management.md) for details.
- **Enhanced Streamlit Debug Interface**: The `agno_interface.py` has been significantly upgraded with a comprehensive debug sidebar, real-time tool call display, and performance metrics. This provides a much richer environment for inspecting and understanding the agent's behavior. See [ADR-052](./refs/adr/052-enhanced-streamlit-debug-interface.md) for details.
- **Non-Blocking Background Tool**: Introduced a new `run_in_background` tool to allow the agent to execute long-running shell commands without blocking the main execution thread. This enhances the agent's ability to manage background processes and improves overall responsiveness. See [ADR-046](./refs/adr/046-background-tool-execution.md) for details.
- **Semantic Knowledge Ingestion Tools**: Introduced a new `SemanticKnowledgeIngestionTools` toolkit to provide a complete suite of ingestion tools (`ingest_semantic_file`, `ingest_semantic_text`, etc.) for the local LanceDB-based semantic knowledge base. This achieves feature parity with the LightRAG ingestion tools and allows users to easily populate the local vector store. See [ADR-044](./refs/adr/044-semantic-knowledge-ingestion-and-unified-querying.md) for details.
- **Standalone Ollama Reasoning Team**: Introduced a new, lightweight, standalone multi-agent team that uses local Ollama models for reasoning tasks. This team is defined in `src/personal_agent/team/reasoning_team.py` and can be run via the `paga_team_cli` command. It provides a flexible way to perform tasks like web search, financial analysis, and calculations without the full overhead of the `AgnoPersonalAgent`. See [ADR-042](./refs/adr/042-ollama-reasoning-team.md) for more details.
- **Direct Knowledge Query Tool**: Added a new `query_lightrag_knowledge_direct` tool to the `KnowledgeTools` toolkit. This tool allows for direct, unfiltered queries to the LightRAG knowledge base, providing more control for specific use cases like the new reasoning team.
- **Qwen3-8B Summary**: Added a new document summarizing the features and capabilities of the Qwen3-8B model.
- **Formalized Agent Personality**: Embraced and formalized the agent's emergent "AI Friend" personality as a core feature. The agent is now explicitly guided to use memories creatively for building rapport and generating personalized content, while maintaining a strong distinction between its identity and the user's. See [ADR-031](./docs/adr/031-formalizing-emergent-agent-personality.md) for details.
- **Issue Tracking**: Added a new `ISSUES.md` file for internal tracking of running issues and todos.

### Changed
- **Tool Naming**: Renamed `AgnoMemoryTools` to `PersagMemoryTools` and `KnowledgeTools` to `PersagKnowledgeTools` to better reflect their roles within the personal agent (`persag`) ecosystem.
- **Streamlined Streamlit UI and Default Team Mode**: The Streamlit application now defaults to the more capable team-based mode, with a `--single` flag to run in a single-agent configuration. The runtime mode-switching UI has been removed to simplify the user experience. This change is documented in [ADR-072](./refs/adr/072-streamlit-ui-simplification.md).
- **Enhanced Team and Agent Visibility**: The `show_members_responses` and `show_tool_calls` flags are now enabled by default for the `PersonalAgentTeam` and most specialized agents, respectively. This provides greater transparency into agent operations.
- **Dedicated Knowledge Agent for Team Memory and Knowledge Operations**: All memory and knowledge-related operations within the `PersonalAgentTeam` are now explicitly routed through a dedicated `Knowledge Agent` (an `AgnoPersonalAgent` instance). This ensures consistent fact restatement, LLM processing, and streamlines UI integration for memory storage, retrieval, and knowledge management. This refines the architectural decisions made in [ADDR-071](./refs/adr/071-dedicated-knowledge-agent-for-team-memory.md).
- **Optimized Semantic KB Recreate**: Improved the performance and reliability of the semantic knowledge base by implementing a selective recreate strategy. Batch ingestions now trigger a single, efficient vector embedding reload at the end of the process, while single ingestions continue to reload immediately for instant data availability. This reduces batch processing time and prevents race conditions. See [ADR-064](./refs/adr/064-optimized-semantic-kb-recreate.md) for details.
- **Consolidated Knowledge Ingestion**: Overhauled the knowledge ingestion architecture by consolidating logic from four redundant classes into a single, authoritative `KnowledgeTools` toolkit. This eliminated over 1000 lines of duplicate code, established a single source of truth for both LightRAG and semantic knowledge operations, and significantly simplified the agent's architecture and maintainability. For a detailed overview, see the [technical summary](./refs/KNOWLEDGE_INGESTION_CONSOLIDATION_SUMMARY.md) and [ADR-063](./refs/adr/063-consolidated-knowledge-ingestion.md).
- **Unambiguous Data Directory Configuration**: Refactored data directory management to remove ambiguity. The new `USER_DATA_DIR` variable now explicitly points to the current user's data directory, while `DATA_DIR` consistently refers to the global application data root (`PERSAG_ROOT`). This improves configuration clarity and maintainability. See [ADR-062](./refs/adr/062-unambiguous-data-directory-configuration.md) for details.
- **Agent Instruction Refinement**: Updated agent instructions to prevent the output of internal reasoning or chain-of-thought, ensuring responses are direct and user-focused.
- **Centralized Configuration Management**: Consolidated all configuration variables into the `src/personal_agent/config` package, making them centrally accessible and improving maintainability. See [ADR-061](./refs/adr/061-centralized-configuration-management.md) for details.
- **User Identity Single Source of Truth**: Refactored all user identity and path management logic into a single source of truth (`src/personal_agent/config/user_id_mgr.py`) to eliminate duplication and ensure consistent, predictable behavior across the application. See [ADR-060](./refs/adr/060-user-identity-sot-refactor.md) for details.
- **Centralized Configuration Display**: Consolidated all configuration display logic into `src/personal_agent/tools/show_config.py` to eliminate redundancy and improve maintainability. The `settings.py` module no longer contains display logic, adhering to the Single Responsibility Principle. See [ADR-059](./refs/adr/059-centralized-configuration-display.md) for details.
- **Modular User ID Management**: Refactored user ID and path management into a dedicated module (`src/personal_agent/config/user_id_mgr.py`) to resolve circular dependencies and improve modularity. User-specific configurations, including Docker files, are now centralized in a `~/.persag` directory in the user's home, which is created and populated automatically on first run. See [ADR-058](./refs/adr/058-modular-user-id-management.md) for details.
- **Refactoring**: Renamed `src/personal_agent/team/ollama_reasoning_multi_purpose_team.py` to `src/personal_agent/team/reasoning_team.py` and updated all references to the old name. This change was made to simplify the file name and improve clarity.
- **Topic Classification**: Expanded the `astronomy` topic in `topics.yaml` with more keywords to improve memory classification accuracy.
- **Simplified Agent Execution**: Refactored the `AgnoPersonalAgent` to use a simpler, more reliable, non-streaming execution pattern. This removes over 200 lines of complex custom code for response and tool-call handling, resolving multiple bugs and improving maintainability. See [ADR-054](./refs/adr/054-simplified-agent-execution.md) for details.
- **Centralized User Memory Storage**: Refactored all agent and team implementations to use the central `AgentMemoryManager` for storing user memories. This eliminates code duplication and ensures consistent application of critical logic like memory restatement and dual storage across the entire system. See [ADR-053](./refs/adr/053-centralized-user-memory-storage.md) for details.
- **Task Management**: Migrated from a local `TODO.md` file to GitHub Issues for more robust and collaborative task management. See [ADR-051](./refs/adr/051-github-issues-for-task-management.md) for details.
- **Centralized Service Management**: Introduced a new `ServiceManager` to handle all Docker service operations, decoupling them from the `UserManager`. This improves modularity and simplifies the user switching process. A new `switch-user.py` script provides a unified CLI for managing user contexts. See [ADR-049](./refs/adr/049-centralized-service-management.md) for details.
- **Decoupled User and Docker Configuration**: Refactored the entire configuration system to centralize all user-specific and Docker-related files into a `~/.persag` directory in the user's home directory. This decouples the agent's configuration from the project repository, establishes a single source of truth, and enables true multi-user isolation. The new `PersagManager` class handles automatic migration, validation, and provides a dynamic `get_userid()` function to ensure the correct user context is always used. See [ADR-048](./refs/adr/048-decoupled-user-docker-config.md) for details.
- **Robust Docker User Synchronization**: The `DockerUserSync` class has been significantly refactored to improve stability and data integrity. The update introduces comprehensive input validation, robust error handling for file and subprocess operations, atomic file writes to prevent corruption, and more secure, reliable path detection. This ensures the user synchronization process is resilient and predictable. See [ADR-047](./refs/adr/047-robust-docker-user-synchronization.md) for details.
- **Enhanced Ollama Reasoning Team**: The standalone Ollama Reasoning Team (`paga_team_cli`) has been significantly upgraded. It now integrates a full instance of the `AgnoPersonalAgent` as its memory and knowledge manager, providing feature parity with the main agent. The CLI has been rebuilt with `rich` and the `CommandParser` to support advanced memory commands (`!`, `?`, `@`) and deliver a more intuitive, consistent user experience. See [ADR-045](./refs/adr/045-enhanced-ollama-reasoning-team.md) for details.
- **Agent Initialization**: Refactored the `AgnoPersonalAgent` to use a lazy initialization pattern. The agent is now instantiated synchronously (`agent = AgnoPersonalAgent(...)`) and heavy initialization occurs automatically on first use. This simplifies agent creation, improves code clarity, and makes it easier to use agents within teams. The old `create_agno_agent()` factory is now deprecated but maintained for backward compatibility. See [ADR-043](./refs/adr/043-agno-agent-lazy-initialization.md) for details.
- **Model Tuning**: Adjusted the default temperature and top-k parameters for the `qwen3` model to improve the quality and coherence of its responses.
- **Topic Classification**: Enhanced the topic classification system by adding a comprehensive `relationships` category. This resolves a bug where statements about social connections were misclassified as `unknown` and improves the agent's ability to understand and organize memories about personal and professional relationships. See [ADR-039](./refs/adr/039-enhanced-topic-classification-for-relationships.md) for details.
- **Separation of Concerns**: Refactored the unified `MemoryAndKnowledgeTools` class into two distinct, focused toolkits: `KnowledgeTools` for factual data and `AgnoMemoryTools` for personal user information. This improves architectural clarity, enhances agent guidance through descriptive docstrings, and provides clearer boundaries between knowledge and memory operations. See [ADR-037](./refs/adr/037-knowledge-memory-tool-separation.md) for details.
- **Decisive Tool Usage**: Overhauled the agent's instructions to be more decisive and accurate. The new prompts establish a clear distinction between "Memory" (user-specific info) and "Knowledge" (factual info), provide an explicit decision-making flowchart, and map common queries directly to specific tool calls (e.g., "what do you know about me" -> `get_all_memories()`). This resolves issues of tool hesitation and incorrect tool selection. See [ADR-036](./refs/adr/036-tool-use-hesitation-fix.md) for details.
- **Unified Tool Architecture**: Refactored the agent's architecture by consolidating all memory and knowledge-related tools into a single, cohesive `MemoryAndKnowledgeTools` class. This simplifies agent initialization, improves modularity, and aligns with `agno` framework best practices. See [ADR-035](./refs/adr/035-unified-memory-and-knowledge-tools.md) for details.
- **Agno Response Handling Simplification**: Refactored agent response processing to trust Agno's built-in parsing, eliminating redundant content extraction and simplifying streaming logic. This reduces code complexity and improves maintainability. See [ADR-033](./docs/adr/033-agno-response-handling-simplification.md) for details.

### Fixed
- **Tool Call Extraction and Response Handling**: Overhauled the response handling logic to correctly parse and display tool calls and their results. This resolves a critical bug where the Streamlit UI would show raw tool call syntax instead of the executed content from the writer agent. The new `extract_tool_calls_and_metrics` function now robustly handles various tool call formats from different models and agents.
- **Team Delegation and Reasoning**: Switched the `personal_agent_team` from `route` to `coordinate` mode and integrated `ReasoningTools` to significantly improve the coordinator's ability to delegate tasks to the correct specialized agents.
- **Streamlit `arun` Compatibility**: Fixed a bug that caused the Streamlit app to crash when using `agent.arun()` with asynchronous tools in single-agent mode.
- **File Tools Path Handling**: Corrected a recurring issue where file-related tools (`FileTools`, `ShellTools`, `PythonTools`) were failing due to being initialized with string paths instead of the required `pathlib.Path` objects. All tools now correctly use `Path` objects and consistently point to the user's home directory, resolving multiple `'str' object has no attribute 'iterdir'` and `'str' object has no attribute 'joinpath'` errors. This is documented in [ADR-073](./refs/adr/073-file-tools-path-fix.md).
- **Corrected Model Name Typo**: Fixed a typo in `src/personal_agent/core/agent_model_manager.py` from `qwen3:1.7B` to `qwen3:1.7b` to ensure correct model loading.
- **Streamlit Memory Deletion Functionality**: Resolved a critical bug in `tools/paga_streamlit_agno.py` where memory deletion was non-functional due to Streamlit's conditional rendering context issues. The UI now reliably handles memory deletion with proper confirmation flows and immediate visual feedback.
- **`switch-user.py` Script**: Fixed a critical bug in the `switch-user.py` script that prevented it from working correctly with the `~/.persag` home directory structure. The script now correctly locates and manages the LightRAG Docker services, ensuring that user switching is fully functional. See [ADR-065](./refs/adr/065-switch-user-persag-home-fix.md) for details.
- **Memory System Consistency**: Resolved several critical inconsistencies across the memory system. The `show-config` tool now accurately reflects all available memory tools, their dependencies, and the dynamic user ID. The `clear_all_memories` function and the Streamlit UI deletion logic have been consolidated to correctly wipe data from all storage systems (local and graph). A validation script has also been added to prevent future regressions. See [ADR-057](./refs/adr/057-memory-system-consistency-and-validation.md) for details.
- **Memory Instruction Clarity**: Resolved a key ambiguity in the agent's instructions regarding the handling of user memories. The agent is now given a clear, three-stage process (Input, Storage, Presentation) that distinguishes its responsibility (presenting memories in the second person) from the system's (storing memories in the third person). This eliminates confusion and ensures consistent memory processing. See [ADR-055](./refs/adr/055-clarified-memory-instructions.md) for details.
- **Knowledge Coordinator Initialization**: Fixed a critical bug where the `KnowledgeCoordinator` was not being initialized with the local `agno_knowledge` base, preventing local and hybrid knowledge queries from functioning. The coordinator is now correctly instantiated in the `KnowledgeTools` constructor, ensuring reliable query routing. See [ADR-050](./refs/adr/050-knowledge-coordinator-initialization-fix.md) for details.
- **Unified Knowledge Querying**: Refactored the `query_knowledge_base` tool to use the central `KnowledgeCoordinator`. This resolves a bug where `mode="local"` failed to query the semantic knowledge base and ensures all knowledge queries are intelligently and reliably routed to the correct backend (local semantic or LightRAG). See [ADR-044](./refs/adr/044-semantic-knowledge-ingestion-and-unified-querying.md) for details.
- **Agno Role Mapping Bug**: Applied a workaround to fix a critical bug in the `agno` framework where the `system` role was incorrectly mapped to `developer`, causing errors with OpenAI-compatible APIs like LMStudio. The role mapping is now corrected at runtime for all model providers. See [ADR-030](./refs/adr/030-agno-role-mapping-bug-workaround.md) for details.
- **Team Memory Tools**: Resolved a validation issue in the `get_recent_memories` tool that occurred when the agent was used within a team context. The tool now correctly handles default parameter values.
- **Team Agent Responses**: Fixed a bug where the `AgnoPersonalAgent`, when used as a team member, would incorrectly return raw JSON tool calls instead of executing them and returning a natural language response. The agent's internal instructions have been improved to ensure proper tool execution.
- **Qwen3 Tool Calling**: Resolved a critical issue where the `qwen3` model failed to execute tool calls. The `AgentModelManager` has been reverted to use the standard `agno.models.ollama.Ollama` class instead of the unreliable `OllamaTools` wrapper, restoring reliable tool-calling functionality. See [ADR-041](./refs/adr/041-qwen3-tool-calling-fix.md) for details.
- **LightRAG URL Specificity**: Corrected an issue where tools could ambiguously target the wrong LightRAG server. All LightRAG-interacting methods now require an explicit `url` parameter, ensuring that requests for knowledge and memory are always sent to the correct server instance. See [ADR-040](./refs/adr/040-explicit-lightrag-url-parameterization.md) for details.
- **LightRAG URL Configuration**: Corrected the LightRAG URL configuration to ensure proper communication with the LightRAG server. The `query_lightrag_knowledge_direct` method in `agno_agent.py` now consistently uses `LIGHTRAG_URL` for knowledge queries. The `knowledge_coordinator.py` now correctly imports both `LIGHTRAG_URL` (for knowledge queries) and `LIGHTRAG_MEMORY_URL` (for memory queries) to ensure accurate routing between the knowledge and memory LightRAG instances. This resolves issues where the agent was attempting to query the wrong LightRAG instance.
- **Memory Clearing**: Resolved a critical bug where clearing memories via scripts did not consistently update the agent's state. The fix standardizes database connection handling and ensures all components are properly synchronized. See [ADR-038](./refs/adr/038-standardized-memory-clearing.md).
- **Toolkit Initialization**: Corrected a bug in the `MemoryAndKnowledgeTools` `Toolkit` where `async` tools were not being registered correctly. All sync and async tools are now passed to the parent constructor at once, ensuring all tools are available to the agent.
- **Model Compatibility**: Resolved a startup failure with `deepseek-r1` models by documenting that they lack required tool-calling support and recommending compatible alternatives like `qwen3:8b`.
- **Instruction Override**: Removed a flawed optimization that replaced detailed instructions with a simplified version for prompts over 1000 characters. This ensures the agent always uses the full, intended instruction set, preserving its configured sophistication and performance. See [ADR-034](./refs/adr/034-smollm2-optimization-fix.md) for details.
- **Tool Call Extraction**: Resolved an issue where tool calls were not consistently displayed in the Streamlit sidebar, despite successful execution. Implemented an event-based collection strategy to ensure reliable visibility of tool usage. See [ADR-033](./docs/adr/033-agno-response-handling-simplification.md) for details.
- **Memory Grammar Conversion**: Corrected an issue where memories stored in third-person were not consistently converted to second-person when presented to the user, improving conversational flow and identity consistency. See [ADR-032](./docs/adr/032-memory-grammar-conversion-fix.md) for details.

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
- **Comprehensive Memory System Technical Summary**: Updated `COMPREHensive_MEMORY_SYSTEM_TECHNICAL_SUMMARY.md` to reflect the CLI refactor, enhanced memory tool CLI, and new testing infrastructure.

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
