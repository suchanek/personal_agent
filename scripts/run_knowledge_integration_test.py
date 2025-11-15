#!/usr/bin/env python3
"""
Quick runner script for the KnowledgeTools integration test.

This script provides a simple way to run the integration test and verify
that our KnowledgeTools integration doesn't interfere with memory operations.
"""

import asyncio
import sys
from pathlib import Path

from personal_agent.utils import add_src_to_path

add_src_to_path()

async def main():
    """Run the KnowledgeTools integration test."""
    
    print("🚀 RUNNING KNOWLEDGE TOOLS INTEGRATION TEST")
    print("=" * 60)
    print()
    
    try:
        # Import and run the test
        from test_knowledge_tools_integration import main as run_tests
        
        success = await run_tests()
        
        if success:
            print("\n🎉 SUCCESS: All tests passed!")
            print("✅ KnowledgeTools integration is working correctly")
            print("✅ Memory system maintains priority")
            return 0
        else:
            print("\n❌ FAILURE: Some tests failed!")
            print("⚠️  Check the output above for details")
            return 1
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the project root directory")
        return 1
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
