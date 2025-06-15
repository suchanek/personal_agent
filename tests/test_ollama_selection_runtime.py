#!/usr/bin/env python
"""
Test script for validating the Ollama server selection in agno_main.py.

This script runs the agent with both local and remote Ollama options
and captures the output to verify the correct server is being used.
"""

import os
import subprocess
import sys
import time
from pathlib import Path

# Add the src directory to the Python path
src_dir = str(Path(__file__).parent.parent / "src")
sys.path.insert(0, src_dir)


def run_command_with_timeout(cmd, timeout=3):
    """Run a command and kill it after the timeout."""
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        universal_newlines=True,
    )

    # Collect output for a few seconds
    output = []
    start_time = time.time()
    while time.time() - start_time < timeout:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            output.append(line.strip())
            print(line.strip())

    # Kill the process if it's still running
    if process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            process.kill()

    return "\n".join(output)


def test_ollama_selection_runtime():
    """Test the --remote-ollama flag with actual agent execution."""
    print("\n=== Testing Ollama Server Selection with Runtime Execution ===\n")

    # Test 1: Run with local Ollama (default)
    print("\n=== Test 1: Running with local Ollama (default) ===\n")
    cmd = ["python", "-m", "personal_agent.agno_main", "--cli"]
    output = run_command_with_timeout(cmd)

    # Verify the local Ollama message is in the output
    if "Using local Ollama at: http://localhost:11434" in output:
        print("\n✅ Successfully verified local Ollama is used by default")
    else:
        print("\n❌ Failed to verify local Ollama usage")

    time.sleep(1)  # Brief pause between tests

    # Test 2: Run with remote Ollama flag
    print("\n=== Test 2: Running with remote Ollama flag ===\n")
    cmd = ["python", "-m", "personal_agent.agno_main", "--cli", "--remote-ollama"]
    output = run_command_with_timeout(cmd)

    # Verify the remote Ollama message is in the output
    if "Using remote Ollama at: http://tesla.local:11434" in output:
        print(
            "\n✅ Successfully verified remote Ollama is used with --remote-ollama flag"
        )
    else:
        print("\n❌ Failed to verify remote Ollama usage")

    print("\n=== Ollama server selection runtime tests completed ===")


if __name__ == "__main__":
    # Activate virtual environment if needed
    if "VIRTUAL_ENV" not in os.environ:
        print(
            "Note: It's recommended to run this test within the activated virtual environment"
        )
        print("You can activate it with: source .venv/bin/activate")

    test_ollama_selection_runtime()
