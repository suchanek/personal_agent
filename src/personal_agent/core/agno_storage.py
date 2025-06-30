"""Agno native storage and knowledge management utilities.

Enhanced storage module that provides factory functions for Agno's native
memory and storage components, featuring LLM-free semantic memory management
and advanced knowledge base capabilities.

Primary functions:
- create_agno_storage(): SQLite storage for agent sessions
- create_agno_memory(): Memory instance with SemanticMemoryManager for LLM-free memory management
- create_combined_knowledge_base(): Unified knowledge base handling both text and PDF sources
- load_combined_knowledge_base(): Async loading for combined knowledge base

Memory Management (v0.7.2 - SemanticMemoryManager Integration):
- Integrated with SemanticMemoryManager for LLM-free memory operations
- Advanced semantic duplicate detection without requiring LLM calls
- Automatic topic classification using rule-based patterns
- Enhanced semantic search with topic matching and content similarity
- Configurable similarity thresholds and memory management settings
- Rich memory statistics and analytics capabilities
- Debug mode for detailed memory operation logging

Key Features:
- LLM-free semantic duplicate detection (similarity threshold: 0.8)
- Automatic topic classification (personal_info, work, education, etc.)
- Enhanced semantic search combining content and topic matching
- Memory deletion and clearing capabilities
- Rich analytics: memory statistics, topic distribution, usage patterns
- Debug mode for detailed operation insights

Removed redundant functions (v0.5.3):
- create_agno_knowledge(), load_agno_knowledge(): Redundant with combined knowledge base
- load_personal_knowledge(), load_personal_knowledge_async(): Redundant text-only functions
- load_pdf_knowledge(), load_pdf_knowledge_async(): Redundant PDF-only functions
"""

from pathlib import Path
from typing import Optional

import aiohttp
from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.arxiv import ArxivKnowledgeBase
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.knowledge.text import TextKnowledgeBase
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.storage.sqlite import SqliteStorage
from agno.vectordb.lancedb import LanceDb, SearchType

# Handle imports for both module import and direct execution
try:
    from ..config import DATA_DIR, LOG_LEVEL, OLLAMA_URL
    from ..utils import setup_logging
    from .semantic_memory_manager import (
        SemanticMemoryManager,
        SemanticMemoryManagerConfig,
    )
except ImportError:
    # When running directly, use absolute imports
    import os
    import sys

    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    from personal_agent.config import DATA_DIR, OLLAMA_URL
    from personal_agent.core.semantic_memory_manager import (
        SemanticMemoryManager,
        SemanticMemoryManagerConfig,
    )
    from personal_agent.utils import setup_logging

logger = setup_logging(__name__, level=LOG_LEVEL)


def create_agno_storage(storage_dir: str = None) -> SqliteStorage:
    """Create SQLite storage for agent sessions.

    :param storage_dir: Directory for storage files (defaults to DATA_DIR/agno)
    :return: Configured SQLite storage instance
    """
    if storage_dir is None:
        storage_dir = f"{DATA_DIR}/agno"

    storage_path = Path(storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)

    storage = SqliteStorage(
        table_name="personal_agent_sessions",
        db_file=str(storage_path / "agent_sessions.db"),
        auto_upgrade_schema=True,
    )

    logger.info(
        "Created Agno SQLite storage at: %s", storage_path / "agent_sessions.db"
    )
    return storage


def create_agno_memory(storage_dir: str = None, debug_mode: bool = False) -> Memory:
    """Create Memory instance with SemanticMemoryManager for LLM-free memory management.

    Uses the advanced SemanticMemoryManager that provides intelligent duplicate detection,
    automatic topic classification, and semantic search capabilities without requiring
    LLM calls for memory operations.

    Features:
    - LLM-free semantic duplicate detection (similarity threshold: 0.8)
    - Automatic topic classification using rule-based patterns
    - Enhanced semantic search with topic matching
    - Memory deletion and clearing capabilities
    - Rich memory statistics and analytics
    - Debug mode for detailed logging

    :param storage_dir: Directory for storage files (defaults to DATA_DIR/agno)
    :param debug_mode: Enable debug logging for memory operations
    :return: Configured Memory instance with SemanticMemoryManager
    """
    if storage_dir is None:
        storage_dir = f"{DATA_DIR}/agno"

    storage_path = Path(storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)

    # Create SQLite memory database
    memory_db = SqliteMemoryDb(
        table_name="personal_agent_memory",
        db_file=str(storage_path / "agent_memory.db"),
    )

    # Create semantic memory manager configuration
    semantic_config = SemanticMemoryManagerConfig(
        similarity_threshold=0.8,
        enable_semantic_dedup=True,
        enable_exact_dedup=True,
        enable_topic_classification=True,
        debug_mode=debug_mode,
        max_memory_length=500,
        recent_memory_limit=100,
    )

    # Create semantic memory manager
    semantic_memory_manager = SemanticMemoryManager(config=semantic_config)

    # Create Agno Memory instance with SemanticMemoryManager
    memory = Memory(
        db=memory_db,
        memory_manager=semantic_memory_manager,
    )

    logger.info(
        "Created Memory with SemanticMemoryManager at: %s (debug_mode=%s)",
        storage_path / "agent_memory.db",
        debug_mode,
    )
    return memory


# REMOVED: create_agno_knowledge() and load_agno_knowledge() functions
# These functions were redundant with create_combined_knowledge_base()
# which properly handles both text and PDF sources in a unified manner.


def create_combined_knowledge_base(
    storage_dir: str = None, knowledge_dir: str = None, db_url: SqliteStorage = None
) -> Optional[CombinedKnowledgeBase]:
    """Create a combined knowledge base with text and PDF sources (synchronous creation).

    :param storage_dir: Directory for storage files (defaults to DATA_DIR/agno)
    :param knowledge_dir: Directory containing knowledge files to load (defaults to DATA_DIR/knowledge)
    :param db_url: SqliteStorage for the database
    :return: Configured CombinedKnowledgeBase instance or None if no knowledge found
    """
    if storage_dir is None:
        storage_dir = f"{DATA_DIR}/agno"
    if knowledge_dir is None:
        knowledge_dir = f"{DATA_DIR}/knowledge"

    storage_path = Path(storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)

    knowledge_path = Path(knowledge_dir)
    if not knowledge_path.exists():
        logger.info(
            "No knowledge directory found at %s, skipping knowledge loading",
            knowledge_path,
        )
        return None

    # Check for available knowledge files
    text_files = list(knowledge_path.glob("*.txt")) + list(knowledge_path.glob("*.md"))
    pdf_files = list(knowledge_path.glob("*.pdf"))

    if not text_files and not pdf_files:
        logger.info("No knowledge files found in %s", knowledge_path)
        return None

    logger.info(
        "Found %d text files and %d PDF files in %s",
        len(text_files),
        len(pdf_files),
        knowledge_path,
    )

    # Create vector databases for each knowledge type
    embedder = OllamaEmbedder(id="nomic-embed-text", host=OLLAMA_URL, dimensions=768)

    knowledge_sources = []

    # Create text knowledge base if text files exist
    if text_files:
        text_vector_db = LanceDb(
            uri=str(storage_path / "lancedb"),
            table_name="text_knowledge",
            search_type=SearchType.hybrid,
            embedder=embedder,
        )

        text_kb = TextKnowledgeBase(
            path=knowledge_path,
            vector_db=text_vector_db,
            num_documents=len(text_files),
        )
        knowledge_sources.append(text_kb)
        logger.info("Created TextKnowledgeBase with %d files", len(text_files))

    # Create PDF knowledge base if PDF files exist
    if pdf_files:
        pdf_vector_db = LanceDb(
            uri=str(storage_path / "lancedb"),
            table_name="pdf_knowledge",
            search_type=SearchType.hybrid,
            embedder=embedder,
        )

        pdf_kb = PDFKnowledgeBase(
            path=knowledge_path,
            vector_db=pdf_vector_db,
        )
        knowledge_sources.append(pdf_kb)
        logger.info("Created PDFKnowledgeBase with %d files", len(pdf_files))

    # Create a knowledge base with the ArXiv documents
    arxiv_vector_db = LanceDb(
        uri=str(storage_path / "lancedb"),
        table_name="arxive_knowledge",
        search_type=SearchType.hybrid,
        embedder=embedder,
    )
    arxive_kb = ArxivKnowledgeBase(vector_db=arxiv_vector_db)

    knowledge_sources.append(arxive_kb)
    logger.info("Created Arxive KnowledgeBase")

    # Create combined knowledge base
    if knowledge_sources:
        combined_vector_db = LanceDb(
            uri=str(storage_path / "lancedb"),
            table_name="combined_knowledge",
            search_type=SearchType.hybrid,
            embedder=embedder,
        )

        combined_kb = CombinedKnowledgeBase(
            sources=knowledge_sources,
            vector_db=combined_vector_db,
        )

        logger.info(
            "Successfully created combined knowledge base with %d sources (%d text, %d PDF)",
            len(knowledge_sources),
            len(text_files),
            len(pdf_files),
        )

        return combined_kb

    return None


async def load_combined_knowledge_base(
    knowledge_base: CombinedKnowledgeBase, recreate: bool = False
) -> None:
    """Load combined knowledge base content (async loading).

    :param knowledge_base: CombinedKnowledgeBase instance to load
    :param recreate: Whether to recreate the knowledge base from scratch
    """
    logger.info("Loading combined knowledge base content...")

    # Use synchronous load in an async context - this matches agno framework patterns
    # The synchronous load method is more stable than aload which can return async generators
    knowledge_base.load(recreate=recreate)

    logger.info("Combined knowledge base loaded successfully")


async def load_lightrag_knowledge_base(base_url: str = "http://localhost:9621") -> dict:
    """
    Load the LightRAG knowledge base metadata.

    :param base_url: Base URL for the LightRAG server
    :return: Dictionary with knowledge base status/info
    """
    url = f"{base_url}/documents"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, timeout=60) as resp:
            resp.raise_for_status()
            return await resp.json()


async def main():
    """Demonstrate knowledge base loading functionality.

    This main routine shows how to:
    1. Create a combined knowledge base with text and PDF sources
    2. Load the knowledge base content
    3. Display basic information about the loaded knowledge base
    """
    import asyncio
    import os
    import sys

    # Add the project root to Python path for imports when running directly
    if __name__ == "__main__":
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)

    print("\n" + "=" * 60)
    print("🚀 AGNO KNOWLEDGE BASE LOADING DEMO")
    print("=" * 60)

    # Create storage and memory components
    print("\n📦 Creating storage components...")
    try:
        storage = create_agno_storage()
        memory = create_agno_memory(
            debug_mode=False
        )  # Disable debug for cleaner output
        print("   ✅ Storage and memory components created successfully")
    except Exception as e:
        print(f"   ❌ Failed to create storage components: {e}")
        print(
            "   💡 Make sure Ollama is running and the required dependencies are installed"
        )
        return

    # Create combined knowledge base
    print("\n🧠 Creating combined knowledge base...")
    try:
        knowledge_base = create_combined_knowledge_base()
    except Exception as e:
        print(f"   ❌ Failed to create knowledge base: {e}")
        return

    if knowledge_base is None:
        print("   ⚠️  No knowledge base created - no knowledge files found")
        print("\n📋 To test knowledge base loading:")
        print("   1. Create a 'data/knowledge' directory")
        print("   2. Add some .txt, .md, or .pdf files to it")
        print("   3. Run this demo again")
        return

    # Load the knowledge base content
    print("\n📚 Loading knowledge base content...")
    try:
        await load_combined_knowledge_base(knowledge_base, recreate=False)
        print("   ✅ Knowledge base loaded successfully!")

        # Display basic information about the knowledge base
        print("\n📊 Knowledge Base Information:")
        print(f"   📁 Total Sources: {len(knowledge_base.sources)}")

        for i, source in enumerate(knowledge_base.sources):
            source_type = type(source).__name__
            if source_type == "TextKnowledgeBase":
                icon = "📄"
                description = "Text files (.txt, .md)"
            elif source_type == "PDFKnowledgeBase":
                icon = "📕"
                description = "PDF documents"
            else:
                icon = "📋"
                description = source_type

            print(f"   {icon} Source {i + 1}: {description}")

        # Test a simple search if the knowledge base has content
        print("\n🔍 Testing knowledge base search...")
        try:
            # Perform a simple search query
            search_results = knowledge_base.search("knowledge")
            print(f"   📈 Search results found: {len(search_results)}")

            if search_results:
                print("   🎯 Sample results:")
                for i, result in enumerate(search_results[:2]):  # Show first 2 results
                    preview = str(result)[:80].replace("\n", " ").strip()
                    print(f"      {i + 1}. {preview}...")
            else:
                print("   📝 No results found for 'knowledge' query")

        except Exception as search_error:
            print(f"   ⚠️  Search test failed: {search_error}")
            print(
                "   💡 This might be due to Ollama not running - that's okay for the demo"
            )

    except Exception as load_error:
        print(f"   ❌ Failed to load knowledge base: {load_error}")
        return

    print("\n" + "=" * 60)
    print("🎉 DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("💡 Your knowledge base is ready to use with the personal agent")
    print()


if __name__ == "__main__":
    import asyncio
    import os
    import sys

    # Add the project root to Python path for imports when running directly
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

    asyncio.run(main())

# end of file
