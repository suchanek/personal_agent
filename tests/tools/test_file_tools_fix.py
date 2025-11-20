#!/usr/bin/env python3
"""
File Tools Fix Test Suite

This test suite verifies the fixes for file-related tool issues:
- PythonTools base_dir using Path objects instead of strings
- Proper path expansion in generated Python code
- Syntax validation of generated code
- Agent instruction improvements for file operations

Tests the fixes documented in ADR-073: File Tools Path Fix

Usage:
    python -m pytest tests/tools/test_file_tools_fix.py -v
    or
    python tests/tools/test_file_tools_fix.py
"""

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.core.agent_instruction_manager import AgentInstructionManager, InstructionLevel
from personal_agent.core.agno_agent import AgnoPersonalAgent


class TestFileToolsFix(unittest.TestCase):
    """Test suite for file tools fixes."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.user_id = "test_user"

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_python_tools_path_object_initialization(self):
        """Test that PythonTools can be initialized with Path objects."""
        from agno.tools.python import PythonTools

        # Test with Path object (should work)
        try:
            tool_path = PythonTools(base_dir=Path("/tmp"))
            # Check that it was created successfully
            self.assertIsNotNone(tool_path)
            print("✅ PythonTools initialized successfully with Path object")
        except Exception as e:
            self.fail(f"PythonTools failed to initialize with Path object: {e}")

        # Test with string - may fail due to type hints but let's see
        try:
            tool_string = PythonTools(base_dir="/tmp")  # type: ignore
            self.assertIsNotNone(tool_string)
            print("✅ PythonTools initialized with string (backward compatibility)")
        except Exception as e:
            print(f"⚠️  PythonTools with string failed as expected: {e}")

    def test_agent_instruction_manager_path_rules(self):
        """Test that instruction manager includes proper path handling rules."""
        manager = AgentInstructionManager(
            instruction_level=InstructionLevel.CONCISE,
            user_id=self.user_id,
            enable_memory=False,
            enable_mcp=False,
            mcp_servers={}
        )

        instructions = manager.create_instructions()

        # Check for path handling instructions
        self.assertIn("os.path.expanduser", instructions, "Instructions should include os.path.expanduser guidance")
        self.assertIn("Path('~/", instructions, "Instructions should include Path expanduser examples")
        self.assertIn("CRITICAL", instructions, "Instructions should emphasize critical path handling")

        # Check for syntax validation rules
        self.assertIn("Syntax", instructions, "Instructions should include syntax validation rules")
        self.assertIn("indentation", instructions, "Instructions should mention proper indentation")

        print("✅ Agent instruction manager includes proper path and syntax rules")

    def test_agent_instruction_levels_include_path_rules(self):
        """Test that all relevant instruction levels include path handling rules."""
        levels_to_test = [InstructionLevel.CONCISE, InstructionLevel.STANDARD, InstructionLevel.EXPLICIT]

        for level in levels_to_test:
            with self.subTest(level=level):
                manager = AgentInstructionManager(
                    instruction_level=level,
                    user_id=self.user_id,
                    enable_memory=False,
                    enable_mcp=False,
                    mcp_servers={}
                )

                instructions = manager.create_instructions()

                # All levels should include path handling for PythonTools
                self.assertIn("PythonTools", instructions, f"{level.name} should mention PythonTools")
                self.assertIn("path expansion", instructions.lower(), f"{level.name} should include path expansion guidance")

        print("✅ All instruction levels include path handling rules")

    def test_path_expansion_examples_in_instructions(self):
        """Test that instructions provide clear examples of correct path handling."""
        manager = AgentInstructionManager(
            instruction_level=InstructionLevel.STANDARD,
            user_id=self.user_id,
            enable_memory=False,
            enable_mcp=False,
            mcp_servers={}
        )

        instructions = manager.create_instructions()

        # Check for specific examples
        self.assertIn("os.path.expanduser('~/", instructions, "Should show os.path.expanduser example")
        self.assertIn("Path('~/", instructions, "Should show Path expanduser example")
        self.assertIn("WRONG:", instructions, "Should show wrong examples")
        self.assertIn("CORRECT:", instructions, "Should show correct examples")

        print("✅ Instructions provide clear path handling examples")

    def test_agent_uses_path_objects_in_code(self):
        """Test that the agent code uses Path objects as fixed."""
        # Read the agent code to verify the fix
        import inspect
        from personal_agent.core.agno_agent import AgnoPersonalAgent

        # Get the source code
        source = inspect.getsource(AgnoPersonalAgent._do_initialization)

        # Check that PythonTools is initialized with Path("/tmp") not "/tmp"
        self.assertIn('base_dir=Path("/tmp")', source,
                     "Agent code should use Path object for PythonTools base_dir")
        self.assertNotIn('base_dir="/tmp"', source,
                        "Agent code should not use string for PythonTools base_dir")

        print("✅ Agent code uses Path objects for PythonTools initialization")

    def test_path_expansion_utility_functions(self):
        """Test that path expansion works correctly."""
        # Test os.path.expanduser
        test_path = "~/test.txt"
        expanded = os.path.expanduser(test_path)
        self.assertNotEqual(expanded, test_path, "os.path.expanduser should expand tilde")
        self.assertTrue(expanded.startswith("/"), "Expanded path should be absolute")

        # Test Path.expanduser
        path_obj = Path(test_path)
        expanded_path = path_obj.expanduser()
        self.assertNotEqual(str(expanded_path), test_path, "Path.expanduser should expand tilde")
        self.assertTrue(str(expanded_path).startswith("/"), "Expanded Path should be absolute")

        print("✅ Path expansion utility functions work correctly")

    def test_syntax_validation_examples(self):
        """Test that the instructions provide proper syntax examples."""
        manager = AgentInstructionManager(
            instruction_level=InstructionLevel.STANDARD,
            user_id=self.user_id,
            enable_memory=False,
            enable_mcp=False,
            mcp_servers={}
        )

        instructions = manager.create_instructions()

        # Check for syntax-related guidance
        syntax_keywords = ["syntax", "indentation", "line continuation", "parentheses"]
        syntax_found = any(keyword in instructions.lower() for keyword in syntax_keywords)

        self.assertTrue(syntax_found, "Instructions should include syntax validation guidance")

        print("✅ Instructions include syntax validation guidance")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)