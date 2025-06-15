#!/usr/bin/env python3
"""
Simple comprehensive test for Personal Agent Tools.
Tests all tool functionality using /tmp for writes and /Users/egs for reads.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.tools.personal_agent_tools import (
    PersonalAgentFilesystemTools,
    PersonalAgentSystemTools,
    PersonalAgentWebTools,
)


def test_filesystem_tools():
    """Test all filesystem tool methods."""
    print("\n" + "=" * 60)
    print("🗂️  TESTING FILESYSTEM TOOLS")
    print("=" * 60)

    fs_tools = PersonalAgentFilesystemTools()
    test_dir = "/tmp/personal_agent_test"

    # Ensure test directory exists
    os.makedirs(test_dir, exist_ok=True)

    results = {}

    # Test 1: Write file
    print("\n🧪 Test 1: Write File")
    test_file = f"{test_dir}/test_write.txt"
    content = "Hello, World!\nThis is a test file for Personal Agent tools."
    result = fs_tools.write_file(test_file, content)
    print(f"Result: {result}")
    results["write_file"] = "✅ PASS" if "Successfully wrote" in result else "❌ FAIL"

    # Test 2: Read file
    print("\n🧪 Test 2: Read File")
    result = fs_tools.read_file(test_file)
    print(f"Result: {result[:100]}...")
    results["read_file"] = "✅ PASS" if result == content else "❌ FAIL"

    # Test 3: List directory
    print("\n🧪 Test 3: List Directory")
    result = fs_tools.list_directory(test_dir)
    print(f"Result: {result[:200]}...")
    results["list_directory"] = "✅ PASS" if "Contents of" in result else "❌ FAIL"

    # Test 4: Create and save file
    print("\n🧪 Test 4: Create and Save File")
    result = fs_tools.create_and_save_file(
        "created_file.txt", "Created content", test_dir
    )
    print(f"Result: {result}")
    results["create_and_save_file"] = (
        "✅ PASS" if "Successfully wrote" in result else "❌ FAIL"
    )

    # Test 5: Intelligent file search
    print("\n🧪 Test 5: Intelligent File Search")
    # Create search test files
    search_files = {
        "search1.py": "def hello_world():\n    print('Hello, World!')",
        "search2.txt": "This file contains the word hello",
        "search3.md": "# Documentation\nNo matching content here",
    }

    for filename, file_content in search_files.items():
        with open(f"{test_dir}/{filename}", "w") as f:
            f.write(file_content)

    result = fs_tools.intelligent_file_search("hello", test_dir)
    print(f"Result: {result[:200]}...")
    results["intelligent_file_search"] = (
        "✅ PASS" if "Found" in result or "search1.py" in result else "❌ FAIL"
    )

    # Test 6: Security restrictions
    print("\n🧪 Test 6: Security Restrictions")
    result = fs_tools.read_file("/etc/passwd")
    print(f"Result: {result}")
    results["security"] = "✅ PASS" if "Access denied" in result else "❌ FAIL"

    # Summary
    print(f"\n📊 Filesystem Tools Summary:")
    for test, status in results.items():
        print(f"  {test}: {status}")

    return results


def test_system_tools():
    """Test all system tool methods."""
    print("\n" + "=" * 60)
    print("⚙️  TESTING SYSTEM TOOLS")
    print("=" * 60)

    sys_tools = PersonalAgentSystemTools()
    test_dir = "/tmp/personal_agent_test"

    results = {}

    # Test 1: Basic command
    print("\n🧪 Test 1: Basic Shell Command")
    result = sys_tools.shell_command("echo 'Hello from shell'", test_dir)
    print(f"Result: {result[:200]}...")
    results["basic_command"] = (
        "✅ PASS"
        if "Hello from shell" in result and "Return code: 0" in result
        else "❌ FAIL"
    )

    # Test 2: Directory listing
    print("\n🧪 Test 2: Directory Listing Command")
    result = sys_tools.shell_command("ls -la", test_dir)
    print(f"Result: {result[:200]}...")
    results["ls_command"] = "✅ PASS" if "Return code: 0" in result else "❌ FAIL"

    # Test 3: Working directory
    print("\n🧪 Test 3: Working Directory Test")
    with open(f"{test_dir}/test_wd.txt", "w") as f:
        f.write("test content")
    result = sys_tools.shell_command("ls test_wd.txt", test_dir)
    print(f"Result: {result[:200]}...")
    results["working_directory"] = (
        "✅ PASS"
        if "test_wd.txt" in result and "Return code: 0" in result
        else "❌ FAIL"
    )

    # Test 4: Dangerous command blocking
    print("\n🧪 Test 4: Dangerous Command Block")
    result = sys_tools.shell_command("rm -rf /", test_dir)
    print(f"Result: {result}")
    results["dangerous_command"] = (
        "✅ PASS" if "potentially dangerous operation" in result else "❌ FAIL"
    )

    # Test 5: Quick command
    print("\n🧪 Test 5: Quick Command")
    result = sys_tools.shell_command("pwd", test_dir)
    print(f"Result: {result[:200]}...")
    results["quick_command"] = "✅ PASS" if "Return code: 0" in result else "❌ FAIL"

    # Test 6: Restricted directory
    print("\n🧪 Test 6: Restricted Directory Access")
    result = sys_tools.shell_command("ls", "/root")
    print(f"Result: {result}")
    results["restricted_directory"] = (
        "✅ PASS" if "Access denied" in result else "❌ FAIL"
    )

    # Summary
    print(f"\n📊 System Tools Summary:")
    for test, status in results.items():
        print(f"  {test}: {status}")

    return results


def test_web_tools():
    """Test all web tool methods."""
    print("\n" + "=" * 60)
    print("🌐 TESTING WEB TOOLS")
    print("=" * 60)

    web_tools = PersonalAgentWebTools()
    results = {}

    # Test 1: GitHub search
    print("\n🧪 Test 1: GitHub Search")
    result = web_tools.github_search("python machine learning")
    print(f"Result: {result}")
    results["github_search"] = (
        "✅ PASS" if "GitHub search" in result and "MCP server" in result else "❌ FAIL"
    )

    # Test 2: Web search
    print("\n🧪 Test 2: Web Search")
    result = web_tools.web_search("artificial intelligence")
    print(f"Result: {result}")
    results["web_search"] = (
        "✅ PASS"
        if "Web search" in result and "Brave Search MCP server" in result
        else "❌ FAIL"
    )

    # Test 3: URL fetch
    print("\n🧪 Test 3: Fetch URL")
    result = web_tools.fetch_url("https://example.com")
    print(f"Result: {result}")
    results["fetch_url"] = (
        "✅ PASS"
        if "URL fetch" in result and "Puppeteer MCP server" in result
        else "❌ FAIL"
    )

    # Summary
    print(f"\n📊 Web Tools Summary:")
    for test, status in results.items():
        print(f"  {test}: {status}")

    return results


def test_tool_initialization():
    """Test tool class initialization."""
    print("\n" + "=" * 60)
    print("🏗️  TESTING TOOL INITIALIZATION")
    print("=" * 60)

    results = {}

    # Test 1: Filesystem tools init
    print("\n🧪 Test 1: Filesystem Tools Initialization")
    try:
        fs_tools = PersonalAgentFilesystemTools()
        print(f"✅ Initialized with name: {fs_tools.name}")
        results["filesystem_init"] = "✅ PASS"
    except Exception as e:
        print(f"❌ Failed: {e}")
        results["filesystem_init"] = "❌ FAIL"

    # Test 2: System tools init
    print("\n🧪 Test 2: System Tools Initialization")
    try:
        sys_tools = PersonalAgentSystemTools()
        print(f"✅ Initialized with name: {sys_tools.name}")
        results["system_init"] = "✅ PASS"
    except Exception as e:
        print(f"❌ Failed: {e}")
        results["system_init"] = "❌ FAIL"

    # Test 3: Web tools init
    print("\n🧪 Test 3: Web Tools Initialization")
    try:
        web_tools = PersonalAgentWebTools()
        print(f"✅ Initialized with name: {web_tools.name}")
        results["web_init"] = "✅ PASS"
    except Exception as e:
        print(f"❌ Failed: {e}")
        results["web_init"] = "❌ FAIL"

    # Test 4: Selective initialization
    print("\n🧪 Test 4: Selective Tool Initialization")
    try:
        fs_tools = PersonalAgentFilesystemTools(
            read_file=True,
            write_file=False,
            list_directory=True,
            create_and_save_file=False,
            intelligent_file_search=True,
        )
        print(f"✅ Selective init successful")
        results["selective_init"] = "✅ PASS"
    except Exception as e:
        print(f"❌ Failed: {e}")
        results["selective_init"] = "❌ FAIL"

    # Summary
    print(f"\n📊 Initialization Summary:")
    for test, status in results.items():
        print(f"  {test}: {status}")

    return results


def main():
    """Run all tests and print final summary."""
    print("🚀 Personal Agent Tools - Comprehensive Test Suite")
    print("=" * 80)

    all_results = {}

    # Run all test suites
    all_results.update(test_tool_initialization())
    all_results.update(test_filesystem_tools())
    all_results.update(test_system_tools())
    all_results.update(test_web_tools())

    # Final summary
    print("\n" + "=" * 80)
    print("📊 FINAL TEST SUMMARY")
    print("=" * 80)

    total_tests = len(all_results)
    passed_tests = sum(1 for result in all_results.values() if "✅ PASS" in result)
    failed_tests = total_tests - passed_tests

    print(f"Total Tests: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")

    if failed_tests > 0:
        print("\nFailed Tests:")
        for test_name, result in all_results.items():
            if "❌ FAIL" in result:
                print(f"  ❌ {test_name}")

    print("\n" + "=" * 80)
    if failed_tests == 0:
        print("🎉 All tests passed! Personal Agent tools are working correctly.")
    else:
        print(f"⚠️  {failed_tests} test(s) failed.")

    # Cleanup
    import shutil

    test_dir = "/tmp/personal_agent_test"
    if os.path.exists(test_dir):
        shutil.rmtree(test_dir)
        print(f"🧹 Cleaned up test directory: {test_dir}")

    return failed_tests == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
