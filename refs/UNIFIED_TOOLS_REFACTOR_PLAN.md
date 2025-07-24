# Refactoring Plan: Unified Memory and Knowledge Tools

**Date**: 2025-07-23
**Author**: Gemini

## 1. Overview

This document outlines a plan to refactor the `personal-agent` by creating a unified `MemoryAndKnowledgeTools` class. This change is inspired by the clean, modular design of the `persag` example and aims to simplify the agent's initialization, improve maintainability, and align more closely with `agno` framework best practices.

The primary goal is to encapsulate all memory and knowledge-related functionalities—including local semantic memory, LightRAG graph memory, and knowledge base interactions—into a single, cohesive toolset.

## 2. Problem Statement

The current agent initialization process is complex and distributed across multiple files and managers. Tools are registered individually, and the logic for managing them is intertwined with the agent's core, making the system difficult to understand, maintain, and extend.

This complexity is a significant departure from the simplicity and elegance of the `persag` example, and it hinders the agent's long-term viability.

## 3. Proposed Solution: The `MemoryAndKnowledgeTools` Class

We will create a new class, `MemoryAndKnowledgeTools`, that will serve as a single, unified interface for all memory and knowledge operations. This class will be initialized with the necessary managers and will expose all memory and knowledge tools as methods.

### 3.1. Class Structure

The new class will be located at `src/personal_agent/tools/memory_and_knowledge_tools.py`. It will be initialized with the `SemanticMemoryManager` and `LightRAGManager` to ensure it has access to all necessary functionalities.

```python
# src/personal_agent/tools/memory_and_knowledge_tools.py

from agno.tools import tool
from src.personal_agent.core.semantic_memory_manager import SemanticMemoryManager
from src.personal_agent.core.lightrag_manager import LightRAGManager

class MemoryAndKnowledgeTools:
    """A unified toolset for all memory and knowledge operations."""

    def __init__(self, memory_manager: SemanticMemoryManager, lightrag_manager: LightRAGManager):
        self.memory_manager = memory_manager
        self.lightrag_manager = lightrag_manager

    # ... All memory and knowledge tools will be implemented as methods here ...
```

### 3.2. Tool Migration

All existing memory and knowledge tools will be migrated into the `MemoryAndKnowledgeTools` class. This includes, but is not limited to:

**Memory Tools:**

*   `store_user_memory`
*   `query_memory`
*   `get_recent_memories`
*   `get_all_memories`
*   `get_memories_by_topic`
*   `list_memories`
*   `update_memory`
*   `delete_memory`
*   `clear_all_memories`
*   `get_memory_stats`
*   `store_graph_memory`
*   `get_memory_graph_labels`

**Knowledge Tools:**

*   `ingest_knowledge_file`
*   `ingest_knowledge_text`
*   `ingest_knowledge_from_url`
*   `batch_ingest_directory`
*   `query_knowledge_base`

Each of these functions will be implemented as a method of the `MemoryAndKnowledgeTools` class, decorated with `@tool`, and will use the `self.memory_manager` and `self.lightrag_manager` instances to perform their operations.

### 3.3. Refactored Agent Initialization

The agent's initialization logic will be dramatically simplified. Instead of a complex setup process, the agent will be created with a simple, clean, and easy-to-understand configuration.

**Before:**

```python
# A simplified representation of the current, complex initialization
tools = []
tools.extend(get_memory_tools())
tools.extend(get_knowledge_tools())
# ... and so on for all other tools ...

agent = Agent(model=llm, tools=tools)
```

**After:**

```python
# The new, simplified initialization
from src.personal_agent.core.semantic_memory_manager import SemanticMemoryManager
from src.personal_agent.core.lightrag_manager import LightRAGManager
from src.personal_agent.tools.memory_and_knowledge_tools import MemoryAndKnowledgeTools

# 1. Initialize managers
memory_manager = SemanticMemoryManager()
lightrag_manager = LightRAGManager()

# 2. Initialize the unified toolset
memory_and_knowledge_tools = MemoryAndKnowledgeTools(memory_manager, lightrag_manager)

# 3. Create the agent with the unified toolset
agent_tools = [
    memory_and_knowledge_tools,
    CalculatorTools(),
    # ... other tool classes
]

agent = Agent(model=llm, tools=agent_tools)
```

## 4. Action Plan

1.  **Create the `MemoryAndKnowledgeTools` Class:**
    *   Create the file `src/personal_agent/tools/memory_and_knowledge_tools.py`.
    *   Implement the basic structure of the `MemoryAndKnowledgeTools` class, including the `__init__` method.

2.  **Migrate Tools:**
    *   Systematically move each memory and knowledge tool into the new class, refactoring them to use the `self.memory_manager` and `self.lightrag_manager` instances.

3.  **Refactor Agent Initialization:**
    *   Update the agent creation logic to use the new `MemoryAndKnowledgeTools` class.
    *   Remove the old, now-redundant tool registration code.

4.  **Testing and Validation:**
    *   Run all existing tests to ensure that the refactoring has not introduced any regressions.
    *   Create new tests specifically for the `MemoryAndKnowledgeTools` class to verify its functionality in isolation.

5.  **Update Documentation:**
    *   Update `GEMINI.md`, `README.md`, and any other relevant documentation to reflect the new, simplified architecture.

## 5. Conclusion

This refactoring plan will bring a much-needed simplification to the `personal-agent` project. By adopting a more modular, class-based approach to tool management, we can create a more robust, maintainable, and extensible agent, all while preserving the powerful memory and knowledge features that make it so unique.
