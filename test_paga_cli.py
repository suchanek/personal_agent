#!/usr/bin/env python
"""
Test script to verify that the paga_cli command correctly runs in CLI mode.
"""

import os
import sys

from src.personal_agent.agno_main import cli_main

print("Running paga_cli test script...")
print(f"Current arguments: {sys.argv}")

# Add the --remote-ollama flag if not already present
if "--remote-ollama" not in sys.argv:
    sys.argv.append("--remote-ollama")

# Run the CLI main function
cli_main()
