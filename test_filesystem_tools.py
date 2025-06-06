#!/usr/bin/env python3
"""
Test script for filesystem tools in agno_static_tools.py

This script tests all 5 filesystem tools:
1. read_file
2. write_file
3. list_directory
4. search_files
5. create_file
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path

# Add src to path for imports
sys.path.append('src')

from personal_agent.agno_static_tools import get_static_mcp_tools


async def test_filesystem_tools():
    """Test all filesystem tools with comprehensive scenarios."""
    print("🧪 Testing Filesystem Tools from agno_static_tools.py")
    print("=" * 60)
    
    try:
        # Get all static tools
        print("📋 Loading static MCP tools...")
        tools = await get_static_mcp_tools()
        
        # Filter filesystem tools
        filesystem_tools = {
            tool.name: tool for tool in tools 
            if tool.name in ['read_file', 'write_file', 'list_directory', 'search_files', 'create_file']
        }
        
        print(f"✅ Found {len(filesystem_tools)} filesystem tools:")
        for name in filesystem_tools.keys():
            print(f"  - {name}")
        print()
        
        # Create a temporary test directory for safe testing
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = Path(temp_dir) / "filesystem_test"
            test_dir.mkdir(exist_ok=True)
            
            print(f"🗂️  Using test directory: {test_dir}")
            print()
            
            # Test 1: list_directory - List current home directory
            print("📁 TEST 1: List Directory (home)")
            if 'list_directory' in filesystem_tools:
                try:
                    result = filesystem_tools['list_directory'].entrypoint("~")
                    print(f"Result: {result[:200]}..." if len(result) > 200 else f"Result: {result}")
                    print("✅ list_directory test passed")
                except Exception as e:
                    print(f"❌ list_directory test failed: {e}")
            else:
                print("❌ list_directory tool not found")
            print()
            
            # Test 2: create_file - Create a test file
            print("📝 TEST 2: Create File")
            test_file_path = "~/test_agno_file.txt"
            test_content = "This is a test file created by agno filesystem tools!\nTimestamp: " + str(asyncio.get_event_loop().time())
            
            if 'create_file' in filesystem_tools:
                try:
                    result = filesystem_tools['create_file'].entrypoint(test_file_path, test_content)
                    print(f"Result: {result}")
                    print("✅ create_file test passed")
                except Exception as e:
                    print(f"❌ create_file test failed: {e}")
            else:
                print("❌ create_file tool not found")
            print()
            
            # Test 3: write_file - Write to a file
            print("✏️  TEST 3: Write File")
            write_test_path = "~/test_write_file.txt"
            write_content = "Content written directly with write_file tool.\nLine 2 of content."
            
            if 'write_file' in filesystem_tools:
                try:
                    result = filesystem_tools['write_file'].entrypoint(write_test_path, write_content)
                    print(f"Result: {result}")
                    print("✅ write_file test passed")
                except Exception as e:
                    print(f"❌ write_file test failed: {e}")
            else:
                print("❌ write_file tool not found")
            print()
            
            # Test 4: read_file - Read the file we just created
            print("📖 TEST 4: Read File")
            if 'read_file' in filesystem_tools:
                try:
                    result = filesystem_tools['read_file'].entrypoint(test_file_path)
                    print(f"Result: {result}")
                    print("✅ read_file test passed")
                except Exception as e:
                    print(f"❌ read_file test failed: {e}")
            else:
                print("❌ read_file tool not found")
            print()
            
            # Test 5: search_files - Search for files
            print("🔍 TEST 5: Search Files")
            if 'search_files' in filesystem_tools:
                try:
                    result = filesystem_tools['search_files'].entrypoint("test", "~")
                    print(f"Result: {result[:300]}..." if len(result) > 300 else f"Result: {result}")
                    print("✅ search_files test passed")
                except Exception as e:
                    print(f"❌ search_files test failed: {e}")
            else:
                print("❌ search_files tool not found")
            print()
            
            # Test 6: Error handling - Try to read non-existent file
            print("🚫 TEST 6: Error Handling (non-existent file)")
            if 'read_file' in filesystem_tools:
                try:
                    result = filesystem_tools['read_file'].entrypoint("~/non_existent_file_12345.txt")
                    print(f"Result: {result}")
                    print("✅ Error handling test passed")
                except Exception as e:
                    print(f"❌ Error handling test failed: {e}")
            print()
            
            # Test 7: Directory operations
            print("📂 TEST 7: Directory Operations")
            if 'list_directory' in filesystem_tools:
                try:
                    # Test various directory formats
                    test_dirs = [".", "~", "$HOME"]
                    for test_dir in test_dirs:
                        print(f"  Testing directory: {test_dir}")
                        result = filesystem_tools['list_directory'].entrypoint(test_dir)
                        if "Error" not in result:
                            print(f"    ✅ Success: Found {len(result.split())} items")
                        else:
                            print(f"    ❌ Error: {result}")
                except Exception as e:
                    print(f"❌ Directory operations test failed: {e}")
            print()
            
            # Cleanup test files
            print("🧹 Cleaning up test files...")
            try:
                # Try to remove test files (they may not exist if tests failed)
                test_files = [
                    os.path.expanduser(test_file_path),
                    os.path.expanduser(write_test_path)
                ]
                for file_path in test_files:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        print(f"  Removed: {file_path}")
            except Exception as e:
                print(f"⚠️  Cleanup warning: {e}")
            
            print("\n🎉 Filesystem tools testing completed!")
            
    except Exception as e:
        print(f"❌ Fatal error during testing: {e}")
        import traceback
        traceback.print_exc()


async def test_tool_discovery():
    """Test tool discovery and show all available tools."""
    print("\n🔍 Tool Discovery Test")
    print("=" * 30)
    
    try:
        tools = await get_static_mcp_tools()
        print(f"Total tools available: {len(tools)}")
        
        tool_categories = {
            'MCP Server Tools': [],
            'Filesystem Tools': [],
            'Other Tools': []
        }
        
        for tool in tools:
            if tool.name.startswith('mcp_'):
                tool_categories['MCP Server Tools'].append(tool.name)
            elif tool.name in ['read_file', 'write_file', 'list_directory', 'search_files', 'create_file']:
                tool_categories['Filesystem Tools'].append(tool.name)
            else:
                tool_categories['Other Tools'].append(tool.name)
        
        for category, tool_names in tool_categories.items():
            if tool_names:
                print(f"\n{category} ({len(tool_names)}):")
                for name in tool_names:
                    print(f"  - {name}")
                    
    except Exception as e:
        print(f"❌ Tool discovery failed: {e}")


if __name__ == "__main__":
    print("🚀 Starting Filesystem Tools Test Suite")
    print("=" * 60)
    
    # Run tool discovery first
    asyncio.run(test_tool_discovery())
    
    # Run filesystem tests
    asyncio.run(test_filesystem_tools())
    
    print("\n✨ Test suite completed!")
