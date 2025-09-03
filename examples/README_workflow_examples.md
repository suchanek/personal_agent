# Agno Workflow Examples

This directory contains examples demonstrating how to use the Agno Workflow objects for creating sophisticated multi-agent coordination systems.

## Files

### `workflow_memory_writer_example.py`
A comprehensive example showing how to use Agno Workflow objects to create a memory-based writing system that properly coordinates between memory retrieval and content creation.

## Key Features Demonstrated

### 1. **MemoryBasedWritingWorkflow**
- Demonstrates proper memory-to-writer coordination
- Retrieves user memories first, then creates personalized content
- Maintains session state and memory persistence
- Shows the correct workflow pattern that was missing in the original team coordinator

### 2. **StreamingMemoryWritingWorkflow** 
- Shows how to create streaming workflows that yield progress updates
- Demonstrates async generator patterns with workflows
- Provides real-time feedback during long-running operations

### 3. **Comparison Demonstrations**
- Shows the difference between memory-based and generic content
- Demonstrates the value of proper memory integration
- Illustrates the problem that was fixed in the team coordinator

## Running the Examples

```bash
# Make sure Ollama is running with the required models
ollama pull llama3.1:8b

# Run the workflow examples
cd examples
python workflow_memory_writer_example.py
```

## Key Workflow Concepts

### Workflow vs Team
- **Workflow**: Single execution path with defined steps, session management, and state persistence
- **Team**: Multi-agent coordination with delegation and parallel processing
- **When to use Workflow**: Sequential operations, state management, single user sessions
- **When to use Team**: Multi-agent coordination, complex delegation, real-time collaboration

### Memory Integration Patterns

#### ❌ **Wrong Pattern (Original Issue)**:
```python
# Team retrieves memories but doesn't pass them to writer
team.delegate_to_memory_agent("get memories")  # ✅ Gets memories
team.delegate_to_writer_agent("write story")   # ❌ No memories passed
```

#### ✅ **Correct Pattern (Fixed)**:
```python
# Workflow ensures proper data flow
memories = await memory_agent.arun("get memories")     # ✅ Get memories
content = await writer_agent.arun(f"write story using: {memories}")  # ✅ Use memories
```

### Session Management
Workflows automatically handle:
- Session ID generation and persistence
- Memory state across runs
- Storage integration
- User context maintenance

### Error Handling
The examples demonstrate:
- Graceful fallbacks when components fail
- Proper exception handling in async workflows
- Recovery strategies for missing dependencies

## Architecture Benefits

### 1. **Explicit Data Flow**
Unlike teams where data passing between agents can be implicit, workflows make data flow explicit and controllable.

### 2. **State Management**
Workflows provide built-in session and state management, ensuring consistency across runs.

### 3. **Debugging**
Easier to debug and trace execution flow compared to complex team delegation patterns.

### 4. **Reusability**
Workflows can be easily composed and reused in different contexts.

## Integration with Personal Agent

The examples show how to integrate with your existing Personal Agent components:

```python
from personal_agent.config.settings import LLM_MODEL, OLLAMA_URL
from personal_agent.config.user_id_mgr import get_userid
from personal_agent.core.agent_model_manager import AgentModelManager
from personal_agent.core.agno_agent import AgnoPersonalAgent
```

This ensures compatibility with your existing configuration and user management systems.

## Next Steps

Consider using Workflow objects for:
1. **Sequential Operations**: When you need guaranteed order of operations
2. **State Management**: When you need to maintain context across multiple interactions
3. **Complex Coordination**: When team delegation becomes too complex to manage
4. **User Sessions**: When you need persistent user sessions with memory

The team coordinator fix demonstrates that sometimes the right approach is updating coordination logic, while other times a different architectural pattern (like Workflows) might be more appropriate.
