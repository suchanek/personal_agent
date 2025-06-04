#!/usr/bin/env python3
"""
Migration Plan: Personal Agent to SQLite + LanceDB (Simplest)
=============================================================

This approach uses only local storage, eliminating all external database dependencies.
Perfect for personal use, development, and simple deployments.

Benefits:
- Zero external dependencies (no Docker, no servers)
- File-based storage (easy backup/restore)
- Fast local performance
- Simple deployment
"""

from pathlib import Path

from agno.agent import Agent
from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.text import TextKnowledgeBase
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama import Ollama
from agno.storage.agent.sqlite import SqliteAgentStorage
from agno.vectordb.lancedb import LanceDb, SearchType

# Local file paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def create_sqlite_based_agent():
    """Create fully local agent with SQLite + LanceDB storage."""

    # 1. SQLite Memory System
    memory = Memory(
        db=SqliteMemoryDb(
            table_name="personal_agent_memory", db_file=str(DATA_DIR / "memory.db")
        ),
        model=Ollama(id="qwen2.5:7b-instruct"),
    )

    # 2. LanceDB Knowledge Base (local vector storage)
    knowledge = TextKnowledgeBase(
        path=str(DATA_DIR / "knowledge"),
        vector_db=LanceDb(
            table_name="personal_agent_knowledge",
            uri=str(DATA_DIR / "lancedb"),  # Local directory
            search_type=SearchType.hybrid,
            embedder=OllamaEmbedder(id="nomic-embed-text", dimensions=768),
        ),
        formats=[".txt", ".md", ".json"],
    )

    # 3. SQLite Agent Storage
    storage = SqliteAgentStorage(
        table_name="personal_agent_sessions", db_file=str(DATA_DIR / "agents.db")
    )

    # 4. Create the Agent
    agent = Agent(
        name="Personal AI Assistant",
        model=Ollama(id="qwen2.5:7b-instruct"),
        # Memory capabilities
        memory=memory,
        enable_agentic_memory=True,
        enable_user_memories=True,
        enable_session_summaries=True,
        # Knowledge capabilities
        knowledge=knowledge,
        search_knowledge=True,
        # Session management
        storage=storage,
        # Instructions
        instructions=[
            "You are a helpful personal assistant with persistent memory.",
            "Use your knowledge base to provide informed responses.",
            "Remember important user information across sessions.",
        ],
        # Enhanced features
        add_datetime_to_instructions=True,
        read_chat_history=True,
        markdown=True,
    )

    return agent


def show_file_structure():
    """Show the resulting file structure."""

    print("📁 Resulting File Structure:")
    print("data/")
    print("├── memory.db           # SQLite conversation memory")
    print("├── agents.db           # SQLite session storage")
    print("├── lancedb/            # LanceDB vector storage")
    print("│   └── personal_agent_knowledge/")
    print("└── knowledge/          # Your facts as text files")
    print("    ├── facts.txt")
    print("    ├── preferences.md")
    print("    └── conversations.json")


def migration_advantages():
    """Show advantages of this approach."""

    print("\n🎯 SQLite + LanceDB Advantages:")
    print("=" * 40)
    print("✅ No external databases required")
    print("✅ No Docker containers to manage")
    print("✅ File-based storage (easy backup)")
    print("✅ Fast local performance")
    print("✅ Simple deployment")
    print("✅ Works offline")
    print("✅ No network dependencies")
    print("✅ Native agno integration")
    print("✅ Production-ready (used in agno examples)")


if __name__ == "__main__":
    print("🚀 SQLite + LanceDB Migration Plan")
    print("=" * 35)

    migration_advantages()
    show_file_structure()

    print("\n🔧 Migration Steps:")
    print("1. Export your Weaviate facts to text files")
    print("2. Place them in data/knowledge/")
    print("3. Replace current agent with create_sqlite_based_agent()")
    print("4. Remove Weaviate entirely")

    print("\n🎉 Result: Zero external dependencies!")
