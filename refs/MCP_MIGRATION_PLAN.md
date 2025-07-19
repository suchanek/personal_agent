# MCP Migration Plan: Adopting the Official Agno Method

This document outlines the step-by-step plan to refactor the MCP (Model Context Protocol) integration in `AgnoPersonalAgent` from its current custom, on-demand implementation to the simpler, more performant "official" method documented by the `agno` framework.

## 1. Objective

The primary goal is to replace the current "agent-within-an-agent" architecture, where MCP servers are spun up ephemerally for each tool call, with a persistent session model. In the new model, `MCPTools` instances will be initialized once when the agent starts and will maintain a persistent connection to their respective servers.

### Benefits:
-   **Performance:** Eliminates the significant latency of starting a new server process for every MCP tool call.
-   **Simplicity:** Drastically simplifies the `_get_mcp_tools` method and removes the complex sub-agent creation logic.
-   **Standardization:** Aligns the project with the standard, documented usage of the `agno` framework, making it easier to maintain and update.

### Trade-offs:
-   **Loss of Specialized Instructions:** The current method creates temporary sub-agents with highly specialized instructions (e.g., "You are a GitHub assistant"). This feature will be removed. The main agent will rely on its general instructions and the tool's docstring to use the MCP tools correctly.

---

## 2. Files to be Modified

-   `src/personal_agent/core/agno_agent.py`

---

## 3. Step-by-Step Migration Instructions

### Step 1: Add Instance Variable for MCP Tool Instances

In `src/personal_agent/core/agno_agent.py`, modify the `AgnoPersonalAgent.__init__` method to include a placeholder for our persistent `MCPTools` objects.

```python
# In AgnoPersonalAgent.__init__

# ... (existing attributes)

# Agent instance
self.agent = None
self._last_response = None

# Add this line to hold the initialized MCP tools
self.mcp_tools_instances = []

logger.info(
    "Initialized AgnoPersonalAgent with model=%s, memory=%s, mcp=%s, user_id=%s",
    # ...
)
```

### Step 2: Refactor the `_get_mcp_tools` Method

This is the core of the refactoring. Replace the entire `_get_mcp_tools` method with a much simpler version that directly creates `MCPTools` instances. The new method will no longer be `async`.

**Replace the current `_get_mcp_tools` method with this:**

```python
def _get_mcp_tools(self) -> List:
    """Create and return a list of MCPTools instances based on configuration."""
    from agno.tools.mcp import MCPTools

    logger.info(
        "_get_mcp_tools called - enable_mcp: %s, mcp_servers: %s",
        self.enable_mcp,
        self.mcp_servers,
    )

    if not self.enable_mcp or not self.mcp_servers:
        return []

    tools = []
    for server_name, config in self.mcp_servers.items():
        logger.info("Creating MCPTools instance for server: %s", server_name)

        command = config.get("command")
        args = config.get("args", [])
        env = config.get("env", {})

        # The GitHub MCP server expects GITHUB_TOKEN, so we ensure it's set
        # from the environment variable used elsewhere in the project.
        if server_name == "github" and "GITHUB_PERSONAL_ACCESS_TOKEN" in os.environ:
            env["GITHUB_TOKEN"] = os.environ["GITHUB_PERSONAL_ACCESS_TOKEN"]

        if command:
            mcp_tool = MCPTools(
                command=f"{command} {' '.join(args)}",
                # Note: The 'command' parameter in MCPTools takes the full command string.
                # We are combining command and args here.
                # Environment variables are passed to the underlying process.
                env=env,
                name=server_name, # Assign a name for easier identification
            )
            tools.append(mcp_tool)
            logger.info("Created MCPTools instance for: %s", server_name)

    return tools
```

### Step 3: Update the `initialize` Method

Modify `AgnoPersonalAgent.initialize` to call the new `_get_mcp_tools`, initialize each tool (which starts the server process), and add them to the agent's main tool list.

**Find this block in `initialize`:**
```python
# Get MCP tools as function wrappers (no pre-initialization)
mcp_tool_functions = []
if self.enable_mcp:
    mcp_tool_functions = await self._get_mcp_tools()
    tools.extend(mcp_tool_functions)
    logger.info("Added %d MCP tools to agent", len(mcp_tool_functions))
```

**And replace it with this new block:**
```python
# Get and initialize MCP tools
self.mcp_tools_instances = []
if self.enable_mcp:
    # 1. Create the MCPTools instances (now a synchronous call)
    self.mcp_tools_instances = self._get_mcp_tools()

    # 2. Initialize each tool, which starts the server process
    for mcp_tool in self.mcp_tools_instances:
        try:
            await mcp_tool.initialize()
            logger.info("Initialized MCP server for: %s", mcp_tool.name)
        except Exception as e:
            logger.error("Failed to initialize MCP server for %s: %s", mcp_tool.name, e)
            # Optionally, decide if you want to continue if one server fails
            # For now, we'll log the error and continue.
    
    # 3. Add the initialized tools to the agent's tool list
    tools.extend(self.mcp_tools_instances)
    logger.info("Added %d MCP tools to agent", len(self.mcp_tools_instances))
```

### Step 4: Implement Cleanup Logic

Update `AgnoPersonalAgent.cleanup` to properly shut down the persistent MCP server processes when the application exits.

**Find the `cleanup` method and add the MCP cleanup logic:**
```python
async def cleanup(self) -> None:
    """Clean up resources when the agent is being shut down."""
    try:
        logger.info("Cleaning up AgnoPersonalAgent resources...")

        # >>> ADD THIS BLOCK START <<<
        # Clean up MCP tool instances and their server processes
        if self.mcp_tools_instances:
            logger.info("Closing %d MCP tool sessions...", len(self.mcp_tools_instances))
            for mcp_tool in self.mcp_tools_instances:
                try:
                    await mcp_tool.close()
                    logger.info("Closed MCP session for: %s", mcp_tool.name)
                except Exception as e:
                    logger.warning("Error closing MCP session for %s: %s", mcp_tool.name, e)
            self.mcp_tools_instances = []
        # >>> ADD THIS BLOCK END <<<

        # Clean up agent resources
        if self.agent:
            # ... (rest of the method)
```

Also, add a synchronous version for the `sync_cleanup` method.

**Find the `sync_cleanup` method and add the MCP cleanup logic:**
```python
def sync_cleanup(self) -> None:
    """Synchronous cleanup method for compatibility."""
    try:
        logger.info("Running synchronous cleanup...")

        # >>> ADD THIS BLOCK START <<<
        # Synchronously clean up MCP tool instances
        if self.mcp_tools_instances:
            logger.info("Closing %d MCP tool sessions synchronously...", len(self.mcp_tools_instances))
            for mcp_tool in self.mcp_tools_instances:
                try:
                    # Assuming a synchronous close method exists or can be implemented
                    # If not, this might require running the async close in a sync context
                    if hasattr(mcp_tool, 'close_sync'):
                        mcp_tool.close_sync()
                    else:
                        # This is a fallback and might not work in all environments
                        asyncio.run(mcp_tool.close())
                    logger.info("Closed MCP session for: %s", mcp_tool.name)
                except Exception as e:
                    logger.warning("Error closing MCP session for %s synchronously: %s", mcp_tool.name, e)
            self.mcp_tools_instances = []
        # >>> ADD THIS BLOCK END <<<

        # Clean up agent resources without async calls
        if self.agent:
            # ... (rest of the method)
```

---

## 4. Expected Outcome

Upon completion of this migration:

1.  The `AgnoPersonalAgent` will start and manage persistent MCP server processes for its entire lifecycle.
2.  The complex "agent-within-an-agent" logic will be removed, resulting in cleaner, more maintainable code.
3.  The performance of MCP tool calls will improve significantly due to the removal of per-call process startup overhead.
4.  The agent will use MCP tools (e.g., `github.search_repositories`, `filesystem.list_files`) directly, as intended by the `agno` framework.
5.  The application will be more robust, as resources (server processes) will be properly managed and cleaned up on exit.
