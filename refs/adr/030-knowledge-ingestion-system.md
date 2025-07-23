# ADR-030: Knowledge Ingestion System

## Status

Accepted

## Context

The personal agent requires a robust and user-friendly system for ingesting knowledge from various sources. The existing methods for adding knowledge are ad-hoc and lack a unified interface. To address this, a new knowledge ingestion system is proposed, providing a seamless way to add files, text, and web content to the agent's knowledge base.

## Decision

We will implement a new Knowledge Ingestion System with the following features:

- **Multi-Modal Ingestion**: Support for file, text, and URL ingestion.
- **Format Support**: Handle common file types including text, PDF, and DOCX.
- **Intelligent Processing**: Automatic file type detection, content deduplication, and integration with the LightRAG server.
- **Natural Language Interface**: Allow users to ingest knowledge through conversational commands.
- **Toolkit**: Provide a dedicated `KnowledgeIngestionTools` toolkit for the agent.

The system will be composed of the following components:

- **`KnowledgeIngestionTools`**: An Agno toolkit providing the ingestion capabilities.
- **`KnowledgeManager`**: A component to orchestrate knowledge operations and communication with the LightRAG server.
- **LightRAG Integration**: Leverage the LightRAG server for content processing and indexing.
- **File Management**: Handle local file staging and organization.

## Consequences

### Positive

- **Improved User Experience**: Provides a simple and intuitive way to add knowledge to the agent.
- **Enhanced Knowledge Base**: Enables the creation of a comprehensive and well-structured knowledge base.
- **Increased Modularity**: The new components are decoupled and can be independently maintained and improved.
- **Extensibility**: The system is designed to be easily extended with new ingestion methods and file formats.

### Negative

- **Increased Complexity**: The new system adds a layer of complexity to the agent's architecture.
- **Dependency on LightRAG**: The system is tightly coupled with the LightRAG server.

