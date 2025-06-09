"""Agno native storage and knowledge management utilities."""

import logging
from pathlib import Path
from typing import Optional

from agno.embedder.openai import OpenAIEmbedder
from agno.storage.sqlite import SqliteStorage
from agno.vectordb.lancedb import LanceDb, SearchType

logger = logging.getLogger(__name__)


def create_agno_storage(storage_dir: str = "./data/agno") -> SqliteStorage:
    """Create SQLite storage for agent sessions.

    :param storage_dir: Directory for storage files
    :return: Configured SQLite storage instance
    """
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


def create_agno_knowledge(storage_dir: str = "./data/agno") -> LanceDb:
    """Create LanceDB knowledge base for agent.

    :param storage_dir: Directory for knowledge files
    :return: Configured LanceDb instance
    """
    storage_path = Path(storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)

    knowledge_db = LanceDb(
        uri=str(storage_path / "lancedb"),
        table_name="personal_agent_knowledge",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    )

    logger.info("Created Agno LanceDB knowledge at: %s", storage_path / "lancedb")
    return knowledge_db


def load_personal_knowledge(
    vector_db: LanceDb, knowledge_dir: str = "./data/knowledge"
) -> None:
    """Load personal knowledge files into the vector database.

    :param vector_db: Vector database instance
    :param knowledge_dir: Directory containing knowledge files
    """
    from agno.knowledge.text import TextKnowledgeBase

    knowledge_path = Path(knowledge_dir)
    if not knowledge_path.exists():
        logger.info(
            "No knowledge directory found at %s, skipping knowledge loading",
            knowledge_path,
        )
        return

    # Load text files
    text_files = list(knowledge_path.glob("*.txt")) + list(knowledge_path.glob("*.md"))
    if text_files:
        try:
            text_knowledge = TextKnowledgeBase(
                sources=[str(f) for f in text_files], vector_db=vector_db
            )
            text_knowledge.load()
            logger.info(
                "Loaded %d text/markdown files into knowledge base", len(text_files)
            )
        except Exception as e:
            logger.error("Failed to load text knowledge: %s", e)

    # TODO: Add PDF loading support if needed
    # pdf_files = list(knowledge_path.glob("*.pdf"))
    # if pdf_files:
    #     try:
    #         from agno.knowledge.pdf import PdfKnowledge
    #         pdf_knowledge = PdfKnowledge(
    #             sources=[str(f) for f in pdf_files],
    #             vector_db=vector_db
    #         )
    #         pdf_knowledge.load()
    #         logger.info("Loaded %d PDF files into knowledge base", len(pdf_files))
    #     except Exception as e:
    #         logger.error("Failed to load PDF knowledge: %s", e)
