## MCP Agent Initialization

MCP (Model Context Protocol) is a standardized protocol enabling agents to interact with external systems. In this library, MCP integration is primarily handled by the `MCPTools` and `MultiMCPTools` classes, which are passed to an `Agent`'s `tools` argument.

### `MCPTools`: For Single MCP Servers

Use `MCPTools` to connect to a single MCP server. It can be initialized in several ways:

1.  **By Command:** The simplest method is to provide the command to start the MCP server.

    ```python
    from agno.tools.mcp import MCPTools

    mcp_tools = MCPTools(command="npx -y @modelcontextprotocol/server-github")
    ```

2.  **By URL and Transport:** For servers accessible via a URL, specify the URL and the transport protocol (`sse` or `streamable-http`).

    ```python
    from agno.tools.mcp import MCPTools

    mcp_tools = MCPTools(url="http://localhost:8000/sse", transport="sse")
    ```

3.  **With a Pre-initialized Session:** For more control, you can create an MCP session yourself and pass it to `MCPTools`.

    ```python
    import asyncio
    from agno.tools.mcp import MCPTools
    from mcp.client.stdio import stdio_client

    server_process = await asyncio.create_subprocess_exec(
        "npx", "-y", "@modelcontextprotocol/server-github",
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE,
    )

    async with stdio_client(process=server_process) as session:
        mcp_tools = MCPTools(session=session)
    ```

### `MultiMCPTools`: For Multiple MCP Servers

Use `MultiMCPTools` to connect to several MCP servers simultaneously.

```python
from agno.tools.mcp import MultiMCPTools

mcp_tools = MultiMCPTools(
    commands=[
        "npx -y @modelcontextprotocol/server-github",
        "npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",
    ],
    urls=["http://localhost:8000/sse"],
    urls_transports=["sse"]
)
```

### Filtering Tools

Both `MCPTools` and `MultiMCPTools` allow you to filter which tools are exposed to the agent using the `include_tools` and `exclude_tools` arguments.

```python
from agno.tools.mcp import MCPTools

# Only include the 'list_files' tool
mcp_tools = MCPTools(
    command="npx -y @modelcontextprotocol/server-filesystem",
    include_tools=["list_files"]
)

# Exclude the 'delete_file' tool
mcp_tools = MCPTools(
    command="npx -y @modelcontextprotocol/server-filesystem",
    exclude_tools=["delete_file"]
)
```