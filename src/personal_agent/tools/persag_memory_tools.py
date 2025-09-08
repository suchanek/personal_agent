# src/personal_agent/tools/persag_memory_tools.py

from typing import List, Union

from agno.tools import Toolkit

from ..core.semantic_memory_manager import MemoryStorageStatus, SemanticMemoryManager
from ..utils import setup_logging

logger = setup_logging(__name__)


class PersagMemoryTools(Toolkit):
    """Personal Memory Management Tools - For storing and retrieving information ABOUT THE USER.

    Use these tools when you need to:
    - Store personal information the user tells you about themselves
    - Remember user preferences, interests, hobbies, and personal facts
    - Retrieve what you know about the user when they ask
    - Update or manage existing memories about the user
    - Store information the user explicitly asks you to remember

    CRITICAL RULES for what to store:
    - Store facts ABOUT the user (their preferences, experiences, personal info)
    - Store when user says "remember that..." or gives explicit personal information
    - Convert first-person statements to third-person for storage ("I like skiing" → "User likes skiing")

    DO NOT store:
    - Your own actions or tasks you perform FOR the user
    - Conversational filler or acknowledgments
    - Questions the user asks (unless they reveal personal info)
    - Creative content you generate

    When presenting memories, always convert back to second person ("User likes skiing" → "you like skiing").
    These tools help you build a personal relationship by remembering what matters to the user.
    """

    def __init__(self, memory_manager: SemanticMemoryManager):
        self.memory_manager = memory_manager

        # Collect memory tool methods (all async)
        tools = [
            self.store_user_memory,
            self.query_memory,
            self.update_memory,
            self.delete_memory,
            self.get_recent_memories,
            self.get_all_memories,
            self.get_memory_stats,
            self.get_memories_by_topic,
            self.list_all_memories,
            self.store_graph_memory,
            self.query_graph_memory,
            self.get_memory_graph_labels,
            self.clear_semantic_memories,
            self.delete_memories_by_topic,
            self.clear_all_memories,
        ]

        # Initialize the Toolkit
        super().__init__(
            name="persag_memory_tools",
            tools=tools,
            instructions="""Use these tools to remember personal information ABOUT THE USER. 
            Store user preferences, interests, and personal facts they share with you.
            Always check memory when asked about the user. Present memories in second person.
            Do NOT store your own actions - only store facts about the user themselves.""",
        )

    async def store_user_memory(
        self, content: str = "", topics: Union[List[str], str, None] = None
    ) -> str:
        """A tool that wraps the public store_user_memory method."""
        result = await self.memory_manager.store_user_memory(
            content=content, topics=topics
        )

        # Format the result for user display
        if result.is_success:
            if result.status == MemoryStorageStatus.SUCCESS:
                return f"✅ {result.message}"
            elif result.status == MemoryStorageStatus.SUCCESS_LOCAL_ONLY:
                return f"⚠️ {result.message}"
        else:
            # Handle different rejection types with appropriate emojis
            if result.status == MemoryStorageStatus.DUPLICATE_EXACT:
                return f"🔄 {result.message}"
            elif result.status == MemoryStorageStatus.DUPLICATE_SEMANTIC:
                return (
                    f"🔄 {result.message} (similarity: {result.similarity_score:.2f})"
                )
            elif result.status == MemoryStorageStatus.CONTENT_EMPTY:
                return f"❌ {result.message}"
            elif result.status == MemoryStorageStatus.CONTENT_TOO_LONG:
                return f"❌ {result.message}"
            else:
                return f"❌ {result.message}"

    async def query_memory(self, query: str, limit: Union[int, None] = None) -> str:
        """Search user memories using direct SemanticMemoryManager calls."""
        return await self.memory_manager.query_memory(query, limit)

    async def update_memory(
        self, memory_id: str, content: str, topics: Union[List[str], str, None] = None
    ) -> str:
        """Update an existing memory."""
        return await self.memory_manager.update_memory(memory_id, content, topics)

    async def delete_memory(self, memory_id: str) -> str:
        """Delete a memory from both SQLite and LightRAG systems."""
        return await self.memory_manager.delete_memory(memory_id)

    async def get_recent_memories(self, limit: Union[int, None] = 10) -> str:
        """Get recent memories by searching all memories and sorting by date."""
        # Handle None case by using default
        if limit is None:
            limit = 20
        return await self.memory_manager.get_recent_memories(limit)

    async def get_all_memories(self) -> str:
        """Get all user memories with full details including timestamps, IDs, and complete metadata.

        Use this when the user specifically requests detailed information or complete memory data.
        This provides comprehensive memory information but uses more context window space.
        """
        return await self.memory_manager.get_all_memories()

    async def get_memory_stats(self) -> str:
        """Get memory statistics."""
        return await self.memory_manager.get_memory_stats()

    async def get_memories_by_topic(
        self, topics: Union[List[str], str, None] = None, limit: Union[int, None] = None
    ) -> str:
        """Get memories by topic without similarity search."""
        return await self.memory_manager.get_memories_by_topic(topics, limit)

    async def list_all_memories(self) -> str:
        """List all user memories in a concise, summary format optimized for quick overview.

        Use this for general memory listing requests like 'list all memories', 'what do you know about me',
        or 'show me all memories'. This provides a performance-optimized summary without full details.
        PREFERRED for most listing requests to save context window space.
        """
        return await self.memory_manager.list_all_memories()

    async def store_graph_memory(
        self,
        content: str,
        topics: Union[List[str], str, None] = None,
        memory_id: str = None,
    ) -> str:
        """Store a memory in the LightRAG graph database to capture relationships."""
        return await self.memory_manager.store_graph_memory(content, topics, memory_id)

    async def query_graph_memory(
        self,
        query: str,
        mode: str = "mix",
        top_k: int = 5,
        response_type: str = "Multiple Paragraphs",
    ) -> dict:
        """Query the LightRAG memory graph to explore relationships between memories."""
        return await self.memory_manager.query_graph_memory(
            query, mode, top_k, response_type
        )

    async def get_memory_graph_labels(self) -> str:
        """Get the list of all entity and relation labels from the memory graph."""
        return await self.memory_manager.get_memory_graph_labels()

    async def clear_semantic_memories(self) -> str:
        """Clear all semantic memories for the user using direct SemanticMemoryManager calls."""
        try:
            # Direct call to SemanticMemoryManager.clear_memories()
            success, message = (
                self.memory_manager.agno_memory.memory_manager.clear_memories(
                    db=self.memory_manager.agno_memory.db,
                    user_id=self.memory_manager.user_id,
                )
            )

            if success:
                logger.info(
                    "Cleared all memories for user %s", self.memory_manager.user_id
                )
                return f"✅ {message}"
            else:
                logger.error("Failed to clear memories: %s", message)
                return f"❌ Error clearing memories: {message}"

        except Exception as e:
            logger.error("Error clearing memories: %s", e)
            return f"❌ Error clearing memories: {str(e)}"

    async def delete_memories_by_topic(self, topics: Union[List[str], str]) -> str:
        """Delete all memories associated with a specific topic or list of topics from both local and graph memory."""
        return await self.memory_manager.delete_memories_by_topic(topics)

    async def clear_all_memories(self) -> str:
        """Clear all memories from both SQLite and LightRAG systems."""
        return await self.memory_manager.clear_all_memories()
