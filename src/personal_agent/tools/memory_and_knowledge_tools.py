# src/personal_agent/tools/memory_and_knowledge_tools.py

import asyncio
import hashlib
import mimetypes
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import List, Optional, Union
from urllib.parse import urlparse

import aiohttp
import requests
from agno.tools import Toolkit, tool
from agno.utils.log import log_debug

from src.personal_agent.core.knowledge_manager import KnowledgeManager
from src.personal_agent.core.semantic_memory_manager import (
    MemoryStorageStatus,
    SemanticMemoryManager,
)

from ..config import settings
from ..utils import setup_logging

logger = setup_logging(__name__)


class MemoryAndKnowledgeTools(Toolkit):
    """A unified toolset for all memory and knowledge operations."""

    def __init__(
        self, memory_manager: SemanticMemoryManager, knowledge_manager: KnowledgeManager
    ):
        self.memory_manager = memory_manager
        self.knowledge_manager = knowledge_manager

        # Collect memory tool methods only - knowledge tools are now in KnowledgeTools
        tools = [
            # Memory tools (async)
            self.store_user_memory,
            self.query_memory,
            self.update_memory,
            self.delete_memory,
            self.get_recent_memories,
            self.get_all_memories,
            self.get_memory_stats,
            self.get_memories_by_topic,
            self.list_memories,
            self.store_graph_memory,
            self.query_graph_memory,
            self.get_memory_graph_labels,
            self.clear_memories,
            self.delete_memories_by_topic,
            self.clear_all_memories,
        ]

        # Initialize the Toolkit with memory tools only
        super().__init__(
            name="memory_and_knowledge_tools",
            tools=tools,
            instructions="Memory operations tools - knowledge tools are now in KnowledgeTools class",
        )

    # Knowledge ingestion methods have been consolidated into KnowledgeTools
    # This class now focuses only on memory operations

    # Memory Tools will be migrated here

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

    async def get_recent_memories(self, limit: int = 10) -> str:
        """Get recent memories by searching all memories and sorting by date."""
        return await self.memory_manager.get_recent_memories(limit)

    async def get_all_memories(self) -> str:
        """Get all user memories."""
        return await self.memory_manager.get_all_memories()

    async def get_memory_stats(self) -> str:
        """Get memory statistics."""
        return await self.memory_manager.get_memory_stats()

    async def get_memories_by_topic(
        self, topics: Union[List[str], str, None] = None, limit: Union[int, None] = None
    ) -> str:
        """Get memories by topic without similarity search."""
        return await self.memory_manager.get_memories_by_topic(topics, limit)

    async def list_memories(self) -> str:
        """List all memories in a simple, user-friendly format."""
        return await self.memory_manager.list_memories()

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

    async def clear_memories(self) -> str:
        """Clear all memories for the user using direct SemanticMemoryManager calls."""
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
        """Delete all memories associated with a specific topic or list of topics."""
        try:
            if isinstance(topics, str):
                topics = [t.strip() for t in topics.split(",")]

            (
                success,
                message,
            ) = self.memory_manager.agno_memory.memory_manager.delete_memories_by_topic(
                topics=topics,
                db=self.memory_manager.agno_memory.db,
                user_id=self.memory_manager.user_id,
            )

            if success:
                logger.info(
                    "Deleted memories for topics '%s' for user %s",
                    ", ".join(topics),
                    self.memory_manager.user_id,
                )
                return f"✅ {message}"
            else:
                logger.error(
                    "Failed to delete memories for topics %s: %s",
                    ", ".join(topics),
                    message,
                )
                return f"❌ Error deleting memories by topic: {message}"

        except Exception as e:
            logger.error("Error deleting memories by topic: %s", e)
            return f"❌ Error deleting memories by topic: {str(e)}"

    async def clear_all_memories(self) -> str:
        """Clear all memories from both SQLite and LightRAG systems."""
        return await self.memory_manager.clear_all_memories()
