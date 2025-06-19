#!/usr/bin/env python3
"""
Debug Memory Search - Shows similarity scores for all memories
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.schema import UserMemory
from personal_agent.config import AGNO_STORAGE_DIR, USER_ID
from personal_agent.core.semantic_memory_manager import SemanticMemoryManager, SemanticMemoryManagerConfig


def debug_search(query: str, db_path: str = None, user_id: str = USER_ID):
    """Debug search showing all similarity scores."""
    
    if db_path is None:
        db_path = str(Path(AGNO_STORAGE_DIR) / "agent_memory.db")
    
    print(f"🔍 DEBUG SEARCH for: '{query}'")
    print(f"🗄️  Database: {db_path}")
    print(f"👤 User: {user_id}")
    print("=" * 80)
    
    # Initialize components
    memory_db = SqliteMemoryDb(table_name="personal_agent_memory", db_file=db_path)
    semantic_manager = SemanticMemoryManager(
        config=SemanticMemoryManagerConfig(similarity_threshold=0.1, debug_mode=True)
    )
    
    # Get all memories
    try:
        memory_rows = memory_db.read_memories(user_id=user_id)
        memories = []
        
        for row in memory_rows:
            if row.user_id == user_id and row.memory:
                try:
                    user_memory = UserMemory.from_dict(row.memory)
                    memories.append(user_memory)
                except Exception as e:
                    print(f"Warning: Failed to convert memory: {e}")
        
        print(f"📊 Found {len(memories)} memories")
        print()
        
        # Calculate similarity for each memory
        results = []
        for i, memory in enumerate(memories, 1):
            similarity = semantic_manager.duplicate_detector._calculate_semantic_similarity(
                query, memory.memory
            )
            results.append((memory, similarity))
            
            print(f"Memory {i}:")
            print(f"  Content: '{memory.memory}'")
            print(f"  Topics: {memory.topics}")
            print(f"  Similarity to '{query}': {similarity:.4f}")
            
            # Check if query appears directly in content
            query_in_content = query.lower() in memory.memory.lower()
            print(f"  Direct match: {'✅' if query_in_content else '❌'}")
            
            # Check if query appears in topics
            topic_match = any(query.lower() in topic.lower() for topic in (memory.topics or []))
            print(f"  Topic match: {'✅' if topic_match else '❌'}")
            print()
        
        # Sort by similarity
        results.sort(key=lambda x: x[1], reverse=True)
        
        print("🏆 TOP RESULTS BY SIMILARITY:")
        print("-" * 40)
        for i, (memory, similarity) in enumerate(results[:5], 1):
            print(f"{i}. Score: {similarity:.4f}")
            print(f"   Memory: '{memory.memory}'")
            print(f"   Topics: {memory.topics}")
            print()
        
        # Test different thresholds
        print("🎯 RESULTS AT DIFFERENT THRESHOLDS:")
        print("-" * 40)
        thresholds = [0.1, 0.2, 0.3, 0.4, 0.5]
        for threshold in thresholds:
            matches = [r for r in results if r[1] >= threshold]
            print(f"  Threshold {threshold}: {len(matches)} matches")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Debug Memory Search")
    parser.add_argument("query", help="Search query")
    parser.add_argument("--db-path", help="Database path")
    parser.add_argument("--user-id", default=USER_ID, help="User ID")
    
    args = parser.parse_args()
    
    debug_search(args.query, args.db_path, args.user_id)
