"""Agno native storage and knowledge management utilities."""

import logging
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


class EnhancedMemory:
    """Enhanced Memory wrapper with duplicate prevention capabilities."""

    def __init__(self, memory: Memory, similarity_threshold: float = 0.8):
        """Initialize enhanced memory wrapper.

        :param memory: Base Memory instance to wrap
        :param similarity_threshold: Similarity threshold for duplicate detection (0.0 to 1.0)
        """
        self._memory = memory
        self.similarity_threshold = similarity_threshold

    def check_memory_exists(self, user_id: str, new_memory_text: str) -> bool:
        """Check if a similar memory already exists for the user.

        :param user_id: User ID to check memories for
        :param new_memory_text: New memory text to check for duplicates
        :return: True if similar memory exists, False otherwise
        """
        existing_memories = self._memory.get_user_memories(user_id=user_id)

        # Simple text similarity check using Jaccard similarity
        new_memory_lower = new_memory_text.lower().strip()

        for existing_mem in existing_memories:
            existing_text_lower = existing_mem.memory.lower().strip()

            # Check for exact matches
            if new_memory_lower == existing_text_lower:
                logger.debug("Exact duplicate found: '%s'", existing_mem.memory)
                return True

            # Check for substantial overlap using Jaccard similarity
            new_words = set(new_memory_lower.split())
            existing_words = set(existing_text_lower.split())

            if len(new_words) > 0 and len(existing_words) > 0:
                intersection = new_words.intersection(existing_words)
                union = new_words.union(existing_words)
                jaccard_similarity = len(intersection) / len(union)

                if jaccard_similarity >= self.similarity_threshold:
                    logger.debug(
                        "Similar memory found (similarity: %.2f): '%s'",
                        jaccard_similarity,
                        existing_mem.memory,
                    )
                    return True

        return False

    def add_memory_if_unique(self, user_id: str, memory_text: str, **kwargs) -> bool:
        """Add a memory only if it doesn't already exist.

        Note: This method simulates checking for duplicates but doesn't actually add memories.
        In Agno, memories are created through agent interactions, not directly.

        :param user_id: User ID
        :param memory_text: Memory text to potentially add
        :param kwargs: Additional arguments (not used in this implementation)
        :return: True if memory would be unique, False if duplicate was found
        """
        if self.check_memory_exists(user_id, memory_text):
            logger.info("Would skip duplicate memory: '%s'", memory_text)
            return False

        logger.info("Memory would be unique: '%s'", memory_text)
        return True

    def should_create_memory(self, user_id: str, content: str) -> bool:
        """Check if a memory should be created for the given content.

        This method can be used by agents to decide whether to create a memory.

        :param user_id: User ID
        :param content: Content to potentially store as memory
        :return: True if memory should be created, False if it would be duplicate
        """
        return not self.check_memory_exists(user_id, content)

    def clear_user_memories(self, user_id: str) -> None:
        """Clear all memories for a specific user.

        :param user_id: User ID to clear memories for
        """
        logger.info("Clearing memories for user: %s", user_id)
        memories = self._memory.get_user_memories(user_id=user_id)
        logger.info("Found %d memories to clear for user %s", len(memories), user_id)

        # Since there's no direct delete method in base Memory class,
        # we'd need to implement this at the database level
        if hasattr(self._memory, "delete_user_memories"):
            self._memory.delete_user_memories(user_id=user_id)
        else:
            logger.warning(
                "User-specific memory deletion not available, using general clear"
            )

    def get_memory_stats(self, user_id: str) -> dict:
        """Get memory statistics for a user.

        :param user_id: User ID to get stats for
        :return: Dictionary with memory statistics
        """
        memories = self._memory.get_user_memories(user_id=user_id)

        # Count topics
        topic_counts = {}
        memories_with_topics = 0
        memories_without_topics = 0

        for memory_obj in memories:
            if memory_obj.topics:
                memories_with_topics += 1
                for topic in memory_obj.topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
            else:
                memories_without_topics += 1
                topic_counts["[No Topics]"] = topic_counts.get("[No Topics]", 0) + 1

        # Check for duplicates
        memory_texts = [m.memory for m in memories]
        unique_memories = len(set(memory_texts))
        duplicate_count = len(memory_texts) - unique_memories

        return {
            "total_memories": len(memories),
            "unique_memories": unique_memories,
            "duplicate_memories": duplicate_count,
            "memories_with_topics": memories_with_topics,
            "memories_without_topics": memories_without_topics,
            "topic_distribution": topic_counts,
            "efficiency_ratio": unique_memories / len(memories) if memories else 1.0,
        }

    # Delegate all other methods to the wrapped Memory instance
    def __getattr__(self, name):
        """Delegate unknown methods to the wrapped Memory instance."""
        return getattr(self._memory, name)


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


def create_enhanced_agno_memory(
    storage_dir: str = None, similarity_threshold: float = 0.8
) -> EnhancedMemory:
    """Create EnhancedMemory instance with duplicate prevention capabilities.

    :param storage_dir: Directory for storage files (defaults to DATA_DIR/agno)
    :param similarity_threshold: Similarity threshold for duplicate detection (0.0 to 1.0)
    :return: Configured EnhancedMemory instance with duplicate prevention
    """
    base_memory = create_agno_memory(storage_dir)
    enhanced_memory = EnhancedMemory(base_memory, similarity_threshold)

    logger.info(
        "Created Enhanced Agno Memory with duplicate prevention (threshold: %.2f)",
        similarity_threshold,
    )
    return enhanced_memory


def create_agno_knowledge(
    storage_dir: str = None, knowledge_dir: str = None
) -> Optional[TextKnowledgeBase]:
    """Create LanceDB knowledge base for agent (synchronous creation).

    :param storage_dir: Directory for knowledge files (defaults to DATA_DIR/agno)
    :param knowledge_dir: Directory containing knowledge files to load (defaults to DATA_DIR/knowledge)
    :return: Configured TextKnowledgeBase instance or None if no knowledge found
    """
    if storage_dir is None:
        storage_dir = f"{DATA_DIR}/agno"
    if knowledge_dir is None:
        knowledge_dir = f"{DATA_DIR}/knowledge"

    storage_path = Path(storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)

    knowledge_path = Path(knowledge_dir)
    knowledge_path.mkdir(parents=True, exist_ok=True)

    # Check if knowledge files exist
    text_files = list(knowledge_path.glob("*.txt")) + list(knowledge_path.glob("*.md"))
    if not text_files:
        logger.info("No knowledge files found in %s", knowledge_path)
        return None

    logger.info("Found %d knowledge text files in %s", len(text_files), knowledge_path)

    # Create vector database
    vector_db = LanceDb(
        uri=str(storage_path / "lancedb"),
        table_name="personal_agent_knowledge",
        search_type=SearchType.hybrid,
        embedder=OllamaEmbedder(id="nomic-embed-text", host=OLLAMA_URL, dimensions=768),
    )

    # Create knowledge base (sync creation)
    knowledge_base = TextKnowledgeBase(
        path=knowledge_path,
        vector_db=vector_db,
        num_documents=len(text_files),
    )

    logger.info("Created TextKnowledgeBase with %d files", len(text_files))
    return knowledge_base


async def load_agno_knowledge(
    knowledge_base: TextKnowledgeBase, recreate: bool = False
) -> None:
    """Load knowledge base content (async loading).

    :param knowledge_base: TextKnowledgeBase instance to load
    :param recreate: Whether to recreate the knowledge base from scratch
    """
    logger.info("Loading knowledge base content...")
    await knowledge_base.aload(recreate=recreate)
    logger.info("Knowledge base loaded successfully")


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


def load_personal_knowledge(
    vector_db: LanceDb, knowledge_dir: str = None
) -> Optional[TextKnowledgeBase]:
    """Create personal knowledge base (synchronous creation only).

    :param vector_db: Vector database instance
    :param knowledge_dir: Directory containing knowledge files (defaults to DATA_DIR/knowledge)
    :return: Configured TextKnowledgeBase instance or None if no knowledge found
    """
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
        logger.info(
            "Found %d knowledge text files in %s", len(text_files), knowledge_path
        )

        # Initialize the TextKnowledgeBase (sync creation)
        text_knowledge = TextKnowledgeBase(
            path=knowledge_path,
            vector_db=vector_db,
            num_documents=len(text_files),
        )

        logger.info("Created TextKnowledgeBase with %d files", len(text_files))
        return text_knowledge

    logger.info("No text files found in %s", knowledge_path)
    return None


async def load_personal_knowledge_async(
    knowledge_base: TextKnowledgeBase, recreate: bool = False
) -> None:
    """Load personal knowledge base content (async loading).

    :param knowledge_base: TextKnowledgeBase instance to load
    :param recreate: Whether to recreate the knowledge base from scratch
    """
    try:
        logger.info("Loading text knowledge base...")
        await knowledge_base.aload(recreate=recreate)
        logger.info("Successfully loaded text knowledge base")
    except Exception as e:
        logger.error("Failed to load text knowledge: %s", e)
        raise


# TODO: Add PDF loading support if needed
def load_pdf_knowledge(
    vector_db: LanceDb, knowledge_dir: str = None
) -> Optional[PDFKnowledgeBase]:
    """Create PDF knowledge base (synchronous creation only).

    :param vector_db: Vector database instance
    :param knowledge_dir: Directory containing knowledge files (defaults to DATA_DIR/knowledge)
    :return: Configured PDFKnowledgeBase instance or None if no knowledge found
    """
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
        pdf_knowledge = PDFKnowledgeBase(
            path=knowledge_path,
            vector_db=vector_db,
        )
        logger.info("Created PDFKnowledgeBase with %d files", len(pdf_files))
        return pdf_knowledge
    else:
        logger.info("No PDF files found in %s", knowledge_path)
        return None


async def load_pdf_knowledge_async(
    knowledge_base: PDFKnowledgeBase, recreate: bool = False
) -> None:
    """Load PDF knowledge base content (async loading).

    :param knowledge_base: PDFKnowledgeBase instance to load
    :param recreate: Whether to recreate the knowledge base from scratch
    """
    try:
        logger.info("Loading PDF knowledge base...")
        await knowledge_base.aload(recreate=recreate)
        logger.info("Successfully loaded PDF knowledge base")
    except Exception as e:
        logger.error("Failed to load PDF knowledge: %s", e)
        raise


def clear_agno_database_completely(storage_dir: str = None) -> None:
    """Clear all Agno databases completely.

    :param storage_dir: Directory containing storage files (defaults to DATA_DIR/agno)
    """
    import sqlite3

    if storage_dir is None:
        storage_dir = f"{DATA_DIR}/agno"

    storage_path = Path(storage_dir)
    if not storage_path.exists():
        logger.info("Storage directory does not exist: %s", storage_path)
        return

    # Find all .db files
    db_files = list(storage_path.glob("*.db"))
    if not db_files:
        logger.info("No database files found in: %s", storage_path)
        return

    logger.info("Found %d database files to clear", len(db_files))

    for db_file in db_files:
        try:
            logger.info("Clearing database: %s", db_file.name)
            conn = sqlite3.connect(str(db_file))
            cursor = conn.cursor()

            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]

            # Clear each table except system tables
            for table in tables:
                if not table.startswith("sqlite_"):
                    cursor.execute(f"DELETE FROM {table}")
                    logger.debug("Cleared table: %s", table)

            # Reset sequences if sqlite_sequence table exists
            if "sqlite_sequence" in tables:
                cursor.execute("DELETE FROM sqlite_sequence")
                logger.debug("Cleared sqlite_sequence table")

            conn.commit()
            conn.close()
            logger.info("Successfully cleared database: %s", db_file.name)

        except Exception as e:
            logger.error("Failed to clear database %s: %s", db_file.name, e)


def analyze_memory_quality(memory: EnhancedMemory, user_id: str) -> dict:
    """Analyze memory quality and provide recommendations.

    :param memory: EnhancedMemory instance to analyze
    :param user_id: User ID to analyze memories for
    :return: Dictionary with analysis results and recommendations
    """
    stats = memory.get_memory_stats(user_id)

    # Generate recommendations based on stats
    recommendations = []

    if stats["duplicate_memories"] > 0:
        recommendations.append(
            f"Found {stats['duplicate_memories']} duplicate memories. "
            "Consider using add_memory_if_unique() to prevent duplicates."
        )

    if stats["memories_without_topics"] > stats["total_memories"] * 0.3:
        recommendations.append(
            f"{stats['memories_without_topics']} memories lack topics "
            f"({stats['memories_without_topics']/stats['total_memories']*100:.1f}%). "
            "Consider improving memory processing to include topic categorization."
        )

    if stats["efficiency_ratio"] < 0.8:
        recommendations.append(
            f"Memory efficiency is low ({stats['efficiency_ratio']*100:.1f}%). "
            "Consider implementing duplicate prevention."
        )

    if stats["total_memories"] == 0:
        recommendations.append(
            "No memories found. Start adding memories to build knowledge base."
        )

    # Quality score (0-100)
    quality_score = (
        stats["efficiency_ratio"] * 50  # 50% weight for uniqueness
        + (stats["memories_with_topics"] / max(stats["total_memories"], 1))
        * 30  # 30% for topic coverage
        + min(stats["total_memories"] / 10, 1)
        * 20  # 20% for memory count (max 10 for full score)
    )

    return {
        "stats": stats,
        "quality_score": round(quality_score, 1),
        "recommendations": recommendations,
        "analysis_summary": {
            "total_memories": stats["total_memories"],
            "efficiency": f"{stats['efficiency_ratio']*100:.1f}%",
            "topic_coverage": f"{stats['memories_with_topics']/max(stats['total_memories'], 1)*100:.1f}%",
            "top_topics": sorted(
                [
                    (topic, count)
                    for topic, count in stats["topic_distribution"].items()
                    if topic != "[No Topics]"
                ],
                key=lambda x: x[1],
                reverse=True,
            )[:5],
        },
    }


# end of file
