# MCP Manager Asyncio Context Management Fix

**Date**: January 18, 2025  
**Status**: Implemented  
**Type**: Bug Fix / Architecture Change

## Problem Statement

The MCP Manager singleton implementation introduced in the previous ADR was causing critical asyncio context management errors during cleanup:

```
RuntimeError: Attempted to exit cancel scope in a different task than it was entered in
ERROR:asyncio:an error occurred during closing of asynchronous generator <async_generator object stdio_client>
```

These errors occurred because:
1. MCP tools were initialized in one asyncio task context using `AsyncExitStack`
2. Cleanup was attempted from a different asyncio task context
3. The MCP client's `stdio_client` uses `anyio.create_task_group()` which creates task-specific cancel scopes
4. Attempting to exit these scopes from different tasks caused the RuntimeError

## Root Cause Analysis

### The Asyncio Context Problem

The issue stems from how asyncio and anyio manage task contexts:

1. **MCP stdio_client Implementation**: Uses `anyio.create_task_group()` with cancel scopes
2. **Singleton Pattern**: Persistent connections managed across different agent lifecycles
3. **Task Context Mismatch**: Initialization happens in one task, cleanup in another
4. **Cancel Scope Violation**: anyio enforces that cancel scopes must be entered and exited in the same task

### Why AsyncExitStack Didn't Solve It

While `AsyncExitStack` is the correct pattern for managing multiple async context managers, it doesn't solve the fundamental issue of task context boundaries. The underlying MCP stdio connections still create task-specific resources that cannot be cleaned up from different tasks.

## Solution: Factory Pattern with Agno Lifecycle Management

### Architecture Change

**From**: Singleton with persistent connections and manual async context management  
**To**: Factory pattern with agno-managed tool lifecycle

### Key Changes

1. **Removed Persistent State and Manual Context Management**
   ```python
   # OLD: Singleton with persistent connections and manual async context management
   class MCPManager:
       def __init__(self):
           self._async_exit_stack = AsyncExitStack()
           self.mcp_tool_instances = []
       
       async def initialize(self):
           # Initialize persistent connections with manual __aenter__()
           for mcp_tool in self.mcp_tool_configs:
               initialized_tool = await mcp_tool.__aenter__()  # CAUSES ERRORS
       
       async def cleanup(self):
           # Manual cleanup from different task - CAUSES ERRORS
           await mcp_tool_config.__aexit__(None, None, None)
   ```

2. **Implemented Factory Pattern**
   ```python
   # NEW: Factory pattern
   class MCPManager:
       def create_mcp_tools(self) -> List[MCPTools]:
           # Create fresh instances each time
           return [MCPTools(...) for server in self.mcp_servers]
   ```

3. **Let Agno Handle MCP Tool Lifecycle**
   ```python
   # NEW: Let agno manage the MCP tool lifecycle completely
   mcp_tools = mcp_manager.create_mcp_tools()
   if mcp_tools:
       # Add MCP tools directly to the agent without manual initialization
       # Let agno handle the MCP tool lifecycle internally
       tools.extend(mcp_tools)
       self.mcp_tools_instances = mcp_tools
   ```

## Implementation Details

### New MCPManager API

```python
class MCPManager:
    """Factory for creating MCP tool instances with proper configuration."""
    
    def create_mcp_tools(self) -> List[MCPTools]:
        """Create fresh MCP tool instances for each use case."""
    
    def is_enabled(self) -> bool:
        """Check if MCP is enabled."""
    
    def get_tool_count(self) -> int:
        """Get number of configured servers."""
    
    def get_server_info(self) -> Dict:
        """Get server configuration details."""
```

### Benefits of Factory Pattern

1. **Task Context Safety**: Each tool is created and managed within the same asyncio task
2. **Isolation**: Each agent gets its own tool instances, preventing interference
3. **Automatic Cleanup**: Context managers handle cleanup in the correct task context
4. **Follows Agno Patterns**: Aligns with how agno's MCPTools are designed to be used
5. **Simpler Error Handling**: No complex cross-task cleanup logic needed

## Migration Impact

### Code Changes Required

**Agents using MCP tools need to update from:**
```python
# OLD approach
await mcp_manager.initialize()
tools = mcp_manager.get_tools()
# ... use tools
await mcp_manager.cleanup()  # Problematic
```

**To:**
```python
# NEW approach
tools = mcp_manager.create_mcp_tools()
for tool in tools:
    async with tool as initialized_tool:
        # Use initialized_tool
        # Cleanup happens automatically
```

### Backward Compatibility

- The `mcp_manager` global instance is preserved
- Configuration loading remains the same
- Only the usage pattern changes

## Testing

Created `test_mcp_manager_fix.py` to verify:
1. Factory pattern works correctly
2. Multiple agents can use MCP tools without conflicts
3. Proper async context manager usage
4. No asyncio context management errors

## Performance Considerations

### Trade-offs

**Pros:**
- Eliminates asyncio context errors
- Better resource isolation
- Simpler error handling
- More predictable cleanup

**Cons:**
- Slight overhead from creating fresh instances
- No connection reuse between agents

### Mitigation

The overhead is minimal because:
1. MCP tool creation is lightweight (just configuration)
2. Actual connections are established on first use
3. Most agents don't run concurrently for long periods

## Lessons Learned

1. **Asyncio Task Boundaries**: Resources created in one task cannot always be cleaned up from another
2. **Context Manager Scope**: Async context managers must be entered and exited in the same task
3. **Singleton Limitations**: Persistent singletons can create task context issues in async environments
4. **Library Design Matters**: The MCP client's use of anyio task groups enforces strict task boundaries

## Future Considerations

1. **Connection Pooling**: If performance becomes an issue, implement connection pooling within task boundaries
2. **Resource Monitoring**: Monitor MCP connection usage to ensure no resource leaks
3. **Error Handling**: Continue to improve error handling for MCP connection failures

## Conclusion

The factory pattern approach successfully resolves the asyncio context management issues while maintaining the simplicity benefits of the previous singleton approach. Each agent now manages its own MCP tools properly, eliminating the "cancel scope in different task" errors and providing better resource isolation.

This change aligns with Python async best practices and the intended usage patterns of the underlying agno MCP tools library.
