#!/usr/bin/env python3
"""
Test runner for Personal Agent tests.

This script provides a convenient way to run all tests or specific test categories.
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_test(test_file: Path, description: str = "") -> bool:
    """Run a single test file and return success status."""
    print(f"\n{'='*60}")
    print(f"🧪 Running: {test_file.name}")
    if description:
        print(f"📝 Description: {description}")
    print(f"{'='*60}")

    try:
        # Change to the repo root directory
        repo_root = Path(__file__).parent.parent
        result = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=repo_root,
            capture_output=False,  # Show output in real-time
            text=True,
        )

        if result.returncode == 0:
            print(f"✅ {test_file.name} PASSED")
            return True
        else:
            print(f"❌ {test_file.name} FAILED (exit code: {result.returncode})")
            return False

    except Exception as e:
        print(f"❌ {test_file.name} ERROR: {e}")
        return False


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Run Personal Agent tests")
    parser.add_argument(
        "--category",
        choices=["config", "core", "tools", "web", "integration", "debug", "all"],
        default="all",
        help="Test category to run",
    )
    parser.add_argument(
        "--test", help="Specific test file to run (without .py extension)"
    )
    parser.add_argument("--list", action="store_true", help="List all available tests")

    args = parser.parse_args()

    tests_dir = Path(__file__).parent

    # Define test categories
    test_categories = {
        "config": [
            ("test_config_extraction.py", "Test configuration module extraction"),
            ("test_env_vars.py", "Test environment variable handling"),
        ],
        "core": [
            ("test_agent_init.py", "Test agent initialization"),
            ("test_main_fix.py", "Test main module fixes"),
            ("test_mcp.py", "Test MCP client functionality"),
            ("test_mcp_availability.py", "Test MCP server availability"),
        ],
        "tools": [
            ("test_tools.py", "Test individual tools"),
            ("test_logger_injection.py", "Test logger dependency injection"),
            ("test_github.py", "Test GitHub integration"),
            ("test_comprehensive_research.py", "Test research tool"),
            ("test_file_writing.py", "Test file operations"),
            ("test_file_writing_simple.py", "Test simple file operations"),
        ],
        "web": [
            ("test_web_interface.py", "Test web interface functionality"),
            ("test_web_detailed.py", "Test detailed web operations"),
        ],
        "integration": [
            ("test_refactored_system.py", "Test complete refactored system"),
            ("test_cleanup.py", "Test cleanup functionality"),
            ("test_cleanup_improved.py", "Test improved cleanup"),
        ],
        "debug": [
            ("debug_globals.py", "Debug global variable states"),
            ("debug_memory_tools.py", "Debug memory tools creation"),
            ("debug_tool_call.py", "Debug tool call mechanisms"),
            ("debug_github_direct.py", "Debug GitHub direct access"),
            ("debug_github_tools.py", "Debug GitHub tools"),
        ],
    }

    # List available tests
    if args.list:
        print("📋 Available test categories and tests:")
        for category, tests in test_categories.items():
            print(f"\n🏷️  {category.upper()}:")
            for test_file, description in tests:
                print(f"  - {test_file}: {description}")
        return 0

    # Run specific test
    if args.test:
        test_file = tests_dir / f"{args.test}.py"
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return 1

        success = run_test(test_file, "User-specified test")
        return 0 if success else 1

    # Run tests by category
    if args.category == "all":
        tests_to_run = []
        for category_tests in test_categories.values():
            tests_to_run.extend(category_tests)
    else:
        tests_to_run = test_categories.get(args.category, [])

    if not tests_to_run:
        print(f"❌ No tests found for category: {args.category}")
        return 1

    print(f"🚀 Running {len(tests_to_run)} tests in category: {args.category}")

    passed = 0
    failed = 0

    for test_file, description in tests_to_run:
        test_path = tests_dir / test_file
        if test_path.exists():
            if run_test(test_path, description):
                passed += 1
            else:
                failed += 1
        else:
            print(f"⚠️  Test file not found: {test_file}")
            failed += 1

    # Summary
    print(f"\n{'='*60}")
    print(f"📊 TEST SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(
        f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%"
        if (passed + failed) > 0
        else "No tests run"
    )

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit(main())
