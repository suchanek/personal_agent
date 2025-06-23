#!/usr/bin/env python3
"""
Test script to verify that the AgnoPersonalAgent web search functionality works correctly.
This tests the same configuration used in the Streamlit app.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL, USER_ID
from personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_web_search():
    """Test web search functionality with the fixed agent configuration."""
    
    print("🔧 Creating AgnoPersonalAgent with MCP disabled...")
    
    # Create agent with same configuration as fixed Streamlit app
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        user_id=USER_ID,
        debug=True,
        enable_memory=True,
        enable_mcp=False,  # Disabled to avoid conflicts with DuckDuckGo tools
        storage_dir=AGNO_STORAGE_DIR,
    )
    
    print("🚀 Initializing agent...")
    await agent.initialize()
    
    print("📋 Agent configuration:")
    agent_info = agent.get_agent_info()
    print(f"  - MCP enabled: {agent_info['mcp_enabled']}")
    print(f"  - Total tools: {agent_info['tool_counts']['total']}")
    print(f"  - Built-in tools: {agent_info['tool_counts']['built_in']}")
    print(f"  - MCP tools: {agent_info['tool_counts']['mcp']}")
    
    if agent_info['built_in_tools']:
        print("  - Available built-in tools:")
        for tool in agent_info['built_in_tools']:
            print(f"    * {tool['name']}")
    
    print("\n🔍 Testing web search for Middle East unrest headlines...")
    
    try:
        # Test the web search functionality
        query = "list the top 5 headlines about the unrest in the middle east"
        response = await agent.run(query)
        
        print("\n📰 Agent Response:")
        print("=" * 60)
        print(response)
        print("=" * 60)
        
        # Check if the response contains actual headlines or Python code
        if "import" in response and "bss.call" in response:
            print("\n❌ ISSUE: Agent is still returning Python code!")
            print("The MCP server is still being used despite being disabled.")
        elif "headlines" in response.lower() or "news" in response.lower():
            print("\n✅ SUCCESS: Agent is providing actual news content!")
            print("The DuckDuckGo search tools are working correctly.")
        else:
            print("\n⚠️ UNCLEAR: Response doesn't contain obvious Python code or news content.")
            print("Manual review needed.")
            
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("\n🧹 Cleaning up agent...")
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(test_web_search())
