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

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiohttp
from agno.document import Document
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
    from ..config import AGNO_STORAGE_DIR, DATA_DIR, LOG_LEVEL, OLLAMA_URL
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


class EnhancedCombinedKnowledgeBase(CombinedKnowledgeBase):
    """Enhanced CombinedKnowledgeBase that supports similarity_threshold filtering.

    This wrapper extends Agno's CombinedKnowledgeBase to pass through
    similarity_threshold parameter to EnhancedLanceDb instances.
    """

    def search(
        self,
        query: str,
        num_documents: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Document]:
        """Enhanced search with similarity threshold support.

        :param query: Search query string
        :param num_documents: Maximum number of results (0 = no limit)
        :param filters: Optional filters to apply
        :param similarity_threshold: Maximum distance threshold for results
        :return: List of matching documents
        """
        if self.vector_db is None:
            return []

        _num_documents = num_documents if num_documents is not None else self.num_documents

        # If vector_db is EnhancedLanceDb, pass similarity_threshold
        if isinstance(self.vector_db, EnhancedLanceDb):
            return self.vector_db.search(
                query=query,
                limit=_num_documents,
                filters=filters,
                similarity_threshold=similarity_threshold
            )
        else:
            # Fall back to parent behavior for non-enhanced vector DBs
            return self.vector_db.search(query=query, limit=_num_documents, filters=filters)


class EnhancedLanceDb(LanceDb):
    """Enhanced LanceDb that preserves relevance scores and supports similarity filtering.

    This wrapper extends Agno's LanceDb to:
    1. Preserve _distance scores from LanceDB in Document.meta_data
    2. Support similarity_threshold filtering (lower distance = better match)
    3. Support limit=0 to return ALL results (no limit)
    4. Maintain backward compatibility with original LanceDb
    """

    def _build_search_results(self, results) -> List[Document]:
        """Override to preserve _distance scores from LanceDB.

        :param results: Pandas DataFrame from LanceDB search
        :return: List of Documents with _distance preserved in meta_data
        """
        from agno.utils.log import logger

        search_results: List[Document] = []
        try:
            for idx, item in results.iterrows():
                payload = json.loads(item["payload"])
                meta_data = payload.get("meta_data", {}) or {}

                # CRITICAL FIX: Preserve the relevance/distance score from LanceDB
                # _relevance_score: Higher = better match (hybrid search)
                # _distance: Lower = better match (vector search, typical range 0.0-2.0)
                if "_relevance_score" in item:
                    meta_data["_relevance_score"] = float(item["_relevance_score"])
                elif "_distance" in item:
                    meta_data["_distance"] = float(item["_distance"])
                elif "score" in item:  # Fallback to 'score' if available
                    meta_data["_relevance_score"] = float(item["score"])

                search_results.append(
                    Document(
                        name=payload["name"],
                        meta_data=meta_data,
                        content=payload["content"],
                        embedder=self.embedder,
                        embedding=item["vector"],
                        usage=payload.get("usage"),
                    )
                )
        except Exception as e:
            logger.error(f"Error building search results: {e}")
            import traceback
            traceback.print_exc()

        return search_results

    def search(
        self,
        query: str,
        limit: int = 5,
        filters: Optional[Dict[str, Any]] = None,
        similarity_threshold: Optional[float] = None
    ) -> List[Document]:
        """Enhanced search with similarity threshold filtering.

        :param query: Search query string
        :param limit: Maximum number of results (0 = no limit, return all)
        :param filters: Metadata filters
        :param similarity_threshold: Similarity threshold for filtering results.
                                     - For vector search (_distance): Max distance (0.0-2.0, lower=better).
                                       Typical: 0.5=strict, 0.8=moderate, 1.0=loose
                                     - For hybrid search (_relevance_score): Min score (higher=better)
        :return: List of Documents with _distance or _relevance_score in meta_data
        """
        # If limit is 0, get a large number and filter later
        search_limit = limit if limit > 0 else 1000

        # Call parent search (which will use our overridden _build_search_results)
        results = super().search(query=query, limit=search_limit, filters=filters)

        # Apply similarity threshold filter if specified
        if similarity_threshold is not None and results:
            filtered_results = []
            for doc in results:
                if not doc.meta_data:
                    continue

                # Handle both relevance_score (higher=better) and distance (lower=better)
                if "_relevance_score" in doc.meta_data:
                    relevance = doc.meta_data["_relevance_score"]
                    # For relevance scores, keep if >= threshold
                    if relevance >= similarity_threshold:
                        filtered_results.append(doc)
                elif "_distance" in doc.meta_data:
                    distance = doc.meta_data["_distance"]
                    # For distance scores, keep if <= threshold
                    if distance <= similarity_threshold:
                        filtered_results.append(doc)

            logger.debug(
                f"Filtered {len(results)} results to {len(filtered_results)} "
                f"using similarity_threshold={similarity_threshold}"
            )
            results = filtered_results

        # Apply limit if specified (after filtering)
        if limit > 0:
            results = results[:limit]

        return results


def create_agno_storage(storage_dir: str = None) -> SqliteStorage:
    """Create SQLite storage for agent sessions.

    :param storage_dir: Directory for storage files (defaults to DATA_DIR/agno)
    :return: Configured SQLite storage instance
    """
    if storage_dir is None:
        storage_dir = AGNO_STORAGE_DIR

    storage_path = Path(storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)

    storage = SqliteStorage(
        table_name="personal_agent_sessions",
        db_file=str(storage_path / "agent_sessions.db"),
        auto_upgrade_schema=True,
    )

    logger.debug(
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

    logger.debug(
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
) -> Optional[EnhancedCombinedKnowledgeBase]:
    """Create a combined knowledge base with text and PDF sources (synchronous creation).

    :param storage_dir: Directory for storage files (defaults to DATA_DIR/agno)
    :param knowledge_dir: Directory containing knowledge files to load (defaults to DATA_DIR/knowledge)
    :param db_url: SqliteStorage for the database
    :return: Configured EnhancedCombinedKnowledgeBase instance or None if no knowledge found
    """
    if storage_dir is None:
        storage_dir = f"{DATA_DIR}/agno"
    if knowledge_dir is None:
        knowledge_dir = f"{DATA_DIR}/knowledge"

    storage_path = Path(storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)

    knowledge_path = Path(knowledge_dir)
    # Ensure the knowledge directory exists, creating it if necessary.
    knowledge_path.mkdir(parents=True, exist_ok=True)
    logger.debug("Knowledge directory is ready at %s", knowledge_path)

    # Check for available knowledge files
    text_files = list(knowledge_path.glob("*.txt")) + list(knowledge_path.glob("*.md")) + list(knowledge_path.glob("*.html"))
    pdf_files = list(knowledge_path.glob("*.pdf"))

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
        text_vector_db = EnhancedLanceDb(
            uri=str(storage_path / "lancedb"),
            table_name="text_knowledge",
            search_type=SearchType.vector,  # Pure vector search for better semantic discrimination
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
        try:
            pdf_vector_db = EnhancedLanceDb(
                uri=str(storage_path / "lancedb"),
                table_name="pdf_knowledge",
                search_type=SearchType.vector,  # Pure vector search for better semantic discrimination
                embedder=embedder,
            )

            pdf_kb = PDFKnowledgeBase(
                path=knowledge_path,
                vector_db=pdf_vector_db,
            )
            knowledge_sources.append(pdf_kb)
            logger.info("Created PDFKnowledgeBase with %d files", len(pdf_files))
        except Exception as e:
            logger.warning("Failed to create PDFKnowledgeBase due to corrupted PDF files: %s", e)
            logger.warning("Skipping PDF knowledge base. Check for corrupted PDF files in %s", knowledge_path)
            logger.warning("Consider removing or repairing corrupted PDF files like 'allosteric.pdf'")

    # Create a knowledge base with the ArXiv documents
    arxiv_vector_db = EnhancedLanceDb(
        uri=str(storage_path / "lancedb"),
        table_name="arxive_knowledge",
        search_type=SearchType.vector,  # Pure vector search for better semantic discrimination
        embedder=embedder,
    )
    arxive_kb = ArxivKnowledgeBase(vector_db=arxiv_vector_db)

    knowledge_sources.append(arxive_kb)
    logger.info("Created Arxive KnowledgeBase")

    # Log if no local knowledge files were found, but continue with ArXiv
    if not text_files and not pdf_files:
        logger.warning("No local knowledge files found in %s, but ArXiv knowledge base will be available", knowledge_path)

    # Create combined knowledge base
    if knowledge_sources:
        combined_vector_db = EnhancedLanceDb(
            uri=str(storage_path / "lancedb"),
            table_name="combined_knowledge",
            search_type=SearchType.vector,  # Pure vector search for better semantic discrimination
            embedder=embedder,
        )

        combined_kb = EnhancedCombinedKnowledgeBase(
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
    knowledge_base: Union[CombinedKnowledgeBase, EnhancedCombinedKnowledgeBase], recreate: bool = False
) -> None:
    """Load combined knowledge base content (async loading).

    :param knowledge_base: CombinedKnowledgeBase or EnhancedCombinedKnowledgeBase instance to load
    :param recreate: Whether to recreate the knowledge base from scratch
    """
    if recreate:
        logger.info("🔄 RECREATING knowledge base from scratch (recreate=True)")
    else:
        logger.info("Loading combined knowledge base content...")

    # Use synchronous load in an async context - this matches agno framework patterns
    # The synchronous load method is more stable than aload which can return async generators
    knowledge_base.load(recreate=recreate)

    if recreate:
        logger.info("✅ Knowledge base RECREATED successfully")
    else:
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
