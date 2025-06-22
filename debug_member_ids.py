#!/usr/bin/env python3
"""
Debug script to check member IDs in the team.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.team.personal_agent_team import PersonalAgentTeamWrapper
from personal_agent.config import LLM_MODEL, OLLAMA_URL


async def debug_member_ids():
    """Debug the member IDs in the team."""
    print("🔍 Debugging Team Member IDs")
    print("=" * 40)
    
    # Initialize the team wrapper
    team_wrapper = PersonalAgentTeamWrapper(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        storage_dir="./data/agno",
        user_id="test_user",
        debug=True,
    )
    
    # Initialize the team
    success = await team_wrapper.initialize()
    if not success:
        print("❌ Failed to initialize team")
        return
    
    print("✅ Team initialized successfully")
    print(f"📊 Team mode: {team_wrapper.team.mode}")
    
    # Print member information
    print("\n👥 Team Members:")
    for i, member in enumerate(team_wrapper.team.members):
        print(f"\n{i+1}. Member:")
        print(f"   Name: {getattr(member, 'name', 'Unknown')}")
        print(f"   Agent ID: {getattr(member, 'agent_id', 'None')}")
        print(f"   Role: {getattr(member, 'role', 'Unknown')}")
        
        # Get the URL-safe member ID using the team's method
        url_safe_id = team_wrapper.team._get_member_id(member)
        print(f"   URL-safe ID: {url_safe_id}")
        
        # Show tools
        tools = getattr(member, 'tools', [])
        print(f"   Tools: {len(tools)} tools")
        if tools:
            for j, tool in enumerate(tools[:3]):  # Show first 3 tools
                tool_name = getattr(tool, '__name__', str(type(tool).__name__))
                print(f"     - {tool_name}")
            if len(tools) > 3:
                print(f"     ... and {len(tools) - 3} more")


if __name__ == "__main__":
    asyncio.run(debug_member_ids())
