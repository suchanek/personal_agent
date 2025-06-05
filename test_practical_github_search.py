#!/usr/bin/env python3
"""Test practical GitHub search scenarios."""

import sys
from pathlib import Path

# Add the package path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.tools.web import github_search


def test_practical_scenarios():
    """Test practical GitHub search scenarios."""

    print("=== Testing Practical GitHub Search Scenarios ===")

    # Test 1: Find a specific repository
    print("\n1. 🔍 Looking for the proteusPy repository:")
    result1 = github_search.entrypoint("proteusPy")
    print(result1)

    # Test 2: Find repositories by a specific user
    print("\n2. 👤 Finding repositories by user 'suchanek':")
    result2 = github_search.entrypoint("user:suchanek")
    print(result2)

    # Test 3: Search for a popular repository
    print("\n3. 🔥 Searching for React repository:")
    result3 = github_search.entrypoint("react in:name")
    print(result3)

    # Test 4: Search for issues in a specific repo
    print("\n4. 🐛 Finding issues in suchanek/proteusPy:")
    result4 = github_search.entrypoint("bug", "suchanek/proteusPy")
    print(result4)


if __name__ == "__main__":
    test_practical_scenarios()
