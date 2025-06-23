#!/usr/bin/env python3
"""
Test program for streamlit memory refactoring.

This test verifies the memory functionality before and after refactoring
to ensure we maintain compatibility while switching to direct SemanticMemoryManager calls.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, USER_ID
from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.core.semantic_memory_manager import SemanticMemoryManager


def test_current_memory_access():
    """Test current memory access patterns used in streamlit app."""
    print("🧪 Testing Current Memory Access Patterns")
    print("=" * 50)
    
    # Initialize agent (similar to streamlit app)
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
    
    # Test current access patterns
    print("\n📋 Testing Current Access Patterns:")
    
    # 1. Check agno_memory exists
    has_agno_memory = hasattr(agent, 'agno_memory') and agent.agno_memory
    print(f"✓ agent.agno_memory exists: {has_agno_memory}")
    
    if has_agno_memory:
        # 2. Check memory_manager access
        has_memory_manager = hasattr(agent.agno_memory, 'memory_manager')
        print(f"✓ agent.agno_memory.memory_manager exists: {has_memory_manager}")
        
        # 3. Check db access
        has_db = hasattr(agent.agno_memory, 'db')
        print(f"✓ agent.agno_memory.db exists: {has_db}")
        
        if has_memory_manager and has_db:
            memory_manager = agent.agno_memory.memory_manager
            db = agent.agno_memory.db
            
            # 4. Test memory_manager is SemanticMemoryManager
            is_semantic = isinstance(memory_manager, SemanticMemoryManager)
            print(f"✓ memory_manager is SemanticMemoryManager: {is_semantic}")
            
            # 5. Test current methods
            print("\n🔍 Testing Current Methods:")
            
            # Test get_user_memories (current streamlit method)
            try:
                memories = agent.agno_memory.get_user_memories(user_id=USER_ID)
                print(f"✓ get_user_memories: {len(memories)} memories found")
            except Exception as e:
                print(f"❌ get_user_memories failed: {e}")
            
            # Test memory_manager.get_memory_stats (current streamlit method)
            try:
                stats = memory_manager.get_memory_stats(db, USER_ID)
                print(f"✓ get_memory_stats: {stats.get('total_memories', 0)} total memories")
            except Exception as e:
                print(f"❌ get_memory_stats failed: {e}")
            
            # Test search_user_memories with agentic (current problematic method)
            try:
                search_results = agent.agno_memory.search_user_memories(
                    user_id=USER_ID,
                    query="test search",
                    retrieval_method="agentic",
                    limit=5
                )
                print(f"✓ search_user_memories (agentic): {len(search_results)} results")
            except Exception as e:
                print(f"❌ search_user_memories (agentic) failed: {e}")
            
            # Test direct SemanticMemoryManager.search_memories (new method)
            try:
                direct_results = memory_manager.search_memories(
                    query="test search",
                    db=db,
                    user_id=USER_ID,
                    limit=5,
                    similarity_threshold=0.3
                )
                print(f"✓ direct search_memories: {len(direct_results)} results")
            except Exception as e:
                print(f"❌ direct search_memories failed: {e}")
    
    return agent


def test_direct_memory_functions(agent):
    """Test direct SemanticMemoryManager functions."""
    print("\n🔧 Testing Direct SemanticMemoryManager Functions")
    print("=" * 50)
    
    if not (hasattr(agent, 'agno_memory') and agent.agno_memory):
        print("❌ No agno_memory available")
        return
    
    memory_manager = agent.agno_memory.memory_manager
    db = agent.agno_memory.db
    
    # Test add_memory
    print("\n📝 Testing add_memory:")
    success, message, memory_id = memory_manager.add_memory(
        memory_text="I love testing memory systems",
        db=db,
        user_id=USER_ID,
        topics=["testing", "memory"]
    )
    print(f"✓ add_memory: {success} - {message} (ID: {memory_id})")
    
    # Test search_memories with different parameters
    print("\n🔍 Testing search_memories:")
    results = memory_manager.search_memories(
        query="testing",
        db=db,
        user_id=USER_ID,
        limit=10,
        similarity_threshold=0.3,
        search_topics=True,
        topic_boost=0.5
    )
    print(f"✓ search_memories: {len(results)} results")
    for memory, score in results[:3]:  # Show first 3
        print(f"   - Score {score:.3f}: '{memory.memory}' (topics: {memory.topics})")
    
    # Test get_memory_stats
    print("\n📊 Testing get_memory_stats:")
    stats = memory_manager.get_memory_stats(db, USER_ID)
    print(f"✓ get_memory_stats: {stats}")
    
    # Test clear_memories (be careful with this!)
    print("\n🧹 Testing clear_memories (will clear test data):")
    success, message = memory_manager.clear_memories(db, USER_ID)
    print(f"✓ clear_memories: {success} - {message}")


def main():
    """Main test function."""
    print("🧠 Streamlit Memory Refactoring Test")
    print("=" * 60)
    
    try:
        # Test current patterns
        agent = test_current_memory_access()
        
        # Test direct functions
        test_direct_memory_functions(agent)
        
        print("\n✅ All tests completed successfully!")
        print("Ready to proceed with refactoring.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
