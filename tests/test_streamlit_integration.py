#!/usr/bin/env python3
"""
Test script to verify the Streamlit integration with SemanticMemoryManager works correctly.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, USER_ID
from personal_agent.core.semantic_memory_manager import SemanticMemoryManager, SemanticMemoryManagerConfig
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory

def test_streamlit_integration():
    """Test the semantic memory manager integration."""
    print("🧪 Testing Streamlit Integration with SemanticMemoryManager")
    print("=" * 60)
    
    # Create database connection (same as in Streamlit app)
    db_path = Path(AGNO_STORAGE_DIR) / "agent_memory.db"
    print(f"📂 Database: {db_path}")
    
    memory_db = SqliteMemoryDb(table_name="personal_agent_memory", db_file=str(db_path))
    
    # Create semantic memory manager configuration (same as in Streamlit app)
    semantic_config = SemanticMemoryManagerConfig(
        similarity_threshold=0.8,
        enable_semantic_dedup=True,
        enable_exact_dedup=True,
        enable_topic_classification=True,
        debug_mode=True,
    )
    
    # Create semantic memory manager (LLM-free, but with model attribute for compatibility)
    from agno.models.ollama import Ollama
    semantic_memory_manager = SemanticMemoryManager(
        model=Ollama(
            id="llama3.1:8b",  # Use a default model for compatibility only
            host="http://localhost:11434",
            options={
                "num_ctx": 8192,
                "temperature": 0.7,
            },
        ),
        config=semantic_config
    )
    
    # Create memory object with custom memory manager (no model parameter needed)
    memory = Memory(
        db=memory_db,
        memory_manager=semantic_memory_manager,
    )
    
    print("✅ Memory system initialized successfully")
    
    # Test adding a memory
    test_input = "My name is John and I love programming in Python"
    print(f"\n🔄 Processing test input: '{test_input}'")
    
    # Test the process_input method
    result = semantic_memory_manager.process_input(test_input, memory_db, USER_ID)
    
    print(f"📊 Processing result:")
    print(f"   Success: {result['success']}")
    print(f"   Total processed: {result['total_processed']}")
    print(f"   Memories added: {len(result['memories_added'])}")
    print(f"   Memories rejected: {len(result['memories_rejected'])}")
    
    for memory_info in result['memories_added']:
        print(f"   ✅ Added: '{memory_info['memory']}' (topics: {memory_info['topics']})")
    
    for rejection in result['memories_rejected']:
        print(f"   🚫 Rejected: '{rejection['memory']}' - {rejection['reason']}")
    
    # Test memory statistics
    print(f"\n📊 Testing memory statistics...")
    stats = semantic_memory_manager.get_memory_stats(memory_db, USER_ID)
    
    print(f"Memory Statistics:")
    for key, value in stats.items():
        if key == "topic_distribution" and isinstance(value, dict):
            print(f"   {key}:")
            for topic, count in value.items():
                print(f"     - {topic}: {count}")
        else:
            print(f"   {key}: {value}")
    
    # Test memory search
    print(f"\n🔍 Testing memory search...")
    search_results = semantic_memory_manager.search_memories(
        "programming", memory_db, USER_ID, limit=3
    )
    
    print(f"Search results for 'programming':")
    if search_results:
        for i, (memory, similarity) in enumerate(search_results, 1):
            print(f"   {i}. {similarity:.2f}: '{memory.memory}' (topics: {memory.topics})")
    else:
        print("   No results found")
    
    print(f"\n✅ Integration test completed successfully!")
    print(f"🚀 The Streamlit app should now work with the new SemanticMemoryManager")

if __name__ == "__main__":
    test_streamlit_integration()
