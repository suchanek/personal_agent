# System Architecture

This document outlines the architecture of the personal AI assistant, a sophisticated system built on the Agno Framework. It integrates local AI models via Ollama, advanced knowledge management with LightRAG, and a dynamic multi-user environment.

## 1. Core Philosophy

The system is designed to be a modular, extensible, and powerful personal assistant that runs locally, ensuring data privacy and user control. The architecture prioritizes:

- **Modularity**: Components are decoupled and can be independently developed, tested, and upgraded.
- **Extensibility**: New tools, models, and capabilities can be easily integrated.
- **Data Privacy**: User data is stored and processed locally, with a robust multi-user system for data isolation.
- **Performance**: The system is optimized for real-time interaction and efficient use of local resources.

## 2. High-Level Architecture

The architecture can be visualized as a series of interconnected layers, each with a distinct responsibility:

```
+-------------------------------------------------+
|               Interfaces (UI/CLI)               |
|  (Streamlit Web UI, Command-Line Interface)     |
+----------------------+--------------------------+
                       |
+----------------------v--------------------------+
|                 Agent Core (Agno)               |
| (Orchestration, Task Management, Tool Routing)  |
+----------------------+--------------------------+
                       |
+----------------------v--------------------------+
|        Memory & Knowledge Management Layer      |
| (Semantic Memory, Knowledge Base, Multi-User)   |
+----------------------+--------------------------+
                       |
+----------------------v--------------------------+
|                 Backend Services                |
| (Ollama LLMs, LightRAG Server, MCP Servers)     |
+-------------------------------------------------+
```

### 2.1. Interfaces

This layer is the primary entry point for user interaction.

- **Streamlit Web UI (`paga_streamlit`)**: A rich, interactive web interface for managing the agent, users, and system settings. It provides a full-featured dashboard for memory synchronization, user switching, and model selection.
- **Command-Line Interface (`paga_cli`)**: A lightweight, scriptable interface for advanced users and automation. It supports all core functionalities, including agent interaction, user management, and system configuration.

### 2.2. Agent Core (Agno Framework)

The heart of the system, powered by the **Agno Framework**. This layer is responsible for:

- **Orchestration**: Managing the overall workflow of the agent, from receiving user input to generating a response.
- **Task Management**: Decomposing complex tasks into smaller, manageable steps.
- **Tool Routing**: Intelligently selecting and invoking the appropriate tools to fulfill user requests.
- **State Management**: Maintaining the agent's internal state and conversation history.

### 2.3. Memory & Knowledge Management Layer

This layer provides the agent with long-term memory and access to a structured knowledge base.

- **Semantic Memory Manager**: A sophisticated system that stores and retrieves user-specific memories. It uses a hybrid approach, combining a local SQLite database for structured data and a LanceDB-powered vector store for semantic search.
- **Knowledge Base (LightRAG)**: A powerful, RAG-enhanced knowledge base that allows the agent to store, query, and reason about large document collections and complex relationships. It is powered by the LightRAG server.
- **Multi-User System**: A robust system that ensures data isolation and service stability in a multi-user environment. It dynamically manages user contexts, configurations, and services.

### 2.4. Backend Services

This layer consists of the external services that provide the agent with its core capabilities.

- **Ollama**: Provides local access to a wide range of open-source language models (e.g., Llama 3.1, Qwen 2.5).
- **LightRAG Server**: A dedicated server for knowledge management, providing a REST API for document ingestion, querying, and graph-based reasoning.
- **MCP (Model Context Protocol) Servers**: A suite of specialized servers that provide access to external tools and services, such as web search, file system operations, and financial data.

## 3. Data Flow

The data flow within the system is designed to be efficient and secure.

1.  **User Input**: The user interacts with the agent through one of the interfaces (Web UI or CLI).
2.  **Agent Core Processing**: The Agent Core receives the input and, using the Agno Framework, determines the user's intent.
3.  **Tool Selection**: The agent selects the appropriate tool(s) to handle the request. This could be a memory operation, a knowledge query, or a call to an MCP-powered tool.
4.  **Memory/Knowledge Access**: If the request requires memory or knowledge access, the agent interacts with the Semantic Memory Manager or the LightRAG server. All memory operations are user-specific.
5.  **LLM Interaction**: The agent constructs a prompt, including relevant context from memory and knowledge, and sends it to the Ollama-hosted LLM for processing.
6.  **Response Generation**: The LLM generates a response, which is then processed by the agent.
7.  **Output to User**: The final response is sent back to the user through the interface.

## 4. Key Architectural Decisions (ADRs)

The architecture has been shaped by a series of key decisions, documented in Architecture Decision Records (ADRs). These include:

- **ADR-007: Enriched Graph Ingestion Pipeline**: Enhances the accuracy of knowledge graph construction.
- **ADR-008: CLI Refactor**: Modularizes the CLI for improved maintainability.
- **ADR-013: Dynamic Multi-User Management**: Implements a full-stack, dynamic multi-user system.
- **ADR-015: Persistent User Context**: Ensures that the user context persists across sessions.

## 5. Deployment and Configuration

The system is designed for local deployment, with a strong emphasis on ease of use and configuration.

- **Dependencies**: Managed with Poetry.
- **Services**: Key services like LightRAG and Ollama are managed with Docker and can be easily started and stopped with shell scripts.
- **Configuration**: Environment variables are used to configure the system, with a clear separation between user-specific and system-wide settings. The multi-user system dynamically manages the `USER_ID`.

This architecture provides a solid foundation for a powerful, extensible, and user-centric personal AI assistant.
