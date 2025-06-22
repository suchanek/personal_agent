#!/usr/bin/env python3
"""
Test script to debug route mode execution.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.team.personal_agent_team import PersonalAgentTeamWrapper
from personal_agent.config import LLM_MODEL, OLLAMA_URL


async def test_route_execution():
    """Test route mode execution in detail."""
    print("🔍 Testing Route Mode Execution")
    print("=" * 40)
    
    # Initialize the team wrapper
    team_wrapper = PersonalAgentTeamWrapper(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        storage_dir="./data/agno",
        user_id="test_user",
        debug=True,  # Enable debug mode
    )
    
    # Initialize the team
    success = await team_wrapper.initialize()
    if not success:
        print("❌ Failed to initialize team")
        return
    
    print("✅ Team initialized successfully")
    print(f"📊 Team mode: {team_wrapper.team.mode}")
    
    # Test a simple calculation
    print("\n🧮 Testing Calculator Query:")
    print("Query: 'What is 2 + 2?'")
    print("-" * 30)
    
    try:
        response = await team_wrapper.run("What is 2 + 2?")
        print(f"Response: {response}")
        print(f"Response length: {len(response)} chars")
        
        # Check if we got a proper calculation result
        if "4" in response and ("2 + 2" in response or "addition" in response.lower()):
            print("✅ Calculator routing and execution working!")
        else:
            print("❌ Calculator routing or execution failed")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_route_execution())
