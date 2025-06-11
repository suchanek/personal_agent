#!/usr/bin/env python3
"""
Test script to test Agno native memory functions and understand parameter validation.

This script directly tests the Agno memory system to understand how it works
and reproduce any validation errors that might occur during agent interactions.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_agno_memory_system():
    """Test the Agno native memory system."""
    print("🧠 Testing Agno Native Memory System")
    print("=" * 50)
    
    try:
        # Import Agno components
        from agno.agent import Agent
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.models.ollama import Ollama
        
        print("✅ Successfully imported Agno components")
        
        # Create memory system
        print("\n🔧 Creating memory system...")
        memory_db = SqliteMemoryDb(
            table_name="test_memory", 
            db_file="./data/test_memory.db"
        )
        
        memory = Memory(db=memory_db)
        print("✅ Memory system created")
        
        # Test user ID
        user_id = "test_user_eric"
        
        # Create agent with memory enabled
        print("\n🤖 Creating agent with memory enabled...")
        agent = Agent(
            model=Ollama(id="qwen2.5:7b-instruct"),
            user_id=user_id,
            memory=memory,
            enable_agentic_memory=True,
            enable_user_memories=True,
            debug_mode=True,
        )
        print("✅ Agent created with memory enabled")
        
        # Test adding user information
        print(f"\n📝 Testing memory storage for user: {user_id}")
        
        # Test different ways to store information
        test_information = [
            "My name is Eric and I am a software engineer",
            "I was born in 1985 and love programming in Python",
            "My favorite programming languages are Python, TypeScript, and Rust",
            "I work on AI agents and MCP integrations"
        ]
        
        print("\n💾 Storing test information...")
        for i, info in enumerate(test_information, 1):
            print(f"  {i}. Storing: {info[:50]}...")
            response = await agent.arun(f"Please remember this about me: {info}")
            print(f"     Response: {response.content[:100]}...")
        
        # Test memory retrieval
        print("\n🔍 Testing memory retrieval...")
        queries = [
            "What is my name?",
            "When was I born?", 
            "What are my favorite programming languages?",
            "What do you know about me?",
            "Tell me about my work experience"
        ]
        
        for query in queries:
            print(f"\n❓ Query: {query}")
            try:
                response = await agent.arun(query)
                print(f"✅ Response: {response.content[:200]}...")
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.error("Query failed: %s", e, exc_info=True)
        
        # Test direct memory access
        print("\n🔍 Testing direct memory access...")
        try:
            user_memories = memory.get_user_memories(user_id=user_id)
            print(f"✅ Found {len(user_memories)} user memories:")
            for i, mem in enumerate(user_memories, 1):
                print(f"  {i}. {mem.memory[:100]}...")
                print(f"     Topics: {mem.topics}")
                print(f"     Updated: {mem.last_updated}")
        except Exception as e:
            print(f"❌ Error accessing memories: {e}")
            logger.error("Memory access failed: %s", e, exc_info=True)
        
        # Test memory clearing
        print("\n🗑️ Testing memory clearing...")
        try:
            memory.clear()
            print("✅ Memory cleared successfully")
            
            # Verify clearing worked
            remaining_memories = memory.get_user_memories(user_id=user_id)
            print(f"✅ Remaining memories: {len(remaining_memories)}")
        except Exception as e:
            print(f"❌ Error clearing memory: {e}")
            logger.error("Memory clearing failed: %s", e, exc_info=True)
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure Agno is properly installed")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.error("Test failed: %s", e, exc_info=True)
        return False


async def test_agno_personal_agent_memory():
    """Test the personal agent's Agno memory integration."""
    print("\n🤖 Testing Personal Agent Agno Memory Integration")
    print("=" * 55)
    
    try:
        # Import personal agent components
        from personal_agent.core.agno_agent import create_agno_agent
        from personal_agent.core.agno_storage import create_agno_memory
        
        print("✅ Successfully imported personal agent components")
        
        # Create memory
        print("\n🧠 Creating Agno memory...")
        agno_memory = create_agno_memory("./data/test_agno")
        print("✅ Agno memory created")
        
        # Create agent
        print("\n🤖 Creating personal agent with Agno memory...")
        agent = await create_agno_agent(
            model_provider="ollama",
            model_name="qwen2.5:7b-instruct",
            enable_memory=True,
            enable_mcp=False,  # Disable MCP for this test
            storage_dir="./data/test_agno",
            debug=True
        )
        print("✅ Personal agent created")
        
        # Test agent info
        agent_info = agent.get_agent_info()
        print(f"📊 Agent info: {agent_info}")
        
        # Test running with memory
        print("\n💬 Testing agent conversation with memory...")
        queries = [
            "My name is Eric and I love building AI agents",
            "What is my name?",
            "What do I love doing?"
        ]
        
        for query in queries:
            print(f"\n❓ Query: {query}")
            try:
                response = await agent.run(query)
                print(f"✅ Response: {response[:200]}...")
            except Exception as e:
                print(f"❌ Error: {e}")
                logger.error("Agent query failed: %s", e, exc_info=True)
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Personal agent components may not be available")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        logger.error("Personal agent test failed: %s", e, exc_info=True)
        return False


async def test_memory_parameter_validation():
    """Test memory function parameter validation specifically."""
    print("\n🔍 Testing Memory Function Parameter Validation")
    print("=" * 50)
    
    try:
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory

        # Create memory system
        memory_db = SqliteMemoryDb(
            table_name="validation_test", 
            db_file="./data/validation_test.db"
        )
        memory = Memory(db=memory_db)
        
        print("✅ Memory system created for validation testing")
        
        # Test different parameter combinations
        test_cases = [
            # Valid cases
            {
                "description": "Valid user memory creation",
                "user_id": "test_user",
                "memory_text": "User likes Python programming",
                "should_succeed": True
            },
            {
                "description": "Empty user_id",
                "user_id": "",
                "memory_text": "Some memory",
                "should_succeed": False
            },
            {
                "description": "None user_id", 
                "user_id": None,
                "memory_text": "Some memory",
                "should_succeed": False
            },
            {
                "description": "Empty memory text",
                "user_id": "test_user",
                "memory_text": "",
                "should_succeed": False
            },
            {
                "description": "None memory text",
                "user_id": "test_user", 
                "memory_text": None,
                "should_succeed": False
            },
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}: {test_case['description']}")
            try:
                # Test creating user memory directly
                memory.create_user_memory(
                    user_id=test_case["user_id"],
                    memory=test_case["memory_text"]
                )
                
                if test_case["should_succeed"]:
                    print("✅ Test passed - memory created successfully")
                else:
                    print("❌ Test failed - should have raised validation error")
                    
            except Exception as e:
                if test_case["should_succeed"]:
                    print(f"❌ Test failed - unexpected error: {e}")
                else:
                    print(f"✅ Test passed - expected validation error: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Parameter validation test error: {e}")
        logger.error("Parameter validation test failed: %s", e, exc_info=True)
        return False


async def main():
    """Run all memory tests."""
    print("🚀 Starting Agno Memory Function Tests")
    print("=" * 60)
    
    # Ensure data directory exists
    Path("./data").mkdir(exist_ok=True)
    
    test_results = []
    
    # Test 1: Basic Agno memory system
    result1 = await test_agno_memory_system()
    test_results.append(("Agno Memory System", result1))
    
    # Test 2: Personal agent memory integration  
    result2 = await test_agno_personal_agent_memory()
    test_results.append(("Personal Agent Memory", result2))
    
    # Test 3: Parameter validation
    result3 = await test_memory_parameter_validation()
    test_results.append(("Parameter Validation", result3))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, success in test_results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    total_passed = sum(test_results[i][1] for i in range(len(test_results)))
    print(f"\nTotal: {total_passed}/{len(test_results)} tests passed")
    
    if total_passed == len(test_results):
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed - check logs for details")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
