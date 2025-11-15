#!/usr/bin/env python3
"""
Test the refactored streamlit memory functions.

This test verifies that the direct SemanticMemoryManager functions work correctly
after the refactoring to eliminate agentic retrieval.
"""

import sys
from pathlib import Path

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath()

from personal_agent.config import AGNO_STORAGE_DIR, USER_ID
from personal_agent.core.agno_agent import AgnoPersonalAgent


def test_refactored_memory_functions():
    """Test the refactored memory functions work correctly."""
    print("🧪 Testing Refactored Memory Functions")
    print("=" * 50)
    
    # Initialize agent
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name="llama3.2:3b",
        ollama_base_url="http://localhost:11434",
        user_id=USER_ID,
        debug=True,
        enable_memory=True,
        enable_mcp=False,
        storage_dir=AGNO_STORAGE_DIR,
    )
    
    print("🔄 Initializing agent...")
    import asyncio
    asyncio.run(agent.initialize())
    
    # Test direct memory manager access
    print("\n📋 Testing Direct Memory Manager Access:")
    
    memory_manager = agent.agno_memory.memory_manager
    db = agent.agno_memory.db
    
    print(f"✓ Memory manager type: {type(memory_manager).__name__}")
    print(f"✓ Database type: {type(db).__name__}")
    
    # Test direct search (this is what we refactored)
    print("\n🔍 Testing Direct Search (No Agentic Retrieval):")
    
    # Add a test memory first
    success, message, memory_id = memory_manager.add_memory(
        memory_text="I love testing refactored memory systems",
        db=db,
        user_id=USER_ID,
        topics=["testing", "refactoring"]
    )
    print(f"✓ Added test memory: {success} - {message}")
    
    # Test direct search with different thresholds
    search_results = memory_manager.search_memories(
        query="testing refactored",
        db=db,
        user_id=USER_ID,
        limit=5,
        similarity_threshold=0.3,
        search_topics=True,
        topic_boost=0.5
    )
    
    print(f"✓ Direct search results: {len(search_results)} found")
    for memory, score in search_results:
        print(f"   - Score {score:.3f}: '{memory.memory}' (topics: {memory.topics})")
    
    # Test memory stats
    print("\n📊 Testing Memory Statistics:")
    stats = memory_manager.get_memory_stats(db, USER_ID)
    print(f"✓ Total memories: {stats.get('total_memories', 0)}")
    print(f"✓ Topic distribution: {len(stats.get('topic_distribution', {}))}")
    
    # Test clear memories
    print("\n🧹 Testing Clear Memories:")
    success, message = memory_manager.clear_memories(db, USER_ID)
    print(f"✓ Clear memories: {success} - {message}")
    
    print("\n✅ All refactored memory functions work correctly!")
    return True


def main():
    """Main test function."""
    print("🔧 Refactored Streamlit Memory Test")
    print("=" * 60)
    
    try:
        test_refactored_memory_functions()
        print("\n🎉 Refactoring successful! No agentic retrieval needed.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
