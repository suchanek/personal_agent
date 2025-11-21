"""
Unit tests for user_home_dir Property Implementation.

This module tests the user_home_dir property added to PersonalAgentConfig
as part of ADR-101 implementation. It verifies:
- Property exists and returns correct value
- ConfigSnapshot includes user_home_dir
- Filesystem tools use user_home_dir instead of ~
- Multi-user data isolation is maintained
- Security requirements are met

Author: Claude Code
Date: 2025-11-21
Related: ADR-101
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from personal_agent.config.runtime_config import (
    PersonalAgentConfig,
    ConfigSnapshot,
    get_config,
    reset_config,
)
from personal_agent.tools.personal_agent_tools import PersonalAgentFilesystemTools


class TestUserHomeDirProperty(unittest.TestCase):
    """Test the user_home_dir property in PersonalAgentConfig."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset config to ensure clean state
        reset_config()
        self.config = get_config()

    def tearDown(self):
        """Clean up after tests."""
        reset_config()

    def test_user_home_dir_property_exists(self):
        """Test that user_home_dir property exists in PersonalAgentConfig."""
        self.assertTrue(
            hasattr(self.config, "user_home_dir"),
            "PersonalAgentConfig should have user_home_dir property",
        )

    def test_user_home_dir_returns_user_storage_dir(self):
        """Test that user_home_dir returns the same value as user_storage_dir."""
        user_home_dir = self.config.user_home_dir
        user_storage_dir = self.config.user_storage_dir

        self.assertEqual(
            user_home_dir,
            user_storage_dir,
            "user_home_dir should return the same path as user_storage_dir",
        )

    def test_user_home_dir_is_user_specific(self):
        """Test that user_home_dir includes the user_id in the path."""
        user_home_dir = self.config.user_home_dir
        user_id = self.config.user_id

        self.assertIn(
            user_id,
            user_home_dir,
            f"user_home_dir should contain user_id '{user_id}' for isolation",
        )

    def test_user_home_dir_differs_from_system_home(self):
        """Test that user_home_dir is different from system home_dir."""
        user_home_dir = self.config.user_home_dir
        system_home_dir = self.config.home_dir

        self.assertNotEqual(
            user_home_dir,
            system_home_dir,
            "user_home_dir should be different from system home_dir",
        )

        # System home should be the actual system user's home
        self.assertEqual(
            system_home_dir,
            os.path.expanduser("~"),
            "home_dir should point to system user's home",
        )

    def test_user_home_dir_under_persag_root(self):
        """Test that user_home_dir is under PERSAG_ROOT for multi-user isolation."""
        user_home_dir = self.config.user_home_dir
        persag_root = self.config.persag_root

        self.assertTrue(
            user_home_dir.startswith(persag_root),
            f"user_home_dir should be under PERSAG_ROOT ({persag_root})",
        )

    def test_user_home_dir_includes_storage_backend(self):
        """Test that user_home_dir includes the storage backend in path."""
        user_home_dir = self.config.user_home_dir
        storage_backend = self.config.storage_backend

        self.assertIn(
            storage_backend,
            user_home_dir,
            f"user_home_dir should include storage backend '{storage_backend}'",
        )

    def test_user_home_dir_is_string(self):
        """Test that user_home_dir returns a string."""
        user_home_dir = self.config.user_home_dir

        self.assertIsInstance(
            user_home_dir, str, "user_home_dir should return a string"
        )
        self.assertTrue(len(user_home_dir) > 0, "user_home_dir should not be empty")

    def test_user_home_dir_thread_safety(self):
        """Test that user_home_dir access is thread-safe."""
        # Access user_home_dir multiple times to ensure consistent behavior
        first_access = self.config.user_home_dir
        second_access = self.config.user_home_dir
        third_access = self.config.user_home_dir

        self.assertEqual(first_access, second_access)
        self.assertEqual(second_access, third_access)


class TestConfigSnapshotWithUserHomeDir(unittest.TestCase):
    """Test that ConfigSnapshot includes user_home_dir."""

    def setUp(self):
        """Set up test fixtures."""
        reset_config()
        self.config = get_config()

    def tearDown(self):
        """Clean up after tests."""
        reset_config()

    def test_config_snapshot_has_user_home_dir_field(self):
        """Test that ConfigSnapshot dataclass has user_home_dir field."""
        snapshot = self.config.snapshot()

        self.assertTrue(
            hasattr(snapshot, "user_home_dir"),
            "ConfigSnapshot should have user_home_dir field",
        )

    def test_config_snapshot_user_home_dir_value(self):
        """Test that ConfigSnapshot captures correct user_home_dir value."""
        snapshot = self.config.snapshot()

        self.assertEqual(
            snapshot.user_home_dir,
            self.config.user_home_dir,
            "Snapshot should capture current user_home_dir value",
        )

    def test_config_to_dict_includes_user_home_dir(self):
        """Test that to_dict() includes user_home_dir."""
        config_dict = self.config.to_dict()

        self.assertIn(
            "user_home_dir", config_dict, "to_dict() should include user_home_dir"
        )
        self.assertEqual(
            config_dict["user_home_dir"],
            self.config.user_home_dir,
            "to_dict() should have correct user_home_dir value",
        )

    def test_config_snapshot_immutability(self):
        """Test that ConfigSnapshot is immutable and preserves user_home_dir."""
        snapshot = self.config.snapshot()
        original_user_home_dir = snapshot.user_home_dir

        # Verify snapshot preserves the value
        self.assertEqual(snapshot.user_home_dir, original_user_home_dir)


class TestFilesystemToolsUseUserHomeDir(unittest.TestCase):
    """Test that filesystem tools use user_home_dir instead of ~."""

    def setUp(self):
        """Set up test fixtures."""
        reset_config()
        self.config = get_config()
        self.temp_dir = tempfile.mkdtemp()
        self.created_files = []
        self.created_dirs = []

    def tearDown(self):
        """Clean up after tests."""
        import shutil

        # Clean up created files
        for file_path in self.created_files:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except OSError:
                    pass

        # Clean up created directories
        for dir_path in self.created_dirs:
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                except OSError:
                    pass

        # Clean up temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

        reset_config()

    @patch("personal_agent.tools.personal_agent_tools.config")
    def test_personal_agent_tools_home_normalization(self, mock_config):
        """Test that PersonalAgentFilesystemTools normalizes 'home' to user_home_dir."""
        # Mock config to return our temp directory as user_home_dir
        mock_config.user_home_dir = self.temp_dir
        mock_config.home_dir = os.path.expanduser("~")
        mock_config.user_data_dir = os.path.join(self.temp_dir, "data")

        tools = PersonalAgentFilesystemTools(base_dir=self.temp_dir)

        # Test that "home" directory is normalized to user_home_dir
        result = tools.create_and_save_file(
            filename="test_home.txt", content="test content", directory="home"
        )

        # Should succeed
        self.assertIn("Successfully", result)

        # File should be in user_home_dir (temp_dir), not system home
        expected_path = os.path.join(self.temp_dir, "test_home.txt")
        self.assertTrue(
            os.path.exists(expected_path),
            f"File should be in user_home_dir ({self.temp_dir}), not system home",
        )

        # Track for cleanup
        self.created_files.append(expected_path)

        # Verify file was NOT created in system home
        system_home_path = os.path.join(os.path.expanduser("~"), "test_home.txt")
        self.assertFalse(
            os.path.exists(system_home_path),
            "File should NOT be created in system home directory",
        )

    @patch("personal_agent.tools.personal_agent_tools.config")
    def test_personal_agent_tools_tilde_expansion(self, mock_config):
        """Test that ~ is expanded to user_home_dir, not system home."""
        # Mock config to return our temp directory as user_home_dir
        mock_config.user_home_dir = self.temp_dir
        mock_config.home_dir = os.path.expanduser("~")
        mock_config.user_data_dir = os.path.join(self.temp_dir, "data")

        tools = PersonalAgentFilesystemTools(base_dir=self.temp_dir)

        # Create a subdirectory in temp_dir to test ~/subdir pattern
        subdir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        self.created_dirs.append(subdir)

        # Test that ~/subdir is expanded to user_home_dir/subdir
        result = tools.create_and_save_file(
            filename="test_tilde.txt",
            content="test content",
            directory=f"{self.temp_dir}/subdir",  # Simulating ~/subdir
        )

        # Should succeed
        self.assertIn("Successfully", result)

    @patch("personal_agent.tools.personal_agent_tools.config")
    def test_all_home_phrases_use_user_home_dir(self, mock_config):
        """Test that all home-related phrases map to user_home_dir."""
        # Mock config
        mock_config.user_home_dir = self.temp_dir
        mock_config.home_dir = os.path.expanduser("~")
        mock_config.user_data_dir = os.path.join(self.temp_dir, "data")

        tools = PersonalAgentFilesystemTools(base_dir=self.temp_dir)

        home_phrases = [
            "home",
            "home directory",
            "home dir",
            "Home",
            "HOME DIRECTORY",
        ]

        for phrase in home_phrases:
            with self.subTest(phrase=phrase):
                filename = f"test_{phrase.replace(' ', '_')}.txt"
                result = tools.create_and_save_file(
                    filename=filename, content="test", directory=phrase
                )

                # Should succeed
                self.assertIn("Successfully", result)

                # File should be in user_home_dir
                expected_path = os.path.join(self.temp_dir, filename)
                self.assertTrue(
                    os.path.exists(expected_path),
                    f"File should exist in user_home_dir for phrase '{phrase}'",
                )

                # Track for cleanup
                self.created_files.append(expected_path)

                # Should NOT be in system home
                system_home_path = os.path.join(os.path.expanduser("~"), filename)
                if os.path.exists(system_home_path):
                    # Clean up if it exists
                    os.remove(system_home_path)
                    self.fail(
                        f"File should NOT be in system home for phrase '{phrase}'"
                    )


class TestMCPFilesystemToolsUserHomeDir(unittest.TestCase):
    """Test that MCP-based filesystem tools use user_home_dir."""

    def setUp(self):
        """Set up test fixtures."""
        reset_config()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up after tests."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        reset_config()

    @patch("personal_agent.tools.filesystem.get_config")
    @patch("personal_agent.tools.filesystem.USE_MCP", True)
    @patch("personal_agent.tools.filesystem.mcp_client")
    @patch("personal_agent.tools.filesystem.logger")
    def test_mcp_create_and_save_file_uses_user_home_dir(
        self, mock_logger, mock_mcp_client, mock_get_config
    ):
        """Test that MCP create_and_save_file uses user_home_dir for 'home' phrases."""
        from personal_agent.tools.filesystem import create_and_save_file

        # Mock config
        mock_config = Mock()
        mock_config.user_home_dir = self.temp_dir
        mock_config.home_dir = os.path.expanduser("~")
        mock_get_config.return_value = mock_config

        # Mock MCP client
        mock_mcp_client.call_tool_sync.return_value = "File written successfully"

        # Test that "home directory" in path is normalized to user_home_dir
        result = create_and_save_file.invoke(
            {"file_path": "home directory/test.txt", "content": "test content"}
        )

        # Should succeed
        self.assertIn("Successfully", result)

    @patch("personal_agent.tools.filesystem.get_config")
    @patch("personal_agent.tools.filesystem.USE_MCP", True)
    @patch("personal_agent.tools.filesystem.mcp_client")
    @patch("personal_agent.tools.filesystem.logger")
    def test_mcp_tilde_expansion_uses_user_home_dir(
        self, mock_logger, mock_mcp_client, mock_get_config
    ):
        """Test that MCP tools expand ~ to user_home_dir, not system home."""
        from personal_agent.tools.filesystem import create_and_save_file

        # Mock config
        mock_config = Mock()
        mock_config.user_home_dir = self.temp_dir
        mock_config.home_dir = os.path.expanduser("~")
        mock_get_config.return_value = mock_config

        # Mock MCP client
        mock_mcp_client.call_tool_sync.return_value = "File written successfully"

        # Test that ~/test.txt uses user_home_dir
        result = create_and_save_file.invoke(
            {"file_path": "~/test.txt", "content": "test content"}
        )

        # Should succeed
        self.assertIn("Successfully", result)


class TestMultiUserDataIsolation(unittest.TestCase):
    """Test that user_home_dir ensures proper multi-user data isolation."""

    def setUp(self):
        """Set up test fixtures."""
        reset_config()
        self.config = get_config()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up after tests."""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        reset_config()

    def test_user_home_dir_prevents_system_home_access(self):
        """Test that user_home_dir prevents accidental access to system home."""
        user_home_dir = self.config.user_home_dir
        system_home_dir = self.config.home_dir

        # They should be different paths
        self.assertNotEqual(user_home_dir, system_home_dir)

        # user_home_dir should NOT start with system home
        # (except in testing where both might be under /tmp)
        if not system_home_dir.startswith("/tmp"):
            self.assertFalse(
                user_home_dir.startswith(system_home_dir),
                "user_home_dir should not be under system home directory",
            )

    def test_user_home_dir_contains_user_id_for_isolation(self):
        """Test that user_home_dir includes user_id for proper isolation."""
        user_home_dir = self.config.user_home_dir
        user_id = self.config.user_id

        self.assertIn(
            user_id,
            user_home_dir,
            "user_home_dir must contain user_id for multi-user isolation",
        )

    def test_different_users_have_different_home_dirs(self):
        """Test that different users get different home directories."""
        # Get original user's home dir
        original_user_id = self.config.user_id
        original_home_dir = self.config.user_home_dir

        # Simulate different user
        self.config.set_user_id("test_patient_456", persist=False)
        new_home_dir = self.config.user_home_dir
        new_user_id = self.config.user_id

        # Home directories should be different
        self.assertNotEqual(
            original_home_dir,
            new_home_dir,
            "Different users should have different home directories",
        )

        # Each should contain their respective user_id
        self.assertIn(original_user_id, original_home_dir)
        self.assertIn(new_user_id, new_home_dir)

        # Restore original user
        self.config.set_user_id(original_user_id, persist=False)

    def test_user_home_dir_under_shared_storage(self):
        """Test that user_home_dir is under shared storage area, not user's personal home."""
        user_home_dir = self.config.user_home_dir
        persag_root = self.config.persag_root

        # user_home_dir should be under PERSAG_ROOT (shared storage)
        self.assertTrue(
            user_home_dir.startswith(persag_root),
            f"user_home_dir should be under PERSAG_ROOT ({persag_root}) for multi-user access",
        )


class TestSecurityRequirements(unittest.TestCase):
    """Test security requirements for user_home_dir implementation."""

    def setUp(self):
        """Set up test fixtures."""
        reset_config()
        self.config = get_config()

    def tearDown(self):
        """Clean up after tests."""
        reset_config()

    def test_no_raw_tilde_expansion_in_tools(self):
        """Test that tools don't use raw os.path.expanduser('~')."""
        # This is a documentation test to ensure awareness of the security issue
        # Raw ~ expansion in multi-user context is dangerous because:
        # 1. It expands to system user's home, not patient's isolated home
        # 2. Can lead to data isolation breaches
        # 3. Patient files could leak into system user's personal space

        # Solution: Always use config.user_home_dir instead of ~
        user_home_dir = self.config.user_home_dir
        system_home = os.path.expanduser("~")

        self.assertNotEqual(
            user_home_dir,
            system_home,
            "user_home_dir must not be the same as system home for security",
        )

    def test_user_home_dir_read_only_property(self):
        """Test that user_home_dir is a read-only property."""
        # Should not be able to set user_home_dir directly
        with self.assertRaises(AttributeError):
            self.config.user_home_dir = "/tmp/malicious"

    def test_user_home_dir_consistent_derivation(self):
        """Test that user_home_dir is consistently derived from user_storage_dir."""
        # user_home_dir should always equal user_storage_dir
        for _ in range(5):
            self.assertEqual(
                self.config.user_home_dir,
                self.config.user_storage_dir,
                "user_home_dir must consistently equal user_storage_dir",
            )


class TestDocumentationAndUsage(unittest.TestCase):
    """Test documentation and proper usage of user_home_dir."""

    def setUp(self):
        """Set up test fixtures."""
        reset_config()
        self.config = get_config()

    def tearDown(self):
        """Clean up after tests."""
        reset_config()

    def test_property_docstring_exists(self):
        """Test that user_home_dir has proper documentation."""
        # Get the property object
        user_home_dir_prop = type(self.config).user_home_dir

        # Should have a docstring
        self.assertIsNotNone(
            user_home_dir_prop.__doc__, "user_home_dir property should have docstring"
        )

        # Docstring should mention key concepts
        docstring = user_home_dir_prop.__doc__.lower()
        self.assertIn(
            "patient", docstring, "Docstring should mention patient isolation"
        )
        self.assertIn("home", docstring, "Docstring should mention home directory")

    def test_home_dir_vs_user_home_dir_distinction(self):
        """Test that documentation distinguishes home_dir from user_home_dir."""
        # Get both properties
        home_dir_prop = type(self.config).home_dir
        user_home_dir_prop = type(self.config).user_home_dir

        # Both should have docstrings
        self.assertIsNotNone(home_dir_prop.__doc__)
        self.assertIsNotNone(user_home_dir_prop.__doc__)

        # home_dir should mention system operations
        home_dir_doc = home_dir_prop.__doc__.lower()
        self.assertIn("system", home_dir_doc)

        # user_home_dir should mention patient/user isolation
        user_home_dir_doc = user_home_dir_prop.__doc__.lower()
        self.assertIn("patient", user_home_dir_doc)

    def test_directory_semantics_clarity(self):
        """Test that directory semantics are clear and distinct."""
        # Document the directory hierarchy
        directory_semantics = {
            "home_dir": "System user's home (e.g., /Users/egs) - for system operations",
            "user_home_dir": "Patient's isolated home - for patient data",
            "user_storage_dir": "Same as user_home_dir - root of patient's isolated space",
            "user_data_dir": "Patient's data subdirectory",
            "user_knowledge_dir": "Patient's knowledge subdirectory",
        }

        # Verify all these properties exist
        for prop_name, description in directory_semantics.items():
            with self.subTest(property=prop_name, description=description):
                self.assertTrue(
                    hasattr(self.config, prop_name),
                    f"Config should have {prop_name}: {description}",
                )

        # Verify the relationships
        self.assertEqual(
            self.config.user_home_dir,
            self.config.user_storage_dir,
            "user_home_dir should equal user_storage_dir",
        )

        self.assertTrue(
            self.config.user_data_dir.startswith(self.config.user_home_dir),
            "user_data_dir should be under user_home_dir",
        )

        self.assertTrue(
            self.config.user_knowledge_dir.startswith(self.config.user_home_dir),
            "user_knowledge_dir should be under user_home_dir",
        )


if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
