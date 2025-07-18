#!/usr/bin/env python3
"""
Test script to verify that the education query fix works correctly.

This script tests that searching for "education" now finds memories tagged with "academic".
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from personal_agent.core.semantic_memory_manager import create_semantic_memory_manager
from personal_agent.core.topic_classifier import TopicClassifier
from agno.memory.v2.db.sqlite import SqliteMemoryDb
import tempfile

def test_education_query_fix():
    """Test that searching for 'education' finds 'academic' memories."""
    
    print("🧪 Testing Education Query Fix")
    print("=" * 50)
    
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as temp_db:
        temp_db_path = temp_db.name
    
    try:
        # Initialize the memory manager and database
        memory_db = SqliteMemoryDb(
            table_name="test_memory",
            db_file=temp_db_path,
        )
        
        manager = create_semantic_memory_manager(
            similarity_threshold=0.3,  # Lower threshold for testing
            debug_mode=True,
        )
        
        # Test the topic classifier first
        print("\n1. Testing Topic Classifier:")
        classifier = TopicClassifier()
        
        test_texts = [
            "I have a PhD in Biochemistry from Johns Hopkins",
            "I graduated from college in 1982",
            "I went to Lakota High School",
            "I studied biology at university",
        ]
        
        for text in test_texts:
            topics = classifier.classify(text)
            print(f"   '{text}' -> {topics}")
        
        # Test the query expansion
        print("\n2. Testing Query Expansion:")
        test_queries = ["education", "school", "university", "degree"]
        
        for query in test_queries:
            expanded = manager._expand_query(query)
            print(f"   '{query}' expands to: {expanded}")
        
        # Add some test memories
        print("\n3. Adding Test Memories:")
        test_memories = [
            "Eric has a PhD in Biochemistry from Johns Hopkins Medical School",
            "Eric graduated from college at Washington University in St Louis in 1982",
            "Eric went to Lakota High School and graduated Valedictorian in 1978",
            "Eric loves astronomy and building radio-controlled airplanes",
            "Eric was born on April 11, 1960",
        ]
        
        user_id = "test_user"
        
        for memory_text in test_memories:
            result = manager.add_memory(
                memory_text=memory_text,
                db=memory_db,
                user_id=user_id,
            )
            print(f"   Added: '{memory_text[:50]}...' -> {result.topics}")
        
        # Test searching with different queries
        print("\n4. Testing Memory Search:")
        search_queries = [
            "education",      # This should now find academic memories
            "academic",       # This should find academic memories directly
            "school",         # This should find academic memories
            "university",     # This should find academic memories
            "astronomy",      # This should find astronomy memories
            "born",           # This should find personal_info memories
        ]
        
        for query in search_queries:
            print(f"\n   Searching for '{query}':")
            results = manager.search_memories(
                query=query,
                db=memory_db,
                user_id=user_id,
                limit=5,
                similarity_threshold=0.1,  # Very low threshold for testing
            )
            
            if results:
                for memory, score in results:
                    print(f"     Score {score:.3f}: '{memory.memory[:60]}...' (topics: {memory.topics})")
            else:
                print(f"     No results found for '{query}'")
        
        print("\n✅ Test completed successfully!")
        
        # Specific test for the original issue
        print("\n5. Specific Test - Education Query (search_memories):")
        education_results = manager.search_memories(
            query="education",
            db=memory_db,
            user_id=user_id,
            limit=10,
            similarity_threshold=0.1,
        )
        
        academic_memories_found = 0
        for memory, score in education_results:
            if memory.topics and "academic" in memory.topics:
                academic_memories_found += 1
        
        print(f"   Found {len(education_results)} total results for 'education'")
        print(f"   Found {academic_memories_found} academic memories")
        
        if academic_memories_found > 0:
            print("   ✅ SUCCESS: Education query (search_memories) now finds academic memories!")
        else:
            print("   ❌ FAILURE: Education query (search_memories) still doesn't find academic memories")
        
        # Test the get_memories_by_topic method (this is what the ? command uses)
        print("\n6. Specific Test - Education Query (get_memories_by_topic):")
        topic_results = manager.get_memories_by_topic(
            db=memory_db,
            user_id=user_id,
            topics=["education"],
            limit=10,
        )
        
        academic_topic_memories_found = 0
        for memory in topic_results:
            if memory.topics and "academic" in memory.topics:
                academic_topic_memories_found += 1
        
        print(f"   Found {len(topic_results)} total results for topic 'education'")
        print(f"   Found {academic_topic_memories_found} academic memories")
        
        if academic_topic_memories_found > 0:
            print("   ✅ SUCCESS: Education topic query now finds academic memories!")
        else:
            print("   ❌ FAILURE: Education topic query still doesn't find academic memories")
        
        # Overall success check
        overall_success = academic_memories_found > 0 and academic_topic_memories_found > 0
        if overall_success:
            print("\n🎉 COMPLETE SUCCESS: Both search methods now work with 'education' queries!")
        else:
            print("\n⚠️ PARTIAL SUCCESS: Some search methods still need work")
            
    finally:
        # Clean up the temporary database
        try:
            os.unlink(temp_db_path)
        except:
            pass

if __name__ == "__main__":
    test_education_query_fix()
