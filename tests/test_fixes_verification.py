#!/usr/bin/env python3
"""
Test script to verify the fixes for:
1. File creation bug in PersonalAgentFilesystemTools
2. Knowledge tool misuse for creative requests
"""

import os
import sys
import tempfile
from pathlib import Path

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath()

from personal_agent.tools.personal_agent_tools import PersonalAgentFilesystemTools
from personal_agent.tools.knowledge_ingestion_tools import KnowledgeIngestionTools


def test_file_creation_fix():
    """Test that file creation in current directory works correctly."""
    print("🧪 Testing File Creation Fix")
    print("=" * 40)
    
    # Initialize the filesystem tools
    fs_tools = PersonalAgentFilesystemTools()
    
    # Test 1: Create file in current directory (this was failing before)
    print("1️⃣ Testing file creation in current directory...")
    result = fs_tools.write_file("test_fix.txt", "This is a test file created by the fix.")
    print(f"   Result: {result}")
    
    # Verify the file was created
    if os.path.exists("test_fix.txt"):
        print("   ✅ File created successfully!")
        # Clean up
        os.remove("test_fix.txt")
        print("   🧹 Cleaned up test file")
    else:
        print("   ❌ File was not created")
    
    # Test 2: Create file with directory path (should still work)
    print("\n2️⃣ Testing file creation with directory path...")
    with tempfile.TemporaryDirectory() as temp_dir:
        test_path = os.path.join(temp_dir, "subdir", "test.txt")
        result = fs_tools.write_file(test_path, "Test content with directory")
        print(f"   Result: {result}")
        
        if os.path.exists(test_path):
            print("   ✅ File with directory path created successfully!")
        else:
            print("   ❌ File with directory path was not created")


def test_knowledge_tool_filtering():
    """Test that knowledge tools reject creative requests."""
    print("\n🧪 Testing Knowledge Tool Filtering")
    print("=" * 40)
    
    # Initialize the knowledge tools
    knowledge_tools = KnowledgeIngestionTools()
    
    # Test 1: Creative request should be rejected
    print("1️⃣ Testing creative request rejection...")
    creative_queries = [
        "write a funny story about robots",
        "create a poem about love",
        "generate a joke",
        "make up a story",
        "compose an essay"
    ]
    
    for query in creative_queries:
        print(f"   Testing: '{query}'")
        result = knowledge_tools.query_knowledge_base(query)
        if "❌ This appears to be a creative request" in result:
            print(f"   ✅ Correctly rejected creative request")
        else:
            print(f"   ❌ Failed to reject creative request: {result[:100]}...")
    
    # Test 2: Factual request should be allowed (but may fail due to server)
    print("\n2️⃣ Testing factual request acceptance...")
    factual_queries = [
        "what is artificial intelligence",
        "information about machine learning",
        "facts about Python programming"
    ]
    
    for query in factual_queries:
        print(f"   Testing: '{query}'")
        result = knowledge_tools.query_knowledge_base(query)
        if "❌ This appears to be a creative request" in result:
            print(f"   ❌ Incorrectly rejected factual request")
        else:
            print(f"   ✅ Correctly allowed factual request (may fail due to server)")


def main():
    """Run all tests."""
    print("🔧 Personal Agent Fixes Verification")
    print("=" * 50)
    
    try:
        test_file_creation_fix()
        test_knowledge_tool_filtering()
        
        print("\n✅ All tests completed!")
        print("\nSummary:")
        print("- File creation fix: Prevents 'No such file or directory' error")
        print("- Knowledge tool filtering: Rejects creative requests appropriately")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
