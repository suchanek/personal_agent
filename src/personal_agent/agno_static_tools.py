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

    # Add filesystem tools from tools.filesystem module
    logger.info("Adding filesystem tools...")
    try:
        # Create static filesystem tools that use MCP client
        def make_filesystem_tools(client):

            @tool(
                name="read_file",
                description="Read file content using MCP filesystem server",
            )
            def read_file_tool(file_path: str) -> str:
                """
                Read file content using MCP filesystem server.

                Args:
                    file_path: Path to the file to read

                Returns:
                    str: File content or error message
                """
                try:
                    if not client:
                        return "MCP client not available"

                    # Determine which server to use based on path
                    server_name = "filesystem-home"

                    # Start filesystem server if not already running
                    if server_name not in client.active_servers:
                        start_result = client.start_server_sync(server_name)
                        if not start_result:
                            return "Failed to start MCP filesystem server."

                    # Convert absolute paths to relative paths for the restricted root
                    processed_path = file_path
                    if processed_path.startswith("~/"):
                        processed_path = processed_path[2:]  # Remove "~/" prefix
                    elif processed_path.startswith("/"):
                        processed_path = processed_path[1:]  # Remove leading slash

                    # Call read_file tool with correct parameter name
                    result = client.call_tool_sync(
                        server_name, "read_file", {"path": processed_path}
                    )

                    logger.info("Read file via MCP: %s", file_path)
                    return result

                except Exception as e:
                    logger.error("Error reading file via MCP: %s", str(e))
                    return f"Error reading file: {str(e)}"

            @tool(
                name="write_file",
                description="Write content to file using MCP filesystem server",
            )
            def write_file_tool(file_path: str, content: str) -> str:
                """
                Write content to file using MCP filesystem server.

                Args:
                    file_path: Path to the file to write
                    content: Content to write to the file

                Returns:
                    str: Success message or error
                """
                try:
                    if not client:
                        return "MCP client not available"

                    if not file_path or content is None:
                        return "Error: file_path and content parameters are required"

                    # Determine which server to use based on path
                    server_name = "filesystem-home"

                    # Start filesystem server if not already running
                    if server_name not in client.active_servers:
                        start_result = client.start_server_sync(server_name)
                        if not start_result:
                            return "Failed to start MCP filesystem server."

                    # Convert absolute paths to relative paths for the restricted root
                    processed_path = file_path
                    if processed_path.startswith("~/"):
                        processed_path = processed_path[2:]  # Remove "~/" prefix
                    elif processed_path.startswith("/"):
                        processed_path = processed_path[1:]  # Remove leading slash

                    # Call write_file tool with correct parameter name
                    result = client.call_tool_sync(
                        server_name,
                        "write_file",
                        {"path": processed_path, "content": content},
                    )

                    logger.info("Wrote file via MCP: %s", file_path)
                    return result

                except Exception as e:
                    logger.error("Error writing file via MCP: %s", str(e))
                    return f"Error writing file: {str(e)}"

            @tool(
                name="list_directory",
                description="List directory contents using MCP filesystem server",
            )
            def list_directory_tool(directory_path: str) -> str:
                """
                List directory contents using MCP filesystem server.

                Args:
                    directory_path: Path to the directory to list

                Returns:
                    str: Directory listing or error message
                """
                try:
                    if not client:
                        return "MCP client not available"

                    # Determine which server to use based on path
                    server_name = "filesystem-home"

                    # Start filesystem server if not already running
                    if server_name not in client.active_servers:
                        start_result = client.start_server_sync(server_name)
                        if not start_result:
                            return "Failed to start MCP filesystem server."

                    # Convert absolute paths to relative paths for the restricted root
                    processed_path = directory_path
                    if processed_path in ["~", "$HOME"]:
                        processed_path = "."  # Root directory
                    elif processed_path.startswith("~/"):
                        processed_path = processed_path[2:]  # Remove "~/" prefix
                    elif processed_path.startswith("/"):
                        processed_path = processed_path[1:]  # Remove leading slash

                    # If path is empty after processing, it means we want the root directory
                    if not processed_path:
                        processed_path = "."

                    # Call list_directory tool with the correct path
                    result = client.call_tool_sync(
                        server_name, "list_directory", {"path": processed_path}
                    )

                    logger.info("Listed directory via MCP: %s", directory_path)
                    return result

                except Exception as e:
                    logger.error("Error listing directory via MCP: %s", str(e))
                    return f"Error listing directory: {str(e)}"

            @tool(
                name="search_files",
                description="Search for files and content in the filesystem",
            )
            def search_files_tool(search_query: str, directory: str = ".") -> str:
                """
                Search for files and content in the filesystem.

                Args:
                    search_query: Query to search for
                    directory: Directory to search in (default: current directory)

                Returns:
                    str: Search results or error message
                """
                try:
                    if not client:
                        return "MCP client not available"

                    # Get directory listing using the same logic as list_directory_tool
                    server_name = "filesystem-home"

                    # Start filesystem server if not already running
                    if server_name not in client.active_servers:
                        start_result = client.start_server_sync(server_name)
                        if not start_result:
                            return "Failed to start MCP filesystem server."

                    # Convert absolute paths to relative paths for the restricted root
                    processed_path = directory
                    if processed_path in ["~", "$HOME"]:
                        processed_path = "."  # Root directory
                    elif processed_path.startswith("~/"):
                        processed_path = processed_path[2:]  # Remove "~/" prefix
                    elif processed_path.startswith("/"):
                        processed_path = processed_path[1:]  # Remove leading slash

                    # If path is empty after processing, it means we want the root directory
                    if not processed_path:
                        processed_path = "."

                    # Call list_directory tool to get directory contents
                    directory_listing = client.call_tool_sync(
                        server_name, "list_directory", {"path": processed_path}
                    )

                    # Filter results based on search query
                    lines = directory_listing.split("\n")
                    matching_lines = [
                        line for line in lines if search_query.lower() in line.lower()
                    ]

                    if matching_lines:
                        result = (
                            f"Search results for '{search_query}' in {directory}:\n"
                            + "\n".join(matching_lines)
                        )
                    else:
                        result = (
                            f"No files found matching '{search_query}' in {directory}"
                        )

                    return result

                except Exception as e:
                    logger.error("Error in file search: %s", str(e))
                    return f"Error searching files: {str(e)}"

            @tool(
                name="create_file",
                description="Create a new file with content, creating directories if needed",
            )
            def create_file_tool(file_path: str, content: str) -> str:
                """
                Create a new file with content, creating directories if needed.

                Args:
                    file_path: Path to the file to create
                    content: Content to write to the file

                Returns:
                    str: Success message or error
                """
                try:
                    if not client:
                        return "MCP client not available"

                    # Use the same logic as write_file_tool to create the file
                    if not file_path or content is None:
                        return "Error: file_path and content parameters are required"

                    # Determine which server to use based on path
                    server_name = "filesystem-home"

                    # Start filesystem server if not already running
                    if server_name not in client.active_servers:
                        start_result = client.start_server_sync(server_name)
                        if not start_result:
                            return "Failed to start MCP filesystem server."

                    # Convert absolute paths to relative paths for the restricted root
                    processed_path = file_path
                    if processed_path.startswith("~/"):
                        processed_path = processed_path[2:]  # Remove "~/" prefix
                    elif processed_path.startswith("/"):
                        processed_path = processed_path[1:]  # Remove leading slash

                    # Call write_file tool with correct parameter name
                    result = client.call_tool_sync(
                        server_name,
                        "write_file",
                        {"path": processed_path, "content": content},
                    )

                    if "Error" not in result:
                        logger.info("Created file via MCP: %s", file_path)
                        return f"Successfully created file: {file_path}\n{result}"
                    else:
                        return result

                except Exception as e:
                    logger.error("Error creating file: %s", str(e))
                    return f"Error creating file: {str(e)}"

            return [
                read_file_tool,
                write_file_tool,
                list_directory_tool,
                search_files_tool,
                create_file_tool,
            ]

        # Create filesystem tools with the MCP client
        filesystem_tools = make_filesystem_tools(mcp_client)
        tools.extend(filesystem_tools)
        logger.info("Added %d filesystem tools", len(filesystem_tools))

    except Exception as e:
        logger.warning("Failed to create filesystem tools: %s", e)

    return tools
