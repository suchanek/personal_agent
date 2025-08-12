#!/usr/bin/env python3
"""
Test script to verify knowledge base loading and searching.
"""

import asyncio
import sys
from pathlib import Path

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath()

from personal_agent.core.agno_storage import create_combined_knowledge_base


async def test_knowledge_base():
    """Test knowledge base creation and search."""
    print("🧪 Testing Knowledge Base")
    print("=" * 40)

    try:
        # Create knowledge base
        print("✅ Creating Agno knowledge base...")
        knowledge_db = create_combined_knowledge_base(
            "/Users/egs/data/agno", "/Users/egs/data/knowledge"
        )

        if knowledge_db is None:
            print("❌ No knowledge base created (no knowledge files found)")
            return False

        print(f"✅ Knowledge base created: {type(knowledge_db)}")

        # Test search
        print("✅ Testing search for 'Eric'...")
        try:
            # Try to search the knowledge base directly using the correct API
            search_results = knowledge_db.search("Eric name user")
            print(f"🔍 Search results: {search_results}")

            # Try different search terms
            for term in ["Eric", "Suchanek", "user name", "Name"]:
                results = knowledge_db.search(term)
                print(f"🔍 Search '{term}': {len(results) if results else 0} results")
                if results:
                    # Handle different result types
                    first_result = results[0] if isinstance(results, list) else results
                    if hasattr(first_result, "content"):
                        content = first_result.content[:100]
                    elif hasattr(first_result, "page_content"):
                        content = first_result.page_content[:100]
                    else:
                        content = str(first_result)[:100]
                    print(f"   → {content}...")

        except Exception as e:
            print(f"❌ Search error: {e}")
            import traceback

            traceback.print_exc()

        print("✅ Knowledge base test completed")
        return True

    except Exception as e:
        print(f"❌ Test FAILED: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_knowledge_base())
    sys.exit(0 if success else 1)
