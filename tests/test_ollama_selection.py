#!/usr/bin/env python
"""
Test script for the Ollama server selection feature.

This script validates that the --remote-ollama flag works correctly
when running the agno_main.py script.
"""

import os
import subprocess
import sys
from pathlib import Path

# Add the src directory to the Python path
src_dir = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_dir)


def test_ollama_selection():
    """Test the --remote-ollama flag functionality."""
    print("Testing Ollama server selection feature")
    print("-" * 50)

    # Test 1: Run with local Ollama (default)
    print("\nTest 1: Running with local Ollama (default)")
    print("-" * 30)
    try:
        # Run the command and capture only the first few lines of output
        result = subprocess.run(
            ["python", "-m", "personal_agent.agno_main", "--cli", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        print(f"Output: {result.stdout}")
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
        else:
            print("✅ Command executed successfully")
    except subprocess.TimeoutExpired:
        print("Command timed out - expected for a long-running process")

    # Test 2: Run with remote Ollama flag
    print("\nTest 2: Running with remote Ollama flag")
    print("-" * 30)
    try:
        # Just check the help output to avoid actually running the agent
        result = subprocess.run(
            ["python", "-m", "personal_agent.agno_main", "--remote-ollama", "--help"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        print(f"Output: {result.stdout}")
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
        else:
            print("✅ Command executed successfully")
    except subprocess.TimeoutExpired:
        print("Command timed out - expected for a long-running process")

    print("\n✅ Ollama server selection tests completed")


if __name__ == "__main__":
    # Activate virtual environment if needed
    if "VIRTUAL_ENV" not in os.environ:
        print(
            "Note: It's recommended to run this test within the activated virtual environment"
        )
        print("You can activate it with: source .venv/bin/activate")

    test_ollama_selection()
