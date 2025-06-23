#!/usr/bin/env python3
"""
Simple test runner for the comprehensive SemanticMemoryManager capabilities test.

This script provides an easy way to run the comprehensive test suite with
proper error handling and clean output formatting.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Import from the same directory
sys.path.insert(0, str(Path(__file__).parent))
from test_direct_semantic_memory_capabilities import MemoryTestSuite


def print_banner():
    """Print a nice banner for the test suite."""
    print("\n" + "🧠" * 20)
    print("🧠 SEMANTIC MEMORY MANAGER CAPABILITY TESTS 🧠")
    print("🧠" * 20)
    print("\nThis test suite validates all 8 memory tools:")
    print("1. store_user_memory - Store new memories")
    print("2. query_memory - Search memories semantically")
    print("3. update_memory - Update existing memories")
    print("4. delete_memory - Delete specific memories")
    print("5. clear_memories - Clear all user memories")
    print("6. get_recent_memories - Get recent memories")
    print("7. get_all_memories - Get all memories")
    print("8. get_memory_stats - Get memory statistics")
    print("\nFeatures tested:")
    print("• Bulk fact storage with timing")
    print("• Semantic search capabilities")
    print("• Memory management operations")
    print("• Performance benchmarking")
    print("• Error handling validation")
    print("\n" + "🧠" * 20 + "\n")


def print_requirements():
    """Print requirements for running the tests."""
    print("📋 REQUIREMENTS:")
    print("• Ollama server running with llama3.2:3b model")
    print("• Personal agent dependencies installed")
    print("• Write access to ./data/test_agno_comprehensive/")
    print("\n🚀 Starting tests in 3 seconds...")
    print("   (Press Ctrl+C to cancel)")


async def run_tests():
    """Run the comprehensive test suite with error handling."""
    try:
        print_banner()
        print_requirements()
        
        # Give user a chance to cancel
        await asyncio.sleep(3)
        
        # Run the test suite
        test_suite = MemoryTestSuite()
        await test_suite.run_comprehensive_tests()
        
        print("\n🎉 All tests completed successfully!")
        return True
        
    except KeyboardInterrupt:
        print("\n⚠️ Tests cancelled by user")
        return False
        
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point."""
    try:
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
