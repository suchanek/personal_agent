# Personal AI Agent - Technical Architecture

**Version**: 0.8.7dev
**Date**: October 7, 2025
**Framework**: Agno (Native Python AI Agent Framework)
**Status**: Production Ready ✅

## Overview

The Personal AI Agent is a sophisticated, multi-user AI assistant built using the Agno framework. It provides intelligent automation, advanced knowledge management through a **dual knowledge base system**, comprehensive memory management with **semantic memory and duplicate detection**, and extensive tool integration. The system emphasizes local data control, privacy, and seamless user interaction through multiple interfaces (CLI, Streamlit web UI, and REST API) while supporting both single-agent and multi-agent team modes.

## Core Architecture

### 🏗️ **System Design Principles**

1. **Manager-Based Architecture**: Specialized manager classes for models, memory, knowledge, tools, and instructions with clear separation of concerns.
2. **Multi-User Support**: Complete user isolation with dynamic path resolution and per-user data storage.
3. **Dual Memory System**: Combined local (SQLite/LanceDB) and graph-based (LightRAG Memory Server on port 9622) memory with semantic search and deduplication.
4. **Dual Knowledge System**: Integrates graph-based (LightRAG KB Server on port 9621) and vector-based (local semantic) knowledge bases for comprehensive understanding.
5. **Dual LightRAG Servers**: Two separate Docker containers - one for knowledge graphs (port 9621) and one for memory graphs (port 9622).
6. **Lazy Initialization**: Thread-safe, async initialization with on-demand component loading for efficient startup.
7. **Local-First**: All data stored locally, with LightRAG servers running in isolated Docker containers.
8. **Framework Native**: Leverages Agno's built-in capabilities instead of manual implementations.
9. **MCP Integration**: Optional Model Context Protocol tool support with dynamic server management.

### 📊 **Architecture Diagram**

```
┌─────────────────────────────────────────────────────────────────┐
│                    Personal AI Agent System                     │
├─────────────────────────────────────────────────────────────────┤
│  🤖 AgnoPersonalAgent Core (Manager-Based Architecture)        │
│  ├── AgentModelManager: LLM provider management               │
│  │   ├── Ollama (qwen3:1.7b, qwen3:8b, llama3.1:8b)           │
│  │   ├── OpenAI (gpt-4o-mini, gpt-4)                          │
│  │   └── LM Studio (local server)                             │
│  ├── AgentInstructionManager: 4-tier instruction levels       │
│  ├── AgentMemoryManager: Dual memory orchestration            │
│  ├── AgentKnowledgeManager: KB lifecycle management           │
│  ├── AgentToolManager: Dynamic tool registration              │
│  └── UserManager: Multi-user support with isolation           │
├─────────────────────────────────────────────────────────────────┤
│  🧠 Dual Memory System                                          │
│  ┌──────────────────────────┬───────────────────────────────┐  │
│  │ **Semantic Memory**      │  **LightRAG Memory Server**   │  │
│  │ - SQLite + LanceDB       │  - Docker Container           │  │
│  │ - Duplicate Detection    │  - Memory Knowledge Graphs    │  │
│  │ - Topic Classification   │  - Relationship Mapping       │  │
│  │ - Anti-Duplicate Manager │  - Port: 9622                 │  │
│  └──────────────────────────┴───────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  📚 Dual Knowledge System                                       │
│  ┌──────────────────────────┬───────────────────────────────┐  │
│  │ **Semantic KB (Vector)**  │  **LightRAG KB Server**      │  │
│  │ - Local LanceDB/Agno     │  - Docker Container           │  │
│  │ - Vector Embeddings      │  - Knowledge Graphs           │  │
│  │ - Similarity Search      │  - Global/Hybrid Search       │  │
│  │ - nomic-embed-text       │  - Port: 9621                 │  │
│  └──────────────────────────┴───────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  🔧 Tool Ecosystem                                              │
│  ├── Built-in: Google Search, Calculator, YFinance            │
│  ├── System: Python execution, Shell commands, Filesystem     │
│  ├── Knowledge: Document ingestion, KB queries                │
│  ├── Memory: Store, search, restate, seed, clear              │
│  └── MCP (Optional): GitHub, Filesystem, Brave Search, etc.   │
├─────────────────────────────────────────────────────────────────┤
│  🌐 Multi-Interface & Remote Access Layer                       │
│  ├── CLI: paga_cli (single), rteam-cli (team)                 │
│  ├── Web: Streamlit UI with dual-mode (single/team)           │
│  ├── Dashboard: System management and monitoring (port 8502)  │
│  ├── REST API: RESTful endpoints for remote integration       │
│  ├── Tailscale: Secure mesh VPN for remote access             │
│  └── iOS Shortcuts: iPhone/iPad memory operations via API     │
└─────────────────────────────────────────────────────────────────┘
```

## Technical Specifications

### 🔧 **Core Components**

#### **1. AgnoPersonalAgent Framework**

- **Framework**: Native Python Agno framework with manager-based architecture
- **Core Class**: `AgnoPersonalAgent` extending `agno.agent.Agent`
- **Initialization**: Lazy, thread-safe with `asyncio.Lock` for async operations
- **Platform**: macOS-optimized deployment (recommended: Mac mini M4 Pro or similar)

**Model Provider System:**

The system supports dynamic switching between multiple LLM providers through `AgentModelManager`:

**Local Providers (Recommended for Privacy & Performance):**
- **Ollama** (default):
  - Base URL: `http://localhost:11434`
  - Recommended models:
    - `qwen3:4b` or `hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:q8_0` (primary recommendation)
    - Unsloth variants generally preferred for quality
    - `qwen3:8b` (more capable, slower)
  - **Note**: LLaMA models (llama3.1) show inconsistent tool calling behavior
  - Model selection prioritizes **usability and throughput** over raw capability
  - Smaller models (4B-8B parameters) balance speed and capability on Apple Silicon
  - No API costs, complete privacy

- **LM Studio**:
  - Base URL: `http://localhost:1234/v1`
  - OpenAI-compatible API
  - **Trade-off**: Faster inference, but can be more brittle/unpredictable
  - Visual model management interface
  - Still evaluating reliability for production use

**Cloud Provider (Optional):**
- **OpenAI**:
  - Base URL: `https://api.openai.com/v1`
  - Models: `gpt-4o-mini`, `gpt-4`, `gpt-4-turbo`
  - **Non-local**: Data sent to OpenAI servers
  - **Cost**: Pay-per-token via API credits
  - Use case: When maximum capability needed and privacy less critical

**Provider Switching:**
- Runtime switching via environment variable: `PROVIDER=ollama|lm-studio|openai`
- Or via `AgentModelManager.switch_provider()`
- No code changes required
- All features work across providers

**Model Selection Philosophy:**
- **Throughput over capability**: Smaller, faster models for daily use
- **Usability focus**: Response times balanced with capability for interactive experience
- **Tool calling reliability**: Qwen models show more consistent tool/function calling than LLaMA
- **Apple Silicon optimization**: Leverage Metal acceleration on M-series chips
- **Memory efficiency**: 4B-8B models fit comfortably in 24GB RAM with room for system
- **Active evaluation**: Model selection and provider performance still being fine-tuned

**Manager System:**
- `AgentModelManager`: LLM provider and model management with dynamic switching
- `AgentInstructionManager`: 4-tier instruction levels (MINIMAL, CONCISE, STANDARD, DETAILED)
- `AgentMemoryManager`: Dual memory system orchestration
- `AgentKnowledgeManager`: Knowledge base lifecycle
- `AgentToolManager`: Dynamic tool registration and introspection
- `UserManager`: Multi-user support with data isolation

#### **2. Dual Knowledge Management**

The agent features a dual knowledge base system, managed by the consolidated `KnowledgeTools`, to provide both broad, relational understanding and fast, semantic retrieval.

**A. LightRAG Knowledge Base (Graph-based)**
- **Technology**: LightRAG Knowledge Server (via Docker)
- **Port**: 9621
- **URL**: `http://localhost:9621`
- **Architecture**: Remote server accessed via HTTP API
- **Strengths**: Builds a knowledge graph to understand relationships between entities. Ideal for complex, relational queries.
- **Search Modes**: Global (graph), Local (semantic), Hybrid, and Mix
- **Storage**: `~/.persag/<user_id>/lightrag_server/`
- **Data Location**: Source files are stored in `~/.persag/<user>/knowledge/` and uploaded to the LightRAG server for processing

**B. Semantic Knowledge Base (Vector-based)**
- **Technology**: Agno `TextKnowledgeBase` with LanceDB.
- **Architecture**: Local, file-based vector database integrated directly into the agent.
- **Strengths**: Fast, efficient vector similarity search for direct questions and fact retrieval.
- **Search Modes**: Vector similarity search.
- **Data Location**: Source files are stored in `PERSAG_ROOT/agno/<user>/knowledge/`.

#### **3. Dual Memory System**

The system features a sophisticated dual memory architecture combining local semantic memory with graph-based memory:

**A. Semantic Memory (Local)**
- **Technology**: `SemanticMemoryManager` with SQLite + LanceDB
- **Storage Locations**:
  - SQLite: `$PERSAG_ROOT/agno/<user_id>/agent_memory.db`
  - LanceDB: `$PERSAG_ROOT/agno/<user_id>/lancedb/`
- **Features**:
  - **Duplicate Detection**: Anti-duplicate manager prevents redundant memories
  - **Topic Classification**: Automatic categorization (personal, work, health, finance, etc.)
  - **Semantic Search**: Vector similarity search for relevant memory retrieval
  - **Memory Analytics**: Statistics, topic distribution, and memory management
- **Operations**: Store, search, restate, seed, check duplicates, clear

**B. Graph Memory (LightRAG Memory Server)**
- **Technology**: Dedicated LightRAG server in Docker container
- **Port**: 9622 (separate from knowledge server)
- **URL**: `http://localhost:9622`
- **Storage**: `~/.persag/<user_id>/lightrag_memory_server/`
- **Purpose**: Build memory knowledge graphs for relationship mapping
- **Features**:
  - Memory relationship mapping and graph construction
  - Context building from historical conversations
  - Graph-based memory retrieval and traversal
  - Temporal memory connections
- **Integration**: Coordinated through `AgentMemoryManager`
- **Status**: Infrastructure in place, direct interface pending implementation

**C. Session & Conversation Management**
- **Session Storage**: SQLite (`$PERSAG_ROOT/agno/<user_id>/agent_sessions.db`)
- **Persistence**: Cross-session memory and conversation history
- **Context**: Automatic context building and retrieval across sessions

**D. Advanced Memory Features**

**1. Intelligent Topic Classification**
- **Technology**: YAML-based extensible topic system (`src/personal_agent/core/topics.yaml`)
- **Categories**: 20+ predefined categories with keyword matching
  - Core: personal_info, work, family, friends, health, finance
  - Activities: hobbies, learning, skills, goals, pets
  - Specialized: academic, technology, automotive, astronomy, weather
  - Emotional: feelings, preferences, journal
  - Safety: self_harm_risk (with crisis detection keywords)
- **Dual Matching**: Both individual keywords and multi-word phrases
- **Extensibility**: Easy to add new categories and keywords without code changes
- **Auto-Classification**: Automatic topic assignment during memory storage

**2. Temporal Memory Journaling (delta_year)**
- **Purpose**: Enable memory recording "as if" the user is at a specific age
- **Field**: `delta_year` in user profile (0-150 range)
- **Calculation**: If delta_year > 0, memory timestamp = birth_year + delta_year
- **Use Cases**:
  - **Historical Journaling**: Record childhood memories from the perspective of that age
  - **Life Story Documentation**: Build chronological life narrative
  - **Memory Reconstruction**: Capture memories from different life periods
  - **Therapeutic Applications**: Age-appropriate memory recording for cognitive support
- **Example**: User born 1960, delta_year=6 → memories stamped as 1966
- **Integration**: Automatically applied in `AgentMemoryManager.store_memory()`

**3. Cognitive State Tracking**
- **Purpose**: Gauge memory fidelity and reliability for users with cognitive challenges
- **Field**: `cognitive_state` in user profile (0-100 scale, default: 100)
- **Scale Interpretation**:
  - **100-80**: Full cognitive function, high memory reliability
  - **79-60**: Mild cognitive impairment, good memory fidelity
  - **59-40**: Moderate impairment, reduced reliability
  - **39-20**: Significant impairment, questionable accuracy
  - **19-0**: Severe impairment, very low confidence
- **Memory Confidence**: Enables calculation of confidence scores for stored memories
- **Formula**: `memory_confidence = (cognitive_state / 100) * base_confidence`
- **Applications**:
  - Weight memory retrieval by reliability
  - Flag memories requiring verification
  - Track cognitive decline over time
  - Adjust memory processing based on user capability
- **UI Integration**: Visual slider in Streamlit interface with progress bar display

**4. Memory by Proxy (Future Feature)**
- **Concept**: Designated person can add memories on behalf of the primary user
- **Fields** (planned):
  - `memory_proxy_person`: Designated proxy user_id or name
  - `proxy_relationship`: Relationship to primary user (caregiver, family, therapist)
  - `proxy_permissions`: Scope of proxy capabilities (read, write, edit)
- **Use Cases**:
  - **Cognitive Decline**: Caregiver records daily activities for patient
  - **Children**: Parents record childhood memories
  - **Elderly Care**: Family members document life events
  - **Medical Support**: Healthcare providers maintain patient memory records
- **Implementation Plan**:
  - Add proxy fields to User model
  - Create proxy authorization system
  - Tag memories with originator (self vs proxy)
  - Enable proxy switching in UI
  - Audit trail for proxy-added memories

#### **4. User Profile Model**

The system uses a comprehensive user model (`User` dataclass in `user_model.py`) that extends beyond basic identity:

**Core Identity Fields:**
- `user_id`: Unique identifier
- `user_name`: Display name
- `user_type`: User classification (Standard, Premium, etc.)
- `created_at`: Account creation timestamp
- `last_seen`: Last activity timestamp

**Extended Profile Fields:**
- `email`: Email address with validation
- `phone`: Phone number with flexible format support
- `address`: Physical address
- `birth_date`: Birth date in ISO format (YYYY-MM-DD)

**Advanced Memory Features:**
- **`delta_year`** (0-150): Years from birth for memory timestamp adjustment
  - Enables "memory as if at age X" functionality
  - Automatic year calculation: `memory_year = birth_year + delta_year`
  - Supports historical memory reconstruction
  - Example: Born 1960, delta_year=6 → memories timestamped as 1966

- **`cognitive_state`** (0-100): Cognitive function gauge for memory fidelity
  - **100-80**: Full cognitive function, high reliability
  - **79-60**: Mild impairment, good fidelity
  - **59-40**: Moderate impairment, reduced reliability
  - **39-20**: Significant impairment, questionable accuracy
  - **19-0**: Severe impairment, very low confidence
  - Used for memory confidence calculation
  - Enables weighted memory retrieval
  - Tracks cognitive decline over time

**Future Proxy Fields (Planned):**
- `memory_proxy_person`: Designated proxy user_id
- `proxy_relationship`: Relationship to primary user
- `proxy_permissions`: Scope of proxy capabilities
- Enables caregiver/family memory recording on behalf of user

**Validation:**
- Email format validation with regex
- Phone number format validation (7-15 digits)
- Birth date reasonableness checks (year 1 to 9999)
- Cognitive state range enforcement (0-100)
- Delta year range validation (0-150)

#### **5. REST API & Remote Access**

The system provides comprehensive REST API access for remote integration and mobile device support.

**API Architecture:**
- **Framework**: FastAPI-based RESTful endpoints
- **Location**: `src/personal_agent/tools/rest_api.py`
- **Authentication**: Token-based secure access
- **Response Format**: JSON with structured responses
- **Async Support**: Non-blocking operations for scalability

**Core API Endpoints:**
- **Memory Operations**:
  - `POST /memory/store` - Store new memory
  - `GET /memory/search` - Search memories by query
  - `GET /memory/list` - List recent memories
  - `GET /memory/stats` - Memory statistics and analytics
  - `DELETE /memory/clear` - Clear memories by criteria
- **Knowledge Operations**:
  - `POST /knowledge/query` - Query knowledge base
  - `POST /knowledge/upload` - Upload documents
  - `GET /knowledge/status` - KB status and info
- **User Operations**:
  - `GET /user/profile` - Get user profile
  - `PUT /user/profile` - Update user profile
  - `GET /user/switch` - Switch active user
- **Agent Operations**:
  - `POST /agent/run` - Execute agent query
  - `GET /agent/status` - Agent status and info
  - `POST /agent/stream` - Streaming responses

**Tailscale Mesh VPN Integration:**
- **Secure Network**: Personal AI Agent runs on dedicated server within Tailscale mesh
- **Device Registration**: Only explicitly registered devices can access
- **Zero Trust Model**: Network-level security with encrypted tunnels
- **Access Control**: Per-device authentication and authorization
- **Deployment Pattern**:
  - Run agent on home server or cloud instance
  - Join server to Tailscale network
  - Access from iPhone, iPad, Mac via Tailscale IP
  - No port forwarding or public IP exposure required

**iOS/macOS Shortcuts Integration:**
Pre-built Shortcuts enable native iOS memory operations:

1. **Save Memory Shortcut**:
   - Capture memory via voice or text input
   - Optionally add topic tags
   - Send to Personal Agent via REST API
   - Receive confirmation with memory ID

2. **List Memories Shortcut**:
   - Fetch recent memories from agent
   - Display in formatted list
   - Option to filter by topic or date

3. **Search Memories Shortcut**:
   - Input search query
   - Query agent via API
   - Display matching memories with relevance scores

4. **Memory Stats Shortcut**:
   - Fetch memory count and topic distribution
   - Display cognitive state and confidence metrics
   - Show recent activity summary

**Shortcut Configuration:**
- Base URL: Tailscale IP of server (e.g., `http://100.x.x.x:8000`)
- API Token: Configured in shortcut for authentication
- User ID: Select target user for multi-user systems
- Timeout: Configurable for network conditions

**Benefits:**
- **On-the-Go Memory Capture**: Record memories immediately from iPhone
- **Voice Input Support**: Use Siri to capture memories hands-free
- **Secure Access**: Tailscale ensures only your devices can access
- **No Cloud Required**: Direct connection to your personal server
- **Offline Queuing**: Shortcuts can queue operations when offline (iOS feature)

#### **6. MCP Tool Ecosystem**

```yaml
MCP Servers (6 active):
  github:
    command: npx
    args: [-y, @modelcontextprotocol/server-github]
    env: GITHUB_TOKEN
    
  filesystem:
    command: npx  
    args: [-y, @modelcontextprotocol/server-filesystem]
    env: ALLOWED_DIRECTORIES
    
  brave-search:
    command: npx
    args: [-y, @modelcontextprotocol/server-brave-search]
    env: BRAVE_API_KEY
    
  puppeteer:
    command: npx
    args: [-y, @modelcontextprotocol/server-puppeteer]
    
  fetch:
    command: npx
    args: [-y, @modelcontextprotocol/server-fetch]
    
  postgres:
    command: npx
    args: [-y, @modelcontextprotocol/server-postgres]
    env: DATABASE_URL
```

### 📁 **File Structure (User Data)**

User-specific data is stored in two main locations for complete isolation:

**1. PERSAG_HOME (`~/.persag/`)**
```
~/.persag/
├── current_user.json                    # Active user ID
├── user_registry.json                   # All registered users
├── lightrag_server/                     # Knowledge Docker config
│   ├── docker-compose.yml
│   └── storage/<user_id>/               # Graph KB storage
├── lightrag_memory_server/              # Memory Docker config
│   ├── docker-compose.yml
│   └── storage/<user_id>/               # Graph memory storage
└── <user_id>/
    ├── knowledge/                       # Source files for LightRAG KB
    └── user_profile.json                # User metadata

```

**2. PERSAG_ROOT (Default: `/Users/Shared/personal_agent_data`)**
```
$PERSAG_ROOT/agno/<user_id>/
├── agent_sessions.db                    # SQLite: Session management
├── agent_memory.db                      # SQLite: Semantic memory
├── knowledge/                           # Source files for Semantic KB
└── lancedb/                             # LanceDB: Vector embeddings
    ├── memory_vectors.lance             # Semantic memory vectors
    └── knowledge_vectors.lance          # Knowledge vectors
```

**3. Core Application Code**
```
src/personal_agent/
├── core/                                # Core agent components
│   ├── agno_agent.py                   # Main agent class
│   ├── agent_model_manager.py          # LLM provider management
│   ├── agent_memory_manager.py         # Memory orchestration
│   ├── agent_knowledge_manager.py      # KB lifecycle
│   ├── agent_tool_manager.py           # Tool management
│   ├── agent_instruction_manager.py    # Instruction assembly
│   ├── semantic_memory_manager.py      # Semantic memory + deduplication
│   ├── knowledge_coordinator.py        # Unified KB queries
│   ├── user_manager.py                 # Multi-user support
│   └── ...
├── tools/                               # Tool implementations
│   ├── knowledge_tools.py              # KB operations
│   ├── memory_functions.py             # Standalone memory operations
│   ├── personal_agent_tools.py         # System integration
│   ├── paga_streamlit_agno.py          # Main Streamlit UI
│   └── rest_api.py                     # REST endpoints
├── config/                              # Configuration
│   ├── settings.py                     # Environment variables
│   └── user_id_mgr.py                  # User ID management
├── streamlit/                           # Additional UIs
│   └── dashboard.py                    # System dashboard
└── team/                                # Multi-agent team
    └── reasoning_team.py               # Team orchestration
```

## Key Capabilities

### 🎯 **Core Features**

#### **1. Advanced Memory Management**

**Intelligent Topic Classification:**
- **YAML-Based System**: 20+ extensible topic categories in `topics.yaml`
- **Auto-Classification**: Automatic topic assignment using keyword and phrase matching
- **Easy Extension**: Add new categories without code changes
- **Comprehensive Coverage**: Personal, work, health, academic, hobbies, feelings, and more
- **Safety Detection**: Built-in self-harm risk category with crisis keywords

**Temporal Memory Journaling (delta_year):**
- **Age-Contextual Recording**: Record memories "as if" at a specific age
- **Historical Reconstruction**: Build chronological life narratives
- **Timestamp Adjustment**: Automatic year calculation based on birth_year + delta_year
- **Therapeutic Support**: Enable age-appropriate memory recording
- **Use Case Example**: Born 1960, delta_year=6 → memories timestamped as 1966

**Cognitive State Tracking:**
- **Reliability Gauge**: 0-100 scale tracking cognitive function
- **Memory Confidence**: Calculate confidence scores for memory fidelity
- **Decline Tracking**: Monitor cognitive changes over time
- **Weighted Retrieval**: Adjust memory reliability based on cognitive state
- **Visual Indicators**: UI displays cognitive state with progress bars

**Memory by Proxy (Planned):**
- **Proxy Recording**: Designated persons can add memories on behalf of user
- **Caregiver Support**: Family members document memories for loved ones
- **Authorization System**: Controlled permissions for proxy access
- **Audit Trail**: Track who recorded each memory
- **Use Cases**: Cognitive decline support, childhood memories, elderly care

#### **2. Knowledge-Aware Responses**

- **Personal Information Retrieval**: Automatically searches knowledge base for user information
- **Contextual Understanding**: Combines knowledge base data with conversation context
- **Technical Specification Queries**: Provides detailed system architecture information
- **Project Status Updates**: Tracks development progress and migration status
- **Dual KB Search**: Queries both graph-based and vector-based knowledge systems

#### **3. Comprehensive Tool Integration**

**Built-in Tools:**
- **Google Search**: Real-time web search via `googlesearch-python`
- **Calculator**: Mathematical computations via Agno's CalculatorTools
- **YFinance**: Stock market data and financial information
- **Python Execution**: Code execution in isolated environment
- **Shell Commands**: System command execution with restrictions

**Knowledge & Memory Tools:**
- **Knowledge Operations**: Document ingestion, search, KB management via `KnowledgeTools`
- **Memory Functions**: Standalone operations via `memory_functions.py`
  - Store memories with topic classification
  - Search semantic and graph memory
  - Restate for clarity and deduplication
  - Seed initial memories from templates
  - Check duplicates before storage
  - Clear memory by topic or date range

**System Tools:**
- **Filesystem Operations**: Via `PersonalAgentFilesystemTools` with user-specific restrictions
- **System Integration**: Via `PersonalAgentSystemTools` for agent info and configuration

**MCP Server Tools (Optional):**
- **GitHub**: Repository operations, PR management, issue tracking
- **Filesystem**: Advanced file operations
- **Brave Search**: Web search API
- **Puppeteer**: Browser automation and web scraping
- **Fetch**: HTTP requests and content retrieval
- **PostgreSQL**: Database queries and data analysis

#### **4. Multi-Interface & Remote Access Support**

**Local Interfaces:**
- **CLI Modes**:
  - **Single Agent**: `poetry run paga_cli` or `poe cli` - Direct agent interaction
  - **Team Mode**: `poetry run rteam-cli` or `poe team` - Multi-agent team collaboration
- **Web Interfaces**:
  - **Unified Streamlit UI**: `poe serve-persag` - Dual-mode interface (single/team) on port 8501
  - **System Dashboard**: `poe dashboard` - Monitoring and management on port 8502
- **Mode Switching**: Dynamic switching between single-agent and team modes in web UI
- **Multi-User UI**: User selection and switching directly in interface

**Remote Access via Tailscale Mesh VPN:**
- **Secure Network**: System accessible on Tailscale mesh VPN network
- **Device Support**: Access from registered iPhones, iPads, and other trusted devices
- **Server Deployment**: Run on dedicated server, access from anywhere
- **Zero Trust Security**: Only registered devices on personal mesh network can connect
- **Encrypted Communication**: All traffic encrypted through Tailscale tunnel

**REST API Integration:**
- **RESTful Endpoints**: Full API via `rest_api.py` for programmatic access
- **Remote Operations**: Store, retrieve, search memories via API
- **iOS/macOS Shortcuts**: Pre-built Shortcuts for common operations
  - **Save Memory**: Quick capture from iPhone/iPad
  - **List Memories**: Browse recent memories
  - **Search Memories**: Find specific memories by query
  - **Memory Statistics**: View counts and analytics
- **Streaming Responses**: Real-time response generation with async support
- **Authentication**: Secure API access for remote clients

### 🚀 **Advanced Capabilities**

#### **1. Intelligent Memory Management Example**

```python
# Example: Recording a childhood memory with temporal context
# User profile: birth_year=1960, delta_year=6, cognitive_state=100

# Store memory with automatic features
memory_content = "I learned to ride my bicycle without training wheels today!"

# The system automatically:
# 1. Classifies topic → "hobbies", "learning"
# 2. Adjusts timestamp → 1966 (birth_year + delta_year)
# 3. Calculates confidence → 1.0 (cognitive_state=100)
# 4. Checks for duplicates using semantic similarity
# 5. Stores in both semantic (local) and graph (LightRAG) memory

response = await agent.memory_manager.store_memory(
    content=memory_content,
    user=user_profile  # Contains delta_year and cognitive_state
)

# Result: Memory stored with:
# - Topics: ["hobbies", "learning"]
# - Timestamp: 1966-10-07 (age-adjusted)
# - Confidence: 1.0 (full reliability)
# - Duplicate check: Passed
```

#### **2. Cognitive State and Memory Confidence**

```python
# Example: User with cognitive impairment
# User profile: cognitive_state=60 (mild impairment)

# When storing memory:
base_confidence = 0.95  # Initial confidence from duplicate check
cognitive_factor = user.cognitive_state / 100  # 0.60
memory_confidence = base_confidence * cognitive_factor  # 0.57

# System can use this to:
# - Flag memories requiring verification
# - Weight retrieval results by reliability
# - Track confidence changes over time
# - Alert caregivers to significant decline
```

#### **3. Intelligent Knowledge Search**

```python
# Automatic knowledge search for personal queries
Query: "What is my name?"
→ Agent automatically calls: asearch_knowledge_base(query="Eric user identity")
→ Returns: Detailed profile information about Eric G. Suchanek
```

#### **4. Multi-Tool Coordination**

- **GitHub + Knowledge**: Correlates repository data with personal projects
- **Web + Memory**: Researches topics while maintaining conversation context
- **Files + Knowledge**: Analyzes local files with knowledge base context
- **Memory + Topic Classification**: Stores memories with automatic categorization

#### **5. Technical Analysis**

- **System Architecture**: Explains its own technical implementation
- **Memory Analytics**: Provides statistics on topic distribution and memory patterns
- **Cognitive Tracking**: Monitors cognitive state changes over time
- **Performance Metrics**: Monitors response times and resource usage

## Performance Characteristics

### 💻 **Recommended Hardware Configuration**

**Ideal Deployment Platform:**
- **Device**: Mac mini M4 Pro (or equivalent Apple Silicon Mac)
- **Processor**: M4 Pro chip (14-core CPU, 20-core GPU)
- **Memory**: 24GB unified memory (recommended minimum)
- **Storage**: 512GB SSD (minimum), 1TB recommended
- **Network**: Ethernet or Wi-Fi 6E for Tailscale performance

**Why Mac mini M4 Pro?**
- **Apple Silicon Performance**: Metal acceleration for ML workloads
- **Unified Memory**: 24GB shared between CPU/GPU/Neural Engine
- **Power Efficiency**: Silent operation, low power consumption (~5-15W idle)
- **Always-On Server**: Designed for 24/7 operation
- **Compact Form Factor**: Desk-friendly, doesn't take space
- **Price/Performance**: Excellent value for AI inference workloads

**Memory Allocation (24GB System):**
- **macOS System**: ~4-6GB
- **LLM Model (qwen3:4b)**: ~4-5GB when loaded
- **LightRAG Servers**: ~2-4GB (Docker containers)
- **Vector Databases**: ~1-2GB (LanceDB)
- **Streamlit/API Server**: ~1GB
- **Available Headroom**: ~8-10GB for browser, apps, multi-user

**Alternative Configurations:**
- **Mac Studio M2 Max/Ultra**: More power, higher cost
- **MacBook Pro M3/M4**: Portable option, higher idle power
- **Mac mini M2/M2 Pro**: Budget option, still excellent performance
- **Not Recommended**: Intel Macs (no Metal acceleration, higher power usage)

### ⚡ **System Performance**

**On Mac mini M4 Pro with qwen3:4b (typical workload):**

| Metric | Value | Notes |
|--------|-------|-------|
| **Startup Time** | < 5 seconds | Lazy initialization, no external dependencies |
| **Response Time** | 2-5 seconds | Varies by query complexity and model load |
| **Token Generation** | ~20-40 tokens/sec | Apple Silicon Metal acceleration |
| **Memory Usage** | ~12-16GB total | Includes all services and LLM |
| **Storage Size** | 1-10GB | Grows with memories and knowledge |
| **Concurrent Users** | 1-5 users | Limited by model context, not hardware |
| **Uptime** | 99%+ | Stable macOS operation |

**Model Performance Comparison (on M4 Pro, approximate):**

| Model | Parameters | RAM Usage | Response Time | Tool Calling | Notes |
|-------|-----------|-----------|---------------|--------------|-------|
| qwen3:4b | 4B | ~4-5GB | 2-4s | Reliable | **Primary recommendation** |
| qwen3:4b-unsloth | 4B | ~4-5GB | 2-4s | Reliable | Higher quality variant |
| qwen3:8b | 8B | ~6-8GB | 3-6s | Reliable | More capable, slower |
| llama3.1:8b | 8B | ~6-8GB | 3-6s | Inconsistent | Not recommended for tool use |
| lmstudio models | Varies | Varies | Faster | Brittle | Under evaluation |
| gpt-4o-mini | Cloud | 0GB local | 3-8s | Excellent | Cloud option, costs money |

**Performance Notes:**
- Response times vary significantly based on query complexity, context length, and system load
- First query after model load may be slower (cold start)
- Times shown are typical for interactive use, not benchmarks
- Model and provider selection still being optimized for best balance

### 🔄 **Operational Metrics**

- **Knowledge Base**: 6 documents, 4 files actively indexed
- **Vector Dimensions**: 768 (nomic-embed-text)
- **Search Results**: Typically 3-6 relevant documents per query
- **Tool Success Rate**: >95% for properly configured MCP servers
- **Session Persistence**: 100% across restarts

## Security and Privacy

### 🔒 **Data Protection**

1. **Local Storage Only**: All data remains on local machine
2. **No Cloud Dependencies**: Zero external data transmission
3. **File-Based Encryption**: Optional encryption for sensitive files
4. **Access Control**: Directory-based permission system
5. **Audit Logging**: Complete interaction history tracking

### 🛡️ **Security Features**

- **Environment Isolation**: MCP servers run in isolated environments
- **Permission Management**: Explicit directory access controls
- **Token Security**: API keys stored in environment variables
- **Process Isolation**: Each MCP server runs as separate process

## Development and Maintenance

### 🔧 **Development Setup**

```bash
# Environment setup
poetry install
source .venv/bin/activate

# Run CLI interface
poetry run paga_cli

# Run tests
poetry run pytest tests/

# Simple knowledge agent test
python corrected_personal_agent.py
```

### 📊 **Monitoring and Debugging**

```python
# Debug mode enables detailed logging
agent = AgnoPersonalAgent(debug=True)

# View tool calls and reasoning
agent.show_tool_calls = True

# Check agent status
agent_info = agent.get_agent_info()
```

## Recent Achievements

### ✅ **Major Milestones (v0.8.x - 2025)**

1. **Manager-Based Architecture**: Implemented specialized manager classes for clean separation of concerns
2. **Dual LightRAG Servers**: Two separate Docker containers - Knowledge Server (port 9621) and Memory Server (port 9622)
3. **Dual Memory System**: Integrated semantic memory (SQLite/LanceDB) with graph-based memory (LightRAG)
4. **Dual Knowledge System**: Combined graph-based (LightRAG) and vector-based (local semantic) knowledge bases
5. **Multi-User Support**: Complete user isolation with dynamic path resolution and user registry
6. **Tailscale Mesh VPN Integration**: Secure remote access from registered iOS/iPad devices
7. **iOS/macOS Shortcuts**: Pre-built shortcuts for memory operations via REST API
8. **REST API**: Full RESTful endpoints for remote and programmatic integration
9. **Unified Web Interface**: Streamlit UI with dual-mode support (single-agent and team)
10. **YAML-Based Topic Classification**: Extensible 20+ topic categories with keyword matching (`topics.yaml`)
11. **Temporal Memory Journaling**: delta_year parameter enables age-contextual memory recording
12. **Cognitive State Tracking**: 0-100 scale for memory fidelity and confidence scoring
13. **Anti-Duplicate System**: Semantic similarity checking prevents redundant memories
14. **Comprehensive Testing**: 52-memory test corpus with 13 diverse search scenarios
15. **Four-Tier Instructions**: Adaptive instruction levels for performance tuning
16. **System Dashboard**: Streamlit-based monitoring and management interface
17. **Safety Detection**: Self-harm risk category with crisis keyword detection

### 🔄 **Key Improvements**

- **Lazy Initialization**: Thread-safe async initialization with efficient startup
- **Dynamic Tool Management**: Runtime tool registration/unregistration with introspection
- **Memory Analytics**: Statistics, topic distribution, and temporal analysis
- **User Management**: Switch between users with `poe switch-user` command
- **Docker Integration**: Two LightRAG services in isolated containers (knowledge + memory)
- **Memory Knowledge Graphs**: Dedicated LightRAG server builds memory relationship graphs
- **Standalone Memory Functions**: Memory operations decoupled from agent for flexibility
- **Enhanced Debugging**: Detailed logging and pretty-printed responses

## Future Roadmap

### 🎯 **Short-term Goals**

- [ ] **LightRAG Memory Server Integration**: Direct interface to port 9622 for graph-based memory queries
- [ ] **Memory Graph Visualization**: Visualize memory relationship graphs from LightRAG Memory Server
- [ ] **Memory by Proxy System**: Enable designated caregivers/family to add memories on behalf of users
- [ ] **Memory Confidence Scoring**: Implement confidence calculations based on cognitive_state
- [ ] **Enhanced Memory Search**: Temporal queries with date ranges and cognitive state filtering
- [ ] **Topic Analytics Dashboard**: Visualize topic distribution and memory patterns over time
- [ ] **Knowledge Base Auto-Updates**: Learn from conversations and update KB automatically
- [ ] **Additional MCP Servers**: Slack, Discord, Email integrations
- [ ] **Performance Optimization**: Response caching and query optimization
- [ ] **Memory Timeline View**: Interactive timelines showing memories by delta_year context
- [ ] **Team Coordination**: Improved agent specialization and collaboration

### 🚀 **Long-term Vision**

- [ ] Advanced reasoning with chain-of-thought and planning
- [ ] Custom tool development framework with templates
- [ ] Mobile interface development (iOS/Android apps)
- [ ] Voice interface integration
- [ ] Multi-modal support (images, audio, video processing)
- [ ] Federated learning across user instances (privacy-preserving)
- [ ] Plugin marketplace for community-developed tools
- [ ] Advanced analytics and insights dashboard

## Configuration

### ⚙️ **Environment Variables**

```bash
# Core Configuration
LOG_LEVEL=INFO                                      # Logging level (DEBUG, INFO, WARNING, ERROR)
PERSAG_ROOT=/Users/Shared/personal_agent_data      # Root directory for user data
PERSAG_HOME=~/.persag                              # User registry and Docker configs

# LLM Configuration
PROVIDER=ollama                                     # LLM provider (ollama, openai, lm-studio)
LLM_MODEL=qwen3:1.7b                               # Default model
OLLAMA_URL=http://localhost:11434                  # Ollama server URL
LMSTUDIO_URL=http://localhost:1234/v1             # LM Studio server URL (if used)
INSTRUCTION_LEVEL=CONCISE                          # Instruction level (MINIMAL, CONCISE, STANDARD, DETAILED)

# LightRAG Services (Docker) - Two separate servers
LIGHTRAG_URL=http://localhost:9621                 # Knowledge graph server
LIGHTRAG_MEMORY_URL=http://localhost:9622          # Memory graph server
LIGHTRAG_PORT=9621                                 # Knowledge server port
LIGHTRAG_MEMORY_PORT=9622                          # Memory server port

# Storage Backend
STORAGE_BACKEND=agno                               # Always use agno (weaviate deprecated)

# MCP Configuration (Optional)
USE_MCP=true                                       # Enable MCP server tools
GITHUB_TOKEN=ghp_xxx...                           # GitHub access token
BRAVE_API_KEY=BSA_xxx...                          # Brave search API key
DATABASE_URL=postgresql://...                      # PostgreSQL connection string

# Directory Configuration (Auto-configured per user)
HOME_DIR=/Users/<username>                         # User home directory
ROOT_DIR=/                                         # Root for MCP filesystem server
REPO_DIR=./repos                                   # Repository directory

# Model Settings (Advanced)
QWEN_INSTRUCT_TEMPERATURE=0.7                     # Instruct model temperature
QWEN_INSTRUCT_TOP_P=0.80                          # Instruct model top_p
QWEN_THINKING_TEMPERATURE=0.6                     # Thinking model temperature
QWEN_THINKING_TOP_P=0.95                          # Thinking model top_p
```

**Note**: Most variables have sensible defaults in `settings.py`. User-specific paths are dynamically resolved based on the active user ID stored in `~/.persag/current_user.json`.

### 🏃 **Quick Start**

**Web Interface (Recommended):**
```bash
# Unified Streamlit interface (default: team mode)
poe serve-persag

# Single-agent mode
poe serve-persag --single

# System dashboard
poe dashboard
```

**CLI Interface:**
```bash
# Single agent CLI
poe cli

# Team mode CLI
poe team
```

**User Management:**
```bash
# Switch users
poe switch-user <user_id>

# Check current user
poe switch-user --status

# Create new user
poe switch-user new_user --user-name "John Doe" --user-type standard
```

**Memory Management:**
```bash
# Store a fact
poe store-fact "I work as a software engineer at Google"

# Test memory system
poe test-memory

# Clean memory
poe memory-clean
```

**Development:**
```bash
# Run comprehensive tests
poe test-all

# Install MCP servers
poe mcp-install

# Restart LightRAG services
poe restart-lightrag

# View configuration
poe config
```

## Conclusion

The Personal AI Agent represents a mature, production-ready implementation of a sophisticated multi-user AI assistant system. Built on the Agno framework with a manager-based architecture, it demonstrates several key innovations:

### 🎯 **Key Achievements**

1. **Manager-Based Architecture**: Clean separation of concerns through specialized manager classes for models, memory, knowledge, tools, and instructions.

2. **Dual Memory System**: Innovative combination of local semantic memory (with duplicate detection and topic classification) and graph-based memory (dedicated LightRAG Memory Server on port 9622) for comprehensive memory management.

3. **Multi-User Support**: Complete user isolation with dynamic path resolution, enabling true multi-tenancy with dedicated storage per user.

4. **Dual Knowledge System**: Integration of graph-based (LightRAG Knowledge Server on port 9621) and vector-based (local semantic) knowledge bases for nuanced information retrieval.

5. **Mobile & Remote Access**: Tailscale mesh VPN integration with iOS/macOS Shortcuts for secure memory capture from iPhone, iPad, and Mac devices.

6. **Flexible Deployment**: Multiple interfaces (CLI, Streamlit web UI, dashboard, REST API) with support for both single-agent and multi-agent team modes.

7. **Comprehensive Testing**: Extensive test suite covering unit tests, integration tests, memory system tests (52 memories, 13 test cases), and tool functionality validation.

### 🌟 **Technical Highlights**

- **Thread-Safe Async Initialization**: Lazy loading with asyncio.Lock for efficient startup
- **Four-Tier Instruction System**: Adaptive instruction levels (MINIMAL, CONCISE, STANDARD, DETAILED) for performance tuning
- **Dual LightRAG Architecture**: Separate servers for knowledge (port 9621) and memory (port 9622) graphs
- **Tailscale Mesh VPN**: Secure remote access from registered iOS/iPad/Mac devices
- **iOS/macOS Shortcuts**: Native mobile memory operations via REST API
- **YAML-Based Topic System**: 20+ extensible categories with easy keyword addition in `topics.yaml`
- **Temporal Memory Journaling**: delta_year parameter enables age-contextual memory recording
- **Cognitive State Tracking**: 0-100 scale for memory fidelity and confidence calculation
- **Anti-Duplicate Memory**: Semantic similarity checking prevents redundant memory storage
- **Memory by Proxy (Planned)**: Caregiver/family memory recording on behalf of users
- **Dynamic Tool Management**: Runtime tool registration/unregistration with introspection
- **Docker-Based Services**: Two isolated LightRAG containers build separate knowledge and memory graphs
- **RESTful API**: Full remote access via FastAPI-based endpoints
- **Local-First Privacy**: All data stored locally with complete user control
- **Safety Detection**: Self-harm risk category with crisis keyword monitoring

The system demonstrates a robust, scalable, and maintainable approach to building intelligent personal assistants that balance sophisticated reasoning capabilities with practical usability.

**Status**: ✅ Production Ready - Manager-based architecture operational, dual memory system functional, multi-user support active, and comprehensive test coverage in place.

---

*Last Updated: October 7, 2025*
*Version: 0.8.7dev*
*Author: Eric G. Suchanek, PhD*
