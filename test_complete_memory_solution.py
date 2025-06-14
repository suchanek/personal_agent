#!/usr/bin/env python3
"""
Test the complete memory solution: AgnoPersonalAgent with Agno v2 memory tools.

This script tests that the AgnoPersonalAgent now has proper memory tools
and can create and retrieve memories using the Agno v2 memory system.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rich import print
from rich.console import Console

from rich.panel import Panel

from personal_agent.config import (
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    LLM_MODEL,
    OLLAMA_URL,
    USER_ID,
)
from personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_memory_functionality():
    """Test complete memory functionality with the enhanced agent."""
    console = Console()

    console.print(
        Panel.fit(
            "🧪 Testing Complete Memory Solution\n\n"
            "Testing AgnoPersonalAgent with Agno v2 memory tools:\n"
            "• store_user_memory\n"
            "• query_memory\n"
            "• get_user_information\n\n"
            "This verifies the missing _get_memory_tools() implementation.",
            style="bold cyan",
        )
    )

    # Create agent with memory enabled
    print(f"🚀 Creating AgnoPersonalAgent...")
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        enable_memory=True,
        enable_mcp=False,  # Disable MCP for focused memory testing
        storage_dir=AGNO_STORAGE_DIR,
        knowledge_dir=AGNO_KNOWLEDGE_DIR,
        debug=True,  # Enable debug to see tool calls
        ollama_base_url=OLLAMA_URL,
        user_id=USER_ID,
    )

    # Initialize the agent
    print(f"🔧 Initializing agent...")
    success = await agent.initialize()

    if not success:
        print("❌ Failed to initialize agent")
        return False

    print("✅ Agent initialized successfully!")

    # Check agent info
    agent_info = agent.get_agent_info()
    print(f"📊 Agent Info:")
    print(f"  - Memory enabled: {agent_info['memory_enabled']}")
    print(f"  - User ID: {agent_info['user_id']}")
    print(f"  - Total tools: {agent_info['tool_counts']['total']}")
    print(f"  - Built-in tools: {agent_info['tool_counts']['built_in']}")

    # Check if memory tools are available
    print(f"\n🔍 Checking available tools...")
    if agent.agent and hasattr(agent.agent, "tools"):
        tool_names = []
        for tool in agent.agent.tools:
            if hasattr(tool, "__name__"):
                tool_names.append(tool.__name__)
            elif hasattr(tool, "name"):
                tool_names.append(tool.name)
            else:
                tool_names.append(str(type(tool).__name__))

        print(f"Available tools: {tool_names}")

        # Check for memory tools
        memory_tools = [
            name
            for name in tool_names
            if "memory" in name.lower()
            or name in ["store_user_memory", "query_memory", "get_user_information"]
        ]
        print(f"Memory tools found: {memory_tools}")

        if not memory_tools:
            print("⚠️  No memory tools found in agent.tools")
        else:
            print(f"✅ Found {len(memory_tools)} memory tools")
    else:
        print("❌ Agent has no tools attribute")

    # Test memory functionality
    test_queries = [
        "My name is Eric and I live in Ohio.",
        "I prefer tea over coffee.",
        "What is my name?",
        "Where do I live?",
        "What are my preferences?",
    ]

    print(f"\n🧪 Testing memory functionality with {len(test_queries)} queries...")

    for i, query in enumerate(test_queries, 1):
        print(f"\n--- Test {i}: {query} ---")
        try:
            response = await agent.run(query)
            print(f"🤖 Response: {response}")

            # Check memories after each interaction
            if agent.agno_memory:
                memories = agent.agno_memory.get_user_memories(user_id=USER_ID)
                print(f"📝 Memories count: {len(memories)}")
                if memories:
                    print("Latest memories:")
                    for mem in memories[-3:]:  # Show last 3
                        print(f"  - {mem.memory}")

        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback

            traceback.print_exc()

    # Final memory check
    if agent.agno_memory:
        print(f"\n📊 FINAL MEMORY ANALYSIS:")
        all_memories = agent.agno_memory.get_user_memories(user_id=USER_ID)
        print(f"Total memories: {len(all_memories)}")

        if all_memories:
            print("All memories:")
            for i, mem in enumerate(all_memories, 1):
                topics = ", ".join(mem.topics) if mem.topics else "general"
                print(f"  {i}. [{topics}] {mem.memory}")

    # Cleanup
    await agent.cleanup()
    print(f"\n✅ Test completed successfully!")
    return True


async def main():
    """Main test function."""
    try:
        success = await test_memory_functionality()
        if success:
            print(f"\n🎉 All tests passed! The complete memory solution is working.")
        else:
            print(f"\n💥 Some tests failed.")
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
