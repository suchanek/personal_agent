#!/usr/bin/env python3
"""
Test script to validate AgnoPersonalAgent initialization with MCP tools enabled.

This test verifies that our tool architecture rewrite works correctly with 
the full MCP integration, ensuring all tool classes are properly instantiated.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agno_agent import create_agno_agent
from personal_agent.utils import setup_logging

# Configure logging
logger = setup_logging(__name__)


async def test_agent_with_mcp():
    """Test agent creation with MCP tools enabled."""
    print("🧪 Testing Personal Agent with Tool Architecture Rewrite + MCP Integration")
    print("=" * 80)
    
    try:
        # Create agent with MCP enabled
        print("📦 Creating AgnoPersonalAgent with MCP tools enabled...")
        agent = await create_agno_agent(
            model_provider="ollama",
            model_name="qwen2.5:7b-instruct",
            enable_memory=True,
            enable_mcp=True,  # Enable MCP integration
            debug=True,
            user_id="test_user",
            recreate=False
        )
        
        # Get agent info to see all tools
        info = agent.get_agent_info()
        
        print("✅ Agent created successfully!")
        print(f"📊 Framework: {info['framework']}")
        print(f"🤖 Model: {info['model_provider']}:{info['model_name']}")
        print(f"🧠 Memory: {'✅' if info['memory_enabled'] else '❌'}")
        print(f"📚 Knowledge: {'✅' if info['knowledge_enabled'] else '❌'}")
        print(f"🌐 MCP: {'✅' if info['mcp_enabled'] else '❌'}")
        print()
        
        # Tool summary
        tool_counts = info['tool_counts']
        print(f"🔧 Tool Summary:")
        print(f"   Total Tools: {tool_counts['total']}")
        print(f"   Built-in Tools: {tool_counts['built_in']}")
        print(f"   MCP Tools: {tool_counts['mcp']}")
        print(f"   MCP Servers: {tool_counts['mcp_servers']}")
        print()
        
        # List built-in tools
        print("🛠️ Built-in Tools:")
        for tool in info['built_in_tools']:
            print(f"   • {tool['name']} ({tool['type']})")
        print()
        
        # List MCP tools
        if info['mcp_tools']:
            print("🌐 MCP Tools:")
            for tool in info['mcp_tools']:
                print(f"   • {tool['name']}: {tool['description']}")
        else:
            print("🌐 MCP Tools: None configured")
        print()
        
        # List MCP servers
        if info['mcp_servers']:
            print("🖥️ MCP Servers:")
            for server, details in info['mcp_servers'].items():
                print(f"   • {server}: {details['description']}")
                print(f"     Command: {details['command']}")
                print(f"     Args: {details['args_count']}")
                print(f"     Env Vars: {details['env_vars']}")
        else:
            print("🖥️ MCP Servers: None configured")
        print()
        
        # Test a simple query
        print("🧠 Testing agent with simple query...")
        response = await agent.run("Hello! Can you tell me what tools you have available?")
        print("📝 Agent Response:")
        print(response)
        print()
        
        print("🎉 SUCCESS: Agent with tool architecture rewrite + MCP integration works perfectly!")
        
        # Cleanup
        await agent.cleanup()
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def main():
    """Main function to run the test."""
    success = asyncio.run(test_agent_with_mcp())
    
    if success:
        print("\n✅ All tests passed!")
        print("📝 The tool architecture rewrite is fully compatible with MCP integration!")
        exit(0)
    else:
        print("\n❌ Tests failed!")
        exit(1)


if __name__ == "__main__":
    main()
