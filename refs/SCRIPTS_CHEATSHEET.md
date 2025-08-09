# Personal Agent Scripts Cheatsheet

This document provides a quick reference for the various scripts and tools available in this project, with a focus on memory and document management.

## 🧠 Memory & Fact Management

These scripts are for managing the agent's semantic and graph memories, and for injecting personal facts.

| Script | Description | Usage Example |
| --- | --- | --- |
| `tools/clear_all_memories.py` | **(Recommended)** Clears memories from BOTH local SQLite and LightRAG graph systems. Prevents data drift. | `python tools/clear_all_memories.py` |
| `tools/memory_manager_tool.py` | An interactive tool to inspect the memory database, view/delete memories by user, search, and get stats. | `python tools/memory_manager_tool.py` |
| `tools/inject_eric_facts_v2.py` | **(Modern)** Injects personal facts using the `SemanticMemoryManager` with auto-topic classification and dual storage. | `python tools/inject_eric_facts_v2.py --clear-first` |
| `scripts/auto_send_facts.py` | A fully automated script to send personal facts directly to the agent and monitor for success. | `python scripts/auto_send_facts.py all` |
| `scripts/clear_lightrag_memory_data.py` | A low-level script to clear specific data files from the LightRAG memory storage directories. | `python scripts/clear_lightrag_memory_data.py` |
| `scripts/send_facts_helper.py` | A helper to generate formatted fact messages to be copy-pasted into the chat UI. | `python scripts/send_facts_helper.py all` |
| `scripts/store_fact.py` | A simple utility to store a single fact directly into the knowledge base. | `python scripts/store_fact.py "My cat's name is Luna"` |
| `tools/initialize_eric_memories.py` | (Legacy) The original script for feeding facts to the agent one-by-one. | `python tools/initialize_eric_memories.py all` |

---

## 📄 Document & Knowledge Base Management

Tools for managing documents within the LightRAG knowledge base.

| Script | Description | Usage Example |
| --- | --- | --- |
| `tools/docmgr.py` | **(Modern/Recommended)** Manages LightRAG documents by integrating directly with the agent's tools. Handles listing, deleting, and retrying. | `python tools/docmgr.py --list` |
| `scripts/send_to_lightrag.py` | Sends a local file to the LightRAG server for ingestion into the knowledge base. | `python scripts/send_to_lightrag.py my_document.pdf` |
| `scripts/delete_lightrag_documents_enhanced.py` | An advanced tool for deleting documents with options for persistent storage removal and Docker management. | `python scripts/delete_lightrag_documents_enhanced.py --delete-failed --persistent` |
| `tools/lightrag_docmgr_v2.py` | (Legacy) Manages LightRAG documents using direct API calls. | `python tools/lightrag_docmgr_v2.py --list` |
| `tools/docmgr_wrapper.sh` | (Legacy) A wrapper for an older version of the document manager. | `./tools/docmgr_wrapper.sh --delete-name '*.pdf'` |

---

## 🚀 Agent & Server Management

Scripts for running, monitoring, and managing the agent and its dependent services.

| Script | Description | Usage Example |
| --- | --- | --- |
| `tools/paga_streamlit_agno.py` | **(Main UI)** Runs the primary Streamlit web interface for the personal agent. | `poetry run paga` or `streamlit run tools/paga_streamlit_agno.py` |
| `tools/paga_streamlit_team.py` | Runs the Streamlit UI for the multi-agent "Team" configuration. | `streamlit run tools/paga_streamlit_team.py` |
| `scripts/agent_status_display.py` | Displays a comprehensive status of the agent's configuration, tools, memory, and system health. | `python scripts/agent_status_display.py` |
| `tools/show-config.py` | Prints a detailed view of all loaded configuration variables and their sources. | `python tools/show-config.py` |
| `scripts/docker_user_sync.py` | Ensures the `USER_ID` is consistent between the main system and the Docker-based LightRAG servers. | `python scripts/docker_user_sync.py --sync` |
| `scripts/debug-ollama-connection.sh` | A utility to diagnose connection issues with the Ollama server. | `./scripts/debug-ollama-connection.sh http://localhost:11434` |
| `scripts/restart-container.sh` | A simple script to restart a specific Docker container by name. | `./scripts/restart-container.sh lightrag_pagent` |
| `scripts/install_mcp.py` | Installs all required Node.js-based MCP servers. | `python scripts/install_mcp.py` |
| `scripts/kepler_ollama_installer.sh` | (macOS) Installs Ollama as a headless, boot-persistent Docker service. | `./scripts/kepler_ollama_installer.sh` |

---

## ⚙️ Configuration & Environment

Utilities for managing the project's environment files.

| Script | Description | Usage Example |
| --- | --- | --- |
| `scripts/backup_env.sh` | Interactively creates a timestamped backup of your `.env` file, with an option for GPG encryption. | `./scripts/backup_env.sh` |
| `scripts/auto_backup_env.sh` | A non-interactive version of the backup script, suitable for automation and cron jobs. | `./scripts/auto_backup_env.sh` |
| `scripts/restore_env.sh` | Interactively restores your `.env` file from a list of available backups. | `./scripts/restore_env.sh` |
| `scripts/setup_gpg.sh` | A helper script to guide you through creating a GPG key for encrypting backups. | `./scripts/setup_gpg.sh` |
