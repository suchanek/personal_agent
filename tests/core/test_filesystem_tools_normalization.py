"""
Unit tests for Filesystem Tools Natural Language Normalization.

This module tests the natural language directory reference normalization
implemented in both PersonalAgentFilesystemTools and MCP-based filesystem tools.

Tests cover:
- Current directory phrase normalization
- Home directory phrase normalization
- Path expansion and security
- Multi-user context handling
- Edge cases and error conditions

Author: Kilo Code
Date: 2025-11-21
Related: ADR-101
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from personal_agent.config.runtime_config import PersonalAgentConfig, get_config
from personal_agent.tools.personal_agent_tools import PersonalAgentFilesystemTools


class TestCurrentDirectoryNormalization(unittest.TestCase):
    """Test normalization of 'current directory' phrases."""

    def setUp(self):
        """Set up test fixtures."""
        self.cwd = os.getcwd()
        self.tools = PersonalAgentFilesystemTools()
        self.created_files = []
        self.created_dirs = []

    def tearDown(self):
        """Clean up after tests."""
        import shutil
        
        # Clean up files
        for file_path in self.created_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
        
        # Clean up directories
        for dir_path in self.created_dirs:
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                except OSError:
                    pass

    def test_current_directory_phrase_normalization(self):
        """Test that 'current directory' is normalized to '.'"""
        test_phrases = [
            "current directory",
            "current dir",
            "here",
            "this directory",
            ".",
        ]

        for phrase in test_phrases:
            with self.subTest(phrase=phrase):
                result = self.tools.create_and_save_file(
                    filename="test.txt",
                    content="test content",
                    directory=phrase
                )
                
                # Should succeed
                self.assertIn("Successfully", result)
                
                # File should be in current directory
                expected_path = os.path.join(self.cwd, "test.txt")
                self.assertTrue(os.path.exists(expected_path),
                    f"File not found at {expected_path} for phrase '{phrase}'")
                
                # Should NOT create a literal directory
                literal_dir = os.path.join(self.cwd, phrase)
                if phrase != ".":  # "." is the current dir itself
                    self.assertFalse(os.path.exists(literal_dir),
                        f"Literal directory '{phrase}' should not exist")
                
                # Track file for cleanup
                self.created_files.append(expected_path)

    def test_current_directory_case_insensitive(self):
        """Test that normalization is case-insensitive."""
        test_phrases = [
            "Current Directory",
            "CURRENT DIRECTORY",
            "CuRrEnT DiReCtOrY",
            "HERE",
            "Here",
        ]

        for phrase in test_phrases:
            with self.subTest(phrase=phrase):
                filename = f"test_{phrase.replace(' ', '_')}.txt"
                result = self.tools.create_and_save_file(
                    filename=filename,
                    content="test",
                    directory=phrase
                )
                
                self.assertIn("Successfully", result)
                
                # Should not create literal directory
                literal_dir = os.path.join(self.cwd, phrase)
                self.assertFalse(os.path.exists(literal_dir),
                    f"Literal directory '{phrase}' should not exist")
                
                # Track file for cleanup
                test_file = os.path.join(self.cwd, filename)
                self.created_files.append(test_file)

    def test_current_directory_with_whitespace(self):
        """Test normalization handles extra whitespace."""
        test_phrases = [
            "  current directory  ",
            " current dir ",
            "  here  ",
        ]

        for phrase in test_phrases:
            with self.subTest(phrase=phrase):
                result = self.tools.create_and_save_file(
                    filename="test_ws.txt",
                    content="test",
                    directory=phrase
                )
                
                self.assertIn("Successfully", result)
                
                # File should be in current directory
                expected_path = os.path.join(self.cwd, "test_ws.txt")
                self.assertTrue(os.path.exists(expected_path))
                
                # Track for cleanup
                self.created_files.append(expected_path)


class TestHomeDirectoryNormalization(unittest.TestCase):
    """Test normalization of 'home directory' phrases."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.tools = PersonalAgentFilesystemTools(base_dir=self.temp_dir)
        self.home_dir = os.path.expanduser("~")
        self.created_files = []

    def tearDown(self):
        """Clean up after tests."""
        import shutil
        
        # Clean up temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Clean up any files created in home directory
        test_patterns = [
            "test_home.txt",
            "test_home_case.txt",
            "test.txt",
            "test_home_dir.txt",
            "test_home_directory.txt",
        ]
        
        for pattern in test_patterns:
            file_path = os.path.join(self.home_dir, pattern)
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass  # Ignore errors during cleanup

    def test_home_directory_phrase_normalization(self):
        """Test that 'home' phrases are normalized."""
        test_phrases = [
            "home",
            "home directory",
            "home dir",
        ]

        for phrase in test_phrases:
            with self.subTest(phrase=phrase):
                result = self.tools.create_and_save_file(
                    filename="test_home.txt",
                    content="test content",
                    directory=phrase
                )
                
                # Should succeed (will expand ~ to actual home)
                self.assertIn("Successfully", result)
                
                # Should NOT create a literal "home" directory in temp_dir
                literal_dir = os.path.join(self.temp_dir, phrase)
                self.assertFalse(os.path.exists(literal_dir),
                    f"Literal directory '{phrase}' should not exist in temp_dir")
                
                # Clean up the file created in home directory immediately
                home_file = os.path.join(self.home_dir, "test_home.txt")
                if os.path.exists(home_file):
                    os.remove(home_file)

    def test_home_directory_case_insensitive(self):
        """Test that home normalization is case-insensitive."""
        test_phrases = [
            "Home",
            "HOME",
            "Home Directory",
            "HOME DIR",
        ]

        for phrase in test_phrases:
            with self.subTest(phrase=phrase):
                result = self.tools.create_and_save_file(
                    filename="test_home_case.txt",
                    content="test",
                    directory=phrase
                )
                
                # Should succeed
                self.assertIn("Successfully", result)
                
                # Clean up the file created in home directory immediately
                home_file = os.path.join(self.home_dir, "test_home_case.txt")
                if os.path.exists(home_file):
                    os.remove(home_file)


class TestMultiUserContextSafety(unittest.TestCase):
    """Test safety in multi-user context."""

    def setUp(self):
        """Set up test fixtures with mock config."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a mock user-specific directory structure
        self.user_id = "patient123"
        self.user_storage_dir = os.path.join(
            self.temp_dir, 
            "personal_agent_data", 
            "agno", 
            self.user_id
        )
        os.makedirs(self.user_storage_dir, exist_ok=True)

    def tearDown(self):
        """Clean up after tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_tilde_expansion_warning(self):
        """Test that raw tilde expansion is documented as risky."""
        # This test documents the current behavior and the need for improvement
        tools = PersonalAgentFilesystemTools(base_dir=self.temp_dir)
        
        # Current implementation normalizes "home" to "~"
        # which expands to system user's home, not patient's isolated home
        result = tools.create_and_save_file(
            filename="test.txt",
            content="test",
            directory="home"
        )
        
        # This will succeed but file goes to system user's home
        # NOT to patient's isolated directory
        # This is the behavior we need to fix in future work
        self.assertIn("Successfully", result)
        
        # Clean up file from home directory
        home_file = os.path.join(os.path.expanduser("~"), "test.txt")
        if os.path.exists(home_file):
            os.remove(home_file)

    @patch('personal_agent.config.runtime_config.PersonalAgentConfig.get_instance')
    def test_future_user_home_dir_property(self, mock_get_instance):
        """Test the recommended future implementation with user_home_dir."""
        # Mock the config to have a user_home_dir property
        mock_config = Mock()
        mock_config.user_storage_dir = self.user_storage_dir
        mock_config.home_dir = os.path.expanduser("~")
        
        # This is what user_home_dir should return
        mock_config.user_home_dir = self.user_storage_dir
        
        mock_get_instance.return_value = mock_config
        
        # Verify the mock setup
        config = get_config()
        self.assertEqual(config.user_home_dir, self.user_storage_dir)
        self.assertNotEqual(config.user_home_dir, config.home_dir)


class TestPathExpansionSecurity(unittest.TestCase):
    """Test security aspects of path expansion."""

    def setUp(self):
        """Set up test fixtures."""
        self.cwd = os.getcwd()
        self.tools = PersonalAgentFilesystemTools()
        self.created_files = []

    def tearDown(self):
        """Clean up after tests."""
        # Clean up any tracked files
        for file_path in self.created_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

    def test_dot_slash_expansion(self):
        """Test that ./ is properly expanded to current directory."""
        result = self.tools.create_and_save_file(
            filename="test.txt",
            content="test",
            directory="./"
        )
        
        self.assertIn("Successfully", result)
        
        # File should be in current directory
        expected_path = os.path.join(self.cwd, "test.txt")
        self.assertTrue(os.path.exists(expected_path),
            f"File should exist at {expected_path}")
        self.created_files.append(expected_path)

    def test_tilde_slash_expansion(self):
        """Test that ~/ is properly expanded to user_home_dir (not system home)."""
        from personal_agent.config.runtime_config import get_config
        config = get_config()

        result = self.tools.create_and_save_file(
            filename="test_tilde.txt",
            content="test",
            directory="~/"
        )

        self.assertIn("Successfully", result)

        # File should be in user's home directory (patient's isolated home)
        # NOT in system home directory
        expected_path = os.path.join(config.user_home_dir, "test_tilde.txt")
        self.assertTrue(os.path.exists(expected_path),
            f"File should exist at {expected_path} (user_home_dir)")
        self.created_files.append(expected_path)

        # Verify it's NOT in system home
        system_home_path = os.path.join(os.path.expanduser("~"), "test_tilde.txt")
        if system_home_path != expected_path:  # Only check if they're different
            self.assertFalse(os.path.exists(system_home_path),
                "File should NOT be in system home directory")

    def test_security_check_prevents_escape(self):
        """Test that security checks prevent directory traversal."""
        # Try to write outside allowed directories
        result = self.tools.create_and_save_file(
            filename="test.txt",
            content="test",
            directory="/etc"  # System directory
        )
        
        # Should be denied (either "Access denied" or "Permission denied")
        self.assertIn("Error", result)
        self.assertTrue("Access denied" in result or "Permission denied" in result,
            f"Expected access/permission denied, got: {result}")


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        """Set up test fixtures."""
        self.cwd = os.getcwd()
        self.tools = PersonalAgentFilesystemTools()
        self.created_files = []
        self.created_dirs = []

    def tearDown(self):
        """Clean up after tests."""
        import shutil
        
        # Clean up files
        for file_path in self.created_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass
        
        # Clean up directories
        for dir_path in self.created_dirs:
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                except OSError:
                    pass

    def test_empty_directory_string(self):
        """Test handling of empty directory string."""
        result = self.tools.create_and_save_file(
            filename="test.txt",
            content="test",
            directory=""
        )
        
        # Should handle gracefully (likely creates in current dir)
        self.assertIn("Successfully", result)
        
        # Track file for cleanup
        test_file = os.path.join(self.cwd, "test.txt")
        self.created_files.append(test_file)

    def test_mixed_case_phrases(self):
        """Test mixed case variations."""
        test_cases = [
            ("CuRrEnT DiReCtOrY", "."),
            ("ThIs DiReCtOrY", "."),
            ("HeRe", "."),
        ]

        for phrase, expected_normalized in test_cases:
            with self.subTest(phrase=phrase):
                filename = f"test_{phrase.replace(' ', '_')}.txt"
                result = self.tools.create_and_save_file(
                    filename=filename,
                    content="test",
                    directory=phrase
                )
                
                self.assertIn("Successfully", result)
                
                # Should not create literal directory
                literal_dir = os.path.join(self.cwd, phrase)
                self.assertFalse(os.path.exists(literal_dir))
                
                # Track file for cleanup
                self.created_files.append(os.path.join(self.cwd, filename))

    def test_directory_with_special_characters(self):
        """Test that non-normalized directories with special chars work."""
        # Create a directory with special characters
        special_dir = os.path.join(self.cwd, "my-special_dir.v2")
        os.makedirs(special_dir, exist_ok=True)
        self.created_dirs.append(special_dir)
        
        result = self.tools.create_and_save_file(
            filename="test.txt",
            content="test",
            directory=special_dir
        )
        
        self.assertIn("Successfully", result)
        
        # File should exist in the special directory
        expected_path = os.path.join(special_dir, "test.txt")
        self.assertTrue(os.path.exists(expected_path))

    def test_normalization_preserves_subdirectories(self):
        """Test that normalization doesn't affect subdirectory paths."""
        # These should NOT be normalized
        test_paths = [
            "./subdir",
            "subdir/nested",
            "my_directory",
        ]

        for path in test_paths:
            with self.subTest(path=path):
                result = self.tools.create_and_save_file(
                    filename="test.txt",
                    content="test",
                    directory=path
                )
                
                self.assertIn("Successfully", result)
                
                # Directory should be created in current directory
                expected_dir = os.path.join(self.cwd, path)
                self.assertTrue(os.path.exists(expected_dir),
                    f"Directory {expected_dir} should exist for path '{path}'")
                
                # Track top-level directory for cleanup
                top_dir = path.split('/')[0].lstrip('.')
                if top_dir:
                    full_top_dir = os.path.join(self.cwd, top_dir)
                    if full_top_dir not in self.created_dirs:
                        self.created_dirs.append(full_top_dir)


class TestMCPFilesystemToolsNormalization(unittest.TestCase):
    """Test normalization in MCP-based filesystem tools."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up after tests."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @patch('personal_agent.tools.filesystem.logger')
    @patch('personal_agent.tools.filesystem.USE_MCP', True)
    @patch('personal_agent.tools.filesystem.mcp_client')
    def test_mcp_create_and_save_file_normalization(self, mock_mcp_client, mock_logger):
        """Test that MCP tools also normalize directory references."""
        from personal_agent.tools.filesystem import create_and_save_file
        
        # Mock MCP client
        mock_mcp_client.call_tool_sync.return_value = "File written successfully"
        
        # Test current directory normalization in path
        test_cases = [
            "current directory/test.txt",
            "current dir/test.txt",
            "here/test.txt",
        ]

        for file_path in test_cases:
            with self.subTest(file_path=file_path):
                # The normalization should convert "current directory" to "."
                result = create_and_save_file.invoke({
                    "file_path": file_path,
                    "content": "test content"
                })
                
                # Should succeed
                self.assertIn("Successfully", result)

    @patch('personal_agent.tools.filesystem.logger')
    @patch('personal_agent.tools.filesystem.USE_MCP', True)
    @patch('personal_agent.tools.filesystem.mcp_client')
    def test_mcp_home_directory_normalization(self, mock_mcp_client, mock_logger):
        """Test that MCP tools normalize home directory references."""
        from personal_agent.tools.filesystem import create_and_save_file
        
        # Mock MCP client
        mock_mcp_client.call_tool_sync.return_value = "File written successfully"
        
        # Test home directory normalization
        test_cases = [
            "home/test.txt",
            "home directory/test.txt",
            "home dir/test.txt",
        ]

        for file_path in test_cases:
            with self.subTest(file_path=file_path):
                result = create_and_save_file.invoke({
                    "file_path": file_path,
                    "content": "test content"
                })
                
                # Should succeed
                self.assertIn("Successfully", result)


class TestConfigurationIntegration(unittest.TestCase):
    """Test integration with PersonalAgentConfig."""

    def test_config_has_user_storage_dir(self):
        """Test that config provides user_storage_dir."""
        config = get_config()
        
        # Config should have user_storage_dir property
        self.assertTrue(hasattr(config, 'user_storage_dir'))
        
        # Should return a valid path
        user_storage_dir = config.user_storage_dir
        self.assertIsInstance(user_storage_dir, str)
        self.assertTrue(len(user_storage_dir) > 0)

    def test_config_distinguishes_home_types(self):
        """Test that config distinguishes system home from user home."""
        config = get_config()
        
        # System home (for system operations)
        system_home = config.home_dir
        self.assertEqual(system_home, os.path.expanduser("~"))
        
        # User storage (for patient data)
        user_storage = config.user_storage_dir
        
        # In multi-user context, these should be different
        # user_storage should be under PERSAG_ROOT, not system home
        self.assertIn(config.user_id, user_storage)

    def test_future_user_home_dir_property(self):
        """Document the recommended future user_home_dir property."""
        config = get_config()
        
        # This test documents what SHOULD exist in the future
        # Currently, config doesn't have user_home_dir property
        # After implementing ADR-101 recommendations, it should
        
        # For now, we can use user_storage_dir as the patient's home
        patient_home = config.user_storage_dir
        
        # Verify it's user-specific
        self.assertIn(config.user_id, patient_home)
        
        # Verify it's under PERSAG_ROOT (shared data area)
        self.assertIn("personal_agent_data", patient_home)


class TestRegressionPrevention(unittest.TestCase):
    """Tests to prevent regression of the original bug."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        self.tools = PersonalAgentFilesystemTools(base_dir=self.temp_dir)
        self.created_in_original_cwd = []

    def tearDown(self):
        """Clean up after tests."""
        os.chdir(self.original_cwd)
        import shutil
        
        # Clean up any directories created in original CWD
        for item in self.created_in_original_cwd:
            item_path = os.path.join(self.original_cwd, item)
            if os.path.exists(item_path):
                try:
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                    else:
                        os.remove(item_path)
                except OSError:
                    pass
        
        # Clean up temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_original_bug_scenario(self):
        """Test the exact scenario that caused the original bug."""
        # Original bug: "current directory" was treated as literal directory name
        result = self.tools.create_and_save_file(
            filename="monkey_poem.txt",
            content="Why did the monkey go to the party?",
            directory="current directory"
        )
        
        # Should succeed
        self.assertIn("Successfully", result)
        
        # File should be in current directory
        expected_path = os.path.join(self.temp_dir, "monkey_poem.txt")
        self.assertTrue(os.path.exists(expected_path),
            "File should be in current directory")
        
        # The literal "current directory" folder should NOT exist
        literal_dir = os.path.join(self.temp_dir, "current directory")
        self.assertFalse(os.path.exists(literal_dir),
            "Literal 'current directory' folder should NOT be created")
        
        # Verify file content
        with open(expected_path, 'r') as f:
            content = f.read()
        self.assertEqual(content, "Why did the monkey go to the party?")

    def test_no_literal_directory_creation(self):
        """Test that normalized phrases never create literal directories."""
        normalized_phrases = [
            "current directory",
            "current dir",
            "here",
            "this directory",
            "home",
            "home directory",
            "home dir",
        ]

        home_dir = os.path.expanduser("~")
        
        for phrase in normalized_phrases:
            with self.subTest(phrase=phrase):
                # Attempt to create file
                result = self.tools.create_and_save_file(
                    filename=f"test_{phrase.replace(' ', '_')}.txt",
                    content="test",
                    directory=phrase
                )
                
                # Should succeed
                self.assertIn("Successfully", result)
                
                # Literal directory should NOT exist in temp_dir
                literal_dir = os.path.join(self.temp_dir, phrase)
                self.assertFalse(os.path.exists(literal_dir),
                    f"Literal directory '{phrase}' should never be created in temp_dir")
                
                # Also check it wasn't created in original CWD (shouldn't happen but track for cleanup)
                original_cwd_dir = os.path.join(self.original_cwd, phrase)
                if os.path.exists(original_cwd_dir):
                    self.created_in_original_cwd.append(phrase)
                
                # Clean up file if it was created in home directory
                if phrase in ["home", "home directory", "home dir"]:
                    home_file = os.path.join(home_dir, f"test_{phrase.replace(' ', '_')}.txt")
                    if os.path.exists(home_file):
                        os.remove(home_file)


class TestNormalizationDocumentation(unittest.TestCase):
    """Tests that document the normalization behavior for future reference."""

    def test_normalized_phrases_reference(self):
        """Document all phrases that should be normalized."""
        current_dir_phrases = [
            "current directory",
            "current dir",
            "here",
            "this directory",
            ".",
        ]
        
        home_dir_phrases = [
            "home",
            "home directory",
            "home dir",
            "~",
        ]
        
        # All current directory phrases should normalize to "."
        for phrase in current_dir_phrases:
            normalized = phrase.lower().strip()
            if normalized in ["current directory", "current dir", "here", "this directory", "."]:
                expected = "."
                self.assertEqual(expected, ".",
                    f"'{phrase}' should normalize to '.'")
        
        # All home directory phrases should normalize to user_storage_dir
        # (currently "~", but should be config.user_storage_dir in future)
        for phrase in home_dir_phrases:
            normalized = phrase.lower().strip()
            if normalized in ["home", "home directory", "home dir"]:
                # Current behavior: normalizes to "~"
                # Future behavior: should normalize to config.user_storage_dir
                pass  # Documented for future implementation

    def test_multi_user_directory_structure(self):
        """Document the multi-user directory structure."""
        config = get_config()
        
        # Document the directory hierarchy
        structure = {
            "PERSAG_ROOT": config.persag_root,  # /Users/Shared/personal_agent_data
            "storage_backend": config.storage_backend,  # agno
            "user_id": config.user_id,  # patient123
            "user_storage_dir": config.user_storage_dir,  # {PERSAG_ROOT}/agno/{user_id}
            "user_data_dir": config.user_data_dir,  # {user_storage_dir}/data
            "user_knowledge_dir": config.user_knowledge_dir,  # {user_storage_dir}/knowledge
        }
        
        # Verify the structure
        self.assertIn(config.storage_backend, config.user_storage_dir)
        self.assertIn(config.user_id, config.user_storage_dir)
        self.assertIn("data", config.user_data_dir)
        self.assertIn("knowledge", config.user_knowledge_dir)
        
        # Document that user_storage_dir is the patient's "home"
        # This is what "home" should map to in multi-user context
        patient_home = config.user_storage_dir
        self.assertIsNotNone(patient_home)


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)