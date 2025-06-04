#!/usr/bin/env python3
"""
Migration Plan: Personal Agent from Weaviate to PgVector
========================================================

This script outlines the migration from Weaviate to agno's native PgVector setup,
following production patterns from agno examples.

Benefits of PgVector Migration:
- Native agno integration (no schema mismatches)
- Production-ready (used in all agno production examples)
- Unified storage stack (memory + knowledge + sessions)
- Better performance with hybrid search
- Simplified deployment (one database instead of two)
"""

from pathlib import Path

from agno.agent import Agent
from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.text import TextKnowledgeBase
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.memory import Memory
from agno.models.ollama import Ollama
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.vectordb.pgvector import PgVector, SearchType

# Database configuration
DB_URL = "postgresql+psycopg://ai:ai@localhost:5532/ai"


def create_new_agno_native_agent():
    """Create fully native agno agent with PgVector storage."""

    # 1. Native Memory System (replaces Weaviate conversation storage)
    memory = Memory(
        db=PostgresMemoryDb(table_name="personal_agent_memory", db_url=DB_URL),
        # Use same model for memory operations
        model=Ollama(id="qwen2.5:7b-instruct"),
    )

    # 2. Native Knowledge Base (replaces Weaviate knowledge storage)
    knowledge = TextKnowledgeBase(
        path="data/knowledge",  # Your facts and documents
        vector_db=PgVector(
            table_name="personal_agent_knowledge",
            db_url=DB_URL,
            search_type=SearchType.hybrid,  # Best of both worlds
            embedder=OllamaEmbedder(id="nomic-embed-text", dimensions=768),
        ),
        formats=[".txt", ".md", ".json"],
    )

    # 3. Native Agent Storage (session management)
    storage = PostgresAgentStorage(table_name="personal_agent_sessions", db_url=DB_URL)

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


def migration_steps():
    """Step-by-step migration process."""

    print("🚀 Personal Agent Migration to Native Agno Stack")
    print("=" * 50)

    print("\n1. 📦 Setup PgVector Database")
    print("   docker run -d \\")
    print("     -e POSTGRES_DB=ai \\")
    print("     -e POSTGRES_USER=ai \\")
    print("     -e POSTGRES_PASSWORD=ai \\")
    print("     -e PGDATA=/var/lib/postgresql/data/pgdata \\")
    print("     -v pgvolume:/var/lib/postgresql/data \\")
    print("     -p 5532:5432 \\")
    print("     --name pgvector \\")
    print("     agnohq/pgvector:16")

    print("\n2. 🔄 Data Migration")
    print("   - Export facts from Weaviate UserKnowledgeBase")
    print("   - Save as text files in data/knowledge/")
    print("   - Let agno native knowledge system index them")

    print("\n3. 🎯 Benefits")
    print("   ✅ No more schema mismatches")
    print("   ✅ Native agno integration")
    print("   ✅ Production-proven architecture")
    print("   ✅ Unified storage (one database)")
    print("   ✅ Better performance")
    print("   ✅ Simpler deployment")

    print("\n4. 🏗️ Architecture Changes")
    print("   BEFORE: FastAPI + Weaviate + MCP + Custom Memory")
    print("   AFTER:  Native Agno + PgVector + Integrated Memory/Knowledge")

    print("\n5. 🔧 Implementation")
    print("   - Replace agno_main.py with native agent creation")
    print("   - Remove Weaviate dependencies")
    print("   - Use PgVector for all vector operations")
    print("   - Leverage agno's built-in memory system")


if __name__ == "__main__":
    migration_steps()

    print("\n🎉 Ready to create native agno agent:")
    print("agent = create_new_agno_native_agent()")
