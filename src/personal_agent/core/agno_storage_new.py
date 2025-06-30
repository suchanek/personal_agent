"""
Agno native storage and knowledge management utilities + LightRAG standalone ingestion.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from agno.embedder.ollama import OllamaEmbedder
from agno.knowledge.arxiv import ArxivKnowledgeBase
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.knowledge.pdf import PDFKnowledgeBase
from agno.knowledge.text import TextKnowledgeBase
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory
from agno.storage.sqlite import SqliteStorage
from agno.vectordb.lancedb import LanceDb, SearchType
from lightrag import LightRAG
from lightrag.database.doc.jsonl import JsonlDocStorage
from lightrag.database.vector.lancedb import LanceDBVectorStorage
from lightrag.utils.env import get_env_value

# Handle imports for both module import and direct execution
try:
    from ..config import DATA_DIR, OLLAMA_URL
    from ..utils import setup_logging
    from .semantic_memory_manager import (
        SemanticMemoryManager,
        SemanticMemoryManagerConfig,
    )
except ImportError:
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

logger = setup_logging(__name__)


def create_agno_storage(storage_dir: str = None) -> SqliteStorage:
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
    if storage_dir is None:
        storage_dir = f"{DATA_DIR}/agno"
    storage_path = Path(storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)
    memory_db = SqliteMemoryDb(
        table_name="personal_agent_memory",
        db_file=str(storage_path / "agent_memory.db"),
    )
    semantic_config = SemanticMemoryManagerConfig(
        similarity_threshold=0.8,
        enable_semantic_dedup=True,
        enable_exact_dedup=True,
        enable_topic_classification=True,
        debug_mode=debug_mode,
        max_memory_length=500,
        recent_memory_limit=100,
    )
    semantic_memory_manager = SemanticMemoryManager(config=semantic_config)
    memory = Memory(db=memory_db, memory_manager=semantic_memory_manager)
    logger.info(
        "Created Memory with SemanticMemoryManager at: %s (debug_mode=%s)",
        storage_path / "agent_memory.db",
        debug_mode,
    )
    return memory


def create_combined_knowledge_base(
    storage_dir: str = None, knowledge_dir: str = None
) -> Optional[CombinedKnowledgeBase]:
    if storage_dir is None:
        storage_dir = f"{DATA_DIR}/agno"
    if knowledge_dir is None:
        knowledge_dir = f"{DATA_DIR}/knowledge"

    storage_path = Path(storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)

    knowledge_path = Path(knowledge_dir)
    if not knowledge_path.exists():
        logger.warning("No knowledge directory found at %s", knowledge_path)
        return None

    text_files = list(knowledge_path.glob("*.txt")) + list(knowledge_path.glob("*.md"))
    pdf_files = list(knowledge_path.glob("*.pdf"))

    if not text_files and not pdf_files:
        logger.warning("No knowledge files found in %s", knowledge_path)
        return None

    embedder = OllamaEmbedder(id="nomic-embed-text", host=OLLAMA_URL, dimensions=768)
    knowledge_sources = []

    if text_files:
        text_vector_db = LanceDb(
            uri=str(storage_path / "lancedb"),
            table_name="text_knowledge",
            search_type=SearchType.hybrid,
            embedder=embedder,
        )
        text_kb = TextKnowledgeBase(
            path=knowledge_path, vector_db=text_vector_db, num_documents=len(text_files)
        )
        knowledge_sources.append(text_kb)
        logger.info("Created TextKnowledgeBase with %d files", len(text_files))

    if pdf_files:
        pdf_vector_db = LanceDb(
            uri=str(storage_path / "lancedb"),
            table_name="pdf_knowledge",
            search_type=SearchType.hybrid,
            embedder=embedder,
        )
        pdf_kb = PDFKnowledgeBase(path=knowledge_path, vector_db=pdf_vector_db)
        knowledge_sources.append(pdf_kb)
        logger.info("Created PDFKnowledgeBase with %d files", len(pdf_files))

    arxiv_vector_db = LanceDb(
        uri=str(storage_path / "lancedb"),
        table_name="arxiv_knowledge",
        search_type=SearchType.hybrid,
        embedder=embedder,
    )
    arxiv_kb = ArxivKnowledgeBase(vector_db=arxiv_vector_db)
    knowledge_sources.append(arxiv_kb)
    logger.info("Created ArxivKnowledgeBase")

    if knowledge_sources:
        combined_vector_db = LanceDb(
            uri=str(storage_path / "lancedb"),
            table_name="combined_knowledge",
            search_type=SearchType.hybrid,
            embedder=embedder,
        )
        combined_kb = CombinedKnowledgeBase(
            sources=knowledge_sources, vector_db=combined_vector_db
        )
        logger.info("Successfully created combined knowledge base")
        return combined_kb

    return None


async def ingest_into_lightrag(knowledge_path: Path):
    logger.info("Starting LightRAG ingestion...")

    # Set up storage directories
    storage_dir = Path(DATA_DIR) / "lightrag"
    storage_dir.mkdir(parents=True, exist_ok=True)

    vector_storage = LanceDBVectorStorage(str(storage_dir / "vector_store"))
    doc_storage = JsonlDocStorage(str(storage_dir / "doc_store.jsonl"))

    lightrag = LightRAG(
        vector_storage=vector_storage,
        host=get_env_value("LIGHTRAG_HOST", default="http://localhost:9621"),
        api_key=get_env_value("LIGHTRAG_API_KEY", default=None),
    )

    await lightrag.initialize_storages()

    for file_path in knowledge_path.glob("**/*"):
        if file_path.is_file() and file_path.suffix.lower() in {
            ".pdf",
            ".txt",
            ".md",
            ".docx",
        }:
            logger.info(f"Ingesting file into LightRAG: {file_path}")
            await lightrag.ingest_file(str(file_path))

    logger.info("Completed LightRAG ingestion.")


async def build_and_ingest():
    logger.info("Starting full knowledge base build and LightRAG ingestion...")
    create_agno_storage()
    create_agno_memory()
    create_combined_knowledge_base()

    knowledge_path = Path(f"{DATA_DIR}/knowledge")
    await ingest_into_lightrag(knowledge_path)


if __name__ == "__main__":
    asyncio.run(build_and_ingest())
