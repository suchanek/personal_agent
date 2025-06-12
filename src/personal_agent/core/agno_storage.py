"""Agno native storage and knowledge management utilities.

Simplified storage module that provides factory functions for Agno's native
memory and storage components, following the agentic memory pattern where
the LLM intelligently manages memory creation and prevents duplicates naturally.

Primary functions:
- create_agno_storage(): SQLite storage for agent sessions
- create_agno_memory(): Memory instance with SQLite backend for persistent memory
- create_combined_knowledge_base(): Unified knowledge base handling both text and PDF sources
- load_combined_knowledge_base(): Async loading for combined knowledge base

Removed redundant functions (v0.5.3):
- create_agno_knowledge(), load_agno_knowledge(): Redundant with combined knowledge base
- load_personal_knowledge(), load_personal_knowledge_async(): Redundant text-only functions
- load_pdf_knowledge(), load_pdf_knowledge_async(): Redundant PDF-only functions
"""

from pathlib import Path
from typing import Optional

from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.knowledge.text import TextKnowledgeBase
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.storage.sqlite import SqliteStorage
from agno.vectordb.lancedb import LanceDb, SearchType

from ..config import DATA_DIR, OLLAMA_URL
from ..utils import setup_logging

logger = setup_logging(__name__)


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
    )

    logger.info(
        "Created Agno SQLite storage at: %s", storage_path / "agent_sessions.db"
    )
    return storage


def create_agno_memory(storage_dir: str = None) -> Memory:
    """Create Memory instance with SQLite backend for persistent memory.

    Uses Agno's native agentic memory approach where the LLM intelligently
    decides what information to store as memories, naturally preventing
    duplicates through smart content evaluation.

    :param storage_dir: Directory for storage files (defaults to DATA_DIR/agno)
    :return: Configured Memory instance
    """
    if storage_dir is None:
        storage_dir = f"{DATA_DIR}/agno"

    storage_path = Path(storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)

    memory_db = SqliteMemoryDb(
        table_name="personal_agent_memory",
        db_file=str(storage_path / "agent_memory.db"),
    )

    memory = Memory(db=memory_db)

    logger.info(
        "Created Agno Memory with SQLite backend at: %s",
        storage_path / "agent_memory.db",
    )
    return memory


# REMOVED: create_agno_knowledge() and load_agno_knowledge() functions
# These functions were redundant with create_combined_knowledge_base()
# which properly handles both text and PDF sources in a unified manner.


def create_combined_knowledge_base(
    storage_dir: str = None, knowledge_dir: str = None
) -> Optional[CombinedKnowledgeBase]:
    """Create a combined knowledge base with text and PDF sources (synchronous creation).

    :param storage_dir: Directory for storage files (defaults to DATA_DIR/agno)
    :param knowledge_dir: Directory containing knowledge files to load (defaults to DATA_DIR/knowledge)
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
    await knowledge_base.aload(recreate=recreate)
    logger.info("Combined knowledge base loaded successfully")


# REMOVED: load_personal_knowledge() and load_personal_knowledge_async() functions
# These functions were redundant with create_combined_knowledge_base()
# which properly handles both text and PDF sources in a unified manner.


# REMOVED: load_pdf_knowledge() and load_pdf_knowledge_async() functions
# These functions were redundant with create_combined_knowledge_base()
# which properly handles both text and PDF sources in a unified manner.

# end of file
