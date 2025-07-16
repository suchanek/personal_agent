# AgnoPersonalAgent Refactoring Plan

## Table of Contents
1. [Introduction](#introduction)
2. [Current Issues](#current-issues)
3. [Proposed Architecture](#proposed-architecture)
4. [Detailed Class Specifications](#detailed-class-specifications)
5. [Method Extraction Map](#method-extraction-map)
6. [Implementation Steps](#implementation-steps)
7. [Testing Strategy](#testing-strategy)
8. [Backward Compatibility](#backward-compatibility)

## Introduction

The `AgnoPersonalAgent` class in `src/personal_agent/core/agno_agent.py` has grown to over 2800 lines of code, handling multiple responsibilities including memory management, instruction creation, tool management, and knowledge base operations. This document outlines a comprehensive plan to refactor this monolithic class into a more modular, maintainable architecture.

## Current Issues

1. **Excessive Size**: The class is over 2800 lines long, making it difficult to maintain and understand.
2. **Multiple Responsibilities**: The class handles everything from memory management to instruction creation to tool management.
3. **Long Methods**: Many methods are quite lengthy and do too many things at once.
4. **Duplicate Code**: There's repetition in memory handling and tool creation.
5. **Tight Coupling**: Different functionalities are intertwined, making changes risky.
6. **Testing Difficulty**: The monolithic structure makes it difficult to test individual components.

## Proposed Architecture

We will refactor the `AgnoPersonalAgent` class into a modular architecture with the following components:

```
AgnoPersonalAgent (Main coordinator class)
├── AgentModelManager (Manages model creation and configuration)
├── AgentInstructionManager (Manages agent instructions)
├── AgentMemoryManager (Manages memory operations)
├── AgentKnowledgeManager (Manages knowledge bases)
└── AgentToolManager (Manages tool creation and execution)
```

### Component Responsibilities

1. **AgentModelManager**: Handles model creation and configuration
2. **AgentInstructionManager**: Manages the creation of agent instructions
3. **AgentMemoryManager**: Handles all memory operations
4. **AgentKnowledgeManager**: Manages knowledge bases and queries
5. **AgentToolManager**: Manages tool creation and execution
6. **Refactored AgnoPersonalAgent**: Acts as a coordinator between components

## Detailed Class Specifications

### AgentModelManager

```python
class AgentModelManager:
    """Manages model creation and configuration."""
    
    def __init__(self, model_provider, model_name, ollama_base_url, seed=None):
        self.model_provider = model_provider
        self.model_name = model_name
        self.ollama_base_url = ollama_base_url
        self.seed = seed
        
    def create_model(self):
        """Create the appropriate model instance based on provider."""
        # Implementation from _create_model in AgnoPersonalAgent
        
    def get_model_context_size(self):
        """Get the context size for the current model."""
        # Implementation from the model creation logic
```

### AgentInstructionManager

```python
class AgentInstructionManager:
    """Manages the creation and customization of agent instructions."""
    
    def __init__(self, instruction_level, user_id, enable_memory, enable_mcp, mcp_servers):
        self.instruction_level = instruction_level
        self.user_id = user_id
        self.enable_memory = enable_memory
        self.enable_mcp = enable_mcp
        self.mcp_servers = mcp_servers
        
    def create_instructions(self):
        """Create complete instructions based on the sophistication level."""
        # Implementation from _create_agent_instructions
        
    def get_header_instructions(self):
        """Returns the header section of the instructions."""
        # Implementation from _get_header_instructions
        
    def get_identity_rules(self):
        """Returns the critical identity rules for the agent."""
        # Implementation from _get_identity_rules
        
    def get_personality_and_tone(self):
        """Returns the personality and tone guidelines."""
        # Implementation from _get_personality_and_tone
        
    def get_concise_memory_rules(self):
        """Returns concise rules for the semantic memory system."""
        # Implementation from _get_concise_memory_rules
        
    def get_detailed_memory_rules(self):
        """Returns detailed rules for the semantic memory system."""
        # Implementation from _get_detailed_memory_rules
        
    def get_concise_tool_rules(self):
        """Returns concise rules for general tool usage."""
        # Implementation from _get_concise_tool_rules
        
    def get_detailed_tool_rules(self):
        """Returns detailed rules for general tool usage."""
        # Implementation from _get_detailed_tool_rules
        
    def get_anti_hesitation_rules(self):
        """Returns explicit rules to prevent hesitation and overthinking."""
        # Implementation from _get_anti_hesitation_rules
        
    def get_tool_list(self, available_tools):
        """Dynamically returns the list of available tools."""
        # Implementation from _get_tool_list
        
    def get_core_principles(self):
        """Returns the core principles and conversation guidelines."""
        # Implementation from _get_core_principles
```

### AgentMemoryManager

```python
class AgentMemoryManager:
    """Manages memory operations including storage, retrieval, and updates."""
    
    def __init__(self, user_id, storage_dir, agno_memory=None, lightrag_url=None, lightrag_memory_url=None):
        self.user_id = user_id
        self.storage_dir = storage_dir
        self.agno_memory = agno_memory
        self.lightrag_url = lightrag_url
        self.lightrag_memory_url = lightrag_memory_url
        
    def initialize(self, agno_storage):
        """Initialize the memory manager with storage."""
        # Set up agno_memory
        
    def direct_search_memories(self, query, limit=10, similarity_threshold=0.3):
        """Direct semantic search without agentic retrieval."""
        # Implementation from _direct_search_memories
        
    async def get_memory_tools(self):
        """Create memory tools using direct SemanticMemoryManager method calls."""
        # Implementation from _get_memory_tools
        
    async def store_user_memory(self, content, topics=None):
        """Store information as a user memory in both local SQLite and LightRAG graph systems."""
        # Implementation from store_user_memory
        
    def restate_user_fact(self, content):
        """Restate a user fact from first-person to third-person."""
        # Implementation from _restate_user_fact
        
    async def seed_entity_in_graph(self, entity_name, entity_type):
        """Seed an entity into the graph by creating and uploading a physical file."""
        # Implementation from seed_entity_in_graph
        
    async def check_entity_exists(self, entity_name):
        """Check if entity exists in the graph."""
        # Implementation from check_entity_exists
        
    async def clear_all_memories(self):
        """Clear all memories from both SQLite and LightRAG systems."""
        # Implementation from clear_all_memories
        
    async def query_memory(self, query, limit=None):
        """Search user memories using direct SemanticMemoryManager calls."""
        # Implementation from the query_memory function in _get_memory_tools
        
    async def update_memory(self, memory_id, content, topics=None):
        """Update an existing memory."""
        # Implementation from the update_memory function in _get_memory_tools
        
    async def delete_memory(self, memory_id):
        """Delete a memory from both SQLite and LightRAG systems."""
        # Implementation from the delete_memory function in _get_memory_tools
        
    async def get_recent_memories(self, limit=10):
        """Get recent memories by searching all memories and sorting by date."""
        # Implementation from the get_recent_memories function in _get_memory_tools
        
    async def get_all_memories(self):
        """Get all user memories."""
        # Implementation from the get_all_memories function in _get_memory_tools
        
    async def get_memory_stats(self):
        """Get memory statistics."""
        # Implementation from the get_memory_stats function in _get_memory_tools
        
    async def get_memories_by_topic(self, topics=None, limit=None):
        """Get memories by topic without similarity search."""
        # Implementation from the get_memories_by_topic function in _get_memory_tools
        
    async def list_memories(self):
        """List all memories in a simple, user-friendly format."""
        # Implementation from the list_memories function in _get_memory_tools
        
    async def store_graph_memory(self, content, topics=None, memory_id=None):
        """Store a memory in the LightRAG graph database to capture relationships."""
        # Implementation from the store_graph_memory function in _get_memory_tools
        
    async def query_graph_memory(self, query, mode="mix", top_k=5, response_type="Multiple Paragraphs"):
        """Query the LightRAG memory graph to explore relationships between memories."""
        # Implementation from the query_graph_memory function in _get_memory_tools
        
    async def get_memory_graph_labels(self):
        """Get the list of all entity and relation labels from the memory graph."""
        # Implementation from the get_memory_graph_labels function in _get_memory_tools
```

### AgentKnowledgeManager

```python
class AgentKnowledgeManager:
    """Manages knowledge bases and knowledge-related operations."""
    
    def __init__(self, storage_dir, knowledge_dir, lightrag_url=None):
        self.storage_dir = storage_dir
        self.knowledge_dir = knowledge_dir
        self.lightrag_url = lightrag_url
        self.agno_knowledge = None
        self.lightrag_knowledge = None
        self.knowledge_coordinator = None
        
    async def initialize(self, agno_storage, recreate=False):
        """Initialize knowledge bases."""
        # Extract knowledge base initialization logic from AgnoPersonalAgent.initialize
        
    async def query_lightrag_knowledge_direct(self, query, params):
        """Directly query the LightRAG knowledge base."""
        # Implementation from query_lightrag_knowledge_direct
        
    async def query_knowledge_base(self, query, mode="auto", limit=5, response_type="Multiple Paragraphs"):
        """Unified knowledge base query with intelligent routing."""
        # Implementation from the query_knowledge_base function in _get_memory_tools
        
    async def query_lightrag_knowledge(self, query, mode="naive", top_k=5, response_type="Multiple Paragraphs"):
        """Direct query to LightRAG knowledge base for backward compatibility."""
        # Implementation from the query_lightrag_knowledge function in _get_memory_tools
        
    async def query_semantic_knowledge(self, query, limit=5):
        """Search the local semantic knowledge base for specific facts or documents."""
        # Implementation from the query_semantic_knowledge function in _get_memory_tools
```

### AgentToolManager

```python
class AgentToolManager:
    """Manages tool creation, configuration, and execution."""
    
    def __init__(self, enable_mcp, mcp_servers, model_provider, model_name, debug, ollama_base_url, user_id):
        self.enable_mcp = enable_mcp
        self.mcp_servers = mcp_servers
        self.model_provider = model_provider
        self.model_name = model_name
        self.debug = debug
        self.ollama_base_url = ollama_base_url
        self.user_id = user_id
        
    async def get_mcp_tools(self):
        """Create MCP tools as native async functions compatible with Agno."""
        # Implementation from _get_mcp_tools
        
    def extract_tool_call_info(self, tool_call):
        """Extract tool call information from various tool call formats."""
        # Implementation from _extract_tool_call_info
        
    def get_last_tool_calls(self, last_response):
        """Get tool call information from the last response object."""
        # Implementation from get_last_tool_calls
        
    def create_base_tools(self):
        """Create the base set of tools for the agent."""
        # Extract tool creation logic from AgnoPersonalAgent.initialize
```

### Refactored AgnoPersonalAgent

```python
class AgnoPersonalAgent:
    """
    Agno-based Personal AI Agent with MCP integration and native storage.
    
    This class coordinates the different components of the agent system.
    """

    def __init__(self, model_provider="ollama", model_name=LLM_MODEL, enable_memory=True, 
                 enable_mcp=True, storage_dir=AGNO_STORAGE_DIR, knowledge_dir=AGNO_KNOWLEDGE_DIR, 
                 debug=False, ollama_base_url=OLLAMA_URL, user_id=USER_ID, recreate=False, 
                 instruction_level=InstructionLevel.STANDARD, seed=None):
        # Basic configuration
        self.model_provider = model_provider
        self.model_name = model_name
        self.enable_memory = enable_memory
        self.enable_mcp = enable_mcp and USE_MCP
        self.debug = debug
        self.ollama_base_url = ollama_base_url
        self.user_id = user_id
        self.recreate = recreate
        self.instruction_level = instruction_level
        self.seed = seed
        
        # Set up storage paths
        self._setup_storage_paths(storage_dir, knowledge_dir, user_id)
        
        # Initialize component managers
        self.model_manager = AgentModelManager(model_provider, model_name, ollama_base_url, seed)
        
        self.tool_manager = AgentToolManager(
            self.enable_mcp, 
            get_mcp_servers() if self.enable_mcp else {}, 
            model_provider, model_name, debug, ollama_base_url, user_id
        )
        
        self.instruction_manager = AgentInstructionManager(
            instruction_level, user_id, enable_memory, 
            self.enable_mcp, get_mcp_servers() if self.enable_mcp else {}
        )
        
        self.memory_manager = AgentMemoryManager(
            user_id, self.storage_dir, 
            lightrag_url=LIGHTRAG_URL, 
            lightrag_memory_url=LIGHTRAG_MEMORY_URL
        )
        
        self.knowledge_manager = AgentKnowledgeManager(
            self.storage_dir, self.knowledge_dir, LIGHTRAG_URL
        )
        
        # Storage components
        self.agno_storage = None
        
        # Agent instance
        self.agent = None
        self._last_response = None

    def _setup_storage_paths(self, storage_dir, knowledge_dir, user_id):
        """Set up storage paths based on user ID."""
        # Implementation from the initialization logic in __init__
        
    async def initialize(self, recreate=False):
        """Initialize the agent with all components."""
        # Coordinate initialization of all components
        
    async def run(self, query, stream=False, add_thought_callback=None):
        """Run a query through the agent."""
        # Implementation from run
        
    async def store_user_memory(self, content, topics=None):
        """Public method to store user memory, delegating to memory manager."""
        return await self.memory_manager.store_user_memory(content, topics)
        
    async def cleanup(self):
        """Clean up resources."""
        # Implementation from cleanup
        
    async def clear_all_memories(self):
        """Clear all memories, delegating to memory manager."""
        return await self.memory_manager.clear_all_memories()
        
    def get_agent_info(self):
        """Get comprehensive information about the agent configuration."""
        # Implementation from get_agent_info
        
    def print_agent_info(self, console=None):
        """Pretty print comprehensive agent information."""
        # Implementation from print_agent_info
        
    def quick_agent_summary(self, console=None):
        """Print a quick one-line summary of the agent."""
        # Implementation from quick_agent_summary
```

## Method Extraction Map

This section maps methods from the current `AgnoPersonalAgent` class to their new locations in the refactored architecture.

### AgentModelManager Methods

From the current AgnoPersonalAgent class:
- `_create_model()` → `create_model()`

### AgentInstructionManager Methods

From the current AgnoPersonalAgent class:
- `_create_agent_instructions()` → `create_instructions()`
- `_get_header_instructions()` → `get_header_instructions()`
- `_get_identity_rules()` → `get_identity_rules()`
- `_get_personality_and_tone()` → `get_personality_and_tone()`
- `_get_concise_memory_rules()` → `get_concise_memory_rules()`
- `_get_detailed_memory_rules()` → `get_detailed_memory_rules()`
- `_get_concise_tool_rules()` → `get_concise_tool_rules()`
- `_get_detailed_tool_rules()` → `get_detailed_tool_rules()`
- `_get_anti_hesitation_rules()` → `get_anti_hesitation_rules()`
- `_get_tool_list()` → `get_tool_list()`
- `_get_core_principles()` → `get_core_principles()`

### AgentMemoryManager Methods

From the current AgnoPersonalAgent class:
- `_direct_search_memories()` → `direct_search_memories()`
- `_get_memory_tools()` → Split into individual memory operation methods
- `store_user_memory()` → `store_user_memory()`
- `_restate_user_fact()` → `restate_user_fact()`
- `seed_entity_in_graph()` → `seed_entity_in_graph()`
- `check_entity_exists()` → `check_entity_exists()`
- `clear_all_memories()` → `clear_all_memories()`

From the `_get_memory_tools()` method, extract these as separate methods:
- `store_user_memory_tool` → `store_user_memory()`
- `query_memory` → `query_memory()`
- `update_memory` → `update_memory()`
- `delete_memory` → `delete_memory()`
- `clear_memories` → `clear_memories()`
- `delete_memories_by_topic` → `delete_memories_by_topic()`
- `get_recent_memories` → `get_recent_memories()`
- `get_all_memories` → `get_all_memories()`
- `get_memory_stats` → `get_memory_stats()`
- `get_memories_by_topic` → `get_memories_by_topic()`
- `list_memories` → `list_memories()`
- `store_graph_memory` → `store_graph_memory()`
- `query_graph_memory` → `query_graph_memory()`
- `get_memory_graph_labels` → `get_memory_graph_labels()`

### AgentKnowledgeManager Methods

From the current AgnoPersonalAgent class:
- `query_lightrag_knowledge_direct()` → `query_lightrag_knowledge_direct()`

From the `_get_memory_tools()` method, extract these as separate methods:
- `query_knowledge_base` → `query_knowledge_base()`
- `query_lightrag_knowledge` → `query_lightrag_knowledge()`
- `query_semantic_knowledge` → `query_semantic_knowledge()`

### AgentToolManager Methods

From the current AgnoPersonalAgent class:
- `_get_mcp_tools()` → `get_mcp_tools()`
- `_extract_tool_call_info()` → `extract_tool_call_info()`
- `get_last_tool_calls()` → `get_last_tool_calls()`

### Methods to Keep in AgnoPersonalAgent

These methods should remain in the main class as they coordinate between components:
- `__init__()`
- `_setup_storage_paths()`
- `initialize()`
- `run()`
- `cleanup()`
- `get_agent_info()`
- `print_agent_info()`
- `quick_agent_summary()`

## Implementation Steps

### Phase 1: Preparation and Setup

1. **Create New Files**:
   - Create new Python files for each new class:
     ```
     src/personal_agent/core/agent_model_manager.py
     src/personal_agent/core/agent_instruction_manager.py
     src/personal_agent/core/agent_memory_manager.py
     src/personal_agent/core/agent_knowledge_manager.py
     src/personal_agent/core/agent_tool_manager.py
     ```

2. **Set Up Basic Class Structures**:
   - Define the basic class structure in each file with proper imports
   - Add docstrings and type hints
   - Implement `__init__` methods for each class

3. **Create Unit Tests**:
   - Create unit tests for the existing functionality to ensure refactoring doesn't break anything
   - Focus on testing the public API of the AgnoPersonalAgent class

### Phase 2: Extract Instruction Management

1. **Implement AgentInstructionManager**:
   - Copy all instruction-related methods from AgnoPersonalAgent to AgentInstructionManager
   - Adjust method signatures and references as needed
   - Ensure proper imports and dependencies

2. **Modify AgnoPersonalAgent to Use AgentInstructionManager**:
   - Create an instance of AgentInstructionManager in AgnoPersonalAgent.__init__
   - Replace direct calls to instruction methods with calls to the manager
   - Test to ensure functionality is preserved

### Phase 3: Extract Model Management

1. **Implement AgentModelManager**:
   - Move the `_create_model` method to AgentModelManager
   - Add any additional model-related functionality

2. **Modify AgnoPersonalAgent to Use AgentModelManager**:
   - Create an instance of AgentModelManager in AgnoPersonalAgent.__init__
   - Replace direct model creation with calls to the manager
   - Test to ensure functionality is preserved

### Phase 4: Extract Memory Management

1. **Implement Core AgentMemoryManager Functionality**:
   - Move basic memory-related methods to AgentMemoryManager
   - Ensure proper imports and dependencies

2. **Extract Memory Tool Methods**:
   - Carefully extract each memory tool function from `_get_memory_tools`
   - Convert them to proper methods in AgentMemoryManager
   - Maintain the same functionality and error handling

3. **Modify AgnoPersonalAgent to Use AgentMemoryManager**:
   - Create an instance of AgentMemoryManager in AgnoPersonalAgent.__init__
   - Replace direct memory operations with calls to the manager
   - Update `_get_memory_tools` to delegate to the memory manager
   - Test to ensure functionality is preserved

### Phase 5: Extract Knowledge Management

1. **Implement AgentKnowledgeManager**:
   - Move knowledge-related methods to AgentKnowledgeManager
   - Extract knowledge-related tool functions from `_get_memory_tools`
   - Ensure proper imports and dependencies

2. **Modify AgnoPersonalAgent to Use AgentKnowledgeManager**:
   - Create an instance of AgentKnowledgeManager in AgnoPersonalAgent.__init__
   - Replace direct knowledge operations with calls to the manager
   - Test to ensure functionality is preserved

### Phase 6: Extract Tool Management

1. **Implement AgentToolManager**:
   - Move tool-related methods to AgentToolManager
   - Ensure proper imports and dependencies

2. **Modify AgnoPersonalAgent to Use AgentToolManager**:
   - Create an instance of AgentToolManager in AgnoPersonalAgent.__init__
   - Replace direct tool operations with calls to the manager
   - Test to ensure functionality is preserved

### Phase 7: Refactor AgnoPersonalAgent

1. **Streamline AgnoPersonalAgent**:
   - Remove any remaining duplicated code
   - Ensure all delegations to manager classes are working correctly
   - Clean up imports and dependencies

2. **Update Public API Methods**:
   - Ensure all public methods properly delegate to the appropriate manager
   - Maintain backward compatibility for external callers

3. **Comprehensive Testing**:
   - Run all unit tests to ensure functionality is preserved
   - Test the system end-to-end to verify everything works correctly

### Phase 8: Documentation and Cleanup

1. **Update Documentation**:
   - Update docstrings for all classes and methods
   - Document the new architecture and class relationships
   - Add examples of how to use the refactored classes

2. **Code Cleanup**:
   - Remove any commented-out code or TODOs
   - Ensure consistent coding style across all files
   - Run linters and fix any issues

3. **Performance Optimization**:
   - Identify and address any performance bottlenecks introduced by the refactoring
   - Ensure efficient communication between components

## Testing Strategy

1. **Unit Tests**:
   - Create unit tests for each new class
   - Test each public method with various inputs
   - Use mocks for dependencies to isolate testing

2. **Integration Tests**:
   - Test interactions between components
   - Verify that components work together correctly

3. **End-to-End Tests**:
   - Test the complete system with real inputs
   - Verify that the refactored system behaves the same as the original

4. **Regression Tests**:
   - Ensure that existing functionality is preserved
   - Test edge cases and error handling

## Backward Compatibility

To maintain backward compatibility:

1. **Public API Preservation**:
   - Keep the same public methods in AgnoPersonalAgent
   - Ensure method signatures remain the same
   - Delegate to the appropriate manager classes internally

2. **Error Handling**:
   - Maintain the same error handling behavior
   - Ensure exceptions are propagated correctly

3. **Performance Considerations**:
   - Monitor performance during refactoring
   - Ensure the refactored code is as efficient as the original

4. **Documentation**:
   - Document any subtle changes in behavior
   - Provide migration guides if needed