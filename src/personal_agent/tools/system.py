"""System tools for the Personal Agent."""

import json
import subprocess
from typing import TYPE_CHECKING

from langchain.tools import tool

if TYPE_CHECKING:
    from ..core.memory import WeaviateVectorStore

# These will be injected by the main module
USE_MCP = False
USE_WEAVIATE = False
mcp_client = None
vector_store: "WeaviateVectorStore" = None
store_interaction = None
logger = None


@tool
def mcp_shell_command(command: str, timeout: int = 30) -> str:
    """Execute shell commands safely using subprocess (MCP shell server unavailable)."""
    # Handle case where parameters might be JSON strings from LangChain
    if isinstance(command, str) and command.startswith("{"):
        try:
            params = json.loads(command)
            command = params.get("command", command)
            timeout = params.get("timeout", timeout)
        except (json.JSONDecodeError, TypeError):
            pass

    try:
        # Use subprocess for safe shell command execution
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        output = f"Command: {command}\nReturn code: {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"

        # Store the shell command operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = f"Shell command: {command}\nOutput: {output[:300]}..."
            store_interaction.invoke(
                {"text": interaction_text, "topic": "shell_commands"}
            )

        logger.info("Shell command executed: %s", command)
        return output

    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout} seconds"
        logger.error("Shell command timeout: %s", command)
        return error_msg
    except Exception as e:
        logger.error("Error executing shell command: %s", str(e))
        return f"Error executing shell command: {str(e)}"
