#!/usr/bin/env python3
"""
Test script to isolate knowledge search behavior with 'snoopy' query.

This script replicates the exact search path used by the Streamlit UI to debug
why unrelated results are being returned.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from personal_agent.config.runtime_config import get_config
from personal_agent.core.agno_storage import create_combined_knowledge_base

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_direct_search():
    """Test direct search on agno_knowledge (replicates Streamlit path)."""

    print("\n" + "="*80)
    print("🔍 KNOWLEDGE SEARCH TEST: Direct Search Path (Streamlit UI)")
    print("="*80)

    # Get configuration
    config = get_config()
    print(f"\n📋 Configuration:")
    print(f"   User: {config.user_id}")
    print(f"   Storage: {config.agno_storage_dir}")
    print(f"   Knowledge: {config.agno_knowledge_dir}")

    # Initialize agent properly like reasoning_team.py does (line 828-841)
    print(f"\n🤖 Creating AgnoPersonalAgent (single mode, recreate=False)...")
    try:
        from personal_agent.core.agno_agent import AgnoPersonalAgent
        from personal_agent.core.agent_instruction_manager import InstructionLevel

        # Create agent exactly like create_memory_agent() does (reasoning_team.py:828-841)
        agent = AgnoPersonalAgent(
            enable_memory=True,
            enable_mcp=False,
            debug=True,
            user_id=config.user_id,
            recreate=True,  # Recreate to use EnhancedLanceDb!
            alltools=True,   # Single mode = all tools enabled
            instruction_level=InstructionLevel.CONCISE,
            use_remote=False,
        )

        # Wait for initialization to complete (reasoning_team.py:841)
        print(f"⏳ Initializing agent (this may take a moment)...")
        await agent._ensure_initialized()

        print(f"✅ Agent initialized successfully!")

        # Access the knowledge base from the initialized agent
        knowledge_base = agent.agno_knowledge

        if not knowledge_base:
            print("❌ Agent has no knowledge base")
            return

        print(f"✅ Knowledge base available: {type(knowledge_base).__name__}")

        # Check document count
        try:
            doc_count = await knowledge_base.count()
            print(f"   Documents in KB: {doc_count}")
        except Exception as e:
            print(f"   Could not get doc count: {e}")

    except Exception as e:
        print(f"❌ Error initializing agent: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test queries
    test_queries = [
        ("machine learning", 3),    # Should have GOOD matches
        ("python programming", 3),  # Should have GOOD matches
        ("snoopy", 5),              # Should have BAD matches (problematic query)
        ("asdfqwerzxcv", 3),        # Random garbage - should have BAD matches
    ]

    print(f"\n" + "="*80)
    print("🧪 TESTING SEARCH QUERIES")
    print("="*80)

    for query, limit in test_queries:
        print(f"\n{'─'*80}")
        print(f"Query: '{query}' (limit={limit})")
        print(f"{'─'*80}")

        try:
            # THIS IS THE EXACT CALL FROM streamlit_helpers.py:787
            # km.search(query=query, num_documents=limit)
            results = knowledge_base.search(query=query, num_documents=limit)

            print(f"✅ Search returned {len(results)} results")

            if not results:
                print("   (No results found)")
                continue

            # Display results with relevance scores if available
            for i, result in enumerate(results, 1):
                print(f"\n   Result {i}:")

                # Check for similarity/relevance score in meta_data
                distance = None
                if hasattr(result, 'meta_data') and result.meta_data:
                    if '_distance' in result.meta_data:
                        distance = result.meta_data['_distance']
                        print(f"      Distance: {distance:.4f} (from meta_data)")
                    else:
                        print(f"      meta_data keys: {list(result.meta_data.keys())}")

                # Also check direct attributes
                if hasattr(result, 'score'):
                    print(f"      Score (attr): {result.score:.4f}")
                elif hasattr(result, 'similarity'):
                    print(f"      Similarity (attr): {result.similarity:.4f}")
                elif hasattr(result, 'distance'):
                    print(f"      Distance (attr): {result.distance:.4f}")
                elif distance is None:
                    print(f"      Score: (no score found)")

                # Source info
                if hasattr(result, 'source'):
                    print(f"      Source: {result.source}")

                # Content preview
                if hasattr(result, 'content'):
                    content = result.content[:200].replace('\n', ' ')
                    print(f"      Content: {content}...")
                else:
                    print(f"      Content: (no content attribute)")

        except Exception as e:
            print(f"❌ Search failed: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n" + "="*80)
    print("🔬 TESTING WITH SIMILARITY THRESHOLD (if supported)")
    print("="*80)

    # Test if similarity_threshold parameter is supported with different thresholds
    # NOTE: For vector search, _distance is used where LOWER = BETTER
    # Typical distance range: 0.0 (perfect) to 2.0 (very different)
    test_thresholds = [
        ("machine learning", 0.8, "Should keep good matches (distance <= 0.8)"),
        ("machine learning", 0.5, "Stricter: only very close matches (distance <= 0.5)"),
        ("snoopy", 0.8, "Should filter out bad matches (distance > 0.8)"),
        ("snoopy", 1.5, "Loose threshold: might keep some marginal matches"),
    ]

    # Check if method supports similarity_threshold
    import inspect
    search_sig = inspect.signature(knowledge_base.search)
    params = search_sig.parameters
    print(f"\n   Search method parameters: {list(params.keys())}")

    if 'similarity_threshold' not in params and 'threshold' not in params:
        print(f"   ❌ Similarity threshold parameter NOT supported")
        print(f"   Available parameters: {list(params.keys())}")
    else:
        print(f"   ✅ Similarity threshold parameter is supported!")

        # Run threshold tests
        for query, threshold, description in test_thresholds:
            print(f"\n{'─'*80}")
            print(f"Query: '{query}' with similarity_threshold={threshold}")
            print(f"Expected: {description}")

            try:
                results = knowledge_base.search(
                    query=query,
                    num_documents=10,
                    similarity_threshold=threshold
                )
                print(f"   ✅ Results: {len(results)} documents")

                # Show relevance scores
                for i, doc in enumerate(results[:3], 1):
                    if doc.meta_data and '_relevance_score' in doc.meta_data:
                        score = doc.meta_data['_relevance_score']
                        content_preview = doc.content[:60].replace('\n', ' ')
                        print(f"      {i}. Score={score:.4f}: {content_preview}...")

            except Exception as e:
                print(f"   ❌ Error: {e}")
                import traceback
                traceback.print_exc()

    print(f"\n" + "="*80)
    print("✅ TEST COMPLETE")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_direct_search())
