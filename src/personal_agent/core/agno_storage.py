"""Agno native storage and knowledge management utilities."""

import logging
from pathlib import Path
from typing import Optional

from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.knowledge.text import TextKnowledgeBase
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.storage.sqlite import SqliteStorage
from agno.vectordb.lancedb import LanceDb, SearchType

from ..config import DATA_DIR, OLLAMA_URL

logger = logging.getLogger(__name__)


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


async def create_agno_knowledge(
    storage_dir: str = None, knowledge_dir: str = None
) -> Optional[TextKnowledgeBase]:
    """Create LanceDB knowledge base for agent and load personal knowledge.

    :param storage_dir: Directory for knowledge files (defaults to DATA_DIR/agno)
    :param knowledge_dir: Directory containing knowledge files to load (defaults to DATA_DIR/knowledge)
    :return: Configured TextKnowledgeBase instance or None if no knowledge found
    """
    if storage_dir is None:
        storage_dir = f"{DATA_DIR}/agno"

    storage_path = Path(storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)

    vector_db = LanceDb(
        uri=str(storage_path / "lancedb"),
        table_name="personal_agent_knowledge",
        search_type=SearchType.hybrid,
        embedder=OllamaEmbedder(id="nomic-embed-text", host=OLLAMA_URL, dimensions=768),
    )

    logger.info("Created Agno LanceDB knowledge at: %s", storage_path / "lancedb")

    # Load personal knowledge and return the TextKnowledgeBase
    knowledge_base = await load_personal_knowledge(vector_db, knowledge_dir)
    return knowledge_base


async def load_personal_knowledge(
    vector_db: LanceDb, knowledge_dir: str = None, recreate: bool = False
) -> Optional[TextKnowledgeBase]:
    """Load personal knowledge files into the vector database.

    :param vector_db: Vector database instance
    :param knowledge_dir: Directory containing knowledge files (defaults to DATA_DIR/knowledge)
    :return: Configured TextKnowledgeBase instance or None if no knowledge found
    """
    from agno.knowledge.text import TextKnowledgeBase

    if knowledge_dir is None:
        knowledge_dir = f"{DATA_DIR}/knowledge"

    knowledge_path = Path(knowledge_dir)
    if not knowledge_path.exists():
        logger.info(
            "No knowledge directory found at %s, skipping knowledge loading",
            knowledge_path,
        )
        return None

    # Load text files
    text_files = list(knowledge_path.glob("*.txt")) + list(knowledge_path.glob("*.md"))
    if text_files:
        try:
            logger.info(
                "Found %d knowledge text files in %s", len(text_files), knowledge_path
            )

            # Initialize the TextKnowledgeBase following the working example pattern
            text_knowledge = TextKnowledgeBase(
                path=knowledge_path,
                vector_db=vector_db,
                num_documents=len(
                    text_files
                ),  # Add num_documents parameter like in the example
                recreate=recreate,  # Use recreate parameter to control loading
            )

            logger.info("Loading text knowledge base...")
            # Use aload with recreate=False like in the working example
            # Let Agno handle whether to recreate or not based on existing data
            await text_knowledge.aload(recreate=recreate)

            logger.info(
                "Successfully loaded %d text/markdown files into knowledge base",
                len(text_files),
            )
            return text_knowledge

        except Exception as e:
            logger.error("Failed to load text knowledge: %s", e)
            return None


# TODO: Add PDF loading support if needed
async def load_pdf_knowledge(
    vector_db: LanceDb, knowledge_dir: str = None, recreate: bool = False
) -> Optional[PDFKnowledgeBase]:
    """Load personal knowledge files into the vector database.

    :param vector_db: Vector database instance
    :param knowledge_dir: Directory containing knowledge files (defaults to DATA_DIR/knowledge)
    :return: Configured TextKnowledgeBase instance or None if no knowledge found
    """
    from agno.knowledge.text import PdfKnowledgeBase

    if knowledge_dir is None:
        knowledge_dir = f"{DATA_DIR}/knowledge"

    knowledge_path = Path(knowledge_dir)
    if not knowledge_path.exists():
        logger.info(
            "No knowledge directory found at %s, skipping knowledge loading",
            knowledge_path,
        )
        return None

    pdf_files = list(knowledge_path.glob("*.pdf"))
    if pdf_files:
        try:
            pdf_knowledge = PdfKnowledgeBase(
                sources=[str(f) for f in pdf_files], vector_db=vector_db
            )
            # Set to True to load the knowledge base (only needs to be done once)
            load_knowledge = True
            if load_knowledge:
                await pdf_knowledge.aload(recreate=recreate)
                logger.info("Loaded %d PDF files into knowledge base", len(pdf_files))
                return pdf_knowledge

        except Exception as e:
            logger.error("Failed to load PDF knowledge: %s", e)
            return None
    else:
        logger.error("No PDF files to load.")
        return None


# end of file
