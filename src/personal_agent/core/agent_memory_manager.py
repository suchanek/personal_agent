"""
Agent Memory Manager for the Personal AI Agent.

This module provides a dedicated class for managing memory operations,
extracted from the AgnoPersonalAgent class to improve modularity and maintainability.
"""

import asyncio
import hashlib

# Configure logging
import logging
import os
import re
import tempfile
import time
from textwrap import dedent
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
import spacy

from .semantic_memory_manager import MemoryStorageResult, MemoryStorageStatus

logger = logging.getLogger(__name__)


class AgentMemoryManager:
    """Manages memory operations including storage, retrieval, and updates."""

    def __init__(
        self,
        user_id: str,
        storage_dir: str,
        agno_memory=None,
        lightrag_url: Optional[str] = None,
        lightrag_memory_url: Optional[str] = None,
        enable_memory: bool = True,
    ):
        """Initialize the memory manager.

        Args:
            user_id: User identifier for memory operations
            storage_dir: Directory for storage files
            agno_memory: Optional initialized agno memory instance
            lightrag_url: Optional URL for LightRAG API
            lightrag_memory_url: Optional URL for LightRAG Memory API
            enable_memory: Whether memory is enabled
        """
        self.user_id = user_id
        self.storage_dir = storage_dir
        self.agno_memory = agno_memory
        self.lightrag_url = lightrag_url
        self.lightrag_memory_url = lightrag_memory_url
        self.enable_memory = enable_memory

    def initialize(self, agno_memory):
        """Initialize the memory manager with agno_memory.

        Args:
            agno_memory: The initialized agno memory instance
        """
        self.agno_memory = agno_memory
        logger.info("Memory manager initialized with agno_memory")

    def direct_search_memories(
        self, query: str, limit: int = 10, similarity_threshold: float = 0.3
    ):
        """Direct semantic search without agentic retrieval.

        Args:
            query: The search query
            limit: Maximum number of results to return
            similarity_threshold: Minimum similarity score for results

        Returns:
            List of memory results
        """
        if not self.agno_memory:
            return []

        try:
            results = self.agno_memory.memory_manager.search_memories(
                query=query,
                db=self.agno_memory.db,
                user_id=self.user_id,
                limit=limit,
                similarity_threshold=similarity_threshold,
                search_topics=True,
                topic_boost=0.5,
            )
            return results
        except Exception as e:
            logger.warning("Direct semantic search failed: %s", e)
            return []

    async def get_memory_tools(self) -> List:
        """Create memory tools using direct SemanticMemoryManager method calls.

        This method creates memory tools that directly call SemanticMemoryManager methods
        instead of using complex wrapper functions, making the code much simpler and more maintainable.

        Returns:
            List of memory tool functions
        """
        if not self.enable_memory or not self.agno_memory:
            logger.warning("Memory not enabled or memory not initialized")
            return []

        # Check if memory is available
        if not self.agno_memory:
            logger.error("Memory not initialized")
            return []

        tools = []

        # Define all the memory tool functions
        async def store_user_memory_tool(
            content: str = "", topics: Union[List[str], str, None] = None
        ) -> str:
            """A tool that wraps the public store_user_memory method."""
            result = await self.store_user_memory(content=content, topics=topics)

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
                    return f"🔄 {result.message} (similarity: {result.similarity_score:.2f})"
                elif result.status == MemoryStorageStatus.CONTENT_EMPTY:
                    return f"❌ {result.message}"
                elif result.status == MemoryStorageStatus.CONTENT_TOO_LONG:
                    return f"❌ {result.message}"
                else:
                    return f"❌ {result.message}"

        async def query_memory_tool(query: str, limit: Union[int, None] = None) -> str:
            """Search user memories using direct SemanticMemoryManager calls."""
            return await self.query_memory(query, limit)

        async def update_memory_tool(
            memory_id: str, content: str, topics: Union[List[str], str, None] = None
        ) -> str:
            """Update an existing memory."""
            return await self.update_memory(memory_id, content, topics)

        async def delete_memory_tool(memory_id: str) -> str:
            """Delete a memory from both SQLite and LightRAG systems."""
            return await self.delete_memory(memory_id)

        async def get_recent_memories_tool(limit: int = 10) -> str:
            """Get recent memories by searching all memories and sorting by date."""
            return await self.get_recent_memories(limit)

        async def get_all_memories_tool() -> str:
            """Get all user memories."""
            return await self.get_all_memories()

        async def get_memory_stats_tool() -> str:
            """Get memory statistics."""
            return await self.get_memory_stats()

        async def get_memories_by_topic_tool(
            topics: Union[List[str], str, None] = None, limit: Union[int, None] = None
        ) -> str:
            """Get memories by topic without similarity search."""
            return await self.get_memories_by_topic(topics, limit)

        async def list_memories_tool() -> str:
            """List all memories in a simple, user-friendly format."""
            return await self.list_memories()

        async def store_graph_memory_tool(
            content: str,
            topics: Union[List[str], str, None] = None,
            memory_id: str = None,
        ) -> str:
            """Store a memory in the LightRAG graph database to capture relationships."""
            return await self.store_graph_memory(content, topics, memory_id)

        async def query_graph_memory_tool(
            query: str,
            mode: str = "mix",
            top_k: int = 5,
            response_type: str = "Multiple Paragraphs",
        ) -> dict:
            """Query the LightRAG memory graph to explore relationships between memories."""
            return await self.query_graph_memory(query, mode, top_k, response_type)

        async def get_memory_graph_labels_tool() -> str:
            """Get the list of all entity and relation labels from the memory graph."""
            return await self.get_memory_graph_labels()

        async def clear_memories_tool() -> str:
            """Clear all memories for the user using direct SemanticMemoryManager calls."""
            try:
                # Direct call to SemanticMemoryManager.clear_memories()
                success, message = self.agno_memory.memory_manager.clear_memories(
                    db=self.agno_memory.db, user_id=self.user_id
                )

                if success:
                    logger.info("Cleared all memories for user %s", self.user_id)
                    return f"✅ {message}"
                else:
                    logger.error("Failed to clear memories: %s", message)
                    return f"❌ Error clearing memories: {message}"

            except Exception as e:
                logger.error("Error clearing memories: %s", e)
                return f"❌ Error clearing memories: {str(e)}"

        async def delete_memories_by_topic_tool(topics: Union[List[str], str]) -> str:
            """Delete all memories associated with a specific topic or list of topics."""
            try:
                if isinstance(topics, str):
                    topics = [t.strip() for t in topics.split(",")]

                (
                    success,
                    message,
                ) = self.agno_memory.memory_manager.delete_memories_by_topic(
                    topics=topics, db=self.agno_memory.db, user_id=self.user_id
                )

                if success:
                    logger.info(
                        "Deleted memories for topics '%s' for user %s",
                        ", ".join(topics),
                        self.user_id,
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

        async def clear_all_memories_tool() -> str:
            """Clear all memories from both SQLite and LightRAG systems."""
            return await self.clear_all_memories()

        # Set proper function names for tool identification
        store_user_memory_tool.__name__ = "store_user_memory"
        query_memory_tool.__name__ = "query_memory"
        update_memory_tool.__name__ = "update_memory"
        delete_memory_tool.__name__ = "delete_memory"
        delete_memories_by_topic_tool.__name__ = "delete_memories_by_topic"
        clear_memories_tool.__name__ = "clear_memories"
        clear_all_memories_tool.__name__ = "clear_all_memories"
        get_recent_memories_tool.__name__ = "get_recent_memories"
        get_all_memories_tool.__name__ = "get_all_memories"
        get_memory_stats_tool.__name__ = "get_memory_stats"
        get_memories_by_topic_tool.__name__ = "get_memories_by_topic"
        list_memories_tool.__name__ = "list_memories"
        store_graph_memory_tool.__name__ = "store_graph_memory"
        query_graph_memory_tool.__name__ = "query_graph_memory"
        get_memory_graph_labels_tool.__name__ = "get_memory_graph_labels"

        # Add tools to the list
        tools.extend(
            [
                store_user_memory_tool,
                query_memory_tool,
                update_memory_tool,
                delete_memory_tool,
                delete_memories_by_topic_tool,
                clear_memories_tool,
                clear_all_memories_tool,
                get_recent_memories_tool,
                get_all_memories_tool,
                get_memory_stats_tool,
                get_memories_by_topic_tool,
                list_memories_tool,
                store_graph_memory_tool,
                query_graph_memory_tool,
                get_memory_graph_labels_tool,
            ]
        )

        logger.info(
            "Created %d memory tools using direct SemanticMemoryManager calls",
            len(tools),
        )
        return tools

    async def store_user_memory(
        self, content: str = "", topics: Union[List[str], str, None] = None
    ) -> MemoryStorageResult:
        """Store information as a user memory in BOTH local SQLite and LightRAG graph systems.

        Args:
            content: The information to store as a memory
            topics: Optional list of topics/categories for the memory (None = auto-classify)

        Returns:
            MemoryStorageResult: Structured result with detailed status information
        """
        # Validate that content is provided
        if not content or not content.strip():
            return MemoryStorageResult(
                status=MemoryStorageStatus.CONTENT_EMPTY,
                message="Content is required to store a memory. Please provide the information you want me to remember.",
                local_success=False,
                graph_success=False,
            )

        try:
            # Restate the user fact from first-person to third-person
            restated_content = self.restate_user_fact(content)
            
            # SIMPLIFIED TOPIC HANDLING: Handle the common cases simply
            if topics is None:
                # Leave as None - let memory manager auto-classify
                pass
            elif isinstance(topics, str):
                # Convert string to list, handle comma-separated values
                if "," in topics:
                    topics = [t.strip() for t in topics.split(",") if t.strip()]
                else:
                    topics = [topics.strip()] if topics.strip() else None
            elif isinstance(topics, list):
                # Clean up list - remove empty entries
                topics = [str(t).strip() for t in topics if str(t).strip()]
                if not topics:
                    topics = None
            else:
                # Convert anything else to string and put in list
                topic_str = str(topics).strip()
                topics = [topic_str] if topic_str and topic_str != "None" else None

            # 1. Store in local SQLite memory system
            local_result = self.agno_memory.memory_manager.add_memory(
                memory_text=restated_content,
                db=self.agno_memory.db,
                user_id=self.user_id,
                topics=topics,
            )

            # Handle different rejection cases
            if not local_result.is_success:
                logger.info("Local memory rejected: %s", local_result.message)
                # Return the rejection status directly from the memory manager
                return local_result

            # Local storage succeeded
            logger.info(
                "Stored in local memory: %s... (ID: %s)",
                content[:50],
                local_result.memory_id,
            )

            # 2. Store in LightRAG graph memory system
            graph_success = False
            graph_message = ""

            try:
                # Store in graph memory
                graph_result = await self.store_graph_memory(
                    restated_content, local_result.topics, local_result.memory_id
                )
                logger.info("Graph memory result: %s", graph_result)
                if "✅" in graph_result:
                    graph_success = True
                    graph_message = "Graph memory synced successfully"
                else:
                    graph_message = f"Graph memory sync failed: {graph_result}"

            except Exception as e:
                logger.error("Error storing in graph memory: %s", e)
                graph_message = f"Graph memory error: {str(e)}"

            # Determine final status based on local and graph results
            if graph_success:
                final_status = MemoryStorageStatus.SUCCESS
                final_message = (
                    f"Memory stored successfully in both systems: {content[:50]}..."
                )
                logger.info(
                    "✅ DUAL STORAGE SUCCESS: Memory stored in both local SQLite and LightRAG graph"
                )
            else:
                final_status = MemoryStorageStatus.SUCCESS_LOCAL_ONLY
                final_message = f"Memory stored in local system only: {content[:50]}... | {graph_message}"
                logger.warning(
                    "⚠️ PARTIAL STORAGE: Memory stored in local SQLite only (graph sync failed)"
                )

            # Return the enhanced result with dual storage information
            return MemoryStorageResult(
                status=final_status,
                message=final_message,
                memory_id=local_result.memory_id,
                topics=local_result.topics,
                local_success=True,
                graph_success=graph_success,
                similarity_score=local_result.similarity_score,
            )

        except Exception as e:
            logger.error("Error storing user memory: %s", e)
            return MemoryStorageResult(
                status=MemoryStorageStatus.STORAGE_ERROR,
                message=f"Error storing memory: {str(e)}",
                local_success=False,
                graph_success=False,
            )

    def restate_user_fact(self, content: str) -> str:
        """Restate a user fact from first-person to third-person.

        This method converts statements like "I have a PhD" to "{user_id} has a PhD"
        to ensure correct entity mapping in the knowledge graph.

        Args:
            content: The original fact from the user

        Returns:
            The restated fact
        """
        # Ensure user_id is a safe string for replacement
        user_id_str = str(self.user_id)

        # Define regex patterns for pronoun and verb replacement
        # Using word boundaries (\b) to avoid replacing parts of words like "mine" in "mining"
        patterns = [
            (r"\bI am\b", f"{user_id_str} is"),
            (r"\bI was\b", f"{user_id_str} was"),
            (r"\bI have\b", f"{user_id_str} has"),
            (r"\bI'm\b", f"{user_id_str} is"),
            (r"\bI've\b", f"{user_id_str} has"),
            (r"\bI\b", user_id_str),
            (r"\bmy\b", f"{user_id_str}'s"),
            (r"\bmine\b", f"{user_id_str}'s"),
            (r"\bmyself\b", user_id_str),
        ]

        restated_content = content
        for pattern, replacement in patterns:
            # Use re.IGNORECASE to handle variations like "i" vs "I"
            restated_content = re.sub(
                pattern, replacement, restated_content, flags=re.IGNORECASE
            )

        return restated_content

    async def seed_entity_in_graph(self, entity_name: str, entity_type: str) -> bool:
        """Seed an entity into the graph by creating and uploading a physical file.

        Args:
            entity_name: Name of the entity to create
            entity_type: Type of the entity

        Returns:
            True if entity was successfully seeded
        """
        try:
            # Create a minimal document to seed the entity
            seed_text = f"{entity_name} is a {entity_type.lower()}."

            # Create a unique filename for this entity seed
            entity_hash = hashlib.md5(
                f"{entity_name}_{entity_type}_{time.time()}".encode()
            ).hexdigest()[:8]
            filename = f"entity_seed_{entity_name.replace(' ', '_').replace('/', '_')}_{entity_hash}.txt"

            # Create a temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as temp_file:
                temp_file.write(seed_text)
                temp_file_path = temp_file.name

            try:
                # Upload the file using the /documents/upload endpoint
                url = f"{self.lightrag_memory_url}/documents/upload"

                async with aiohttp.ClientSession() as session:
                    with open(temp_file_path, "rb") as file:
                        # Create form data for file upload
                        data = aiohttp.FormData()
                        data.add_field(
                            "file", file, filename=filename, content_type="text/plain"
                        )

                        async with session.post(url, data=data, timeout=30) as resp:
                            if resp.status in [200, 201]:
                                logger.info(
                                    f"Successfully seeded entity: {entity_name}"
                                )
                                return True
                            else:
                                error_detail = await resp.text()
                                logger.warning(
                                    f"Failed to seed entity {entity_name}: {error_detail}"
                                )
                                return False

            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass  # Ignore cleanup errors

        except Exception as e:
            logger.error(f"Error seeding entity {entity_name}: {e}")
            return False

    async def check_entity_exists(self, entity_name: str) -> bool:
        """Check if entity exists in the graph using the correct /graph/entity/exists endpoint.

        Args:
            entity_name: Name of the entity to check

        Returns:
            True if entity exists
        """
        try:
            url = f"{self.lightrag_memory_url}/graph/entity/exists"

            # Try different parameter formats that LightRAG might expect
            params_options = [
                {"entity_name": entity_name},
                {"name": entity_name},
                {"entity": entity_name},
            ]

            async with aiohttp.ClientSession() as session:
                for params in params_options:
                    try:
                        async with session.get(url, params=params, timeout=10) as resp:
                            if resp.status == 200:
                                result = await resp.json()
                                # Handle different response formats
                                if isinstance(result, bool):
                                    exists = result
                                elif isinstance(result, dict):
                                    exists = result.get("exists", False) or result.get(
                                        "found", False
                                    )
                                else:
                                    exists = False

                                logger.debug(
                                    f"Entity {entity_name} exists: {exists} (params: {params})"
                                )
                                return exists
                            elif resp.status == 422:
                                # Try next parameter format
                                continue
                            else:
                                logger.warning(
                                    f"Failed to check entity existence for {entity_name}: {resp.status}"
                                )
                                break
                    except Exception as e:
                        logger.debug(f"Error with params {params}: {e}")
                        continue

                # If all parameter formats fail, fall back to label list approach
                logger.debug(
                    f"All parameter formats failed for {entity_name}, falling back to label list"
                )
                url = f"{self.lightrag_memory_url}/graph/label/list"
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        labels_data = await resp.json()

                        # Handle both response formats: direct array or dict with 'labels' key
                        if isinstance(labels_data, list):
                            all_labels = labels_data
                        elif isinstance(labels_data, dict) and "labels" in labels_data:
                            all_labels = labels_data["labels"]
                        else:
                            all_labels = []

                        # Check if entity name exists in labels (case-insensitive)
                        exists = any(
                            label.lower() == entity_name.lower() for label in all_labels
                        )
                        logger.debug(
                            f"Entity {entity_name} exists (via labels): {exists}"
                        )
                        return exists
                    else:
                        logger.warning(
                            f"Failed to get graph labels for entity check: {resp.status}"
                        )
                        return False

        except Exception as e:
            logger.error(f"Error checking entity existence for {entity_name}: {e}")
            return False

    async def clear_all_memories(self) -> str:
        """Clear all memories from both SQLite and LightRAG systems.

        This method provides a complete reset of the dual memory system by:
        1. Clearing all memories from the local SQLite database
        2. Clearing all documents from the LightRAG memory server
        3. Deleting the knowledge graph file

        Returns:
            str: Success or error message
        """
        try:
            results = []

            # 1. Clear local SQLite memories
            if self.agno_memory and self.agno_memory.memory_manager:
                success, message = self.agno_memory.memory_manager.clear_memories(
                    db=self.agno_memory.db, user_id=self.user_id
                )

                if success:
                    logger.info(
                        "Cleared all memories from SQLite for user %s", self.user_id
                    )
                    results.append("✅ Local memory: All memories cleared successfully")
                else:
                    logger.error("Failed to clear memories from SQLite: %s", message)
                    results.append(f"❌ Local memory error: {message}")
            else:
                logger.warning(
                    "Memory system not initialized, skipping SQLite memory clear"
                )
                results.append("⚠️ Local memory: System not initialized")

            # 2. Clear LightRAG graph memories
            try:
                # Use LightRAG API to delete all documents
                url = f"{self.lightrag_memory_url}/documents"

                # First get all documents
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=30) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            all_docs = []

                            # Extract documents from response
                            if isinstance(data, dict) and "statuses" in data:
                                statuses = data["statuses"]
                                for status_name, docs_list in statuses.items():
                                    if isinstance(docs_list, list):
                                        all_docs.extend(docs_list)
                            elif isinstance(data, dict) and "documents" in data:
                                all_docs = data["documents"]
                            elif isinstance(data, list):
                                all_docs = data

                            if all_docs:
                                # Delete all documents
                                doc_ids = [doc["id"] for doc in all_docs]
                                payload = {"doc_ids": doc_ids, "delete_file": True}

                                async with session.delete(
                                    f"{self.lightrag_memory_url}/documents/delete_document",
                                    json=payload,
                                    timeout=60,
                                ) as del_resp:
                                    if del_resp.status == 200:
                                        logger.info(
                                            "Cleared all memories from LightRAG (%d documents)",
                                            len(doc_ids),
                                        )
                                        results.append(
                                            f"✅ Graph memory: All memories cleared successfully ({len(doc_ids)} documents)"
                                        )
                                    else:
                                        error_text = await del_resp.text()
                                        logger.error(
                                            "Failed to clear memories from LightRAG: %s",
                                            error_text,
                                        )
                                        results.append(
                                            f"❌ Graph memory error: {error_text}"
                                        )
                            else:
                                logger.info("No documents found in LightRAG to clear")
                                results.append(
                                    "✅ Graph memory: No documents found to clear"
                                )
                        else:
                            error_text = await resp.text()
                            logger.error(
                                "Failed to get documents from LightRAG: %s", error_text
                            )
                            results.append(f"❌ Graph memory error: {error_text}")

                    # 3. Clear the knowledge graph file
                    try:
                        # Clear cache to ensure all in-memory data is flushed
                        await session.post(
                            f"{self.lightrag_memory_url}/documents/clear_cache",
                            json={"modes": None},
                            timeout=30,
                        )

                        # Delete the knowledge graph files
                        import os

                        from ..config.settings import (
                            LIGHTRAG_MEMORY_STORAGE_DIR,
                            LIGHTRAG_STORAGE_DIR,
                        )

                        graph_file_paths = [
                            os.path.join(
                                LIGHTRAG_MEMORY_STORAGE_DIR,
                                "graph_chunk_entity_relation.graphml",
                            )
                        ]

                        graph_deleted = False
                        for graph_file_path in graph_file_paths:
                            if os.path.exists(graph_file_path):
                                os.remove(graph_file_path)
                                logger.info(
                                    "Deleted knowledge graph file: %s", graph_file_path
                                )
                                graph_deleted = True

                        if graph_deleted:
                            results.append(
                                "✅ Knowledge graph: Graph file deleted successfully"
                            )
                        else:
                            logger.info("No knowledge graph files found to delete")
                            results.append(
                                "ℹ️ Knowledge graph: No graph files found to delete"
                            )

                    except Exception as e:
                        logger.error("Error deleting knowledge graph file: %s", e)
                        results.append(f"❌ Knowledge graph error: {str(e)}")

            except Exception as e:
                logger.error("Error clearing LightRAG memories: %s", e)
                results.append(f"❌ Graph memory error: {str(e)}")

            # Return combined results
            return " | ".join(results)

        except Exception as e:
            logger.error("Error clearing all memories: %s", e)
            return f"❌ Error clearing all memories: {str(e)}"

    # The following methods will be implemented in subsequent phases
    # They are placeholders for now

    async def query_memory(self, query: str, limit: Union[int, None] = None) -> str:
        """Search user memories using direct SemanticMemoryManager calls.

        Args:
            query: The query to search for in memories
            limit: Maximum number of memories to return

        Returns:
            str: Found memories or message if none found
        """
        try:
            stripped_query = query.strip().lower()

            # List of phrases that should trigger get_all_memories instead of search
            get_all_phrases = [
                "all",
                "all memories",
                "everything",
                "summarize all memories",
                "what do you know about me",
                "what have i told you",
                "list all memories",
                "show all memories",
                "tell me everything",
                "list everything you know",
            ]

            if stripped_query in get_all_phrases:
                logger.info(
                    "Generic query '%s' detected. Delegating to get_all_memories.",
                    query,
                )
                return await self.get_all_memories()

            # Validate query parameter
            if not query or not query.strip():
                logger.warning("Empty query provided to query_memory")
                return "❌ Error: Query cannot be empty. Please provide a search term."

            # Direct call to SemanticMemoryManager.search_memories()
            results = self.agno_memory.memory_manager.search_memories(
                query=query.strip(),
                db=self.agno_memory.db,
                user_id=self.user_id,
                limit=limit,
                similarity_threshold=0.3,
                search_topics=True,
                topic_boost=0.5,
            )

            if not results:
                logger.info("No matching memories found for query: %s", query)
                return f"🔍 No memories found for '{query}'. Try different keywords or ask me to remember something new!"

            # Format results
            display_memories = results[:limit] if limit else results
            result_note = f"🧠 MEMORY RETRIEVAL (found {len(results)} matches via semantic search)"

            result = f"{result_note}: The following memories were found for '{query}'. You must restate this information addressing the user as 'you' (second person), not as if you are the user:\n\n"

            for i, (memory, score) in enumerate(display_memories, 1):
                result += f"{i}. {memory.memory} (similarity: {score:.2f})\n"
                if memory.topics:
                    result += f"   Topics: {', '.join(memory.topics)}\n"
                result += "\n"

            result += "\nREMEMBER: Restate this information as an AI assistant talking ABOUT the user, not AS the user. Use 'you' instead of 'I' when referring to the user's information."

            logger.info("Found %d matching memories for query: %s", len(results), query)
            return result

        except Exception as e:
            logger.error("Error querying memories: %s", e)
            return f"❌ Error searching memories: {str(e)}"

    async def update_memory(
        self, memory_id: str, content: str, topics: Union[List[str], str, None] = None
    ) -> str:
        """Update an existing memory using direct SemanticMemoryManager calls.

        Args:
            memory_id: ID of the memory to update
            content: New memory content
            topics: Optional list of topics/categories for the memory

        Returns:
            str: Success or error message
        """
        try:
            # SIMPLIFIED TOPIC HANDLING: Handle the common cases simply
            if topics is None:
                # Leave as None - let memory manager auto-classify
                pass
            elif isinstance(topics, str):
                # Convert string to list, handle comma-separated values
                if "," in topics:
                    topics = [t.strip() for t in topics.split(",") if t.strip()]
                else:
                    topics = [topics.strip()] if topics.strip() else None
            elif isinstance(topics, list):
                # Clean up list - remove empty entries
                topics = [str(t).strip() for t in topics if str(t).strip()]
                if not topics:
                    topics = None
            else:
                # Convert anything else to string and put in list
                topic_str = str(topics).strip()
                topics = [topic_str] if topic_str and topic_str != "None" else None

            # Direct call to SemanticMemoryManager.update_memory()
            success, message = self.agno_memory.memory_manager.update_memory(
                memory_id=memory_id,
                memory_text=content,
                db=self.agno_memory.db,
                user_id=self.user_id,
                topics=topics,
            )

            if success:
                logger.info("Updated memory %s: %s...", memory_id, content[:50])
                return f"✅ Successfully updated memory: {content[:50]}..."
            else:
                logger.error("Failed to update memory %s: %s", memory_id, message)
                return f"❌ Error updating memory: {message}"

        except Exception as e:
            logger.error("Error updating memory: %s", e)
            return f"❌ Error updating memory: {str(e)}"

    async def delete_memory(self, memory_id: str) -> str:
        """Delete a memory from both SQLite and LightRAG systems.

        Args:
            memory_id: ID of the memory to delete

        Returns:
            str: Success or error message
        """
        try:
            results = []

            # 1. Delete from local SQLite memory system
            success, message = self.agno_memory.memory_manager.delete_memory(
                memory_id=memory_id, db=self.agno_memory.db, user_id=self.user_id
            )

            if success:
                logger.info("Deleted memory %s from SQLite", memory_id)
                results.append("✅ Local memory: Deleted successfully")
            else:
                logger.error(
                    "Failed to delete memory %s from SQLite: %s", memory_id, message
                )
                results.append(f"❌ Local memory error: {message}")

            # 2. Delete from LightRAG graph memory system
            try:
                # Construct the filename pattern to search for
                filename_pattern = f"memory_{memory_id}_*.txt"

                # Use LightRAG API to find documents matching the pattern
                url = f"{self.lightrag_memory_url}/documents"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=30) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            all_docs = []

                            # Extract documents from response
                            if isinstance(data, dict) and "statuses" in data:
                                statuses = data["statuses"]
                                for status_name, docs_list in statuses.items():
                                    if isinstance(docs_list, list):
                                        all_docs.extend(docs_list)
                            elif isinstance(data, dict) and "documents" in data:
                                all_docs = data["documents"]
                            elif isinstance(data, list):
                                all_docs = data

                            # Find documents matching our memory_id pattern
                            docs_to_delete = []
                            for doc in all_docs:
                                file_path = doc.get("file_path", "")
                                if file_path and f"memory_{memory_id}_" in file_path:
                                    docs_to_delete.append(doc)

                            if docs_to_delete:
                                # Delete the matching documents
                                doc_ids = [doc["id"] for doc in docs_to_delete]
                                payload = {"doc_ids": doc_ids, "delete_file": True}

                                async with session.delete(
                                    f"{self.lightrag_memory_url}/documents/delete_document",
                                    json=payload,
                                    timeout=60,
                                ) as del_resp:
                                    if del_resp.status == 200:
                                        logger.info(
                                            "Deleted memory %s from LightRAG", memory_id
                                        )
                                        results.append(
                                            "✅ Graph memory: Deleted successfully"
                                        )
                                    else:
                                        error_text = await del_resp.text()
                                        logger.error(
                                            "Failed to delete memory %s from LightRAG: %s",
                                            memory_id,
                                            error_text,
                                        )
                                        results.append(
                                            f"❌ Graph memory error: {error_text}"
                                        )
                            else:
                                logger.info(
                                    "No matching documents found in LightRAG for memory %s",
                                    memory_id,
                                )
                                results.append(
                                    "⚠️ Graph memory: No matching documents found"
                                )
                        else:
                            error_text = await resp.text()
                            logger.error(
                                "Failed to get documents from LightRAG: %s", error_text
                            )
                            results.append(f"❌ Graph memory error: {error_text}")
            except Exception as e:
                logger.error("Error deleting from LightRAG: %s", e)
                results.append(f"❌ Graph memory error: {str(e)}")

            # Return combined results
            return " | ".join(results)

        except Exception as e:
            logger.error("Error deleting memory: %s", e)
            return f"❌ Error deleting memory: {str(e)}"

    async def get_recent_memories(self, limit: int = 10) -> str:
        """Get recent memories by searching all memories and sorting by date.

        Args:
            limit: Maximum number of memories to return

        Returns:
            str: Formatted string of recent memories
        """
        try:
            # Direct call to SemanticMemoryManager.get_all_memories()
            memories = self.agno_memory.memory_manager.get_all_memories(
                db=self.agno_memory.db, user_id=self.user_id
            )

            if not memories:
                logger.info("No memories found for user %s", self.user_id)
                return "🔍 No memories found. Try storing some information first!"

            # Sort memories by timestamp (newest first)
            sorted_memories = sorted(
                memories,
                key=lambda m: m.timestamp if hasattr(m, "timestamp") else 0,
                reverse=True,
            )

            # Limit the number of memories
            display_memories = sorted_memories[:limit] if limit else sorted_memories

            # Format results
            result = f"🧠 RECENT MEMORIES (showing {len(display_memories)} of {len(memories)} total memories):\n\n"

            for i, memory in enumerate(display_memories, 1):
                # Format the memory content
                result += f"{i}. {memory.memory}\n"

                # Add topics if available
                if hasattr(memory, "topics") and memory.topics:
                    result += f"   Topics: {', '.join(memory.topics)}\n"

                # Add timestamp if available
                if hasattr(memory, "timestamp") and memory.timestamp:
                    # Convert timestamp to readable format
                    from datetime import datetime

                    timestamp = datetime.fromtimestamp(memory.timestamp)
                    result += f"   Created: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"

                # Add memory ID for reference
                result += f"   ID: {memory.memory_id}\n\n"

            logger.info(
                "Retrieved %d recent memories for user %s",
                len(display_memories),
                self.user_id,
            )
            return result

        except Exception as e:
            logger.error("Error retrieving recent memories: %s", e)
            return f"❌ Error retrieving recent memories: {str(e)}"

    async def get_all_memories(self) -> str:
        """Get all user memories.

        Returns:
            str: Formatted string of all memories
        """
        try:
            # Direct call to SemanticMemoryManager.get_all_memories()
            memories = self.agno_memory.memory_manager.get_all_memories(
                db=self.agno_memory.db, user_id=self.user_id
            )

            if not memories:
                logger.info("No memories found for user %s", self.user_id)
                return "🔍 No memories found. Try storing some information first!"

            # Sort memories by timestamp (newest first)
            sorted_memories = sorted(
                memories,
                key=lambda m: m.timestamp if hasattr(m, "timestamp") else 0,
                reverse=True,
            )

            # Format results
            result = f"🧠 ALL MEMORIES ({len(memories)} total):\n\n"

            for i, memory in enumerate(sorted_memories, 1):
                # Format the memory content
                result += f"{i}. {memory.memory}\n"

                # Add topics if available
                if hasattr(memory, "topics") and memory.topics:
                    result += f"   Topics: {', '.join(memory.topics)}\n"

                # Add timestamp if available
                if hasattr(memory, "timestamp") and memory.timestamp:
                    # Convert timestamp to readable format
                    from datetime import datetime

                    timestamp = datetime.fromtimestamp(memory.timestamp)
                    result += f"   Created: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"

                # Add memory ID for reference
                result += f"   ID: {memory.memory_id}\n\n"

            logger.info(
                "Retrieved all %d memories for user %s", len(memories), self.user_id
            )
            return result

        except Exception as e:
            logger.error("Error retrieving all memories: %s", e)
            return f"❌ Error retrieving all memories: {str(e)}"

    async def get_memory_stats(self) -> str:
        """Get memory statistics.

        Returns:
            str: Formatted string with memory statistics
        """
        try:
            # Direct call to SemanticMemoryManager.get_all_memories()
            memories = self.agno_memory.memory_manager.get_all_memories(
                db=self.agno_memory.db, user_id=self.user_id
            )

            if not memories:
                logger.info("No memories found for user %s", self.user_id)
                return "🔍 No memories found. Try storing some information first!"

            # Calculate basic statistics
            total_memories = len(memories)

            # Get all unique topics
            all_topics = {}
            for memory in memories:
                if hasattr(memory, "topics") and memory.topics:
                    for topic in memory.topics:
                        all_topics[topic] = all_topics.get(topic, 0) + 1

            # Sort topics by frequency (most common first)
            sorted_topics = sorted(all_topics.items(), key=lambda x: x[1], reverse=True)

            # Calculate average memory length
            total_length = sum(len(memory.memory) for memory in memories)
            avg_length = total_length / total_memories if total_memories > 0 else 0

            # Get oldest and newest memory timestamps
            timestamps = [
                memory.timestamp for memory in memories if hasattr(memory, "timestamp")
            ]
            oldest_timestamp = min(timestamps) if timestamps else None
            newest_timestamp = max(timestamps) if timestamps else None

            # Format results
            result = f"📊 MEMORY STATISTICS\n\n"
            result += f"Total memories: {total_memories}\n"
            result += f"Average memory length: {avg_length:.1f} characters\n"

            if oldest_timestamp:
                from datetime import datetime

                oldest_date = datetime.fromtimestamp(oldest_timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                result += f"Oldest memory: {oldest_date}\n"

            if newest_timestamp:
                from datetime import datetime

                newest_date = datetime.fromtimestamp(newest_timestamp).strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
                result += f"Newest memory: {newest_date}\n"

            if sorted_topics:
                result += f"\nTop topics:\n"
                # Show top 10 topics
                for topic, count in sorted_topics[:10]:
                    result += f"- {topic}: {count} memories\n"

                if len(sorted_topics) > 10:
                    result += f"... and {len(sorted_topics) - 10} more topics\n"

            logger.info("Generated memory statistics for user %s", self.user_id)
            return result

        except Exception as e:
            logger.error("Error retrieving memory statistics: %s", e)
            return f"❌ Error retrieving memory statistics: {str(e)}"

    async def get_memories_by_topic(
        self, topics: Union[List[str], str, None] = None, limit: Union[int, None] = None
    ) -> str:
        """Get memories by topic without similarity search.

        Args:
            topics: Topic or list of topics to filter memories by
            limit: Maximum number of memories to return

        Returns:
            str: Formatted string of memories matching the topics
        """
        try:
            # Validate topics parameter
            if topics is None:
                logger.warning("No topics provided to get_memories_by_topic")
                return (
                    "❌ Error: No topics provided. Please specify at least one topic."
                )

            # Parse topics parameter
            if isinstance(topics, str):
                # Convert string to list, handle comma-separated values
                if "," in topics:
                    topic_list = [t.strip() for t in topics.split(",") if t.strip()]
                else:
                    topic_list = [topics.strip()] if topics.strip() else []
            elif isinstance(topics, list):
                # Clean up list - remove empty entries
                topic_list = [str(t).strip() for t in topics if str(t).strip()]
            else:
                # Convert anything else to string and put in list
                topic_str = str(topics).strip()
                topic_list = [topic_str] if topic_str and topic_str != "None" else []

            if not topic_list:
                logger.warning("No valid topics provided after parsing")
                return "❌ Error: No valid topics provided. Please specify at least one topic."

            # Get all memories first
            all_memories = self.agno_memory.memory_manager.get_all_memories(
                db=self.agno_memory.db, user_id=self.user_id
            )

            if not all_memories:
                logger.info("No memories found for user %s", self.user_id)
                return "🔍 No memories found. Try storing some information first!"

            # Filter memories by topic
            filtered_memories = []
            for memory in all_memories:
                if hasattr(memory, "topics") and memory.topics:
                    # Check if any of the requested topics match this memory's topics
                    if any(
                        topic.lower() in [t.lower() for t in memory.topics]
                        for topic in topic_list
                    ):
                        filtered_memories.append(memory)

            if not filtered_memories:
                topics_str = ", ".join(topic_list)
                logger.info("No memories found for topics: %s", topics_str)
                return f"🔍 No memories found for topics: {topics_str}. Try different topics or store new memories with these topics."

            # Sort memories by timestamp (newest first)
            sorted_memories = sorted(
                filtered_memories,
                key=lambda m: m.timestamp if hasattr(m, "timestamp") else 0,
                reverse=True,
            )

            # Limit the number of memories if specified
            display_memories = sorted_memories[:limit] if limit else sorted_memories

            # Format results
            topics_str = ", ".join(topic_list)
            result = f"🧠 MEMORIES BY TOPIC: {topics_str} (showing {len(display_memories)} of {len(filtered_memories)} matching memories)\n\n"

            for i, memory in enumerate(display_memories, 1):
                # Format the memory content
                result += f"{i}. {memory.memory}\n"

                # Add topics if available
                if hasattr(memory, "topics") and memory.topics:
                    result += f"   Topics: {', '.join(memory.topics)}\n"

                # Add timestamp if available
                if hasattr(memory, "timestamp") and memory.timestamp:
                    # Convert timestamp to readable format
                    from datetime import datetime

                    timestamp = datetime.fromtimestamp(memory.timestamp)
                    result += f"   Created: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"

                # Add memory ID for reference
                result += f"   ID: {memory.memory_id}\n\n"

            logger.info(
                "Retrieved %d memories for topics %s", len(display_memories), topics_str
            )
            return result

        except Exception as e:
            logger.error("Error retrieving memories by topic: %s", e)
            return f"❌ Error retrieving memories by topic: {str(e)}"

    async def list_memories(self) -> str:
        """List all memories in a simple, user-friendly format.

        This method provides a more concise view of all memories compared to get_all_memories,
        focusing on just the content and topics without additional metadata.

        Returns:
            str: Simplified list of all memories
        """
        try:
            # Direct call to SemanticMemoryManager.get_all_memories()
            memories = self.agno_memory.memory_manager.get_all_memories(
                db=self.agno_memory.db, user_id=self.user_id
            )

            if not memories:
                logger.info("No memories found for user %s", self.user_id)
                return "🔍 No memories found. Try storing some information first!"

            # Sort memories by timestamp (newest first)
            sorted_memories = sorted(
                memories,
                key=lambda m: m.timestamp if hasattr(m, "timestamp") else 0,
                reverse=True,
            )

            # Format results in a simplified way
            result = f"📝 MEMORY LIST ({len(memories)} total):\n\n"

            for i, memory in enumerate(sorted_memories, 1):
                # Just show the memory content and topics, omit other metadata
                memory_preview = (
                    memory.memory[:100] + "..."
                    if len(memory.memory) > 100
                    else memory.memory
                )
                result += f"{i}. {memory_preview}\n"

                # Add topics if available
                if hasattr(memory, "topics") and memory.topics:
                    result += f"   Topics: {', '.join(memory.topics)}\n"

                result += "\n"

            logger.info(
                "Listed all %d memories for user %s in simplified format",
                len(memories),
                self.user_id,
            )
            return result

        except Exception as e:
            logger.error("Error listing memories: %s", e)
            return f"❌ Error listing memories: {str(e)}"

    async def store_graph_memory(
        self,
        content: str,
        topics: Union[List[str], str, None] = None,
        memory_id: str = None,
    ) -> str:
        """Store a memory in the LightRAG graph database to capture relationships.

        This method creates a text file with the memory content and uploads it to the LightRAG
        memory server, which then processes it to extract entities and relationships.

        Args:
            content: The memory content to store
            topics: Optional list of topics/categories for the memory
            memory_id: Optional memory ID to link with the SQLite memory

        Returns:
            str: Success or error message
        """
        try:
            if not self.lightrag_memory_url:
                logger.warning("LightRAG memory URL not configured")
                return "❌ Graph memory not configured. Memory not stored in graph database."

            # Validate content
            if not content or not content.strip():
                logger.warning("Empty content provided to store_graph_memory")
                return "❌ Error: Content cannot be empty."

            # Parse topics parameter
            topic_list = []
            if topics is not None:
                if isinstance(topics, str):
                    # Convert string to list, handle comma-separated values
                    if "," in topics:
                        topic_list = [t.strip() for t in topics.split(",") if t.strip()]
                    else:
                        topic_list = [topics.strip()] if topics.strip() else []
                elif isinstance(topics, list):
                    # Clean up list - remove empty entries
                    topic_list = [str(t).strip() for t in topics if str(t).strip()]
                else:
                    # Convert anything else to string and put in list
                    topic_str = str(topics).strip()
                    topic_list = (
                        [topic_str] if topic_str and topic_str != "None" else []
                    )

            # Create a unique filename for this memory
            timestamp = int(time.time())
            memory_hash = hashlib.md5(f"{content}_{timestamp}".encode()).hexdigest()[:8]

            # If memory_id is provided, use it in the filename for traceability
            if memory_id:
                filename = f"memory_{memory_id}_{memory_hash}.txt"
            else:
                filename = f"memory_{memory_hash}.txt"

            # Prepare the content with metadata
            file_content = content

            # Add topics as metadata if available
            if topic_list:
                file_content += f"\n\nTopics: {', '.join(topic_list)}"

            # Create a temporary file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".txt", delete=False
            ) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            try:
                # Upload the file using the /documents/upload endpoint
                url = f"{self.lightrag_memory_url}/documents/upload"

                async with aiohttp.ClientSession() as session:
                    with open(temp_file_path, "rb") as file:
                        # Create form data for file upload
                        data = aiohttp.FormData()
                        data.add_field(
                            "file", file, filename=filename, content_type="text/plain"
                        )

                        async with session.post(url, data=data, timeout=30) as resp:
                            if resp.status in [200, 201]:
                                logger.info(
                                    "Successfully stored memory in graph database: %s",
                                    filename,
                                )
                                return f"✅ Memory successfully stored in graph database: {content[:50]}..."
                            else:
                                error_detail = await resp.text()
                                logger.warning(
                                    f"Failed to store memory in graph: {error_detail}"
                                )
                                return (
                                    f"❌ Error storing memory in graph: {error_detail}"
                                )

            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    pass  # Ignore cleanup errors

        except Exception as e:
            logger.error("Error storing memory in graph: %s", e)
            return f"❌ Error storing memory in graph: {str(e)}"

    async def query_graph_memory(
        self,
        query: str,
        mode: str = "mix",
        top_k: int = 5,
        response_type: str = "Multiple Paragraphs",
    ) -> dict:
        """Query the LightRAG memory graph to explore relationships between memories.

        This method sends a query to the LightRAG memory server to retrieve memories and their
        relationships based on the query. It supports different query modes and response formats.

        Args:
            query: The query to search for in the memory graph
            mode: Query mode - "semantic" (vector search), "graph" (graph traversal), or "mix" (combined)
            top_k: Maximum number of results to return
            response_type: Format of the response - "Multiple Paragraphs", "Single Paragraph", etc.

        Returns:
            dict: Query results with memories and their relationships
        """
        try:
            if not self.lightrag_memory_url:
                logger.warning("LightRAG memory URL not configured")
                return {
                    "error": "Graph memory not configured. Cannot query graph database."
                }

            # Validate query
            if not query or not query.strip():
                logger.warning("Empty query provided to query_graph_memory")
                return {"error": "Query cannot be empty. Please provide a search term."}

            # Validate mode
            valid_modes = ["semantic", "graph", "mix"]
            if mode not in valid_modes:
                logger.warning(f"Invalid mode '{mode}' provided to query_graph_memory")
                mode = "mix"  # Default to mix mode

            # Validate response_type
            valid_response_types = [
                "Multiple Paragraphs",
                "Single Paragraph",
                "Bullet Points",
                "JSON",
            ]
            if response_type not in valid_response_types:
                logger.warning(
                    f"Invalid response_type '{response_type}' provided to query_graph_memory"
                )
                response_type = "Multiple Paragraphs"  # Default to multiple paragraphs

            # Prepare the query parameters
            params = {
                "query": query.strip(),
                "mode": mode,
                "top_k": top_k,
                "response_type": response_type,
            }

            # Send the query to the LightRAG memory server
            url = f"{self.lightrag_memory_url}/graph/query"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=60) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        logger.info(
                            f"Successfully queried graph memory: {query[:50]}..."
                        )
                        return result
                    else:
                        error_detail = await resp.text()
                        logger.warning(f"Failed to query graph memory: {error_detail}")
                        return {
                            "error": f"Error querying graph memory: {error_detail}",
                            "query": query,
                            "mode": mode,
                        }

        except Exception as e:
            logger.error(f"Error querying graph memory: {e}")
            return {
                "error": f"Error querying graph memory: {str(e)}",
                "query": query,
                "mode": mode,
            }

    async def get_memory_graph_labels(self) -> str:
        """Get the list of all entity and relation labels from the memory graph.

        This method retrieves all entity and relation labels from the LightRAG memory graph,
        providing insights into the types of information stored in the graph.

        Returns:
            str: Formatted string with entity and relation labels
        """
        try:
            if not self.lightrag_memory_url:
                logger.warning("LightRAG memory URL not configured")
                return "❌ Graph memory not configured. Cannot retrieve graph labels."

            # Send the request to the LightRAG memory server
            url = f"{self.lightrag_memory_url}/graph/label/list"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=30) as resp:
                    if resp.status == 200:
                        data = await resp.json()

                        # Handle different response formats
                        entity_labels = []
                        relation_labels = []

                        # Format 1: Direct array of all labels
                        if isinstance(data, list):
                            all_labels = data
                            # We can't distinguish between entity and relation labels in this format
                            entity_labels = all_labels

                        # Format 2: Dict with 'labels' key containing all labels
                        elif isinstance(data, dict) and "labels" in data:
                            all_labels = data["labels"]
                            # We can't distinguish between entity and relation labels in this format
                            entity_labels = all_labels

                        # Format 3: Dict with separate 'entity_labels' and 'relation_labels' keys
                        elif isinstance(data, dict):
                            if "entity_labels" in data:
                                entity_labels = data["entity_labels"]
                            if "relation_labels" in data:
                                relation_labels = data["relation_labels"]

                        # Format the result
                        result = "🏷️ MEMORY GRAPH LABELS\n\n"

                        if entity_labels:
                            result += "Entity Types:\n"
                            for label in sorted(entity_labels):
                                result += f"- {label}\n"
                            result += "\n"

                        if relation_labels:
                            result += "Relation Types:\n"
                            for label in sorted(relation_labels):
                                result += f"- {label}\n"

                        if not entity_labels and not relation_labels:
                            result += "No labels found in the memory graph. Try storing some memories first!"

                        logger.info("Retrieved memory graph labels successfully")
                        return result
                    else:
                        error_detail = await resp.text()
                        logger.warning(
                            f"Failed to retrieve graph labels: {error_detail}"
                        )
                        return f"❌ Error retrieving graph labels: {error_detail}"

        except Exception as e:
            logger.error(f"Error retrieving memory graph labels: {e}")
            return f"❌ Error retrieving memory graph labels: {str(e)}"
