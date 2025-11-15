![Personal Agent Logo](../brochure/logo-horizontal-transparent.png)

# Personal Agent System Overview

This document unifies the messaging from the executive summary, product brochure, and architecture notes into a single, developer-friendly reference. Use it to understand what the Personal Agent is, how it is built, and how to operate or extend it without introducing inconsistencies across the documentation suite.

## 1. Mission and Value Proposition

| Pillar | Description |
| --- | --- |
| Privacy-First AI | 100% local execution with Ollama/LM Studio ensures conversations, memories, and documents never leave the users hardware. |
| Intelligent Memory Companion | Dual storage (SQLite/LanceDB + LightRAG) captures day-to-day memories, complex relationships, and temporal journaling, supporting individuals, families, and caregivers. |
| Digital Legacy Engine | Knowledge ingestion pipelines transform personal archives, research corpora, and publications into searchable Digital Brains that can serve future generations. |
| Multi-User Readiness | Dynamic user switching, per-user storage roots, and service isolation make the system safe for households, teams, or organizations. |

These pillars match the storytelling tone of the brochure while reflecting the technical guarantees in the executive summary.

## 2. Core Architecture at a Glance

```
Interfaces (Streamlit, CLI, REST, Shortcuts)  >  Agno Core (lazy init, managers, routing)  >  Tools (built-ins + MCP)  >  Dual Memory + Dual Knowledge  >  Model Providers (Ollama, LM Studio, OpenAI-compatible)
                          ^
                          |
                     Multi-User Layer (UserManager, LightRAGManager, config)
```

### Key Components

- **AgnoPersonalAgent**: Manager-based orchestrator using lazy initialization with `asyncio.Lock` to keep startup instant while deferring heavyweight resources until first use.
- **Manager Suite**: Dedicated managers for models, instructions, tools, memory, knowledge, and users keep concerns isolated and make refactors safer.
- **Tooling Layer**:
  - Built-in tools: semantic memory functions, knowledge queries, DuckDuckGo, Python, finance, shell, etc.
  - MCP servers: always invoked through **ephemeral clients** (create > execute > teardown) for stability.
- **Dual Memory System**:
  - SQLite + LanceDB for fast semantic recall, deduplication, topic tagging.
  - LightRAG memory server for relationship graphs and cognitive health metadata.
- **Dual Knowledge System**:
  - Local semantic KB (LanceDB) for low-latency similarity search on ingested docs.
  - LightRAG knowledge server for graph reasoning, multi-hop questions, and knowledge synthesis.
- **Multi-User Isolation**: `~/.persag/env.userid` drives per-user storage, Docker configs, and LightRAG containers. `switch-user.py` and the Streamlit dashboard coordinate clean transitions.

## 3. Experience Overview

| Persona | Capabilities Highlight |
| --- | --- |
| Individuals & Families | Capture life stories, temporal journaling (set "memory age"), use iOS/Apple Watch Shortcuts over Tailscale for instant voice capture. |
| Cognitive Care | Cognitive state scoring (0100), memory confidence, caregiver proxy roadmap, alerts for concerning statements. |
| Professionals & Researchers | Ingest entire corpora, run deep semantic searches, build digital intellectual legacies, map citations and relationships. |
| Organizations | Preserve institutional knowledge, support onboarding, safeguard tribal knowledge before retirements. |

These scenarios mirror the brochure stories (Sarah, Michael, Johnson family) and the executive summarys digital-legacy emphasis.

## 4. Operational Workflows

### 4.1 Environment & Services

1. **Dependencies**: Python 3.11+, Poetry, Docker, Node.js (MCP servers), Ollama (local LLM), optional LM Studio.
2. **Install & Bootstrap**:
   - `poetry install`
   - First agent run auto-creates `~/.persag` with Docker configs and user registry.
3. **Start LightRAG Services**: `./restart-lightrag.sh` (uses user-scoped configs; prevents port collisions).
4. **Manage Users**:
   - `python switch-user.py <user>` or Streamlit dashboard.
   - Each user gets isolated storage (`$PERSAG_ROOT/agno/<user_id>/`).
5. **Launch Interfaces**:
   - `poetry run paga_streamlit` for the management dashboard + REST API.
   - `poetry run paga_cli` for automation scripts.
6. **Model Configuration**:
   - Ollama currently favors the Unsloth Qwen3 4B instruct build (`hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K`), though other models can be swapped in through settings.
   - LM Studio runs the MLX-native `qwen3-4b-instruct-2507-mlx` baseline for Metal acceleration.
   - Optional OpenAI-compatible endpoints default to `gpt-4.1-mini` for heavier workloads (with clear privacy trade-offs).

### 4.2 Memory & Knowledge Actions

| Workflow | Tools / Entry Points |
| --- | --- |
| Store personal memory | `store_user_memory` tool (dual write) or Streamlit Memory form. |
| Query semantic memories | `query_memory`, `get_recent_memories`, `list_memories`. |
| Query knowledge bases | `query_knowledge_base(query, mode="auto")` routes to LanceDB or LightRAG. |
| Maintain memories | `update_memory`, `delete_memory`, `delete_memories_by_topic`, `clear_memories` (honors dual storage). |
| Monitor sync state | Dashboard "Memory Sync" view + CLI diagnostics ensure SQLite and LightRAG stay aligned. |

### 4.3 Testing Cadence

- Comprehensive suite via `poe test-all` (unit, integration, memory, MCP).
- Targeted scripts: `poe test-memory`, `poerty run test-mcp-servers`, `python memory_tests/test_comprehensive_memory_search.py`.
- Instruction-level performance validation: `python tests/test_instruction_level_performance.py`.

## 5. Instruction Sets for Hosted Agents

- **CLAUDE.md** and **GEMINI.md** define per-agent personas, safety constraints, and brevity requirements. They ensure hosted assistants align with repository conventions (e.g., no extra comments, concise answers, defensive security stance). Keep new tooling or documentation consistent with these guardrails when integrating third-party LLMs.

## 6. Deployment & Remote Access

- **Streamlit Dashboard** doubles as REST API host and administrators' console (user CRUD, memory browser, synchronization fixes, power controls).
- **Tailscale Integration** exposes the dashboard/API privately to iOS Shortcuts for mobile capture, Siri voice input, and Apple Watch stats. No public endpoints are required.
- **Ollama LaunchAgent** keeps the preferred local model accessible system-wide, independent of user context.

## 7. Roadmap Alignment

Current roadmap (from brochure + executive summary):

- Memory by Proxy (family/caregiver capture) with permissions and audit trails.
- Enhanced analytics: timeline visualization, relationship graphs, cognitive trend dashboards.
- Multimedia ingestion (audio, photo, video) with transcription and retrieval.
- Conversational digital legacy interactions ("immortal memory" experiences).

Ensure new contributions reference these initiatives so public messaging stays synchronized.

## 8. Consistency Checklist

Use this quick checklist before merging architectural or product changes:

1. **Privacy Claims**: Confirm local-only data flow unless explicitly noted (and document trade-offs if enabling cloud models).
2. **Dual Architecture**: Any change touching memory or knowledge must respect *both* local and LightRAG systems.
3. **Ephemeral MCP Requirement**: Never pool MCP clients; recreate per call.
4. **User Isolation**: All file paths and Docker configs must derive from `PersonalAgentConfig` and the active `USER_ID`.
5. **Instruction-Level Messaging**: Keep the tone/principles consistent with CLAUDE/GEMINI guidelines.
6. **Docs Harmony**: Executive summary, brochure, and this overview must agree on feature names, roadmap items, and UX promises.

## 9. Quick Reference Commands

| Scenario | Command |
| --- | --- |
| Install dependencies | `poetry install` |
| Run dashboard (Streamlit + REST) | `poetry run paga_streamlit` |
| CLI agent | `poetry run paga_cli [--recreate]` |
| Restart LightRAG services | `./restart-lightrag.sh` |
| Switch user | `python switch-user.py <user_id>` |
| Run full tests | `poe test-all` |
| Memory repair scripts | `python scripts/clear_all_memories.py --no-confirm` (clean slate) |

_Note: Always `source .venv/bin/activate` before running scripts/tests per repo instructions when not using Poetry wrappers._

## 10. Final Thoughts

Personal Agent blends human-centered storytelling (brochure) with rigorous, privacy-preserving engineering (architecture + executive summary). Treat this document as the bridge between those worlds: when proposing changes, verify they reinforce the four pillars above, respect the dual architectures, and keep the user promise of owning their story forever.
