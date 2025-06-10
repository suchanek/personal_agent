#!/usr/bin/env python3
"""Test the memory tools directly to see if they can retrieve user facts."""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from personal_agent.core.memory import setup_weaviate, vector_store
from personal_agent.tools.memory_tools import create_memory_tools


def test_memory_retrieval():
    """Test if memory tools can retrieve facts about the user."""
    print("=== Testing Memory Tools ===")

    # Setup Weaviate
    if not setup_weaviate():
        print("❌ Failed to setup Weaviate")
        return

    print("✅ Weaviate setup successful")

    # Get the memory tools
    from personal_agent.core.memory import vector_store, weaviate_client

    if not vector_store or not weaviate_client:
        print("❌ Vector store or client not available")
        return

    print("✅ Vector store and client available")

    # Create memory tools
    tools = create_memory_tools(weaviate_client, vector_store)
    store_interaction, query_knowledge_base, clear_knowledge_base = tools

    # Test queries that should return user facts
    test_queries = [
        "What is the user's name?",
        "Tell me about Eric",
        "What are the user's favorite programming languages?",
        "When was the user born?",
        "What do you know about me?",
        "user facts personal information",
    ]

    print("\n=== Testing Knowledge Retrieval ===")
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            result = query_knowledge_base.invoke({"query": query, "limit": 3})
            if isinstance(result, list):
                if result and result != ["Weaviate is disabled, no context available."]:
                    print("✅ Found results:")
                    for i, item in enumerate(result[:3]):
                        print(f"  {i+1}. {item}")
                else:
                    print("❌ No results found")
            else:
                print(f"✅ Result: {result}")
        except Exception as e:
            print(f"❌ Error: {e}")

    # Test direct vector store search
    print(f"\n=== Testing Direct Vector Store Search ===")
    try:
        results = vector_store.similarity_search("Eric name user", k=3)
        print(f"✅ Direct search found {len(results)} results:")
        for i, doc in enumerate(results):
            metadata = doc.metadata if hasattr(doc, "metadata") else {}
            timestamp = metadata.get("timestamp", "unknown")
            topic = metadata.get("topic", "general")
            content = (
                doc.page_content[:200] + "..."
                if len(doc.page_content) > 200
                else doc.page_content
            )
            print(f"  {i+1}. [{timestamp}] [{topic}] {content}")
    except Exception as e:
        print(f"❌ Direct search error: {e}")


if __name__ == "__main__":
    test_memory_retrieval()
