# ADR-037: Separation of Knowledge and Memory Toolkits

## Status

**Accepted**

## Context

The agent's tool architecture previously combined all memory and knowledge-related operations into a single, unified `MemoryAndKnowledgeTools` class. This class managed two distinct types of information:
- **Knowledge**: Factual, reference-style information, documents, and other materials that are generally static.
- **Memory**: Personal, user-specific information, such as preferences, personal facts, and conversational history, which evolves over time.

While functional, this unified approach created several challenges:
- **Lack of Clear Boundaries**: The distinction between "knowledge" and "memory" was not architecturally enforced, leading to potential confusion for the agent when selecting the appropriate tool.
- **Maintenance Overhead**: A single, large class for two different domains increased complexity and made the codebase harder to maintain and extend.
- **Vague Agent Guidance**: The instructions for the unified toolkit were broad, making it difficult to provide the nuanced guidance required for proper memory storage (e.g., what to store vs. what to ignore).

## Decision

We have decided to refactor the `MemoryAndKnowledgeTools` class into two separate, focused toolkits:

1.  **`KnowledgeTools` (`src/personal_agent/tools/knowledge_tools.py`)**: This class is now exclusively responsible for managing the factual knowledge base. Its operations include ingesting files, text, and URLs, and querying for stored documents and facts. The toolkit's instructions and docstrings explicitly guide the agent to use it for non-personal, factual information.

2.  **`AgnoMemoryTools` (`src/personal_agent/tools/refactored_memory_tools.py`)**: This class is dedicated to managing personal information about the user. It handles storing, retrieving, updating, and deleting user-specific memories. Its instructions contain critical rules for what constitutes a "memory," emphasizing the storage of facts *about the user* and prohibiting the storage of the agent's own actions or conversational filler. It also reinforces the need to convert memories to the second person when presenting them.

The core agent (`AgnoPersonalAgent`) and the `AgentInstructionManager` have been updated to initialize and register these two toolkits separately, providing them to the agent as distinct capabilities.

## Consequences

### Positive
- **Improved Separation of Concerns**: The architecture now clearly delineates between factual knowledge and personal memory, making the system more modular and easier to understand.
- **Enhanced Agent Guidance**: The focused docstrings and instructions for each toolkit provide explicit, unambiguous guidance, reducing tool selection errors and improving the quality of stored memories.
- **Increased Maintainability**: Smaller, single-responsibility classes are easier to maintain, test, and extend independently.
- **Architectural Clarity**: The new structure aligns better with the conceptual model of the agent's information systems.

### Negative
- **Slightly Increased Complexity in Agent Initialization**: The agent now needs to initialize and manage two toolkits instead of one. However, this is a minor trade-off for the significant gains in clarity and maintainability.
- **Potential for Backward Compatibility Issues**: While the original `memory_and_knowledge_tools.py` file was preserved, any code directly depending on the combined class will need to be updated to use the new, separate toolkits for new development.
