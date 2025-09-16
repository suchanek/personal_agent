#!/usr/bin/env python3
"""
Test script to verify the tool parameter fixes.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_filesystem_tools():
    """Test PersonalAgentFilesystemTools with the problematic parameters."""
    print("Testing PersonalAgentFilesystemTools...")
    
    try:
        from personal_agent.tools.personal_agent_tools import PersonalAgentFilesystemTools
        
        # Initialize the tools
        fs_tools = PersonalAgentFilesystemTools()
        
        # Test the create_and_save_file method with the problematic parameters
        result = fs_tools.create_and_save_file(
            filename="test_file.txt",
            content="This is a test file content.",
            directory="./",
            overwrite=True,  # This was causing validation error
            variable_to_return=None  # This was causing validation error
        )
        
        print(f"✅ create_and_save_file result: {result}")
        
        # Clean up the test file
        import os
        if os.path.exists("test_file.txt"):
            os.remove("test_file.txt")
            print("✅ Test file cleaned up")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing PersonalAgentFilesystemTools: {e}")
        return False

def test_knowledge_tools():
    """Test KnowledgeTools with the problematic parameters."""
    print("\nTesting KnowledgeTools...")
    
    try:
        from personal_agent.tools.knowledge_tools import KnowledgeTools
        from personal_agent.core.knowledge_manager import KnowledgeManager
        
        # Create a mock knowledge manager
        km = KnowledgeManager(user_id="test_user")
        
        # Initialize the tools
        knowledge_tools = KnowledgeTools(km, agno_knowledge=None)
        
        # Test the query_knowledge_base method with mode=None
        import asyncio
        
        async def test_query():
            result = await knowledge_tools.query_knowledge_base(
                query="test query",
                mode=None,  # This was causing validation error
                limit=5
            )
            return result
        
        result = asyncio.run(test_query())
        print(f"✅ query_knowledge_base result: {result[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing KnowledgeTools: {e}")
        return False

def test_path_fix():
    """Test the Path string conversion fix."""
    print("\nTesting Path string conversion...")
    
    try:
        from personal_agent.tools.personal_agent_tools import PersonalAgentFilesystemTools
        from pathlib import Path
        
        # This should not cause the 'str' object has no attribute 'joinpath' error
        fs_tools = PersonalAgentFilesystemTools(base_dir="/tmp")
        print("✅ PersonalAgentFilesystemTools initialized with string base_dir")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Path fix: {e}")
        return False

def main():
    """Run all tests."""
    print("🔧 Testing Personal Agent Tool Fixes")
    print("=" * 50)
    
    tests = [
        test_path_fix,
        test_filesystem_tools,
        test_knowledge_tools,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The fixes are working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
