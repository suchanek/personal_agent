#!/usr/bin/env python3
"""
Test script to verify the memory restatement fix works correctly.

This script tests the _restate_user_fact function to ensure it properly converts
first-person statements to third-person for memory storage.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_restate_user_fact():
    """Test the _restate_user_fact function with various inputs."""

    # Import the function from the fixed file
    from personal_agent.team.specialized_agents import _restate_user_fact

    test_cases = [
        # (input, expected_output, description)
        (
            "I have a pet dog named snoopy",
            "test_user has a pet dog named snoopy",
            "Basic 'I have' conversion",
        ),
        (
            "I am a software engineer",
            "test_user is a software engineer",
            "'I am' conversion",
        ),
        ("I was born in 1990", "test_user was born in 1990", "'I was' conversion"),
        (
            "I'm 30 years old",
            "test_user is 30 years old",
            "'I'm' contraction conversion",
        ),
        (
            "I've been to Paris",
            "test_user has been to Paris",
            "'I've' contraction conversion",
        ),
        (
            "My favorite color is blue",
            "test_user's favorite color is blue",
            "'My' possessive conversion",
        ),
        (
            "I like hiking and reading",
            "test_user like hiking and reading",
            "Simple 'I' conversion",
        ),
        ("This is mine", "This is test_user's", "'Mine' possessive conversion"),
        ("I did it myself", "test_user did it test_user", "'Myself' conversion"),
    ]

    user_id = "test_user"

    print("🧪 Testing Memory Restatement Fix")
    print("=" * 50)

    all_passed = True

    for i, (input_text, expected, description) in enumerate(test_cases):
        result = _restate_user_fact(input_text, user_id)
        passed = result == expected

        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{i}. {description}")
        print(f"   Input:    '{input_text}'")
        print(f"   Expected: '{expected}'")
        print(f"   Got:      '{result}'")
        print(f"   Status:   {status}")
        print()

        if not passed:
            all_passed = False

    print("=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED! The memory restatement fix is working correctly.")
        print()
        print("✅ Memories will now be stored in third-person format:")
        print("   Input: 'I have a pet dog named snoopy'")
        print("   Stored: 'test_user has a pet dog named snoopy'")
        print(
            "   Presented: 'you have a pet dog named snoopy' (converted by presentation layer)"
        )
    else:
        print("❌ SOME TESTS FAILED! Please review the _restate_user_fact function.")

    return all_passed


if __name__ == "__main__":
    success = test_restate_user_fact()
    sys.exit(0 if success else 1)
