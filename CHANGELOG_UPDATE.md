# Changelog

## [Unreleased]

### ✨ Features

- **Streamlit UI**: Added a dropdown menu in the Knowledge Base tab to dynamically switch the RAG server location between `localhost` and a remote server (`tesla.local`). The UI now provides more detailed status updates for the RAG server, indicating if it's processing, has items queued, or is ready.

### 🚀 Improvements

- **Topic Classification**: The topic classifier has been enhanced for greater accuracy. It now performs whole-word matching to prevent partial matches (e.g., "ai" in "train") and has an expanded dictionary of keywords and phrases in `topics.yaml` to better understand user input.
- **Docker Restart Script**: The `switch-ollama.sh` script's `restart_docker_services` function has been improved with more detailed output, better error handling, and a clearer status report of the services being restarted.

### 🏗️ Refactoring

- **Technical Documentation**: Updated the Mermaid diagram in the `COMPREHENSIVE_MEMORY_SYSTEM_TECHNICAL_SUMMARY.md` to reflect the current system architecture.