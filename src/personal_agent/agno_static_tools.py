"""
Static MCP tool implementations for Agno instead of dynamic tool creation.
This replaces the temporary agent creation approach with direct MCP client calls.
"""

import logging
from typing import List, Optional

from agno.tools import tool
from agno.tools.function import Function

from .config import USE_MCP, get_mcp_servers


async def get_static_mcp_tools() -> List[Function]:
    """Convert MCP tools to native agno Functions using static tool implementations."""
    # Get logger for this function
    logger = logging.getLogger(__name__)

    tools = []

    if not USE_MCP:
        return tools

    # Get the MCP client instance that was created during initialization
    # Try multiple ways to access it
    mcp_client = None

    # Method 1: Try to access from tools module (preferred)
    try:
        from .tools import web

        mcp_client = getattr(web, "mcp_client", None)
        if mcp_client:
            logger.info("Found MCP client in web tools module")
    except (ImportError, AttributeError) as e:
        logger.debug("Could not access MCP client from web tools: %s", e)

    # Method 2: Create client directly if not found
    if not mcp_client:
        try:
            logger.info("Creating MCP client directly...")
            from .core.mcp_client import SimpleMCPClient

            mcp_servers = get_mcp_servers()
            mcp_client = SimpleMCPClient(mcp_servers)

            if mcp_client.start_servers():
                logger.info("MCP servers started successfully")
            else:
                logger.warning("Failed to start some MCP servers")
                return tools
        except Exception as e:
            logger.warning("Failed to create MCP client: %s", e)
            return tools

    mcp_servers = get_mcp_servers()

    for server_name, config in mcp_servers.items():
        try:
            description = config.get(
                "description", f"Access to {server_name} MCP server"
            )

            # Create static tool functions that call MCP servers directly
            if server_name == "github":
                # Capture the mcp_client and server_name in the closure
                def make_github_tool(client, srv_name):
                    @tool(
                        name="github_search",
                        description=f"Search GitHub repositories, code, and issues: {description}",
                    )
                    def github_search_tool(
                        query: str, repo: Optional[str] = None
                    ) -> str:
                        """
                        Search GitHub repositories or specific repo for code, issues, or documentation.

                        Args:
                            query: Search query terms
                            repo: Optional specific repository to search within (format: owner/repo)

                        Returns:
                            str: Search results or error message
                        """
                        try:
                            # Handle None values for repo parameter
                            if repo is None:
                                repo = ""

                            logger.info(
                                "GitHub search called with query='%s', repo='%s'",
                                query,
                                repo,
                            )

                            # Start GitHub server if not already running
                            if srv_name not in client.active_servers:
                                logger.info("Starting GitHub MCP server...")
                                start_result = client.start_server_sync(srv_name)
                                if not start_result:
                                    return "Failed to start MCP GitHub server. Make sure GITHUB_PERSONAL_ACCESS_TOKEN is set."

                            # Use search_repositories for finding repositories by name
                            # Use search_issues for general issue/repo searches
                            # Use search_code for code-specific searches within repos

                            # Default to repository search if it looks like a repo name search
                            if (
                                not repo
                                and " " not in query
                                and len(query.split()) == 1
                            ):
                                # Single word likely searching for repository
                                tool_name = "search_repositories"
                                params = {"query": query}
                            elif repo and any(
                                keyword in query.lower()
                                for keyword in [
                                    "language:",
                                    "def ",
                                    "class ",
                                    "function",
                                    "import ",
                                    "const ",
                                    "var ",
                                ]
                            ):
                                # For code search within a specific repo
                                tool_name = "search_code"
                                params = {"q": f"repo:{repo} {query}"}
                            else:
                                # For general searches (issues, pull requests, repositories)
                                tool_name = "search_issues"
                                if repo:
                                    params = {"q": f"repo:{repo} {query}"}
                                else:
                                    params = {"q": query}

                            logger.debug(
                                "Using GitHub tool: %s with params: %s",
                                tool_name,
                                params,
                            )

                            # First check if the tool exists
                            available_tools = client.list_tools_sync(srv_name)
                            tool_names = (
                                [tool["name"] for tool in available_tools]
                                if available_tools
                                else []
                            )

                            if tool_name not in tool_names:
                                logger.error(
                                    "Tool %s not found. Available tools: %s",
                                    tool_name,
                                    tool_names,
                                )
                                return f"Error: GitHub tool '{tool_name}' not available. Available tools: {', '.join(tool_names)}"

                            # Call the appropriate GitHub search tool directly
                            result = client.call_tool_sync(srv_name, tool_name, params)

                            # Sanitize the result to prevent parsing issues
                            from .tools.web import _sanitize_github_output

                            result = _sanitize_github_output(result)

                            logger.info("GitHub search completed: %s", query)
                            return result

                        except Exception as e:
                            logger.error("Error searching GitHub via MCP: %s", str(e))
                            return f"Error searching GitHub: {str(e)}"

                    return github_search_tool

                # Create the tool with proper closure
                github_tool = make_github_tool(mcp_client, server_name)
                tools.append(github_tool)
                logger.info("Created static GitHub search tool")

            else:
                # For other MCP servers, create generic tools
                def make_generic_mcp_tool(name: str, desc: str):
                    @tool(
                        name=f"mcp_{name}",
                        description=f"Access {name} MCP server: {desc}",
                    )
                    def generic_mcp_tool(query: str) -> str:
                        """
                        Execute a query against an MCP server.

                        Args:
                            query: The query or command to execute

                        Returns:
                            str: Result from the MCP server
                        """
                        try:
                            # Start server if not already running
                            if name not in mcp_client.active_servers:
                                start_result = mcp_client.start_server_sync(name)
                                if not start_result:
                                    return f"Failed to start {name} MCP server."

                            # For now, use a generic approach - this could be enhanced
                            # with server-specific logic as needed
                            result = f"MCP {name} server executed with query: {query}"

                            logger.info(
                                "%s MCP server query completed: %s", name, query
                            )
                            return result

                        except Exception as e:
                            logger.error("Error using %s MCP server: %s", name, str(e))
                            return f"Error using {name}: {str(e)}"

                    return generic_mcp_tool

                tool_func = make_generic_mcp_tool(server_name, description)
                tools.append(tool_func)
                logger.info("Created static MCP tool for: %s", server_name)

        except Exception as e:
            logger.warning("Failed to create MCP tool for %s: %s", server_name, e)

    return tools
