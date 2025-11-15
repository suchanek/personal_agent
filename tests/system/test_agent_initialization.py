#!/usr/bin/env python3
"""Test script to verify agent initialization with memory and knowledge base."""

import asyncio
import logging
from pathlib import Path

from src.personal_agent.config import DATA_DIR, LLM_MODEL
from src.personal_agent.core.agno_agent import AgnoPersonalAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


def create_sample_knowledge_file():
    """Create a sample knowledge file for testing."""
    knowledge_dir = Path(f"{DATA_DIR}/knowledge")
    knowledge_dir.mkdir(parents=True, exist_ok=True)

    sample_file = knowledge_dir / "user_profile.txt"
    if not sample_file.exists():
        with open(sample_file, "w") as f:
            f.write(
                """User Information
=================
Name: Eric G. Suchanek
Location: User's home directory is /Users/egs
System: macOS with default shell bash

Personal Preferences:
- Programming languages: Python, TypeScript
- Frameworks: Agno, MCP integration
- Tools: VS Code, Terminal, GitHub

Project Context:
- Working on Personal AI Agent
- Migrating from Weaviate to Agno storage
- Using Ollama with qwen3:1.7B model
- Data directory: /Users/egs/data
"""
            )
        print(f"Created sample knowledge file: {sample_file}")
    else:
        print(f"Sample knowledge file already exists: {sample_file}")


async def test_agent_initialization():
    """Test agent initialization with memory and knowledge base."""
    print("🔄 Testing Agent Initialization...")
    print(f"📁 DATA_DIR: {DATA_DIR}")
    print(f"🤖 LLM_MODEL: {LLM_MODEL}")
    print()

    # Create sample knowledge file for testing
    create_sample_knowledge_file()
    print()

    # Initialize agent
    print("🚀 Initializing AgnoPersonalAgent...")
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        enable_memory=True,
        enable_mcp=False,
        storage_dir=f"{DATA_DIR}/agno",
        knowledge_dir=f"{DATA_DIR}/knowledge",
        debug=True,  # Enable debug to see tool calls
    )

    success = await agent.initialize(recreate=False)
    if not success:
        print("❌ Failed to initialize agent")
        return False

    print("✅ Agent initialized successfully")
    print()

    # Print agent information
    try:
        agent_info = agent.get_agent_info()
        print("📊 Agent Information:")
        print(f"  Model: {agent_info['model_provider']}:{agent_info['model_name']}")
        print(f"  Memory: {agent_info['memory_enabled']}")
        print(
            f"  MCP: {agent_info['mcp_enabled']} ({agent_info['mcp_servers']} servers)"
        )
        print(f"  Debug: {agent_info['debug_mode']}")
        print()
    except Exception as e:
        print(f"❌ Failed to get agent info: {e}")
        print()

    # Verify knowledge base is loaded
    if agent.agno_knowledge:
        print("✅ Knowledge base is loaded")
    else:
        print("❌ Knowledge base is not loaded")
    print()

    # Test a simple query
    print("💬 Testing simple query...")
    query = "Hello, who are you?"

    try:
        response = await agent.run(query)
        print(f"Query: {query}")
        print(f"Response: {response}")
        print()
    except Exception as e:
        print(f"❌ Failed to run query: {e}")
        print()

    # Test a knowledge base query
    print("💬 Testing knowledge base query...")
    query = "What do you know about me?"

    try:
        response = await agent.run(query)
        print(f"Query: {query}")
        print(f"Response: {response}")
        print()
    except Exception as e:
        print(f"❌ Failed to run query: {e}")
        print()

    print("✅ Agent initialization test completed")
    return True


async def main():
    """Run the test asynchronously."""
    await test_agent_initialization()


if __name__ == "__main__":
    asyncio.run(main())
