"""
Personal Agent Tools implemented as Agno Toolkit classes.

This module provides proper Agno-compatible tool classes for the Personal Agent,
following the same pattern as YFinanceTools and DuckDuckGoTools.
"""

import os
import subprocess
from typing import Any, List

from agno.tools import Toolkit
from agno.utils.log import log_debug

from ..config import DATA_DIR, HOME_DIR
from ..utils import setup_logging

logger = setup_logging(__name__)


class PersonalAgentFilesystemTools(Toolkit):
    """
    Personal Agent filesystem tools for file operations.

    Args:
        read_file (bool): Enable file reading functionality.
        write_file (bool): Enable file writing functionality.
        list_directory (bool): Enable directory listing functionality.
        create_and_save_file (bool): Enable file creation functionality.
        intelligent_file_search (bool): Enable intelligent file search functionality.
    """

    def __init__(
        self,
        read_file: bool = True,
        write_file: bool = True,
        list_directory: bool = True,
        create_and_save_file: bool = True,
        intelligent_file_search: bool = True,
        **kwargs,
    ):
        tools: List[Any] = []

        if read_file:
            tools.append(self.read_file)
        if write_file:
            tools.append(self.write_file)
        if list_directory:
            tools.append(self.list_directory)
        if create_and_save_file:
            tools.append(self.create_and_save_file)
        if intelligent_file_search:
            tools.append(self.intelligent_file_search)

        super().__init__(name="personal_filesystem", tools=tools, **kwargs)

    def read_file(self, file_path: str) -> str:
        """Read content from a file.

        Args:
            file_path: Path to the file to read

        Returns:
            The file content or error message.
        """
        try:
            # Expand path shortcuts
            if file_path.startswith("~/"):
                file_path = os.path.expanduser(file_path)
            elif file_path.startswith("./"):
                file_path = os.path.abspath(file_path)

            # Security check - ensure file is within allowed directories
            allowed_dirs = [HOME_DIR, DATA_DIR, "/tmp", os.getcwd()]
            file_abs_path = os.path.abspath(file_path)

            if not any(file_abs_path.startswith(allowed_dir) for allowed_dir in allowed_dirs):
                return f"Error: Access denied to {file_path}. Only allowed in home, data, tmp, or current directories."

            if not os.path.exists(file_path):
                return f"Error: File {file_path} does not exist."

            if not os.path.isfile(file_path):
                return f"Error: {file_path} is not a file."

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            log_debug(f"Successfully read file: {file_path} ({len(content)} characters)")
            return content

        except PermissionError:
            return f"Error: Permission denied reading {file_path}"
        except UnicodeDecodeError:
            return f"Error: Unable to decode {file_path} as text file"
        except Exception as e:
            logger.error("Error reading file %s: %s", file_path, e)
            return f"Error reading file: {str(e)}"

    def write_file(self, file_path: str, content: str) -> str:
        """Write content to a file.

        Args:
            file_path: Path to the file to write
            content: Content to write to the file

        Returns:
            Success message or error message.
        """
        try:
            # Expand path shortcuts
            if file_path.startswith("~/"):
                file_path = os.path.expanduser(file_path)
            elif file_path.startswith("./"):
                file_path = os.path.abspath(file_path)

            # Security check - ensure file is within allowed directories
            allowed_dirs = [HOME_DIR, DATA_DIR, "/tmp", os.getcwd()]
            file_abs_path = os.path.abspath(file_path)

            if not any(file_abs_path.startswith(allowed_dir) for allowed_dir in allowed_dirs):
                return f"Error: Access denied to {file_path}. Only allowed in home, data, tmp, or current directories."

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            log_debug(f"Successfully wrote file: {file_path} ({len(content)} characters)")
            return f"Successfully wrote {len(content)} characters to {file_path}"

        except PermissionError:
            return f"Error: Permission denied writing to {file_path}"
        except Exception as e:
            logger.error("Error writing file %s: %s", file_path, e)
            return f"Error writing file: {str(e)}"

    def list_directory(self, directory_path: str = ".") -> str:
        """List contents of a directory.

        Args:
            directory_path: Path to the directory to list

        Returns:
            Directory listing or error message.
        """
        try:
            # Expand path shortcuts
            if directory_path.startswith("~/"):
                directory_path = os.path.expanduser(directory_path)
            elif directory_path.startswith("./"):
                directory_path = os.path.abspath(directory_path)

            # Security check - ensure directory is within allowed directories
            allowed_dirs = [HOME_DIR, DATA_DIR, "/tmp", os.getcwd()]
            dir_abs_path = os.path.abspath(directory_path)

            if not any(dir_abs_path.startswith(allowed_dir) for allowed_dir in allowed_dirs):
                return f"Error: Access denied to {directory_path}. Only allowed in home, data, tmp, or current directories."

            if not os.path.exists(directory_path):
                return f"Error: Directory {directory_path} does not exist."

            if not os.path.isdir(directory_path):
                return f"Error: {directory_path} is not a directory."

            items = []
            for item in sorted(os.listdir(directory_path)):
                item_path = os.path.join(directory_path, item)
                if os.path.isdir(item_path):
                    items.append(f"📁 {item}/")
                else:
                    # Get file size
                    try:
                        size = os.path.getsize(item_path)
                        if size < 1024:
                            size_str = f"{size}B"
                        elif size < 1024 * 1024:
                            size_str = f"{size/1024:.1f}KB"
                        else:
                            size_str = f"{size/(1024*1024):.1f}MB"
                        items.append(f"📄 {item} ({size_str})")
                    except OSError:
                        items.append(f"📄 {item}")

            if not items:
                return f"Directory {directory_path} is empty."

            result = f"Contents of {directory_path}:\n" + "\n".join(items)
            log_debug(f"Listed directory: {directory_path} ({len(items)} items)")
            return result

        except PermissionError:
            return f"Error: Permission denied accessing {directory_path}"
        except Exception as e:
            logger.error("Error listing directory %s: %s", directory_path, e)
            return f"Error listing directory: {str(e)}"

    def create_and_save_file(self, filename: str, content: str, directory: str = "./") -> str:
        """Create a new file with content in specified directory.

        Args:
            filename: Name of the file to create
            content: Content to write to the file
            directory: Directory to create the file in (default: current directory)

        Returns:
            Success message with full path or error message.
        """
        try:
            # Expand directory shortcuts
            if directory.startswith("~/"):
                directory = os.path.expanduser(directory)
            elif directory.startswith("./"):
                directory = os.path.abspath(directory)

            # Create full file path
            file_path = os.path.join(directory, filename)

            # Use the write_file method for consistency
            return self.write_file(file_path, content)

        except Exception as e:
            logger.error("Error creating file %s: %s", filename, e)
            return f"Error creating file: {str(e)}"

    def intelligent_file_search(self, search_term: str, directory: str = ".", file_extensions: str = "") -> str:
        """Search for files containing specific content or matching patterns.

        Args:
            search_term: Term to search for in file names and content
            directory: Directory to search in (default: current directory)
            file_extensions: Comma-separated list of file extensions to search (e.g., "py,txt,md")

        Returns:
            Search results or error message.
        """
        try:
            # Expand directory shortcuts
            if directory.startswith("~/"):
                directory = os.path.expanduser(directory)
            elif directory.startswith("./"):
                directory = os.path.abspath(directory)

            # Security check
            allowed_dirs = [HOME_DIR, DATA_DIR, "/tmp", os.getcwd()]
            dir_abs_path = os.path.abspath(directory)

            if not any(dir_abs_path.startswith(allowed_dir) for allowed_dir in allowed_dirs):
                return f"Error: Access denied to {directory}. Only allowed in home, data, tmp, or current directories."

            if not os.path.exists(directory):
                return f"Error: Directory {directory} does not exist."

            # Parse file extensions
            extensions = []
            if file_extensions:
                extensions = [ext.strip().lower() for ext in file_extensions.split(",")]

            matches = []
            search_term_lower = search_term.lower()

            # Walk through directory tree
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, directory)

                    # Check file extension filter
                    if extensions:
                        file_ext = os.path.splitext(file)[1][1:].lower()  # Remove the dot
                        if file_ext not in extensions:
                            continue

                    # Check filename match
                    filename_match = search_term_lower in file.lower()
                    content_match = False

                    # Check content match for text files
                    try:
                        if os.path.getsize(file_path) < 10 * 1024 * 1024:  # Only search files < 10MB
                            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                                if search_term_lower in content.lower():
                                    content_match = True
                    except (OSError, UnicodeDecodeError):
                        pass  # Skip binary files or files we can't read

                    if filename_match or content_match:
                        match_type = []
                        if filename_match:
                            match_type.append("filename")
                        if content_match:
                            match_type.append("content")

                        matches.append(f"📄 {relative_path} (match: {', '.join(match_type)})")

            if not matches:
                return f"No files found containing '{search_term}' in {directory}"

            result = f"Found {len(matches)} file(s) matching '{search_term}':\n" + "\n".join(matches[:20])
            if len(matches) > 20:
                result += f"\n... and {len(matches) - 20} more files"

            log_debug(f"File search for '{search_term}' found {len(matches)} matches")
            return result

        except Exception as e:
            logger.error("Error searching files: %s", e)
            return f"Error searching files: {str(e)}"


class PersonalAgentSystemTools(Toolkit):
    """
    Personal Agent system tools for shell commands.

    Args:
        shell_command (bool): Enable shell command execution.
    """

    def __init__(self, shell_command: bool = True, **kwargs):
        tools: List[Any] = []

        if shell_command:
            tools.append(self.shell_command)

        super().__init__(name="personal_system", tools=tools, **kwargs)

    def shell_command(self, command: str, working_directory: str = ".") -> str:
        """Execute a shell command safely.

        Args:
            command: Shell command to execute
            working_directory: Directory to execute the command in

        Returns:
            Command output or error message.
        """
        try:
            # Security check - block dangerous commands
            dangerous_commands = [
                "rm -rf", "rmdir", "del", "format", "fdisk",
                "mkfs", "dd", "sudo", "su", "chmod 777",
                "curl", "wget", "nc", "netcat"
            ]

            command_lower = command.lower()
            for dangerous in dangerous_commands:
                if dangerous in command_lower:
                    return f"Error: Command '{command}' contains potentially dangerous operation '{dangerous}'"

            # Expand working directory
            if working_directory.startswith("~/"):
                working_directory = os.path.expanduser(working_directory)
            elif working_directory.startswith("./"):
                working_directory = os.path.abspath(working_directory)

            # Security check for working directory
            allowed_dirs = [HOME_DIR, DATA_DIR, "/tmp", os.getcwd()]
            dir_abs_path = os.path.abspath(working_directory)

            if not any(dir_abs_path.startswith(allowed_dir) for allowed_dir in allowed_dirs):
                return f"Error: Access denied to {working_directory}. Only allowed in home, data, tmp, or current directories."

            # Execute command with timeout
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_directory,
                capture_output=True,
                text=True,
                timeout=30  # 30 second timeout
            )

            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            output += f"Return code: {result.returncode}"

            log_debug(f"Executed command: {command} (return code: {result.returncode})")
            return output

        except subprocess.TimeoutExpired:
            return f"Error: Command '{command}' timed out after 30 seconds"
        except Exception as e:
            logger.error("Error executing command %s: %s", command, e)
            return f"Error executing command: {str(e)}"
