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
        sample_content = """Name: Eric G. Suchanek
Role: Software Developer and AI Enthusiast
Location: California
Interests: Python development, AI agents, automation, MCP tools
Projects: Personal AI Agent with Agno framework integration
Skills: Python, JavaScript, AI/ML, software architecture
Goals: Building intelligent automation systems
"""
        sample_file.write_text(sample_content.strip())
        logger.info(f"Created sample knowledge file: {sample_file}")
        return True
    else:
        logger.info(f"Sample knowledge file already exists: {sample_file}")
        return False


async def test_agent_initialization():
    """Test comprehensive agent initialization."""
    print("🔄 Testing Agno Personal Agent Initialization...")
    print(f"📁 DATA_DIR: {DATA_DIR}")
    print(f"🤖 LLM_MODEL: {LLM_MODEL}")
    print()

    # Create sample knowledge file
    print("📝 Creating sample knowledge file...")
    create_sample_knowledge_file()
    print()

    # Initialize agent
    print("🚀 Initializing AgnoPersonalAgent...")
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        enable_memory=True,
        enable_mcp=False,  # Disable MCP for focused testing
        storage_dir=f"{DATA_DIR}/agno",
        knowledge_dir=f"{DATA_DIR}/knowledge",
        debug=True,  # Enable debug mode
    )

    # Test initialization
    try:
        success = await agent.initialize()
        print(f"✅ Agent initialization: {'SUCCESS' if success else 'FAILED'}")
        print()

        if success:
            # Test agent components
            print("🔍 Testing agent components:")

            # Check storage
            if agent.agno_storage:
                print("✅ Storage: Initialized")
            else:
                print("❌ Storage: Not initialized")

            # Check memory
            if agent.agno_memory:
                print("✅ Memory: Initialized")
            else:
                print("❌ Memory: Not initialized")

            # Check knowledge base
            if agent.agno_knowledge:
                print("✅ Knowledge Base: Initialized")
                print(f"   Type: {type(agent.agno_knowledge).__name__}")
            else:
                print("❌ Knowledge Base: Not initialized")

            # Check agent instance
            if agent.agent:
                print("✅ Agent Instance: Created")
                print(
                    f"   Tools available: {len(agent.agent.tools) if agent.agent.tools else 0}"
                )
                if agent.agent.tools:
                    for i, tool in enumerate(agent.agent.tools, 1):
                        tool_name = getattr(
                            tool, "__name__", getattr(tool, "name", str(tool))
                        )
                        print(f"   {i}. {tool_name}")
            else:
                print("❌ Agent Instance: Not created")

            print()

            # Test directories
            print("📂 Checking directories:")
            storage_dir = Path(f"{DATA_DIR}/agno")
            knowledge_dir = Path(f"{DATA_DIR}/knowledge")

            print(f"   Storage: {'✅' if storage_dir.exists() else '❌'} {storage_dir}")
            print(
                f"   Knowledge: {'✅' if knowledge_dir.exists() else '❌'} {knowledge_dir}"
            )

            # Check knowledge files
            knowledge_files = list(knowledge_dir.glob("*.txt")) + list(
                knowledge_dir.glob("*.md")
            )
            print(f"   Knowledge files: {len(knowledge_files)}")
            for kf in knowledge_files:
                print(f"     - {kf.name}")

            print()

            # Test simple interaction
            print("💬 Testing simple interaction...")
            try:
                response = await agent.run("Hello! Can you tell me about yourself?")
                print(f"Response: {response}")
                print()

                # Test memory-related query
                print("🧠 Testing memory query...")
                memory_response = await agent.run(
                    "What do you know about me from your knowledge base?"
                )
                print(f"Memory Response: {memory_response}")

            except Exception as e:
                print(f"❌ Interaction test failed: {e}")

        else:
            print("❌ Cannot test components - initialization failed")

    except Exception as e:
        logger.error(f"Agent initialization failed: {e}")
        print(f"❌ Initialization error: {e}")
        return False

    return success


async def main():
    """Main test function."""
    print("=" * 80)
    print("🧪 AGNO AGENT INITIALIZATION TEST")
    print("=" * 80)
    print()

    success = await test_agent_initialization()

    print()
    print("=" * 80)
    print(f"🏁 Test Result: {'✅ SUCCESS' if success else '❌ FAILED'}")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
