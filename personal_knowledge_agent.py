#!/usr/bin/env python3
"""
Personal Agent Knowledge Example using Combined Knowledge Bases

This script mirrors the knowledge_agent_example.py but uses our personal agent
paths and configuration. It demonstrates creating an agent with combined
knowledge bases that automatically searches without explicit KnowledgeTools imports.

The agent uses:
- Combined knowledge bases from multiple sources
- PgVector for vector storage
- Automatic knowledge search capabilities
- No explicit model configuration (uses defaults)
"""

import asyncio
import logging
from pathlib import Path

from agno.agent import Agent
from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.text import TextKnowledgeBase
from agno.models.ollama import Ollama
from agno.vectordb.lancedb import LanceDb, SearchType

from src.personal_agent.config import DATA_DIR, LLM_MODEL, OLLAMA_URL

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

# Vector database configuration using LanceDB
vector_db_path = f"{DATA_DIR}/agno/personal_agent_lancedb"


def create_personal_knowledge_agent() -> tuple[Agent, TextKnowledgeBase]:
    """
    Create an agent with text knowledge base using our personal data paths.

    Note: Simplified to use single TextKnowledgeBase to avoid CombinedKnowledgeBase
    async generator bug in agno framework.

    :return: Tuple of (Agent instance, TextKnowledgeBase) for knowledge loading
    """
    # Define our data paths
    knowledge_dir = Path(f"{DATA_DIR}/knowledge")
    storage_path = Path(vector_db_path)
    storage_path.mkdir(parents=True, exist_ok=True)

    logger.info("Creating knowledge base with paths:")
    logger.info(f"  Text knowledge: {knowledge_dir}")
    logger.info(f"  Vector storage: {storage_path}")

    # Create embedder
    embedder = OllamaEmbedder(id="nomic-embed-text", host=OLLAMA_URL, dimensions=768)

    # Check if knowledge files exist
    if knowledge_dir.exists():
        text_files = list(knowledge_dir.glob("*.txt")) + list(
            knowledge_dir.glob("*.md")
        )
        if text_files:
            logger.info(f"Found {len(text_files)} text files in {knowledge_dir}")

            # Create single TextKnowledgeBase (avoiding CombinedKnowledgeBase bug)
            knowledge_base = TextKnowledgeBase(
                path=knowledge_dir,
                vector_db=LanceDb(
                    uri=str(storage_path / "personal_knowledge"),
                    table_name="personal_documents",
                    search_type=SearchType.hybrid,
                    embedder=embedder,
                ),
            )
            logger.info("✅ Created TextKnowledgeBase")
        else:
            logger.warning(f"No text files found in {knowledge_dir}")
            raise ValueError("No knowledge files found")
    else:
        logger.warning(f"Knowledge directory does not exist: {knowledge_dir}")
        raise ValueError("Knowledge directory not found")

    # Create agent with knowledge base
    # Note: No explicit model or KnowledgeTools - agent gets these automatically!
    agent = Agent(
        name="Personal Knowledge Agent",
        knowledge=knowledge_base,
        search_knowledge=True,  # This enables automatic knowledge search
        show_tool_calls=True,  # Show what tools the agent uses
        markdown=True,  # Format responses in markdown
        enable_agentic_memory=True,
        model=Ollama(
            id=LLM_MODEL,
            host=OLLAMA_URL,
        ),
        instructions=[
            "You are a personal AI assistant with access to my knowledge base.",
            "Always search your knowledge base when asked about personal information.",
            "Provide detailed responses based on the information you find.",
            "If you can't find specific information, say so clearly.",
            "Include relevant details from the knowledge base in your responses.",
        ],
    )

    logger.info("✅ Created Personal Knowledge Agent")
    logger.info(f"   Search enabled: {agent.search_knowledge}")
    logger.info(f"   Show tool calls: {agent.show_tool_calls}")

    return agent, knowledge_base


async def test_personal_knowledge_agent() -> None:
    """Test the personal knowledge agent with various queries."""
    logger.info("🚀 Testing Personal Knowledge Agent")
    print("=" * 80)
    print("🤖 PERSONAL KNOWLEDGE AGENT TEST")
    print("=" * 80)

    try:
        # Create agent
        agent, knowledge_base = create_personal_knowledge_agent()

        # Load knowledge base
        print("\n📚 Loading knowledge base...")
        await knowledge_base.aload(recreate=False)
        print("✅ Knowledge base loaded successfully")

        # Test queries
        test_queries = [
            "What do you know about me?",
            "What is my name?",
            "Tell me about my skills and interests",
            "What information do you have in your knowledge base?",
            "Who am I and what do I do?",
        ]

        print(f"\n💬 Testing {len(test_queries)} queries...")
        print("=" * 60)

        for i, query in enumerate(test_queries, 1):
            print(f"\n🔍 Query {i}: {query}")
            print("-" * 40)

            try:
                response = await agent.arun(query)
                print(f"🤖 Response: {response}")

            except Exception as e:
                print(f"❌ Error: {e}")

            print("-" * 40)

        print("\n✅ Testing completed!")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        print(f"❌ Test failed: {e}")


async def interactive_mode() -> None:
    """Run the agent in interactive mode."""
    logger.info("🎯 Starting Interactive Mode")
    print("=" * 80)
    print("🤖 INTERACTIVE PERSONAL KNOWLEDGE AGENT")
    print("=" * 80)
    print("Type 'quit' or 'exit' to stop")
    print()

    try:
        # Create and load agent
        agent, knowledge_base = create_personal_knowledge_agent()

        print("📚 Loading knowledge base...")
        await knowledge_base.aload(recreate=False)
        print("✅ Knowledge base ready!")
        print()

        # Interactive loop
        while True:
            try:
                query = input("💬 Ask me something: ").strip()

                if query.lower() in ["quit", "exit", "q"]:
                    print("👋 Goodbye!")
                    break

                if not query:
                    continue

                print("\n🤖 Thinking...")
                response = await agent.arun(query)
                print(f"\n📝 Response:\n{response}\n")
                print("-" * 60)

            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    except Exception as e:
        logger.error(f"Interactive mode failed: {e}")
        print(f"❌ Failed to start interactive mode: {e}")


async def main() -> None:
    """Main function with options for testing or interactive mode."""
    print("🚀 PERSONAL KNOWLEDGE AGENT")
    print("Choose mode:")
    print("1. Run test queries")
    print("2. Interactive mode")
    print("3. Both")

    try:
        choice = input("\nEnter choice (1/2/3): ").strip()

        if choice == "1":
            await test_personal_knowledge_agent()
        elif choice == "2":
            await interactive_mode()
        elif choice == "3":
            await test_personal_knowledge_agent()
            print("\n" + "=" * 80)
            await interactive_mode()
        else:
            print("Invalid choice. Running test mode by default.")
            await test_personal_knowledge_agent()

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Main execution failed: {e}")
        print(f"❌ Execution failed: {e}")


if __name__ == "__main__":
    # Make sure virtual environment is activated
    print("💡 Make sure to run: source .venv/bin/activate")
    print("💡 Make sure Ollama is running for embeddings")
    print()

    asyncio.run(main())
