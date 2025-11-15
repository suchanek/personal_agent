#!/usr/bin/env python3
"""
Test script to verify automatic topic classification functionality.

This test validates that the memory system correctly auto-classifies topics
when storing memories without explicit topic specification.
"""

import asyncio
import sys
import time
from pathlib import Path

from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.config import (
    AGNO_STORAGE_DIR,
    LLM_MODEL,
    OLLAMA_URL,
    USER_ID,
)
from personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_automatic_topic_classification():
    """Test that memories are automatically classified into appropriate topics."""
    print("🧪 Testing Automatic Topic Classification")
    print("=" * 50)
    
    # Initialize agent
    print("🤖 Initializing agent...")
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        user_id=USER_ID,
        debug=True,
        enable_memory=True,
        enable_mcp=False,
        storage_dir=AGNO_STORAGE_DIR,
    )
    
    success = await agent.initialize()
    if not success:
        print("❌ Failed to initialize agent")
        return False
    
    print(f"✅ Agent initialized with model: {LLM_MODEL}")
    
    # Test facts with expected topic classifications
    test_facts = [
        {
            "fact": "I work as a software engineer at Google",
            "expected_topics": ["work", "technology"],
            "description": "Work and technology fact"
        },
        {
            "fact": "My dog Max loves to play fetch in the park",
            "expected_topics": ["pets", "hobbies"],
            "description": "Pet-related fact"
        },
        {
            "fact": "I have a PhD in Computer Science from Stanford University",
            "expected_topics": ["academic", "personal_info"],
            "description": "Academic achievement"
        },
        {
            "fact": "I am married to Sarah and we have two children",
            "expected_topics": ["family"],
            "description": "Family information"
        },
        {
            "fact": "I love hiking and mountain climbing on weekends",
            "expected_topics": ["hobbies"],
            "description": "Hobby/recreation fact"
        },
        {
            "fact": "I prefer coffee over tea and drink it every morning",
            "expected_topics": ["preferences"],
            "description": "Personal preference"
        },
        {
            "fact": "I drive a BMW X5 and love its performance",
            "expected_topics": ["automotive", "preferences"],
            "description": "Automotive preference"
        },
        {
            "fact": "I have a peanut allergy and carry an EpiPen",
            "expected_topics": ["health"],
            "description": "Health information"
        },
        {
            "fact": "I invest in Tesla stock and follow the market daily",
            "expected_topics": ["finance"],
            "description": "Financial information"
        },
        {
            "fact": "I play piano and guitar in my spare time",
            "expected_topics": ["hobbies"],
            "description": "Musical hobby"
        },
        {
            "fact": "I am 35 years old and live in San Francisco",
            "expected_topics": ["personal_info"],
            "description": "Personal demographic info"
        },
        {
            "fact": "I want to climb Mount Everest someday",
            "expected_topics": ["goals", "hobbies"],
            "description": "Personal goal"
        }
    ]
    
    print(f"\n📝 Testing automatic classification of {len(test_facts)} facts...")
    
    stored_memories = []
    
    for i, test_case in enumerate(test_facts, 1):
        print(f"\n  Test {i}: {test_case['description']}")
        print(f"  Fact: {test_case['fact']}")
        print(f"  Expected topics: {test_case['expected_topics']}")
        
        try:
            # Store memory without specifying topics (let auto-classification work)
            response = await agent.store_user_memory(content=test_case['fact'], topics=None)
            
            if "✅" in response and "Local memory:" in response:
                print(f"    ✅ Stored successfully")
                stored_memories.append({
                    'fact': test_case['fact'],
                    'expected_topics': test_case['expected_topics'],
                    'description': test_case['description']
                })
            else:
                print(f"    ⚠️ Storage unclear: {response[:100]}...")
            
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"    ❌ Failed: {e}")
    
    print(f"\n📊 Stored {len(stored_memories)}/{len(test_facts)} test facts")
    
    # Wait for storage to settle
    print("\n⏳ Waiting for storage to settle...")
    await asyncio.sleep(2)
    
    # Now check the actual stored memories to verify topic classification
    print("\n🔍 Checking automatic topic classification results...")
    
    try:
        # Access the memory database directly to check topic classifications
        if agent.agno_memory and agent.agno_memory.db:
            memory_rows = agent.agno_memory.db.read_memories(user_id=USER_ID)
            
            classification_results = []
            total_memories = 0
            correct_classifications = 0
            
            print("\n📊 Topic Classification Analysis:")
            print("-" * 80)
            
            # Get the most recent memories (our test facts)
            recent_memories = memory_rows[-len(stored_memories):] if len(memory_rows) >= len(stored_memories) else memory_rows
            
            for row in recent_memories:
                if row.user_id == USER_ID and row.memory:
                    try:
                        from agno.memory.v2.schema import UserMemory
                        user_memory = UserMemory.from_dict(row.memory)
                        total_memories += 1
                        
                        memory_text = user_memory.memory
                        actual_topics = user_memory.topics or []
                        
                        # Find the corresponding test case
                        test_case = None
                        for stored in stored_memories:
                            if stored['fact'] in memory_text:
                                test_case = stored
                                break
                        
                        if test_case:
                            expected_topics = test_case['expected_topics']
                            
                            # Check if any expected topics are present in actual topics
                            topic_matches = []
                            for expected in expected_topics:
                                for actual in actual_topics:
                                    if expected.lower() in actual.lower() or actual.lower() in expected.lower():
                                        topic_matches.append((expected, actual))
                            
                            is_correct = len(topic_matches) > 0
                            if is_correct:
                                correct_classifications += 1
                            
                            status = "✅" if is_correct else "❌"
                            print(f"  {status} {test_case['description']}")
                            print(f"      Memory: {memory_text[:60]}...")
                            print(f"      Expected: {expected_topics}")
                            print(f"      Actual: {actual_topics}")
                            if topic_matches:
                                print(f"      Matches: {topic_matches}")
                            print()
                            
                            classification_results.append({
                                'memory': memory_text,
                                'expected': expected_topics,
                                'actual': actual_topics,
                                'correct': is_correct,
                                'matches': topic_matches
                            })
                        else:
                            print(f"  ⚠️ Unknown memory: {memory_text[:60]}...")
                            print(f"      Topics: {actual_topics}")
                            print()
                            
                    except Exception as e:
                        print(f"  ❌ Error parsing memory: {e}")
            
            print("-" * 80)
            print(f"📊 Classification Summary:")
            print(f"  Total memories analyzed: {total_memories}")
            print(f"  Correct classifications: {correct_classifications}")
            print(f"  Classification accuracy: {(correct_classifications / total_memories * 100):.1f}%" if total_memories > 0 else "N/A")
            
            # Detailed analysis
            if classification_results:
                print(f"\n📋 Detailed Results:")
                for result in classification_results:
                    if not result['correct']:
                        print(f"  ❌ Misclassified: {result['memory'][:50]}...")
                        print(f"     Expected: {result['expected']}")
                        print(f"     Got: {result['actual']}")
            
            # Success criteria: at least 70% accuracy
            success_threshold = 0.7
            accuracy = correct_classifications / total_memories if total_memories > 0 else 0
            
            if accuracy >= success_threshold:
                print(f"\n✅ Topic classification test PASSED!")
                print(f"   Accuracy {accuracy:.1%} meets threshold of {success_threshold:.1%}")
                return True
            else:
                print(f"\n❌ Topic classification test FAILED!")
                print(f"   Accuracy {accuracy:.1%} below threshold of {success_threshold:.1%}")
                return False
                
        else:
            print("❌ Could not access memory database for classification checking")
            return False
            
    except Exception as e:
        print(f"❌ Error checking topic classifications: {e}")
        return False


async def test_topic_classifier_directly():
    """Test the topic classifier directly to verify it's working correctly."""
    print("\n🔬 Testing Topic Classifier Directly")
    print("=" * 50)
    
    try:
        from personal_agent.core.topic_classifier import TopicClassifier
        classifier = TopicClassifier()
        
        test_phrases = [
            "I work as a software engineer at Google",
            "My dog Max loves to play fetch",
            "I have a PhD in Computer Science",
            "I am married to Sarah",
            "I love hiking and mountain climbing",
            "I prefer coffee over tea",
            "I drive a BMW X5",
            "I have a peanut allergy",
            "I invest in Tesla stock",
            "I play piano and guitar"
        ]
        
        print("Testing topic classifier on sample phrases:")
        print("-" * 50)
        
        for phrase in test_phrases:
            topics = classifier.classify(phrase)
            print(f"  '{phrase[:40]}...' → {topics}")
        
        print("-" * 50)
        print("✅ Topic classifier test completed")
        return True
        
    except Exception as e:
        print(f"❌ Error testing topic classifier: {e}")
        return False


async def main():
    """Main test function."""
    print("🧪 Automatic Topic Classification Test Suite")
    print("=" * 60)
    
    try:
        # Test topic classifier directly first
        classifier_success = await test_topic_classifier_directly()
        
        # Run automatic classification test
        classification_success = await test_automatic_topic_classification()
        
        print("\n" + "=" * 60)
        print("📋 AUTOMATIC TOPIC CLASSIFICATION TEST SUMMARY")
        print("=" * 60)
        
        print(f"Topic Classifier Test: {'✅ PASS' if classifier_success else '❌ FAIL'}")
        print(f"Auto-Classification Test: {'✅ PASS' if classification_success else '❌ FAIL'}")
        
        overall_success = classifier_success and classification_success
        
        if overall_success:
            print("\n🎉 OVERALL: Automatic topic classification is working correctly!")
            print("✅ Topics are being automatically classified")
            print("✅ Classification accuracy meets expectations")
            return True
        else:
            print("\n⚠️ OVERALL: Topic classification issues detected")
            print("\n💡 Recommendations:")
            if not classifier_success:
                print("  - Check topic classifier configuration and topics.yaml")
            if not classification_success:
                print("  - Review memory storage topic assignment logic")
                print("  - Consider improving topic classification rules")
            return False
            
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Usage: python test_automatic_topic_classification.py")
    print("This test validates automatic topic classification functionality")
    print()
    
    # Run the tests
    success = asyncio.run(main())
    
    if success:
        print("\n✅ Automatic topic classification test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Automatic topic classification test failed!")
        sys.exit(1)
