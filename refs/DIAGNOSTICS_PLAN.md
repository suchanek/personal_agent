# Personal Agent Diagnostics Plan

## 1. Introduction

This document outlines a plan to create a systematic and coherent diagnostic script for the Personal Agent system. The current proliferation of test programs in `tests/` and `memory_tests/` makes it difficult to perform a quick, comprehensive check of the system's health.

The proposed solution is a new diagnostic script, `run_diagnostics.py`, located in the `scripts/` directory. This script will provide a structured way to test each major subsystem of the agent, offering clear, concise, and color-coded output for easy interpretation.

## 2. Major Subsystems

The Personal Agent is comprised of the following major subsystems:

-   **Configuration & Initialization**: Verifies that all configurations are loaded correctly and the agent initializes without errors.
-   **Core Agent**: The main agent logic, including instruction management, model management, and response parsing.
-   **Memory System**: A complex subsystem that includes:
    -   Local Semantic Memory (SQLite + `SemanticMemoryManager`)
    -   Graph Memory (LightRAG)
    -   Knowledge Base (LanceDB + LightRAG)
    -   Dual storage and synchronization mechanisms.
-   **Tool Management**: The registration, management, and execution of all tools, including built-in tools and those provided by the Model Context Protocol (MCP).
-   **User Management**: Handles user creation, switching, and the management of user-specific paths and data.
-   **CLI Interface**: The command-line interface for interacting with the agent.
-   **Web Interface**: The Streamlit-based web UI.

## 3. Proposed Diagnostic Script: `scripts/run_diagnostics.py`

The new diagnostic script will be designed with the following principles in mind:

-   **Modularity**: The script will be divided into logical sections, each testing a specific subsystem.
-   **Clarity**: The output will be clear, concise, and use color-coding to indicate success, failure, or warnings.
-   **Selectivity**: The script will support command-line arguments to run tests for specific subsystems (e.g., `python scripts/run_diagnostics.py --subsystem memory`).
-   **Non-destructive**: The tests will be designed to be non-destructive, using temporary databases and mock objects where appropriate.

### 3.1. Script Structure

The `run_diagnostics.py` script will have the following structure:

```python
import argparse
import asyncio

# Functions to test each subsystem
def test_configuration_and_initialization():
    # ...
    pass

def test_memory_subsystem():
    # ...
    pass

def test_tool_subsystem():
    # ...
    pass

def test_user_management_subsystem():
    # ...
    pass

def test_core_agent_logic():
    # ...
    pass

def main():
    # Parse command-line arguments
    # Run selected tests
    pass

if __name__ == "__main__":
    main()
```

### 3.2. Subsystem Test Plans

#### 3.2.1. Configuration and Initialization

-   Verify that all necessary environment variables are loaded.
-   Check that the `config.py` module correctly resolves all paths.
-   Initialize the `AgnoPersonalAgent` and ensure it does not raise any exceptions.
-   Verify that the agent's components (memory manager, tool manager, etc.) are initialized correctly.

#### 3.2.2. Memory Subsystem

-   **Local Semantic Memory**:
    -   Perform basic CRUD (Create, Read, Update, Delete) operations on the SQLite database.
    -   Test semantic search and duplicate detection.
-   **Graph Memory (LightRAG)**:
    -   Check for connectivity to the LightRAG server.
    -   Store a simple memory and verify that entities and relationships are created.
-   **Knowledge Base**:
    -   Test ingestion of a sample document.
    -   Perform a search on the ingested document.
-   **Dual Storage**:
    -   Store a memory and verify that it is present in both the local and graph databases.

#### 3.2.3. Tool Subsystem

-   Verify that all expected tools are registered with the agent.
-   Execute a simple, non-destructive tool from each major category (e.g., `get_memory_stats`, `duckduckgo_search`, `get_current_stock_price`).
-   Test tool call detection and response parsing.

#### 3.2.4. User Management Subsystem

-   Create a temporary test user.
-   Switch to the new user and verify that the `env.userid` file is updated.
-   Check that user-specific paths are correctly generated for the new user.
-   Clean up the test user.

#### 3.2.5. Core Agent Logic

-   Test the generation of instructions for different `InstructionLevel` settings.
-   Verify that the agent can correctly parse structured responses from the LLM.
-   Test the agent's ability to handle a simple conversational turn.

## 4. Implementation and Next Steps

1.  **Create `scripts/run_diagnostics.py`**: I will create the new diagnostic script in the `scripts/` directory.
2.  **Implement Subsystem Tests**: I will implement the test functions for each subsystem as outlined above, drawing inspiration from the existing tests in `tests/` and `memory_tests/`.
3.  **Refactor Existing Tests (Optional)**: As a follow-up, some of the existing tests could be refactored or removed to reduce redundancy.

This plan provides a clear path forward for creating a robust and maintainable diagnostic system for the Personal Agent.
