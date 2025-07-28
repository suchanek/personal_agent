#!/usr/bin/env python3
"""
Simple test to verify team memory sharing without heavy initialization.
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


async def test_simple_team_memory():
    """Test basic team memory functionality without heavy initialization."""
    print("🧪 Testing Simple Team Memory")
    print("=" * 40)
    
    try:
        from agno.agent import Agent
        from agno.memory.v2.db.sqlite import SqliteMemoryDb
        from agno.memory.v2.memory import Memory
        from agno.team.team import Team
        from agno.models.ollama.tools import OllamaTools
        
        from src.personal_agent.config.settings import LLM_MODEL, OLLAMA_URL
        from src.personal_agent.core.agent_model_manager import AgentModelManager
        
        print("✅ Imports successful")
        
        # Create a simple shared memory system
        memory_db = SqliteMemoryDb(
            table_name="simple_test_memory",
            db_file="tmp/simple_test_memory.db"
        )
        
        # Create model manager
        model_manager = AgentModelManager(
            model_provider="ollama",
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            seed=None,
        )
        model = model_manager.create_model()
        
        shared_memory = Memory(
            model=model,
            db=memory_db
        )
        
        print("✅ Shared memory created")
        
        # Create a simple memory agent
        memory_agent = Agent(
            name="Simple Memory Agent",
            role="Store and retrieve information",
            model=model,
            memory=shared_memory,
            agent_id="memory-agent",
            instructions=[
                "You help store and retrieve information.",
                "When asked to remember something, acknowledge it.",
                "When asked what you remember, provide what you know."
            ]
        )
        
        print("✅ Memory agent created")
        
        # Create a simple team
        team = Team(
            name="Simple Test Team",
            mode="coordinate",
            model=model,
            memory=shared_memory,  # Shared memory
            members=[memory_agent],
            instructions=[
                "You are a simple test team.",
                "Use the memory agent for memory tasks."
            ],
            enable_agentic_context=True,
            share_member_interactions=True,
        )
        
        print("✅ Team created with shared memory")
        print(f"📊 Team has {len(team.members)} members")
        print(f"📊 Team memory: {type(team.memory).__name__}")
        
        # Test basic functionality
        print("\n🚀 Testing basic memory storage...")
        response = await team.arun("Remember that I like testing software")
        print(f"📝 Response: {response.content[:100]}...")
        
        print("\n🚀 Testing memory retrieval...")
        response2 = await team.arun("What do you remember about me?")
        print(f"📝 Response: {response2.content[:100]}...")
        
        print("\n✅ Simple team memory test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the simple test."""
    success = await test_simple_team_memory()
    if success:
        print("\n🎉 Team memory sharing is working!")
    else:
        print("\n💥 Team memory sharing needs more work")


if __name__ == "__main__":
    asyncio.run(main())
