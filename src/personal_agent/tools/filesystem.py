"""Filesystem tools for the Personal Agent using MCP."""

# pylint: disable=w0718,c0103,c0301
import json
import os
from typing import TYPE_CHECKING

from langchain.tools import tool

from ..config import DATA_DIR, HOME_DIR, USER_DATA_DIR, USE_MCP, USE_WEAVIATE
from ..config.runtime_config import get_config

if TYPE_CHECKING:
    from ..core.mcp_client import SimpleMCPClient
    from ..core.memory import WeaviateVectorStore

mcp_client: "SimpleMCPClient" = None
vector_store: "WeaviateVectorStore" = None
store_interaction = None

logger = None


@tool
def mcp_read_file(file_path: str = ".") -> str:
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
        server_name = "filesystem-home"  # Default to home directory access

        # Choose server based on path and desired access level
        if file_path.startswith(USER_DATA_DIR + "/") or file_path.startswith("data/"):
            server_name = "filesystem-data"
        elif file_path.startswith("/") and not file_path.startswith(HOME_DIR):
            # Use root server for paths outside home directory
            server_name = "filesystem-root"

        # Start filesystem server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP filesystem server."

        # Store original path for logging
        original_path = file_path

        # Expand ~ to actual home directory if needed
        if file_path.startswith("~/"):
            file_path = os.path.expanduser(file_path)

        # Convert relative paths to absolute paths
        if not file_path.startswith("/"):
            file_path = os.path.abspath(file_path)

        # Validate path access based on server type
        if server_name == "filesystem-home":
            # Server allows access to HOME_DIR and subdirectories
            if not file_path.startswith(HOME_DIR):
                return f"Error: Path {file_path} is outside the accessible home directory ({HOME_DIR}). Use filesystem-root for full system access."
        elif server_name == "filesystem-data":
            # Server allows access to DATA_DIR and subdirectories
            if not file_path.startswith(DATA_DIR):
                return f"Error: Path {file_path} is outside the accessible data directory ({DATA_DIR})"
        elif server_name == "filesystem-root":
            # Full filesystem access - validate it's an absolute path
            if not file_path.startswith("/"):
                return f"Error: Path {file_path} must be an absolute path for root filesystem access"

        # Use absolute path directly - MCP servers expect absolute paths!

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
def mcp_write_file(file_path: str = ".", content: str = None) -> str:
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

        # Expand ~ to actual home directory if needed
        if file_path.startswith("~/"):
            file_path = os.path.expanduser(file_path)

        # Determine which server to use based on path
        server_name = "filesystem-home"  # Default to home directory access

        # Choose server based on path and desired access level
        if file_path.startswith(DATA_DIR + "/") or file_path.startswith("data/"):
            server_name = "filesystem-data"
        elif file_path.startswith("/") and not file_path.startswith(HOME_DIR):
            # Use root server for paths outside home directory
            server_name = "filesystem-root"

        # Start filesystem server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP filesystem server."

        # Convert relative paths to absolute paths
        if not file_path.startswith("/"):
            file_path = os.path.abspath(file_path)

        # Validate path access based on server type
        if server_name == "filesystem-home":
            # Server allows access to HOME_DIR and subdirectories
            if not file_path.startswith(HOME_DIR):
                return f"Error: Path {file_path} is outside the accessible home directory ({HOME_DIR}). Use filesystem-root for full system access."
        elif server_name == "filesystem-data":
            # Server allows access to DATA_DIR and subdirectories
            if not file_path.startswith(DATA_DIR):
                return f"Error: Path {file_path} is outside the accessible data directory ({DATA_DIR})"
        elif server_name == "filesystem-root":
            # Full filesystem access - validate it's an absolute path
            if not file_path.startswith("/"):
                return f"Error: Path {file_path} must be an absolute path for root filesystem access"

        # Create directory structure if it doesn't exist
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
                logger.info("Created directory structure: %s", dir_path)
            except Exception as e:
                logger.warning("Could not create directory %s: %s", dir_path, e)

        # Use absolute path directly - MCP servers expect absolute paths!

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
def mcp_list_directory(directory_path: str = ".") -> str:
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
        server_name = "filesystem-home"  # Default to home directory access

        # Choose server based on path and desired access level
        if directory_path.startswith(DATA_DIR + "/") or directory_path.startswith(
            "data/"
        ):
            server_name = "filesystem-data"
        elif directory_path.startswith("/") and not directory_path.startswith(HOME_DIR):
            # Use root server for paths outside home directory
            server_name = "filesystem-root"

        # Start filesystem server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP filesystem server."

        # Store original path for logging
        original_path = directory_path

        # Expand ~ to actual home directory if needed
        if directory_path.startswith("~"):
            directory_path = os.path.expanduser(directory_path)

        # Convert relative paths to absolute paths
        if not directory_path.startswith("/"):
            directory_path = os.path.abspath(directory_path)

        # Validate path access based on server type
        if server_name == "filesystem-home":
            # Server allows access to HOME_DIR and subdirectories
            if not directory_path.startswith(HOME_DIR):
                return f"Error: Path {directory_path} is outside the accessible home directory ({HOME_DIR}). Use filesystem-root for full system access."
        elif server_name == "filesystem-data":
            # Server allows access to DATA_DIR and subdirectories
            if not directory_path.startswith(DATA_DIR):
                return f"Error: Path {directory_path} is outside the accessible data directory ({DATA_DIR})"
        elif server_name == "filesystem-root":
            # Full filesystem access - validate it's an absolute path
            if not directory_path.startswith("/"):
                return f"Error: Path {directory_path} must be an absolute path for root filesystem access"

        # Use absolute path directly - MCP servers expect absolute paths!

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
def create_and_save_file(
    file_path: str = "./pai.txt",
    content: str = "Default output for create and save file\n",
    create_dirs: bool = True,
) -> str:
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
        config = get_config()

        # Store original path for logging
        original_path = file_path

        # Normalize natural language path references
        # Extract directory and filename if path contains common phrases
        if "/" in file_path or "\\" in file_path:
            dir_part = os.path.dirname(file_path)
            file_part = os.path.basename(file_path)

            # Normalize directory part
            dir_lower = dir_part.lower().strip()
            if dir_lower in ["current directory", "current dir", "here", "this directory"]:
                dir_part = "."
            elif dir_lower in ["home", "home directory", "home dir"]:
                # Use patient's isolated home directory, not system user's home
                dir_part = config.user_home_dir

            # Reconstruct path
            file_path = os.path.join(dir_part, file_part) if dir_part else file_part

        # Expand ~ to user_home_dir for multi-user isolation
        if file_path.startswith("~/"):
            file_path = file_path.replace("~", config.user_home_dir, 1)

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
