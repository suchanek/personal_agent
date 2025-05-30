"""Filesystem tools for the Personal Agent using MCP."""

import json
import os
from typing import TYPE_CHECKING

from langchain.tools import tool

if TYPE_CHECKING:
    from ..core.mcp_client import SimpleMCPClient
    from ..core.memory import WeaviateVectorStore

# These will be injected by the main module
USE_MCP = False
USE_WEAVIATE = False
mcp_client: "SimpleMCPClient" = None
vector_store: "WeaviateVectorStore" = None
store_interaction = None
ROOT_DIR = ""
DATA_DIR = ""
logger = None


@tool
def mcp_read_file(file_path: str) -> str:
    """Read file content using MCP filesystem server."""
    # Handle case where file_path might be a JSON string from LangChain
    if isinstance(file_path, str) and file_path.startswith("{"):
        try:
            params = json.loads(file_path)
            file_path = params.get("file_path", file_path)
        except (json.JSONDecodeError, TypeError):
            pass  # Use original value if parsing fails

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot read file."

    try:
        # Determine which server to use based on path
        server_name = "filesystem-home"

        # Start filesystem server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP filesystem server."

        # Convert absolute paths to relative paths for the restricted root
        # The server root is ROOT_DIR, so we need to make paths relative to that
        if file_path == ROOT_DIR:
            file_path = "."  # Root directory (though reading a directory as file will likely fail)
        elif file_path.startswith(ROOT_DIR + "/"):
            file_path = file_path[len(ROOT_DIR) + 1 :]  # Remove ROOT_DIR prefix
        elif file_path.startswith("~/"):
            file_path = file_path[2:]  # Remove "~/" prefix
        elif file_path.startswith("/"):
            # If it's an absolute path outside home, we can't access it
            return f"Error: Path {file_path} is outside the accessible directory ({ROOT_DIR})"

        # Ensure path doesn't start with / for relative paths
        if file_path.startswith("/"):
            file_path = file_path[1:]

        logger.debug(
            "Calling read_file with path: %s on server: %s", file_path, server_name
        )

        # Call read_file tool with correct parameter name
        result = mcp_client.call_tool_sync(
            server_name, "read_file", {"path": file_path}
        )

        # Store the file read operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = (
                f"Read file: {file_path}\nContent preview: {result[:200]}..."
            )
            store_interaction.invoke(
                {"text": interaction_text, "topic": "file_operations"}
            )

        logger.info("Read file via MCP: %s", file_path)
        return result

    except Exception as e:
        logger.error("Error reading file via MCP: %s", str(e))
        return f"Error reading file: {str(e)}"


@tool
def mcp_write_file(file_path: str, content: str = None) -> str:
    """Write content to file using MCP filesystem server."""
    # Log the raw inputs for debugging
    logger.debug(
        "mcp_write_file called with file_path: %r, content: %r", file_path, content
    )
    logger.debug("file_path type: %s, content type: %s", type(file_path), type(content))

    # Handle case where LangChain incorrectly passes the entire JSON as file_path
    if (
        isinstance(file_path, str)
        and file_path.startswith("{")
        and file_path.endswith("}")
    ):
        try:
            # This is the case where LangChain passes the entire JSON string as file_path
            logger.debug("Detected JSON string in file_path, attempting to parse...")
            params = json.loads(file_path)
            logger.debug("Successfully parsed JSON: %s", params)

            # Extract the actual parameters
            if "file_path" in params and "content" in params:
                file_path = params["file_path"]
                content = params["content"]
                logger.debug(
                    "Extracted parameters: file_path=%r, content=%r", file_path, content
                )
            else:
                logger.warning(
                    "JSON missing required keys. Available keys: %s",
                    list(params.keys()),
                )
                return "Error: JSON parameters missing required 'file_path' or 'content' keys"

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON from file_path parameter: %s", e)
            return f"Error: Invalid JSON in parameters: {e}"
        except Exception as e:
            logger.error("Unexpected error parsing parameters: %s", e)
            return f"Error parsing parameters: {e}"

    # Validate that we have both required parameters
    if not file_path:
        logger.error("file_path is empty or None")
        return "Error: file_path parameter is required"
    if content is None or content == "":
        logger.error("content is None or empty")
        return "Error: content parameter is required"

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot write file."

    try:
        # Store original path for logging
        original_path = file_path

        # Expand ~ to actual path first
        if file_path.startswith("~/"):
            file_path = os.path.expanduser(file_path)

        # Determine which server to use based on path
        server_name = "filesystem-home"
        if file_path.startswith(DATA_DIR + "/") or file_path.startswith("data/"):
            server_name = "filesystem-data"

        # Start filesystem server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP filesystem server."

        # Convert absolute paths to relative paths for the restricted root
        if server_name == "filesystem-home":
            # The server root is ROOT_DIR
            if file_path == ROOT_DIR:
                return "Error: Cannot write to root directory as a file"
            elif file_path.startswith(ROOT_DIR + "/"):
                file_path = file_path[
                    len(ROOT_DIR + "/") :
                ]  # Remove ROOT_DIR prefix properly
            elif file_path.startswith("/"):
                return f"Error: Path {file_path} is outside the accessible directory ({ROOT_DIR})"
        else:  # filesystem-data
            # The server root is DATA_DIR
            if file_path.startswith(DATA_DIR + "/"):
                file_path = file_path[len(DATA_DIR + "/") :]  # Remove data dir prefix
            elif file_path.startswith("data/"):
                file_path = file_path[5:]  # Remove "data/" prefix

        # Ensure path doesn't start with / for relative paths
        if file_path.startswith("/"):
            file_path = file_path[1:]

        # Create directory structure if it doesn't exist
        dir_path = os.path.dirname(file_path)
        if dir_path:
            full_dir_path = os.path.join(
                ROOT_DIR if server_name == "filesystem-home" else DATA_DIR, dir_path
            )
            if not os.path.exists(full_dir_path):
                try:
                    os.makedirs(full_dir_path, exist_ok=True)
                    logger.info("Created directory structure: %s", full_dir_path)
                except Exception as e:
                    logger.warning(
                        "Could not create directory %s: %s", full_dir_path, e
                    )

        logger.debug(
            "Calling write_file with original path: %s, converted path: %s on server: %s",
            original_path,
            file_path,
            server_name,
        )

        # Call write_file tool with correct parameter name
        result = mcp_client.call_tool_sync(
            server_name, "write_file", {"path": file_path, "content": content}
        )

        # Store the file write operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = f"Wrote file: {original_path}\nContent length: {len(content)} characters"
            store_interaction.invoke(
                {"text": interaction_text, "topic": "file_operations"}
            )

        logger.info("Wrote file via MCP: %s -> %s", original_path, file_path)
        return result

    except Exception as e:
        logger.error("Error writing file via MCP: %s", str(e))
        return f"Error writing file: {str(e)}"


@tool
def mcp_list_directory(directory_path: str) -> str:
    """List directory contents using MCP filesystem server."""
    # Handle case where directory_path might be a JSON string from LangChain
    if isinstance(directory_path, str) and directory_path.startswith("{"):
        try:
            params = json.loads(directory_path)
            directory_path = params.get("directory_path", directory_path)
        except (json.JSONDecodeError, TypeError):
            pass  # Use original value if parsing fails

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot list directory."

    try:
        # Determine which server to use based on path
        server_name = "filesystem-home"
        if directory_path.startswith(DATA_DIR + "/") or directory_path.startswith(
            "data/"
        ):
            server_name = "filesystem-data"

        # Start filesystem server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP filesystem server."

        # Convert absolute paths to relative paths for the restricted root
        original_path = directory_path  # Keep for logging

        if server_name == "filesystem-home":
            # The server root is ROOT_DIR
            if directory_path in [ROOT_DIR, ROOT_DIR, "~", "$HOME"]:
                directory_path = "."  # Root directory
            elif directory_path.startswith(ROOT_DIR + "/"):
                directory_path = directory_path[
                    len(ROOT_DIR + "/") :
                ]  # Remove ROOT_DIR prefix
                if not directory_path:  # If empty after removing prefix
                    directory_path = "."
            elif directory_path.startswith("~/"):
                directory_path = directory_path[2:]  # Remove "~/" prefix
            elif directory_path.startswith("/"):
                return f"Error: Path {directory_path} is outside the accessible directory ({ROOT_DIR})"
        else:  # filesystem-data
            # The server root is DATA_DIR
            if directory_path.startswith(DATA_DIR + "/"):
                directory_path = directory_path[
                    len(DATA_DIR + "/") :
                ]  # Remove data dir prefix
                if not directory_path:  # If empty after removing prefix
                    directory_path = "."
            elif directory_path.startswith("data/"):
                directory_path = directory_path[5:]  # Remove "data/" prefix

        # Ensure path doesn't start with / for relative paths, but handle root directory
        if directory_path.startswith("/"):
            directory_path = directory_path[1:]

        # If path is empty after processing, it means we want the root directory
        if not directory_path:
            directory_path = "."

        logger.debug(
            "Original path: %s, Converted path: %s, Server: %s",
            original_path,
            directory_path,
            server_name,
        )

        # Call list_directory tool with the correct path
        result = mcp_client.call_tool_sync(
            server_name, "list_directory", {"path": directory_path}
        )

        # Store the directory listing operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = (
                f"Listed directory: {original_path}\nResult: {result[:300]}..."
            )
            store_interaction.invoke(
                {"text": interaction_text, "topic": "file_operations"}
            )

        logger.info("Listed directory via MCP: %s -> %s", original_path, directory_path)
        return result

    except Exception as e:
        logger.error("Error listing directory via MCP: %s", str(e))
        return f"Error listing directory: {str(e)}"


@tool
def intelligent_file_search(search_query: str, directory: str = "/") -> str:
    """Search for files and enhance results with memory context."""
    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot search files."

    try:
        # First, search memory for relevant context
        memory_context = []
        if USE_WEAVIATE and vector_store is not None:
            from ..tools.memory_tools import query_knowledge_base

            memory_results = query_knowledge_base.invoke(
                {"query": search_query, "limit": 3}
            )
            memory_context = (
                memory_results
                if memory_results != ["No relevant context found."]
                else []
            )

        # Use MCP to list directory contents and search for relevant files
        directory_listing = mcp_list_directory.invoke({"directory_path": directory})

        # Use LLM to analyze which files might be relevant based on the search query
        analysis_prompt = f"""
        Based on the search query: "{search_query}"
        
        Directory listing: {directory_listing}
        
        Memory context: {memory_context}
        
        Which files in this directory are most relevant to the search query? 
        Provide a focused analysis and suggest the top 2-3 most relevant files to examine.
        """

        # Store this search operation in memory
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = f"File search: {search_query} in {directory}\nFound: {directory_listing[:200]}..."
            store_interaction.invoke({"text": interaction_text, "topic": "file_search"})

        logger.info("Performed intelligent file search: %s", search_query)
        return f"Directory contents: {directory_listing}\n\nMemory context: {memory_context}\n\nAnalysis needed: {analysis_prompt}"

    except Exception as e:
        logger.error("Error in intelligent file search: %s", str(e))
        return f"Error searching files: {str(e)}"


@tool
def create_and_save_file(file_path: str, content: str, create_dirs: bool = True) -> str:
    """Create directories if needed and save file content. This is the preferred tool for creating new files."""
    # Handle case where parameters might be JSON strings from LangChain
    if isinstance(file_path, str) and file_path.startswith("{"):
        try:
            params = json.loads(file_path)
            file_path = params.get("file_path", file_path)
            content = params.get("content", content)
            create_dirs = params.get("create_dirs", create_dirs)
        except (json.JSONDecodeError, TypeError):
            pass

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot create file."

    try:
        # Store original path for logging
        original_path = file_path

        # Expand ~ to actual home directory
        if file_path.startswith("~/"):
            file_path = os.path.expanduser(file_path)

        # Get directory path
        dir_path = os.path.dirname(file_path)

        # Create directories if they don't exist and create_dirs is True
        if create_dirs and dir_path and not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.info("Created directory: %s", dir_path)
            except Exception as e:
                return f"Error creating directory {dir_path}: {str(e)}"

        # Now use the existing mcp_write_file tool
        result = mcp_write_file.invoke({"file_path": original_path, "content": content})

        # Store the file creation operation in memory
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = f"Created file: {original_path}\nContent length: {len(content)} characters\nDirectory created: {create_dirs}"
            store_interaction.invoke(
                {"text": interaction_text, "topic": "file_creation"}
            )

        logger.info("Created and saved file: %s", original_path)
        return f"Successfully created file: {original_path}\n{result}"

    except Exception as e:
        logger.error("Error creating and saving file: %s", str(e))
        return f"Error creating file: {str(e)}"
