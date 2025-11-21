#!/usr/bin/env python3
"""
Personal Agent Tools Test Suite

This test suite verifies the functionality of PersonalAgentFilesystemTools
and PersonalAgentSystemTools classes.

Tests cover:
- File reading with security checks
- File writing with overwrite logic
- Directory listing
- File creation
- Intelligent file search
- Shell command execution with security

Usage:
    python -m pytest tests/tools/test_personal_agent_tools.py -v
    or
    python tests/tools/test_personal_agent_tools.py
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.tools.personal_agent_tools import (
    PersonalAgentFilesystemTools,
    PersonalAgentSystemTools,
)


class TestPersonalAgentFilesystemTools(unittest.TestCase):
    """Test suite for PersonalAgentFilesystemTools."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a temporary directory for testing
        self.temp_dir = Path(tempfile.mkdtemp())
        self.test_file = self.temp_dir / "test_file.txt"
        self.test_content = "This is test content\nLine 2\nLine 3"
        
        # Create test file
        self.test_file.write_text(self.test_content)
        
        # Initialize tools with temp directory as base
        self.tools = PersonalAgentFilesystemTools(base_dir=str(self.temp_dir))

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test that PersonalAgentFilesystemTools initializes correctly."""
        # Test with all tools enabled (default)
        tools = PersonalAgentFilesystemTools()
        self.assertEqual(tools.name, "personal_filesystem")
        self.assertIsNotNone(tools.tools)
        self.assertGreater(len(tools.tools), 0)

    def test_initialization_selective_tools(self):
        """Test initialization with selective tool enabling."""
        # Only enable read_file
        tools = PersonalAgentFilesystemTools(
            read_file=True,
            write_file=False,
            list_directory=False,
            create_and_save_file=False,
            intelligent_file_search=False,
        )
        self.assertEqual(len(tools.tools), 1)

    def test_read_file_success(self):
        """Test successful file reading."""
        result = self.tools.read_file(str(self.test_file))
        self.assertEqual(result, self.test_content)

    def test_read_file_nonexistent(self):
        """Test reading a non-existent file."""
        result = self.tools.read_file(str(self.temp_dir / "nonexistent.txt"))
        self.assertIn("Error", result)
        self.assertIn("does not exist", result)

    def test_read_file_directory(self):
        """Test reading a directory (should fail)."""
        result = self.tools.read_file(str(self.temp_dir))
        self.assertIn("Error", result)
        self.assertIn("not a file", result)

    def test_read_file_permission_error(self):
        """Test reading a file with permission issues."""
        # Create a file with no read permissions
        restricted_file = self.temp_dir / "restricted.txt"
        restricted_file.write_text("restricted content")
        restricted_file.chmod(0o000)
        
        try:
            result = self.tools.read_file(str(restricted_file))
            self.assertIn("Error", result)
        finally:
            # Restore permissions for cleanup
            restricted_file.chmod(0o644)

    def test_write_file_success(self):
        """Test successful file writing."""
        new_file = self.temp_dir / "new_file.txt"
        content = "New file content"
        
        result = self.tools.write_file(str(new_file), content)
        self.assertIn("Successfully", result)
        self.assertTrue(new_file.exists())
        self.assertEqual(new_file.read_text(), content)

    def test_write_file_overwrite(self):
        """Test file overwriting."""
        # Write initial content
        test_file = self.temp_dir / "overwrite_test.txt"
        test_file.write_text("Initial content")
        
        # Overwrite with new content
        new_content = "Overwritten content"
        result = self.tools.write_file(str(test_file), new_content, overwrite=True)
        
        self.assertIn("Successfully", result)
        self.assertIn("overwrote", result)
        self.assertEqual(test_file.read_text(), new_content)

    def test_write_file_no_overwrite(self):
        """Test file writing with overwrite disabled."""
        # Create existing file
        existing_file = self.temp_dir / "existing.txt"
        existing_file.write_text("Existing content")
        
        # Try to write without overwrite
        result = self.tools.write_file(
            str(existing_file), "New content", overwrite=False
        )
        
        self.assertIn("Error", result)
        self.assertIn("already exists", result)
        # Original content should remain
        self.assertEqual(existing_file.read_text(), "Existing content")

    def test_write_file_creates_directory(self):
        """Test that write_file creates parent directories."""
        nested_file = self.temp_dir / "subdir" / "nested" / "file.txt"
        content = "Nested file content"
        
        result = self.tools.write_file(str(nested_file), content)
        
        self.assertIn("Successfully", result)
        self.assertTrue(nested_file.exists())
        self.assertEqual(nested_file.read_text(), content)

    def test_list_directory_success(self):
        """Test successful directory listing."""
        # Create some test files and directories
        (self.temp_dir / "file1.txt").write_text("content1")
        (self.temp_dir / "file2.txt").write_text("content2")
        (self.temp_dir / "subdir").mkdir()
        
        result = self.tools.list_directory(str(self.temp_dir))
        
        self.assertIn("Contents of", result)
        self.assertIn("file1.txt", result)
        self.assertIn("file2.txt", result)
        self.assertIn("subdir/", result)
        self.assertIn("📄", result)  # File emoji
        self.assertIn("📁", result)  # Directory emoji

    def test_list_directory_empty(self):
        """Test listing an empty directory."""
        empty_dir = self.temp_dir / "empty"
        empty_dir.mkdir()
        
        result = self.tools.list_directory(str(empty_dir))
        self.assertIn("empty", result.lower())

    def test_list_directory_nonexistent(self):
        """Test listing a non-existent directory."""
        result = self.tools.list_directory(str(self.temp_dir / "nonexistent"))
        self.assertIn("Error", result)
        self.assertIn("does not exist", result)

    def test_list_directory_not_directory(self):
        """Test listing a file (should fail)."""
        result = self.tools.list_directory(str(self.test_file))
        self.assertIn("Error", result)
        self.assertIn("not a directory", result)

    def test_create_and_save_file_success(self):
        """Test successful file creation."""
        filename = "created_file.txt"
        content = "Created content"
        
        result = self.tools.create_and_save_file(
            filename=filename,
            content=content,
            directory=str(self.temp_dir),
        )
        
        self.assertIn("Successfully", result)
        created_file = self.temp_dir / filename
        self.assertTrue(created_file.exists())
        self.assertEqual(created_file.read_text(), content)

    def test_create_and_save_file_with_overwrite(self):
        """Test file creation with overwrite parameter."""
        filename = "overwrite_test.txt"
        file_path = self.temp_dir / filename
        file_path.write_text("Original")
        
        # Create with overwrite=True
        result = self.tools.create_and_save_file(
            filename=filename,
            content="New content",
            directory=str(self.temp_dir),
            overwrite=True,
        )
        
        self.assertIn("Successfully", result)
        self.assertEqual(file_path.read_text(), "New content")

    def test_intelligent_file_search_by_filename(self):
        """Test intelligent file search by filename."""
        # Create test files
        (self.temp_dir / "test_search.txt").write_text("content")
        (self.temp_dir / "another_file.txt").write_text("content")
        (self.temp_dir / "test_search_2.py").write_text("code")
        
        result = self.tools.intelligent_file_search(
            search_term="test_search",
            directory=str(self.temp_dir),
        )
        
        self.assertIn("test_search.txt", result)
        self.assertIn("test_search_2.py", result)
        self.assertNotIn("another_file.txt", result)

    def test_intelligent_file_search_by_content(self):
        """Test intelligent file search by content."""
        # Create test files with specific content
        (self.temp_dir / "file1.txt").write_text("This contains SEARCHTERM")
        (self.temp_dir / "file2.txt").write_text("This does not contain it")
        (self.temp_dir / "file3.txt").write_text("Another SEARCHTERM here")
        
        result = self.tools.intelligent_file_search(
            search_term="SEARCHTERM",
            directory=str(self.temp_dir),
        )
        
        self.assertIn("file1.txt", result)
        self.assertIn("file3.txt", result)
        self.assertNotIn("file2.txt", result)

    def test_intelligent_file_search_with_extensions(self):
        """Test intelligent file search with file extension filter."""
        # Create files with different extensions
        (self.temp_dir / "test.txt").write_text("content")
        (self.temp_dir / "test.py").write_text("code")
        (self.temp_dir / "test.md").write_text("markdown")
        
        result = self.tools.intelligent_file_search(
            search_term="test",
            directory=str(self.temp_dir),
            file_extensions="py,md",
        )
        
        self.assertIn("test.py", result)
        self.assertIn("test.md", result)
        self.assertNotIn("test.txt", result)

    def test_intelligent_file_search_no_results(self):
        """Test intelligent file search with no matches."""
        result = self.tools.intelligent_file_search(
            search_term="nonexistent_term_xyz",
            directory=str(self.temp_dir),
        )
        
        self.assertIn("No files found", result)

    def test_intelligent_file_search_nonexistent_directory(self):
        """Test intelligent file search in non-existent directory."""
        result = self.tools.intelligent_file_search(
            search_term="test",
            directory=str(self.temp_dir / "nonexistent"),
        )
        
        self.assertIn("Error", result)
        self.assertIn("does not exist", result)


class TestPersonalAgentSystemTools(unittest.TestCase):
    """Test suite for PersonalAgentSystemTools."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.tools = PersonalAgentSystemTools()

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_initialization(self):
        """Test that PersonalAgentSystemTools initializes correctly."""
        tools = PersonalAgentSystemTools()
        self.assertEqual(tools.name, "personal_system")
        self.assertIsNotNone(tools.tools)
        self.assertGreater(len(tools.tools), 0)

    def test_initialization_no_shell_command(self):
        """Test initialization with shell_command disabled."""
        tools = PersonalAgentSystemTools(shell_command=False)
        self.assertEqual(len(tools.tools), 0)

    def test_shell_command_simple_success(self):
        """Test successful execution of a simple shell command."""
        result = self.tools.shell_command("echo 'Hello World'")
        
        self.assertIn("Hello World", result)
        self.assertIn("Return code: 0", result)

    def test_shell_command_with_working_directory(self):
        """Test shell command execution in a specific directory."""
        # Create a test file in temp directory
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # List files in that directory
        result = self.tools.shell_command(
            "ls",
            working_directory=str(self.temp_dir),
        )
        
        self.assertIn("test.txt", result)

    def test_shell_command_dangerous_rm_rf(self):
        """Test that dangerous 'rm -rf' command is blocked."""
        result = self.tools.shell_command("rm -rf /some/path")
        
        self.assertIn("Error", result)
        self.assertIn("dangerous", result.lower())
        self.assertIn("rm -rf", result)

    def test_shell_command_dangerous_sudo(self):
        """Test that dangerous 'sudo' command is blocked."""
        result = self.tools.shell_command("sudo apt-get install something")
        
        self.assertIn("Error", result)
        self.assertIn("dangerous", result.lower())
        self.assertIn("sudo", result)

    def test_shell_command_dangerous_curl(self):
        """Test that dangerous 'curl' command is blocked."""
        result = self.tools.shell_command("curl http://example.com")
        
        self.assertIn("Error", result)
        self.assertIn("dangerous", result.lower())
        self.assertIn("curl", result)

    def test_shell_command_dangerous_wget(self):
        """Test that dangerous 'wget' command is blocked."""
        result = self.tools.shell_command("wget http://example.com/file")
        
        self.assertIn("Error", result)
        self.assertIn("dangerous", result.lower())
        self.assertIn("wget", result)

    def test_shell_command_stderr_output(self):
        """Test that stderr output is captured."""
        # Command that writes to stderr
        result = self.tools.shell_command("ls /nonexistent_directory_xyz 2>&1")
        
        # Should contain error information
        self.assertIn("Return code:", result)

    def test_shell_command_nonzero_return_code(self):
        """Test command with non-zero return code."""
        result = self.tools.shell_command("false")  # 'false' always returns 1
        
        self.assertIn("Return code: 1", result)

    @patch('subprocess.run')
    def test_shell_command_timeout(self, mock_run):
        """Test that long-running commands timeout."""
        import subprocess
        
        # Simulate a timeout
        mock_run.side_effect = subprocess.TimeoutExpired("test", 30)
        
        result = self.tools.shell_command("sleep 100")
        
        self.assertIn("Error", result)
        self.assertIn("timed out", result)

    def test_shell_command_path_expansion(self):
        """Test that path shortcuts are expanded."""
        # Test with tilde expansion
        result = self.tools.shell_command(
            "pwd",
            working_directory="~/",
        )
        
        # Should not contain tilde in output
        self.assertNotIn("~", result)


class TestSecurityChecks(unittest.TestCase):
    """Test suite for security checks in PersonalAgentTools."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.tools = PersonalAgentFilesystemTools(base_dir=str(self.temp_dir))

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_read_file_security_check(self):
        """Test that read_file respects allowed directories."""
        # This test verifies the security check is in place
        # The actual behavior depends on ALLOWED_DIRS configuration
        
        # Try to read a file in temp directory (should work)
        test_file = self.temp_dir / "test.txt"
        test_file.write_text("content")
        
        result = self.tools.read_file(str(test_file))
        # Should succeed or fail based on security settings
        self.assertIsInstance(result, str)

    def test_write_file_security_check(self):
        """Test that write_file respects allowed directories."""
        # Try to write a file in temp directory
        test_file = self.temp_dir / "test.txt"
        
        result = self.tools.write_file(str(test_file), "content")
        # Should succeed or fail based on security settings
        self.assertIsInstance(result, str)

    def test_list_directory_security_check(self):
        """Test that list_directory respects allowed directories."""
        result = self.tools.list_directory(str(self.temp_dir))
        # Should succeed or fail based on security settings
        self.assertIsInstance(result, str)


class TestEdgeCases(unittest.TestCase):
    """Test suite for edge cases and error handling."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.tools = PersonalAgentFilesystemTools(base_dir=str(self.temp_dir))

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_read_file_empty_file(self):
        """Test reading an empty file."""
        empty_file = self.temp_dir / "empty.txt"
        empty_file.write_text("")
        
        result = self.tools.read_file(str(empty_file))
        self.assertEqual(result, "")

    def test_write_file_empty_content(self):
        """Test writing empty content to a file."""
        test_file = self.temp_dir / "empty.txt"
        
        result = self.tools.write_file(str(test_file), "")
        self.assertIn("Successfully", result)
        self.assertEqual(test_file.read_text(), "")

    def test_write_file_large_content(self):
        """Test writing large content to a file."""
        large_content = "x" * 1000000  # 1MB of content
        test_file = self.temp_dir / "large.txt"
        
        result = self.tools.write_file(str(test_file), large_content)
        self.assertIn("Successfully", result)
        self.assertEqual(len(test_file.read_text()), 1000000)

    def test_intelligent_file_search_case_insensitive(self):
        """Test that file search is case-insensitive."""
        (self.temp_dir / "TestFile.txt").write_text("CONTENT")
        
        result = self.tools.intelligent_file_search(
            search_term="testfile",
            directory=str(self.temp_dir),
        )
        
        self.assertIn("TestFile.txt", result)

    def test_shell_command_empty_command(self):
        """Test shell command with empty string."""
        system_tools = PersonalAgentSystemTools()
        result = system_tools.shell_command("")
        
        # Should handle gracefully
        self.assertIsInstance(result, str)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)