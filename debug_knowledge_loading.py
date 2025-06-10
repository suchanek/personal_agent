#!/usr/bin/env python3
"""
Debug script to isolate the knowledge base loading issue.
"""

import asyncio
import logging
from pathlib import Path

from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.knowledge.text import TextKnowledgeBase
from agno.vectordb.lancedb import LanceDb, SearchType

from src.personal_agent.config import DATA_DIR, OLLAMA_URL

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


async def test_knowledge_loading():
    """Test just the knowledge base loading."""
    print("🧪 Testing Knowledge Base Loading")
    print("=" * 50)

    try:
        # Define paths
        knowledge_dir = Path(f"{DATA_DIR}/knowledge")
        storage_path = Path(f"{DATA_DIR}/agno/debug_lancedb")
        storage_path.mkdir(parents=True, exist_ok=True)

        print(f"📁 Knowledge dir: {knowledge_dir}")
        print(f"📁 Storage path: {storage_path}")

        # Check files
        text_files = list(knowledge_dir.glob("*.txt")) + list(
            knowledge_dir.glob("*.md")
        )
        print(
            f"📄 Found {len(text_files)} text files: {[f.name for f in text_files[:3]]}"
        )

        if not text_files:
            print("❌ No text files found!")
            return

        # Create embedder
        print("🔧 Creating embedder...")
        embedder = OllamaEmbedder(
            id="nomic-embed-text", host=OLLAMA_URL, dimensions=768
        )

        # Create simple TextKnowledgeBase first
        print("🔧 Creating TextKnowledgeBase...")
        text_kb = TextKnowledgeBase(
            path=knowledge_dir,
            vector_db=LanceDb(
                uri=str(storage_path / "text_knowledge"),
                table_name="debug_text_documents",
                search_type=SearchType.hybrid,
                embedder=embedder,
            ),
        )

        # Test loading simple knowledge base
        print("📚 Loading TextKnowledgeBase...")
        await text_kb.aload(recreate=False)
        print("✅ TextKnowledgeBase loaded successfully!")

        # Now test combined knowledge base
        print("🔧 Creating CombinedKnowledgeBase...")
        combined_kb = CombinedKnowledgeBase(
            sources=[text_kb],
            vector_db=LanceDb(
                uri=str(storage_path / "combined_knowledge"),
                table_name="debug_combined_documents",
                search_type=SearchType.hybrid,
                embedder=embedder,
            ),
        )

        print("📚 Loading CombinedKnowledgeBase...")
        await combined_kb.aload(recreate=False)
        print("✅ CombinedKnowledgeBase loaded successfully!")

        print("\n🎉 All knowledge bases loaded successfully!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_knowledge_loading())
