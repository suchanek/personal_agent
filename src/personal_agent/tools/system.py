"""System tools for the Personal Agent."""

import json
import subprocess
from typing import TYPE_CHECKING, Optional

from agno.tools import tool

# Global variables that will be injected by the main module
mcp_client: Optional[object] = None
store_interaction: Optional[callable] = None
logger: Optional[object] = None


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

        logger.info("Shell command executed: %s", command)
        return output

    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout} seconds"
        logger.error("Shell command timeout: %s", command)
        return error_msg
    except Exception as e:
        logger.error("Error executing shell command: %s", str(e))
        return f"Error executing shell command: {str(e)}"


@tool
def shell_command(command: str, timeout: int = 30) -> str:
    """
    Execute shell commands safely using subprocess.

    Args:
        command: Shell command to execute
        timeout: Timeout in seconds (default 30)

    Returns:
        str: Command output including return code, stdout, and stderr
    """
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

        # Store the shell command operation in memory for context (if available)
        if store_interaction and logger:
            try:
                interaction_text = (
                    f"Shell command: {command}\nOutput: {output[:300]}..."
                )
                store_interaction(interaction_text, "shell_commands")
            except Exception as e:
                if logger:
                    logger.warning("Failed to store interaction: %s", e)

        if logger:
            logger.info("Shell command executed: %s", command)
        return output

    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout} seconds"
        logger.error("Shell command timeout: %s", command)
        return error_msg
    except Exception as e:
        logger.error("Error executing shell command: %s", str(e))
        return f"Error executing shell command: {str(e)}"


# end of file
