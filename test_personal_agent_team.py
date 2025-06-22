#!/usr/bin/env python3
"""
Test script for the Personal Agent Team

This script tests the specialized agent team approach, validating that:
1. Individual agents work correctly
2. Team coordination functions properly
3. Memory agent specialization works as expected
4. All agents can be called through the team coordinator
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import LLM_MODEL, OLLAMA_URL, USER_ID, AGNO_STORAGE_DIR
from personal_agent.team.personal_agent_team import (
    PersonalAgentTeamWrapper,
    create_personal_agent_team,
)
from personal_agent.team.specialized_agents import (
    create_calculator_agent,
    create_finance_agent,
    create_memory_agent,
    create_web_research_agent,
)
from personal_agent.utils import setup_logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = setup_logging(__name__)


async def test_individual_agents():
    """Test individual specialized agents."""
    print("=" * 80)
    print("🧪 TESTING INDIVIDUAL SPECIALIZED AGENTS")
    print("=" * 80)

    # Test Memory Agent
    print("\n🧠 Testing Memory Agent...")
    try:
        memory_agent = create_memory_agent(
            storage_dir=AGNO_STORAGE_DIR,
            user_id=USER_ID,
            debug=True,
        )
        
        # Test storing a memory
        store_response = await memory_agent.arun("Please remember that I love hiking and outdoor activities.")
        print(f"✅ Memory storage: {store_response.content}")
        
        # Test querying memory
        query_response = await memory_agent.arun("What do you remember about my hobbies?")
        print(f"✅ Memory query: {query_response.content}")
        
    except Exception as e:
        print(f"❌ Memory Agent test failed: {e}")

    # Test Web Research Agent
    print("\n🌐 Testing Web Research Agent...")
    try:
        web_agent = create_web_research_agent(debug=True)
        response = await web_agent.arun("What are the top 3 AI news headlines today?")
        print(f"✅ Web research: {response.content[:200]}...")
    except Exception as e:
        print(f"❌ Web Research Agent test failed: {e}")

    # Test Finance Agent
    print("\n💰 Testing Finance Agent...")
    try:
        finance_agent = create_finance_agent(debug=True)
        response = await finance_agent.arun("Get the current stock price for AAPL")
        print(f"✅ Finance query: {response.content[:200]}...")
    except Exception as e:
        print(f"❌ Finance Agent test failed: {e}")

    # Test Calculator Agent
    print("\n🔢 Testing Calculator Agent...")
    try:
        calc_agent = create_calculator_agent(debug=True)
        response = await calc_agent.arun("Calculate the square root of 144")
        print(f"✅ Calculation: {response.content}")
    except Exception as e:
        print(f"❌ Calculator Agent test failed: {e}")


async def test_team_coordination():
    """Test the team coordination functionality."""
    print("\n" + "=" * 80)
    print("🤝 TESTING TEAM COORDINATION")
    print("=" * 80)

    try:
        # Create team
        team = create_personal_agent_team(
            storage_dir=AGNO_STORAGE_DIR,
            user_id=USER_ID,
            debug=True,
        )
        
        print(f"✅ Team created with {len(team.members)} members")
        
        # Test queries that should be delegated to different agents
        test_queries = [
            ("Memory test", "What do you remember about me?"),
            ("Web research test", "What's happening in AI news today?"),
            ("Finance test", "What's the current price of Tesla stock?"),
            ("Calculation test", "What's 15% of 250?"),
            ("Mixed test", "Remember that I'm interested in Tesla stock, then tell me its current price"),
        ]
        
        for test_name, query in test_queries:
            print(f"\n🔍 {test_name}: {query}")
            try:
                response = await team.arun(query, user_id=USER_ID)
                print(f"✅ Response: {response.content[:300]}...")
            except Exception as e:
                print(f"❌ {test_name} failed: {e}")
                
    except Exception as e:
        print(f"❌ Team coordination test failed: {e}")


async def test_team_wrapper():
    """Test the PersonalAgentTeamWrapper class."""
    print("\n" + "=" * 80)
    print("🎭 TESTING TEAM WRAPPER")
    print("=" * 80)

    try:
        # Create team wrapper
        team_wrapper = PersonalAgentTeamWrapper(
            storage_dir=AGNO_STORAGE_DIR,
            user_id=USER_ID,
            debug=True,
        )
        
        # Initialize
        success = await team_wrapper.initialize()
        if not success:
            print("❌ Team wrapper initialization failed")
            return
            
        print("✅ Team wrapper initialized successfully")
        
        # Test agent info
        agent_info = team_wrapper.get_agent_info()
        print(f"✅ Agent info: {agent_info['framework']} with {agent_info['member_count']} members")
        
        # Test queries
        test_queries = [
            "Hi! What can you help me with?",
            "Remember that I'm a software engineer who loves Python",
            "What do you know about me now?",
            "What's the latest news about artificial intelligence?",
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: {query}")
            try:
                response = await team_wrapper.run(query)
                print(f"✅ Response: {response[:200]}...")
                
                # Check tool calls
                tool_info = team_wrapper.get_last_tool_calls()
                if tool_info["has_tool_calls"]:
                    print(f"🛠️ Tool calls: {tool_info['tool_calls_count']}")
                    
            except Exception as e:
                print(f"❌ Query failed: {e}")
                
        # Cleanup
        await team_wrapper.cleanup()
        print("✅ Team wrapper cleanup completed")
        
    except Exception as e:
        print(f"❌ Team wrapper test failed: {e}")


async def test_memory_specialization():
    """Test that the memory agent properly specializes in memory operations."""
    print("\n" + "=" * 80)
    print("🧠 TESTING MEMORY SPECIALIZATION")
    print("=" * 80)

    try:
        team_wrapper = PersonalAgentTeamWrapper(
            storage_dir=AGNO_STORAGE_DIR,
            user_id=USER_ID,
            debug=True,
        )
        
        await team_wrapper.initialize()
        
        # Test memory-specific operations
        memory_tests = [
            "Please remember that I work at a tech startup in San Francisco",
            "Store this information: I prefer coffee over tea",
            "What do you remember about my work?",
            "What are my beverage preferences?",
            "Show me all my stored memories",
        ]
        
        for test in memory_tests:
            print(f"\n🧠 Memory test: {test}")
            try:
                response = await team_wrapper.run(test)
                print(f"✅ Response: {response[:300]}...")
            except Exception as e:
                print(f"❌ Memory test failed: {e}")
                
        await team_wrapper.cleanup()
        
    except Exception as e:
        print(f"❌ Memory specialization test failed: {e}")


async def main():
    """Main test function."""
    print("🚀 PERSONAL AGENT TEAM TEST SUITE")
    print(f"Model: {LLM_MODEL}")
    print(f"Ollama URL: {OLLAMA_URL}")
    print(f"User ID: {USER_ID}")
    print(f"Storage: {AGNO_STORAGE_DIR}")
    
    try:
        # Test individual agents
        await test_individual_agents()
        
        # Test team coordination
        await test_team_coordination()
        
        # Test team wrapper
        await test_team_wrapper()
        
        # Test memory specialization
        await test_memory_specialization()
        
        print("\n" + "=" * 80)
        print("🎉 ALL TESTS COMPLETED!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n👋 Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("💡 Make sure Ollama is running before starting tests")
    print("💡 This will test the new team-based approach")
    print()
    
    asyncio.run(main())
