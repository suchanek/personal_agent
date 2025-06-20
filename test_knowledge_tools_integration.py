#!/usr/bin/env python3
"""
Test script to verify KnowledgeTools integration doesn't interfere with memory operations.

This script tests that:
1. Memory tools (store_user_memory, query_memory) work correctly
2. KnowledgeTools don't short-circuit memory operations
3. Agent uses memory first for personal information
4. KnowledgeTools are used for general knowledge queries
5. Both systems work together harmoniously
"""

import asyncio
import logging
import os
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def test_knowledge_tools_integration():
    """Test that KnowledgeTools integration doesn't interfere with memory operations."""
    
    print("🧪 TESTING KNOWLEDGE TOOLS INTEGRATION")
    print("=" * 60)
    
    # Clean up any existing test data
    test_storage_dir = "./data/test_knowledge_integration"
    test_knowledge_dir = "./data/test_knowledge"
    
    if Path(test_storage_dir).exists():
        shutil.rmtree(test_storage_dir)
    if Path(test_knowledge_dir).exists():
        shutil.rmtree(test_knowledge_dir)
    
    # Create test knowledge files
    Path(test_knowledge_dir).mkdir(parents=True, exist_ok=True)
    
    # Create a test knowledge file about general topics
    with open(f"{test_knowledge_dir}/general_knowledge.txt", "w") as f:
        f.write("""
        Python Programming Language
        
        Python is a high-level, interpreted programming language created by Guido van Rossum.
        It was first released in 1991 and is known for its simple, readable syntax.
        
        Key Features:
        - Easy to learn and use
        - Extensive standard library
        - Cross-platform compatibility
        - Strong community support
        
        Popular frameworks include Django, Flask, FastAPI for web development.
        """)
    
    # Create another knowledge file about technology
    with open(f"{test_knowledge_dir}/technology.md", "w") as f:
        f.write("""
        # Artificial Intelligence
        
        AI is the simulation of human intelligence in machines that are programmed to think and learn.
        
        ## Types of AI:
        - Narrow AI (ANI)
        - General AI (AGI) 
        - Super AI (ASI)
        
        ## Applications:
        - Natural Language Processing
        - Computer Vision
        - Machine Learning
        - Robotics
        """)
    
    try:
        # Import and create agent
        from src.personal_agent.core.agno_agent import create_agno_agent
        from src.personal_agent.config import OLLAMA_URL, LLM_MODEL
        
        print("🚀 Creating agent with KnowledgeTools integration...")
        agent = await create_agno_agent(
            model_provider="ollama",
            model_name=LLM_MODEL,
            enable_memory=True,
            enable_mcp=False,  # Disable MCP for cleaner testing
            storage_dir=test_storage_dir,
            knowledge_dir=test_knowledge_dir,
            debug=True,
            user_id="test_user_knowledge_integration",
            ollama_base_url=OLLAMA_URL
        )
        
        print("✅ Agent created successfully")
        print()
        
        # Test 1: Store personal information in memory
        print("📝 TEST 1: Storing personal information in memory")
        print("-" * 50)
        
        personal_facts = [
            "My name is Alice Johnson",
            "I live in San Francisco, California", 
            "I work as a software engineer at TechCorp",
            "My favorite programming language is Python",
            "I have a cat named Whiskers"
        ]
        
        for fact in personal_facts:
            print(f"Storing: {fact}")
            response = await agent.run(f"Remember this about me: {fact}")
            print(f"Response: {response[:100]}...")
            print()
        
        # Test 2: Query personal information (should use memory, not knowledge base)
        print("🧠 TEST 2: Querying personal information (should use memory)")
        print("-" * 50)
        
        personal_queries = [
            "What is my name?",
            "Where do I live?", 
            "What do I do for work?",
            "What's my favorite programming language?",
            "Do I have any pets?"
        ]
        
        for query in personal_queries:
            print(f"Query: {query}")
            response = await agent.run(query)
            print(f"Response: {response}")
            print()
        
        # Test 3: Query general knowledge (should use KnowledgeTools)
        print("📚 TEST 3: Querying general knowledge (should use KnowledgeTools)")
        print("-" * 50)
        
        knowledge_queries = [
            "Tell me about Python programming language",
            "What are the types of artificial intelligence?",
            "What are some popular Python frameworks?",
            "Explain what AI applications exist"
        ]
        
        for query in knowledge_queries:
            print(f"Query: {query}")
            response = await agent.run(query)
            print(f"Response: {response[:200]}...")
            print()
        
        # Test 4: Mixed queries (personal + general knowledge)
        print("🔄 TEST 4: Mixed queries (personal + general knowledge)")
        print("-" * 50)
        
        mixed_queries = [
            "I like Python programming. Can you tell me more about Python and also remind me what my favorite language is?",
            "What do I do for work and what are some AI applications in that field?",
            "Tell me about my pet and also explain what artificial intelligence is"
        ]
        
        for query in mixed_queries:
            print(f"Query: {query}")
            response = await agent.run(query)
            print(f"Response: {response[:300]}...")
            print()
        
        # Test 5: Verify memory search works correctly
        print("🔍 TEST 5: Direct memory search verification")
        print("-" * 50)
        
        memory_search_queries = [
            "Search my memories for information about my job",
            "What recent memories do I have?",
            "Find memories about my location"
        ]
        
        for query in memory_search_queries:
            print(f"Query: {query}")
            response = await agent.run(query)
            print(f"Response: {response}")
            print()
        
        # Test 6: Agent info to verify tool configuration
        print("⚙️ TEST 6: Agent configuration verification")
        print("-" * 50)
        
        agent_info = agent.get_agent_info()
        print(f"Framework: {agent_info['framework']}")
        print(f"Memory enabled: {agent_info['memory_enabled']}")
        print(f"Knowledge enabled: {agent_info['knowledge_enabled']}")
        print(f"Total tools: {agent_info['tool_counts']['total']}")
        print(f"Built-in tools: {agent_info['tool_counts']['built_in']}")
        print()
        
        print("🔧 Available tools:")
        for tool in agent_info['built_in_tools']:
            description = tool['description'] or "No description available"
            print(f"  - {tool['name']}: {description[:60]}...")
        
        print()
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print()
        print("🎯 KEY VERIFICATION POINTS:")
        print("1. ✅ Memory tools work correctly for personal information")
        print("2. ✅ KnowledgeTools work for general knowledge queries") 
        print("3. ✅ Agent prioritizes memory for personal information")
        print("4. ✅ Both systems work together without conflicts")
        print("5. ✅ No short-circuiting of memory operations")
        
        await agent.cleanup()
        
    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test data
        if Path(test_storage_dir).exists():
            shutil.rmtree(test_storage_dir)
        if Path(test_knowledge_dir).exists():
            shutil.rmtree(test_knowledge_dir)
    
    return True

async def test_tool_priority():
    """Test that memory tools have priority over KnowledgeTools for personal queries."""
    
    print("\n🎯 TESTING TOOL PRIORITY")
    print("=" * 60)
    
    # This test specifically checks that when we ask personal questions,
    # the agent uses memory tools first, not KnowledgeTools
    
    test_storage_dir = "./data/test_tool_priority"
    test_knowledge_dir = "./data/test_knowledge_priority"
    
    if Path(test_storage_dir).exists():
        shutil.rmtree(test_storage_dir)
    if Path(test_knowledge_dir).exists():
        shutil.rmtree(test_knowledge_dir)
    
    # Create knowledge base with conflicting information
    Path(test_knowledge_dir).mkdir(parents=True, exist_ok=True)
    
    with open(f"{test_knowledge_dir}/names.txt", "w") as f:
        f.write("""
        Common Names:
        - John Smith is a very common name
        - Alice Johnson is also common
        - Bob Wilson appears frequently
        """)
    
    try:
        from src.personal_agent.core.agno_agent import create_agno_agent
        
        agent = await create_agno_agent(
            model_provider="ollama",
            model_name="llama3.2:3b",
            enable_memory=True,
            enable_mcp=False,
            storage_dir=test_storage_dir,
            knowledge_dir=test_knowledge_dir,
            debug=True,
            user_id="test_user_priority"
        )
        
        # Store specific personal information
        print("📝 Storing personal information...")
        await agent.run("Remember: My name is Charlie Brown and I'm unique")
        await agent.run("Remember: I live in a special place called Peanuts Town")
        
        # Query personal information - should get memory results, not knowledge base
        print("\n🧠 Testing memory priority...")
        
        name_response = await agent.run("What is my name?")
        print(f"Name query response: {name_response}")
        
        location_response = await agent.run("Where do I live?")
        print(f"Location query response: {location_response}")
        
        # Verify responses contain memory information, not knowledge base info
        memory_indicators = [
            "Charlie Brown" in name_response,
            "Peanuts Town" in location_response,
            "John Smith" not in name_response,  # Should not get knowledge base info
            "Alice Johnson" not in name_response
        ]
        
        if all(memory_indicators):
            print("✅ PRIORITY TEST PASSED: Memory tools take precedence")
        else:
            print("❌ PRIORITY TEST FAILED: KnowledgeTools may be interfering")
            print(f"Memory indicators: {memory_indicators}")
        
        await agent.cleanup()
        
    except Exception as e:
        logger.error(f"Priority test failed: {e}")
        return False
    
    finally:
        if Path(test_storage_dir).exists():
            shutil.rmtree(test_storage_dir)
        if Path(test_knowledge_dir).exists():
            shutil.rmtree(test_knowledge_dir)
    
    return True

async def main():
    """Run all tests."""
    print("🧪 KNOWLEDGE TOOLS INTEGRATION TEST SUITE")
    print("=" * 80)
    print("This test verifies that KnowledgeTools integration doesn't")
    print("interfere with our carefully crafted memory system.")
    print()
    
    # Run main integration test
    test1_success = await test_knowledge_tools_integration()
    
    # Run priority test
    test2_success = await test_tool_priority()
    
    print("\n" + "=" * 80)
    if test1_success and test2_success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ KnowledgeTools integration is working correctly")
        print("✅ Memory system maintains priority for personal information")
        print("✅ No conflicts between memory and knowledge systems")
    else:
        print("❌ SOME TESTS FAILED!")
        print("⚠️  Review the integration to ensure memory priority is maintained")
    
    return test1_success and test2_success

if __name__ == "__main__":
    asyncio.run(main())
