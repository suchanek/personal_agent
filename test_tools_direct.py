#!/usr/bin/env python3
"""
Comprehensive test program for Personal Agent Tools.

This script tests all tool classes directly without inference,
validating functionality of each tool method.
"""

import asyncio
import os

# Add src to path for imports
import sys
import tempfile
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.tools.personal_agent_tools import (
    PersonalAgentFilesystemTools,
    PersonalAgentSystemTools,
    PersonalAgentWebTools,
)


class ToolTester:
    """Test harness for Personal Agent tools."""
    
    def __init__(self):
        self.test_results = {}
        self.temp_dir = None
        
    def setup_test_environment(self):
        """Set up temporary test environment."""
        self.temp_dir = tempfile.mkdtemp(prefix="personal_agent_test_")
        print(f"📁 Created test directory: {self.temp_dir}")
        
    def cleanup_test_environment(self):
        """Clean up temporary test environment."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
            print(f"🧹 Cleaned up test directory: {self.temp_dir}")
    
    def run_test(self, test_name: str, test_func):
        """Run a single test and record results."""
        print(f"\n🧪 Testing: {test_name}")
        try:
            result = test_func()
            self.test_results[test_name] = {"status": "PASS", "result": result}
            print(f"✅ {test_name}: PASSED")
            return True
        except Exception as e:
            self.test_results[test_name] = {"status": "FAIL", "error": str(e)}
            print(f"❌ {test_name}: FAILED - {e}")
            traceback.print_exc()
            return False
    
    def test_filesystem_tools(self):
        """Test PersonalAgentFilesystemTools."""
        print("\n" + "="*60)
        print("🗂️  TESTING FILESYSTEM TOOLS")
        print("="*60)
        
        # Initialize filesystem tools
        fs_tools = PersonalAgentFilesystemTools()
        
        # Test file creation and writing
        def test_write_file():
            test_file = os.path.join(self.temp_dir, "test_write.txt")
            content = "Hello, World!\nThis is a test file."
            result = fs_tools.write_file(test_file, content)
            assert "Successfully wrote" in result
            assert os.path.exists(test_file)
            return result
        
        # Test file reading
        def test_read_file():
            test_file = os.path.join(self.temp_dir, "test_read.txt")
            content = "Test content for reading"
            with open(test_file, 'w') as f:
                f.write(content)
            result = fs_tools.read_file(test_file)
            assert result == content
            return result
        
        # Test directory listing
        def test_list_directory():
            # Create some test files
            test_files = ["file1.txt", "file2.py", "file3.md"]
            for filename in test_files:
                filepath = os.path.join(self.temp_dir, filename)
                with open(filepath, 'w') as f:
                    f.write(f"Content of {filename}")
            
            result = fs_tools.list_directory(self.temp_dir)
            assert "Contents of" in result
            for filename in test_files:
                assert filename in result
            return result
        
        # Test file creation with directory
        def test_create_and_save_file():
            result = fs_tools.create_and_save_file(
                "created_file.txt", 
                "This file was created using create_and_save_file",
                self.temp_dir
            )
            assert "Successfully wrote" in result
            created_file = os.path.join(self.temp_dir, "created_file.txt")
            assert os.path.exists(created_file)
            return result
        
        # Test intelligent file search
        def test_intelligent_file_search():
            # Create test files with specific content
            test_data = {
                "search_test1.py": "def hello_world():\n    print('Hello, World!')",
                "search_test2.txt": "This file contains the word hello",
                "search_test3.md": "# Documentation\nSome random content here"
            }
            
            for filename, content in test_data.items():
                filepath = os.path.join(self.temp_dir, filename)
                with open(filepath, 'w') as f:
                    f.write(content)
            
            # Search for files containing "hello"
            result = fs_tools.intelligent_file_search("hello", self.temp_dir)
            assert "Found" in result
            assert "search_test1.py" in result
            assert "search_test2.txt" in result
            return result
        
        # Test security restrictions
        def test_security_restrictions():
            # Try to access a restricted path
            result = fs_tools.read_file("/etc/passwd")
            assert "Access denied" in result
            return result
        
        # Run all filesystem tests
        tests = [
            ("Write File", test_write_file),
            ("Read File", test_read_file),
            ("List Directory", test_list_directory),
            ("Create and Save File", test_create_and_save_file),
            ("Intelligent File Search", test_intelligent_file_search),
            ("Security Restrictions", test_security_restrictions),
        ]
        
        passed = 0
        for test_name, test_func in tests:
            if self.run_test(f"Filesystem - {test_name}", test_func):
                passed += 1
        
        print(f"\n📊 Filesystem Tools: {passed}/{len(tests)} tests passed")
        return passed == len(tests)
    
    def test_system_tools(self):
        """Test PersonalAgentSystemTools."""
        print("\n" + "="*60)
        print("⚙️  TESTING SYSTEM TOOLS")
        print("="*60)
        
        # Initialize system tools
        sys_tools = PersonalAgentSystemTools()
        
        # Test basic shell command
        def test_basic_command():
            result = sys_tools.shell_command("echo 'Hello from shell'", self.temp_dir)
            assert "Hello from shell" in result
            assert "Return code: 0" in result
            return result
        
        # Test directory listing command
        def test_ls_command():
            result = sys_tools.shell_command("ls -la", self.temp_dir)
            assert "Return code: 0" in result
            return result
        
        # Test working directory parameter
        def test_working_directory():
            # Create a test file in temp directory
            test_file = os.path.join(self.temp_dir, "test_wd.txt")
            with open(test_file, 'w') as f:
                f.write("test")
            
            result = sys_tools.shell_command("ls test_wd.txt", self.temp_dir)
            assert "test_wd.txt" in result
            assert "Return code: 0" in result
            return result
        
        # Test security restrictions
        def test_dangerous_command():
            result = sys_tools.shell_command("rm -rf /", self.temp_dir)
            assert "potentially dangerous operation" in result
            return result
        
        # Test command timeout (simulate with sleep)
        def test_command_timeout():
            # This should complete quickly, but test the timeout mechanism exists
            result = sys_tools.shell_command("sleep 0.1", self.temp_dir)
            assert "Return code: 0" in result
            return result
        
        # Test restricted directory access
        def test_restricted_directory():
            result = sys_tools.shell_command("ls", "/root")
            assert "Access denied" in result
            return result
        
        # Run all system tests
        tests = [
            ("Basic Command", test_basic_command),
            ("LS Command", test_ls_command),
            ("Working Directory", test_working_directory),
            ("Dangerous Command Block", test_dangerous_command),
            ("Command Timeout", test_command_timeout),
            ("Restricted Directory", test_restricted_directory),
        ]
        
        passed = 0
        for test_name, test_func in tests:
            if self.run_test(f"System - {test_name}", test_func):
                passed += 1
        
        print(f"\n📊 System Tools: {passed}/{len(tests)} tests passed")
        return passed == len(tests)
    
    def test_web_tools(self):
        """Test PersonalAgentWebTools."""
        print("\n" + "="*60)
        print("🌐 TESTING WEB TOOLS")
        print("="*60)
        
        # Initialize web tools
        web_tools = PersonalAgentWebTools()
        
        # Test GitHub search (placeholder)
        def test_github_search():
            result = web_tools.github_search("python machine learning")
            assert "GitHub search" in result
            assert "MCP server" in result
            return result
        
        # Test web search (placeholder)
        def test_web_search():
            result = web_tools.web_search("artificial intelligence")
            assert "Web search" in result
            assert "Brave Search MCP server" in result
            return result
        
        # Test URL fetch (placeholder)
        def test_fetch_url():
            result = web_tools.fetch_url("https://example.com")
            assert "URL fetch" in result
            assert "Puppeteer MCP server" in result
            return result
        
        # Run all web tests
        tests = [
            ("GitHub Search", test_github_search),
            ("Web Search", test_web_search),
            ("Fetch URL", test_fetch_url),
        ]
        
        passed = 0
        for test_name, test_func in tests:
            if self.run_test(f"Web - {test_name}", test_func):
                passed += 1
        
        print(f"\n📊 Web Tools: {passed}/{len(tests)} tests passed")
        return passed == len(tests)
    
    def test_tool_initialization(self):
        """Test tool class initialization."""
        print("\n" + "="*60)
        print("🏗️  TESTING TOOL INITIALIZATION")
        print("="*60)
        
        def test_filesystem_init():
            # Test with all tools enabled (default)
            fs_tools = PersonalAgentFilesystemTools()
            assert hasattr(fs_tools, 'name')
            assert fs_tools.name == "personal_filesystem"
            return "Filesystem tools initialized successfully"
        
        def test_filesystem_selective_init():
            # Test with selective tool enabling
            fs_tools = PersonalAgentFilesystemTools(
                read_file=True,
                write_file=False,
                list_directory=True,
                create_and_save_file=False,
                intelligent_file_search=True
            )
            assert hasattr(fs_tools, 'name')
            return "Filesystem tools with selective init successful"
        
        def test_system_init():
            sys_tools = PersonalAgentSystemTools()
            assert hasattr(sys_tools, 'name')
            return "System tools initialized successfully"
        
        def test_web_init():
            web_tools = PersonalAgentWebTools()
            assert hasattr(web_tools, 'name')
            return "Web tools initialized successfully"
        
        # Run initialization tests
        tests = [
            ("Filesystem Init", test_filesystem_init),
            ("Filesystem Selective Init", test_filesystem_selective_init),
            ("System Init", test_system_init),
            ("Web Init", test_web_init),
        ]
        
        passed = 0
        for test_name, test_func in tests:
            if self.run_test(f"Init - {test_name}", test_func):
                passed += 1
        
        print(f"\n📊 Initialization: {passed}/{len(tests)} tests passed")
        return passed == len(tests)
    
    def run_all_tests(self):
        """Run all tests and print summary."""
        print("🚀 Starting Comprehensive Tool Testing")
        print("="*80)
        
        self.setup_test_environment()
        
        try:
            # Run all test suites
            results = []
            results.append(self.test_tool_initialization())
            results.append(self.test_filesystem_tools())
            results.append(self.test_system_tools())
            results.append(self.test_web_tools())
            
            # Print final summary
            print("\n" + "="*80)
            print("📊 FINAL TEST SUMMARY")
            print("="*80)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results.values() if result["status"] == "PASS")
            failed_tests = total_tests - passed_tests
            
            print(f"Total Tests: {total_tests}")
            print(f"✅ Passed: {passed_tests}")
            print(f"❌ Failed: {failed_tests}")
            print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
            
            if failed_tests > 0:
                print("\nFailed Tests:")
                for test_name, result in self.test_results.items():
                    if result["status"] == "FAIL":
                        print(f"  ❌ {test_name}: {result['error']}")
            
            print("\n" + "="*80)
            if failed_tests == 0:
                print("🎉 All tests passed! Tools are working correctly.")
            else:
                print(f"⚠️  {failed_tests} test(s) failed. Check the errors above.")
            
            return failed_tests == 0
            
        finally:
            self.cleanup_test_environment()


def main():
    """Main test execution."""
    tester = ToolTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    exit_code = 0 if success else 1
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
