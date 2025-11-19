# Personal Agent v0.9.0 Release Notes

**Release Date**: November 19, 2025

## 🎯 Release Highlights

Personal Agent v0.9.0 represents a major stability and performance milestone, with **40x faster memory queries**, comprehensive **multi-provider LLM support**, and a **production-ready REST API** for external integrations. This release introduces atomic configuration management to prevent UI breakage, enhanced memory confidence scoring for cognitive analytics, and significant operational improvements for reliable, predictable deployments.

---

## ✨ Major Features

### 🚀 Performance & Reliability

#### **40x Faster Memory Queries** (ADR-100)
- Intelligent query classification routes common memory operations through fast-path patterns (~1s) instead of expensive full team inference (~40s)
- Pattern matching for natural language variations: "list my memories", "show memories", etc.
- Dramatically improved user experience for frequent memory operations
- **Files affected**: Query handler, query classifier, fast-path routing

#### **Atomic Configuration Transactions for UI Stability**
- New `ConfigStateTransaction` system ensures all model/provider changes are atomic
- If agent/team re-initialization fails, entire configuration rolls back to previous stable state
- Prevents UI from entering inconsistent or broken states
- Provides reliable feedback on configuration changes with automatic recovery

#### **Centralized Configuration Management** (ADR-096)
- Replaces scattered environment variables with thread-safe `PersonalAgentConfig` singleton
- Eliminates race conditions in multi-threaded environments (Streamlit + REST API)
- Enables dynamic configuration changes at runtime
- Provides change notification callbacks for reactive UI updates

---

### 🔄 Multi-Provider LLM Support

#### **Pluggable Provider Architecture** (ADR-082)
- Support for multiple LLM providers: Ollama, OpenAI, LM Studio, and more
- Dynamic provider switching at runtime without application restart
- Unified `AgentModelManager` handles provider abstraction
- Replaced fragile custom wrappers with stable provider implementations

#### **Unified Model Configuration System**
- 70+ pre-configured model profiles with standardized parameters
- Dynamically loaded based on available models in selected provider
- Comprehensive parameter management: temperature, top-p, top-k, context sizes
- Environment variable configuration: `MODEL_PROVIDER`, `OPENAI_API_KEY`

#### **Streamlit Provider State Management**
- Fixed state desynchronization bug when switching LLM providers
- `SESSION_KEY_CURRENT_PROVIDER` acts as single source of truth
- Auto-scanning of available models when provider changes
- Eliminates manual refresh requirements

---

### 🧠 Enhanced Memory System

#### **Memory Confidence Scoring**
- Every memory now includes a `confidence` score (0.0-1.0) indicating reliability
- Enables cognitive decline analytics through confidence trends
- Automatic mapping of cognitive state to confidence levels
- Visual indicators in UI (🟢🟡🟠🔴) for confidence at a glance

#### **Proxy Agent Tracking**
- Distinguish user memories from agent-generated memories via `is_proxy` flag
- `proxy_agent` field provides attribution to specific agents
- Supports multi-agent architecture with memory contribution tracking
- Dashboard shows proxy agent memory counts and statistics

#### **Rich Memory Statistics**
- Dashboard displays average confidence scores with distribution breakdown
- User vs proxy memory attribution counts
- Detailed proxy agent contribution tracking
- Actionable insights into memory quality and system health

#### **Dual-Storage Memory Restatement**
- Sophisticated two-format storage strategy:
  - **Local storage** (SQLite/LanceDB): Second-person "you have" for natural conversational retrieval
  - **Graph storage** (LightRAG): Third-person with user_id for accurate entity mapping
- Intelligent verb conjugation for grammatically correct third-person conversion
- Comprehensive regex patterns for contractions, possessives, and reflexives
- Eliminates need for presentation conversion in agent instructions

---

### 🌐 REST API & Integration

#### **Comprehensive REST API** (ADR-090)
- Full REST API for programmatic access to memory and knowledge bases
- **Memory endpoints**: store, search, retrieve, update, delete, statistics
- **Knowledge endpoints**: ingest files/text/URLs, query, manage documents
- **System endpoints**: health checks, configuration, diagnostics
- Enables external integrations, automations, and alternative frontends

#### **Enhanced Health Checks**
- Detailed `/api/v1/health` endpoint with comprehensive component checks
- Validates Agent, Team, Memory, and Knowledge subsystems
- Only reports healthy when entire system operational
- Detailed status information for debugging and monitoring

#### **Global State Manager**
- Safe sharing of agent instance between Streamlit UI and REST API threads
- Centralized session management
- Synchronized configuration between UI and API

---

### 🔧 Operational Improvements

#### **Robust Ollama Service Management** (ADR-098)
- Migrated from GUI app to proper macOS `launchd` background service
- Automatic startup on system login
- Eliminates conflicts with Ollama GUI application
- Standardized service management via `launchctl`
- Logs to standard `/var/log` locations

#### **First-Run User Profile Setup**
- Interactive `first-run-setup.sh` script for guided user profile creation
- Intelligent user_id normalization: "John Smith" → "john.smith"
- Validation: lowercase alphanumeric, dots, hyphens, underscores
- Automatic virtual environment activation
- Automatic LightRAG service restart
- Available via `poe setup` task

#### **Non-Interactive Installation**
- Completely automated installer suitable for CI/CD pipelines
- Eliminated all interactive prompts and confirmations
- Dry-run mode with accurate resource status reporting
- True idempotency: safe to run multiple times
- Conditional sudo only when actually needed

#### **Offline Model Detection**
- Works without requiring Ollama service to be running
- Inspects Ollama manifest directory structure directly
- Reliable during fresh installations or service shutdown
- Replaces fragile API-dependent model checking

#### **Graceful Docker Image Handling**
- Docker image pulling is non-fatal with graceful degradation
- Displays informative warnings instead of failing installation
- Images auto-pull when containers start via `docker-compose up`
- Enables installation in restrictive network environments

#### **Decoupled Dashboard** (ADR-097)
- Removed fragile direct Docker management from Streamlit dashboard
- Clearer guidance when Docker unavailable instead of crashing
- Docker management now handled reliably via CLI
- Improved stability and reduced permission/dependency errors

---

### 📚 Knowledge Management

#### **Optimized Semantic Knowledge Base Ingestion**
- Batch ingestion triggers single efficient KB recreate instead of N recreates
- Single item ingestion continues immediate recreate for instant availability
- Reduced batch processing time
- Prevents race conditions in concurrent ingestion

#### **Unified Knowledge Ingestion Tools**
- Consolidated redundant ingestion code from four classes into single toolkit
- Eliminated over 1000 lines of duplicate code
- Unified ingestion methods coordinate LightRAG graph and semantic KB simultaneously
- Clear responsibility boundaries: `KnowledgeTools` orchestration, individual methods internal

#### **Granite 3.1 LLM Standardization**
- LightRAG servers now use IBM Granite 3.1 models with full Apache 2.0 licensing
- Knowledge server: `granite3.1-dense:8b` (5.0GB) for robust document processing
- Memory server: `granite3.1-dense:2b` (1.6GB) for lightweight memory extraction
- Reduced context windows from 128K to 32K for concurrent multi-instance deployment on 24GB RAM
- Personal agent inference continues using proven `qwen3:4b` for tool-calling
- Hybrid strategy: ~9-11GB RAG footprint, ~13-15GB available for agent operations

#### **Dynamic Path Resolution**
- Fixed critical issue with static imports causing stale paths in runtime operations
- Dynamic `get_user_storage_paths()` calls ensure current environment variables used
- Resolves failures in Docker environments with late environment loading
- Affects: dashboard operations, memory operations, document management, knowledge tools

---

### 👥 User Management

#### **Case-Insensitive User Management**
- User IDs now case-insensitive, preventing duplicate "Paula" vs "paula"
- Automatic user ID normalization (lowercase, spaces→dots)
- Lowercase comparison preserves original user_name for display
- Regex validation: alphanumeric, dots, hyphens, underscores only

#### **Enhanced Dashboard User Interface**
- New "Basic Info" tab showing user_name and read-only user_id
- Reordered fields: User Name before User ID (user-centric design)
- Better tab organization with Profile Management before Create User
- Functional Switch User tab with automatic Docker restart and system refresh
- Removed phantom `current_user.json` references, simplified to `~/.persagent/env.userid`

#### **Enhanced Memory Display**
- All memory views show complete `EnhancedUserMemory` fields:
  - Confidence scores with color-coded indicators (🟢🟡🟠🔴)
  - Proxy flags (👤 user, 🤖 agent)
  - Proxy agent attribution
- Export/import preserves all enhanced fields in JSON and CSV
- Complete transparency into memory provenance, quality, and source

#### **Configuration Directory Rebranding**
- User configuration directory renamed from `~/.persag` to `~/.persagent`
- Better brand alignment with "Personal Agent"
- All code, scripts, and documentation updated consistently
- Clearer naming reflecting application identity

---

## 🐛 Bug Fixes

### Critical Fixes
- **UI Provider State**: Fixed state desynchronization when switching LLM providers (ADR-100)
- **Memory Fast Path**: Fixed query classifier pattern matching for natural language variations
- **Semantic KB Ingestion**: Ensured Streamlit UI and REST API properly trigger KB recreation
- **Streamlit Import Handling**: Removed unnecessary defensive `sys.path` manipulation
- **Docker Service Hanging**: Removed `--wait` flag that caused indefinite blocking during user switching
- **User Switching Config Bug**: Fixed directory creation with incorrect names when switching users
- **Memory Storage Singleton**: Fixed bug where switching users created incorrect directory names
- **Dynamic Path Resolution**: Fixed stale path issues in dashboard and file operations

### Quality-of-Life Fixes
- **Redundant Consistency Checks**: Eliminated triple consistency checking during user switching
- **Dashboard Directory Creation**: User creation now creates all 6 required directories
- **Dashboard User Display**: Automatic refresh of user display after switching
- **LightRAG Memory Server**: Corrected Docker configuration environment file reference
- **Installer Idempotency**: Enhanced setup functions with existence checking and accurate dry-run reporting
- **Installer Sudo Requirement**: Eliminated upfront sudo requirement, request only when needed
- **LightRAG Docker Startup**: Fixed "too many colons" error that prevented container startup

---

## 📊 Enhanced Metrics & Analytics

- **Memory confidence distribution**: Breakdown of high/medium/low confidence memories
- **Cognitive state tracking**: Automatic confidence mapping for decline monitoring
- **Proxy agent analytics**: Track which agents contribute memories and their patterns
- **System health statistics**: Comprehensive memory subsystem status
- **Performance metrics**: Response time charts, fast-path usage statistics

---

## 🔄 Migration & Upgrade Guide

### From v0.8.x to v0.9.0

#### Configuration Changes
```bash
# The ~/.persag directory is now ~/.persagent
# This is automatic - no manual migration needed
# Old configurations will be found and migrated on first run
```

#### Environment Variables
- `MODEL_PROVIDER`: Now required for provider selection (default: "ollama")
- New optional variables: `OPENAI_API_KEY` for OpenAI provider support
- All configuration now centralized in `PersonalAgentConfig` singleton

#### Database Migration
- Memory system automatically enhanced with confidence/proxy fields
- Existing memories preserved with default confidence values
- No manual database migration required

### Installation
```bash
# Standard installation remains the same
./install-personal-agent.sh

# For interactive first-run setup (recommended)
poe setup

# Or use CLI directly
python scripts/switch-user.py --create-if-missing
```

### Service Restart
```bash
# Ollama now manages itself via launchd
launchctl start com.local.ollama

# LightRAG services restart automatically
# Manual restart if needed:
smart-restart-lightrag.sh
```

---

## ⚠️ Known Issues & Limitations

- **Granite 3.1 Context Window**: Reduced from 128K to 32K to support 24GB RAM deployments
  - Large document ingestion may require batch processing
  - Use `granite3.1-dense:2b` on memory-constrained systems
- **Docker Image Pre-pull**: Disabled by default to support restricted networks
  - Images auto-pull on first container startup (adds ~1-2 minutes)
  - Manual pre-pull via `docker pull egsuchanek/lightrag_pagent:latest` if desired
- **OpenAI Provider**: Requires valid API key in `OPENAI_API_KEY` environment variable
  - Context size limited by OpenAI model selection
  - Rate limiting applies based on OpenAI plan

---

## 📈 Performance Improvements

| Operation | v0.8.x | v0.9.0 | Improvement |
|-----------|--------|--------|-------------|
| List memories query | ~40s | ~1s | **40x faster** |
| Memory confidence display | N/A | Real-time | New feature |
| Configuration change | ~5s | ~2s | 60% faster |
| User switching | ~15s | ~8s | 47% faster |
| Batch knowledge ingestion | Variable | Optimized | Fewer KB recreates |
| Model switching | Unreliable | Atomic | Reliable with rollback |

---

## 📚 Documentation

- **ADR-100**: Streamlit Provider State Management
- **ADR-099**: Enhanced Memory Schema with Confidence Scoring
- **ADR-098**: Robust Ollama Service Management
- **ADR-097**: Decoupling Dashboard from Docker Management
- **ADR-096**: Centralized Configuration Management
- **ADR-090**: REST API for Memory and Knowledge
- **ADR-082**: Multi-Provider Model Support

Full architectural documentation: `/refs/adr/`

---

## 🙏 Contributors

Special thanks to the Personal Agent community for feedback, bug reports, and feature requests that drove these improvements.

---

## 📥 How to Upgrade

```bash
# Pull latest code
git pull origin main

# Reinstall dependencies and services
./install-personal-agent.sh

# Optional: Run first-time setup for enhanced configuration
poe setup

# Verify installation
python -m personal_agent.core.agno_initialization --check
```

For detailed installation instructions, see [README.md](./README.md)

---

## 📞 Support & Feedback

- Report issues: [GitHub Issues](https://github.com/yourusername/personal_agent/issues)
- Documentation: [GitHub Wiki](https://github.com/yourusername/personal_agent/wiki)
- Architecture Decisions: See `/refs/adr/` directory

---

**Happy agent-ing! 🤖**
