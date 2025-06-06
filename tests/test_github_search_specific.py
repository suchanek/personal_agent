#!/usr/bin/env python3
"""Test script to debug specific GitHub repository search."""

import json
import logging
import sys
from pathlib import Path

# Add the package path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.tools.web import github_search

# Set up logging to see what's happening
logging.basicConfig(level=logging.DEBUG)


def test_specific_repo_search():
    """Test searching for the specific suchanek/proteusPy repository."""

    print("=== Testing specific repository search ===")

    # Test 1: Direct repository search
    print("\n1. Searching for 'suchanek/proteusPy' directly:")
    result1 = github_search.entrypoint("suchanek/proteusPy")
    print(f"Result 1:\n{result1}")

    # Test 2: Search within the specific repo
    print("\n2. Searching within repo 'suchanek/proteusPy':")
    result2 = github_search.entrypoint("proteus", "suchanek/proteusPy")
    print(f"Result 2:\n{result2}")

    # Test 3: Search for user 'suchanek'
    print("\n3. Searching for user 'suchanek':")
    result3 = github_search.entrypoint("user:suchanek")
    print(f"Result 3:\n{result3}")

    # Test 4: Search for 'proteusPy' with repo qualifier
    print("\n4. Searching for 'repo:suchanek/proteusPy':")
    result4 = github_search.entrypoint("repo:suchanek/proteusPy")
    print(f"Result 4:\n{result4}")

    # Test 5: Search for proteusPy in repositories
    print("\n5. Searching for 'proteusPy in:name':")
    result5 = github_search.entrypoint("proteusPy in:name")
    print(f"Result 5:\n{result5}")


if __name__ == "__main__":
    test_specific_repo_search()
