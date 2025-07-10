"""
Agno-based agent implementation for the Personal AI Agent.

This module provides an agno framework integration that maintains compatibility
with the existing MCP infrastructure while leveraging agno's enhanced capabilities
including native MCP support, async operations, and advanced agent features.
"""

import asyncio
import importlib.metadata
import os
import re
from enum import Enum, auto
from textwrap import dedent
from typing import Any, Dict, List, Optional, Union

# pylint: disable=C0413, C0415, C0301
import aiohttp

# Set logging levels for better telemetry
if "RUST_LOG" not in os.environ:
    # Enable more verbose Rust logging for debugging
    os.environ["RUST_LOG"] = "debug"

# Enable Ollama debug logging
if "OLLAMA_DEBUG" not in os.environ:
    os.environ["OLLAMA_DEBUG"] = "1"

from agno.agent import Agent
from agno.knowledge.combined import CombinedKnowledgeBase
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.knowledge import KnowledgeTools
from agno.tools.mcp import MCPTools
from agno.tools.python import PythonTools
from agno.tools.shell import ShellTools
from agno.tools.yfinance import YFinanceTools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from rich.console import Console
from rich.table import Table

from ..config import get_mcp_servers
from ..config.model_contexts import get_model_context_size_sync
from ..config.settings import (
    AGNO_KNOWLEDGE_DIR,
    AGNO_STORAGE_DIR,
    DATA_DIR,
    LIGHTRAG_MEMORY_URL,
    LIGHTRAG_URL,
    LLM_MODEL,
    LOG_LEVEL,
    OLLAMA_URL,
    SHOW_SPLASH_SCREEN,
    STORAGE_BACKEND,
    USE_MCP,
    USER_ID,
)
from ..tools.personal_agent_tools import PersonalAgentFilesystemTools
from ..utils import setup_logging
from ..utils.splash_screen import display_splash_screen
from .agno_storage import (
    create_agno_memory,
    create_agno_storage,
    create_combined_knowledge_base,
    load_combined_knowledge_base,
    load_lightrag_knowledge_base,
)
from .knowledge_coordinator import create_knowledge_coordinator

# Configure logging
logger = setup_logging(__name__, level=LOG_LEVEL)


class InstructionLevel(Enum):
    """Defines the sophistication level for agent instructions."""

    MINIMAL = auto()  # For highly capable models needing minimal guidance
    CONCISE = auto()  # For capable models, focuses on capabilities over rules
    STANDARD = auto()  # The current, highly-detailed instructions
    EXPLICIT = auto()  # Even more verbose, for models that need extra guidance


class AgnoPersonalAgent:
    """
    Agno-based Personal AI Agent with MCP integration and native storage.

    This class provides a modern async agent implementation using the agno framework
    with built-in SQLite storage and LanceDB knowledge base.
    """

    def __init__(
        self,
        model_provider: str = "ollama",
        model_name: str = LLM_MODEL,
        enable_memory: bool = True,
        enable_mcp: bool = True,
        storage_dir: str = AGNO_STORAGE_DIR,
        knowledge_dir: str = AGNO_KNOWLEDGE_DIR,
        debug: bool = False,
        ollama_base_url: str = OLLAMA_URL,
        user_id: str = USER_ID,
        recreate: bool = False,
        instruction_level: InstructionLevel = InstructionLevel.STANDARD,
        seed: int = None,
    ) -> None:
        """Initialize the Agno Personal Agent.

        :param model_provider: LLM provider ('ollama' or 'openai')
        :param model_name: Model name to use
        :param enable_memory: Whether to enable memory and knowledge features
        :param enable_mcp: Whether to enable MCP tool integration
        :param storage_dir: Directory for Agno storage files
        :param knowledge_dir: Directory containing knowledge files to load
        :param debug: Enable debug logging and tool call visibility
        :param ollama_base_url: Base URL for Ollama API
        :param user_id: User identifier for memory operations
        :param instruction_level: The sophistication level for agent instructions
        """
        self.model_provider = model_provider
        self.model_name = model_name
        self.enable_memory = enable_memory
        self.enable_mcp = enable_mcp and USE_MCP

        # If user_id differs from default, create user-specific paths
        if user_id != USER_ID:
            # Replace the default user ID in the paths with the custom user ID
            self.storage_dir = os.path.expandvars(
                f"{DATA_DIR}/{STORAGE_BACKEND}/{user_id}"
            )
            self.knowledge_dir = os.path.expandvars(
                f"{DATA_DIR}/{STORAGE_BACKEND}/{user_id}/knowledge"
            )
        else:
            self.storage_dir = storage_dir
            self.knowledge_dir = knowledge_dir

        self.debug = debug
        self.ollama_base_url = ollama_base_url
        self.user_id = user_id
        self.recreate = recreate
        self.instruction_level = instruction_level
        self.seed = seed

        # Agno native storage components
        self.agno_storage = None
        self.agno_knowledge = None
        self.lightrag_knowledge = None
        self.lightrag_knowledge_enabled = False
        self.agno_memory = None
        self.knowledge_coordinator = None

        # MCP configuration
        self.mcp_servers = get_mcp_servers() if self.enable_mcp else {}

        # Agent instance
        self.agent = None

        logger.info(
            "Initialized AgnoPersonalAgent with model=%s, memory=%s, mcp=%s, user_id=%s",
            f"{model_provider}:{model_name}",
            self.enable_memory,
            self.enable_mcp,
            self.user_id,
        )

    def _create_model(self) -> Union[OpenAIChat, Ollama]:
        """Create the appropriate model instance based on provider.

        :return: Configured model instance
        :raises ValueError: If unsupported model provider is specified
        """
        if self.model_provider == "openai":
            return OpenAIChat(id=self.model_name)
        elif self.model_provider == "ollama":
            # Get dynamic context size for this model
            context_size, detection_method = get_model_context_size_sync(
                self.model_name, self.ollama_base_url
            )

            logger.info(
                "Using context size %d for model %s (detected via: %s)",
                context_size,
                self.model_name,
                detection_method,
            )

            # Use Ollama-compatible interface with optimized configuration
            return Ollama(
                id=self.model_name,
                host=self.ollama_base_url,  # Use host parameter for Ollama
                options={
                    "num_ctx": context_size,  # Use dynamically detected context window
                    "temperature": 0.7,  # Optional: set temperature for consistency
                    "num_predict": -1,  # Allow unlimited prediction length
                    "top_k": 40,
                    "top_p": 0.9,
                    "repeat_penalty": 1.1,
                    "seed": self.seed,
                },
            )
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")

    def _direct_search_memories(
        self, query: str, limit: int = 10, similarity_threshold: float = 0.3
    ):
        """Direct semantic search without agentic retrieval."""
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

    async def _get_memory_tools(self) -> List:
        """Create memory tools using direct SemanticMemoryManager method calls.

        This method creates memory tools that directly call SemanticMemoryManager methods
        instead of using complex wrapper functions, making the code much simpler and more maintainable.
        """
        if not self.enable_memory or not self.agno_memory:
            logger.warning("Memory not enabled or memory not initialized")
            return []

        # Check if memory is available
        if not self.agno_memory:
            logger.error("Memory not initialized")
            return []

        tools = []

        async def store_user_memory_tool(
            content: str = "", topics: Union[List[str], str, None] = None
        ) -> str:
            """A tool that wraps the public store_user_memory method."""
            return await self.store_user_memory(content=content, topics=topics)

        async def query_knowledge_base(
            query: str,
            mode: str = "auto",
            limit: int = 5,
            response_type: str = "Multiple Paragraphs",
        ) -> str:
            """
            Unified knowledge base query with intelligent routing.

            This tool automatically routes queries between local semantic search and LightRAG
            based on the mode parameter and query characteristics.

            Args:
                query: The search query
                mode: Routing mode:
                      - "local": Force local semantic search
                      - "global", "hybrid", "mix", "naive", "bypass": Use LightRAG
                      - "auto": Intelligent auto-detection (default)
                limit: Maximum results for local search / top_k for LightRAG
                response_type: Format for LightRAG responses

            Returns:
                Formatted search results from the appropriate knowledge system
            """
            if not self.knowledge_coordinator:
                return "❌ Knowledge coordinator not available."

            try:
                result = await self.knowledge_coordinator.query_knowledge_base(
                    query=query, mode=mode, limit=limit, response_type=response_type
                )
                return result
            except Exception as e:
                logger.error("Error in unified knowledge query: %s", e)
                return f"❌ Error querying knowledge base: {str(e)}"

        async def query_lightrag_knowledge(
            query: str,
            mode: str = "naive",
            top_k: int = 5,
            response_type: str = "Multiple Paragraphs",
        ) -> dict:
            """
            DEPRECATED: Use query_knowledge_base instead.
            Direct query to LightRAG knowledge base for backward compatibility.

            :param query: The query string to search in the knowledge base.
            :param mode: Query mode (default: "hybrid"). Options: "local", "global", "hybrid", "naive", "mix", "bypass".
            :param top_k: The number of top items to retrieve.
            :param response_type: The desired format for the response.
            :return: Dictionary with query results.
            """
            url = f"{LIGHTRAG_URL}/query"
            payload = {
                "query": query,
                "mode": mode,
                "top_k": top_k,
                "response_type": response_type,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=120) as resp:
                    resp.raise_for_status()
                    return await resp.json()

        async def query_memory(query: str, limit: Union[int, None] = None) -> str:
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
                    return await get_all_memories()

                # Validate query parameter
                if not query or not query.strip():
                    logger.warning("Empty query provided to query_memory")
                    return (
                        "❌ Error: Query cannot be empty. Please provide a search term."
                    )

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

                logger.info(
                    "Found %d matching memories for query: %s", len(results), query
                )
                return result

            except Exception as e:
                logger.error("Error querying memories: %s", e)
                return f"❌ Error searching memories: {str(e)}"

        async def update_memory(
            memory_id: str, content: str, topics: Union[List[str], str, None] = None
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

        async def delete_memory(memory_id: str) -> str:
            """Delete a memory using direct SemanticMemoryManager calls.

            Args:
                memory_id: ID of the memory to delete

            Returns:
                str: Success or error message
            """
            try:
                # Direct call to SemanticMemoryManager.delete_memory()
                success, message = self.agno_memory.memory_manager.delete_memory(
                    memory_id=memory_id, db=self.agno_memory.db, user_id=self.user_id
                )

                if success:
                    logger.info("Deleted memory %s", memory_id)
                    return f"✅ Successfully deleted memory: {memory_id}"
                else:
                    logger.error("Failed to delete memory %s: %s", memory_id, message)
                    return f"❌ Error deleting memory: {message}"

            except Exception as e:
                logger.error("Error deleting memory: %s", e)
                return f"❌ Error deleting memory: {str(e)}"

        async def clear_memories() -> str:
            """Clear all memories for the user using direct SemanticMemoryManager calls.

            Returns:
                str: Success or error message
            """
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

        async def delete_memories_by_topic(topics: Union[List[str], str]) -> str:
            """Delete all memories associated with a specific topic or list of topics.

            Args:
                topics: A single topic or a list of topics to delete memories for.

            Returns:
                str: Success or error message.
            """
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

        async def get_recent_memories(limit: int = 10) -> str:
            """Get recent memories by searching all memories and sorting by date.

            Args:
                limit: Maximum number of recent memories to return

            Returns:
                str: Recent memories or message if none found
            """
            try:
                # Use search_memories with empty query to get all memories, then limit
                results = self.agno_memory.memory_manager.search_memories(
                    query="",  # Empty query to get all memories
                    db=self.agno_memory.db,
                    user_id=self.user_id,
                    limit=limit,
                    similarity_threshold=0.0,  # Very low threshold to get all
                    search_topics=False,
                )

                if not results:
                    return "📝 No memories found."

                # Format memories for display
                result = f"📝 Recent {len(results)} memories:\n\n"
                for i, (memory, _) in enumerate(results, 1):
                    result += f"{i}. {memory.memory}\n"
                    if memory.topics:
                        result += f"   Topics: {', '.join(memory.topics)}\n"
                    result += "\n"

                logger.info("Retrieved %d recent memories", len(results))
                return result

            except Exception as e:
                logger.error("Error getting recent memories: %s", e)
                return f"❌ Error getting recent memories: {str(e)}"

        async def get_all_memories() -> str:
            """Get all user memories using direct SemanticMemoryManager calls.

            Returns:
                str: All memories or message if none found
            """
            try:
                # Use search_memories with empty query and no limit to get all memories
                results = self.agno_memory.memory_manager.search_memories(
                    query="",  # Empty query to get all memories
                    db=self.agno_memory.db,
                    user_id=self.user_id,
                    limit=None,  # High limit to get all
                    similarity_threshold=0.0,  # Very low threshold to get all
                    search_topics=False,
                )

                if not results:
                    return "📝 No memories found."

                # Format memories for display
                result = f"📝 All {len(results)} memories:\n\n"
                for i, (memory, _) in enumerate(results, 1):
                    result += f"{i}. {memory.memory}\n"
                    if memory.topics:
                        result += f"   Topics: {', '.join(memory.topics)}\n"
                    result += "\n"

                logger.info("Retrieved %d total memories", len(results))
                return result

            except Exception as e:
                logger.error("Error getting all memories: %s", e)
                return f"❌ Error getting all memories: {str(e)}"

        async def get_memory_stats() -> str:
            """Get memory statistics using direct SemanticMemoryManager calls.

            Returns:
                str: Memory statistics
            """
            try:
                # Direct call to SemanticMemoryManager.get_memory_stats()
                stats = self.agno_memory.memory_manager.get_memory_stats(
                    db=self.agno_memory.db, user_id=self.user_id
                )

                if "error" in stats:
                    return f"❌ Error getting memory stats: {stats['error']}"

                # Format stats for display
                result = "📊 Memory Statistics:\n\n"
                result += f"Total memories: {stats.get('total_memories', 0)}\n"
                result += f"Average memory length: {stats.get('average_memory_length', 0):.1f} characters\n"
                result += (
                    f"Recent memories (24h): {stats.get('recent_memories_24h', 0)}\n"
                )

                if stats.get("most_common_topic"):
                    result += f"Most common topic: {stats['most_common_topic']}\n"

                if stats.get("topic_distribution"):
                    result += "\nTopic distribution:\n"
                    for topic, count in stats["topic_distribution"].items():
                        result += f"  - {topic}: {count}\n"

                logger.info("Retrieved memory statistics")
                return result

            except Exception as e:
                logger.error("Error getting memory stats: %s", e)
                return f"❌ Error getting memory stats: {str(e)}"

        async def search_memory(query: str, limit: Union[int, None] = None) -> str:
            """Search user memories - alias for query_memory for compatibility.

            Args:
                query: The query to search for in memories
                limit: Maximum number of memories to return

            Returns:
                str: Found memories or message if none found
            """
            # This is just an alias for query_memory to maintain compatibility
            return await query_memory(query, limit)

        async def get_memories_by_topic(
            topics: Union[List[str], str, None] = None,
            limit: Union[int, None] = None,
        ) -> str:
            """Get memories by topic without similarity search.

            Args:
                topics: A list of topics to filter by. If None, returns all memories.
                limit: Maximum number of memories to return.

            Returns:
                str: Found memories or a message if none are found.
            """
            try:
                # Ensure topics are in the correct list format
                if isinstance(topics, str):
                    topics = [t.strip() for t in topics.split(",")]

                results = self.agno_memory.memory_manager.get_memories_by_topic(
                    db=self.agno_memory.db,
                    user_id=self.user_id,
                    topics=topics,
                    limit=limit,
                )

                if not results:
                    topic_str = f" for topics {topics}" if topics else ""
                    return f"📝 No memories found{topic_str}."

                # Format memories for display
                result_str = f"📝 Found {len(results)} memories:\n\n"
                for i, memory in enumerate(results, 1):
                    result_str += f"{i}. {memory.memory}\n"
                    if memory.topics:
                        result_str += f"   Topics: {', '.join(memory.topics)}\n"
                    result_str += "\n"

                logger.info("Retrieved %d memories by topic", len(results))
                return result_str

            except Exception as e:
                logger.error("Error getting memories by topic: %s", e)
                return f"❌ Error getting memories by topic: {str(e)}"

        async def list_memories() -> str:
            """List all memories in a simple, user-friendly format."""
            try:
                results = self.agno_memory.memory_manager.get_memories_by_topic(
                    db=self.agno_memory.db,
                    user_id=self.user_id,
                    topics=None,
                    limit=None,
                )

                if not results:
                    return "You haven't told me anything about you yet. I'd love to learn more!"

                # Format memories into a simple list
                result_str = "🌟 Here's what I remember about you:\n"
                for i, memory in enumerate(results, 1):
                    result_str += f"- {memory.memory}\n"

                logger.info("Listed %d memories for the user", len(results))
                return result_str

            except Exception as e:
                logger.error("Error listing memories: %s", e)
                return f"❌ Error listing memories: {str(e)}"

        async def query_semantic_knowledge(query: str, limit: int = 5) -> str:
            """
            Search the local semantic knowledge base (SQLite/LanceDB) for specific facts or documents.

            Args:
                query: The query to search for in the semantic knowledge base.
                limit: The maximum number of results to return.

            Returns:
                A formatted string of search results or a message if no results are found.
            """
            if not self.agno_knowledge:
                return "Semantic knowledge base is not available."
            try:
                results = self.agno_knowledge.search(query=query, num_documents=limit)
                if not results:
                    return f"No results found in the semantic knowledge base for '{query}'."

                formatted_results = [
                    f"Result {i+1}: (ID: {r.id}, Source: {r.source})\n{r.content}"
                    for i, r in enumerate(results)
                ]
                return "\n\n".join(formatted_results)
            except Exception as e:
                logger.error(f"Error searching semantic knowledge base: {e}")
                return f"An error occurred while searching the semantic knowledge base: {e}"

        async def store_graph_memory(
            content: str, topics: Union[List[str], str, None] = None
        ) -> str:
            """
            Store a memory in the LightRAG graph database to capture relationships.
            Uses file upload approach to avoid null file_path issues and explicitly adds relationships.
            Includes improved coreference resolution for pronouns.

            :param content: The information to store as a memory.
            :param topics: Optional list of topics for the memory.
            :return: Success or error message.
            """
            if not content or not content.strip():
                return "❌ Error: Content is required to store a graph memory."
            try:
                import asyncio
                from personal_agent.core.nlp_extractor import extract_entities, extract_relationships
                import spacy

                # Improved Coreference Resolution
                nlp = spacy.load("en_core_web_sm")
                doc = nlp(content)
                resolved_sents = []
                last_person = None
                
                # First pass: collect all person entities
                all_persons = [ent.text for ent in doc.ents if ent.label_ == "PERSON"]
                
                for sent in doc.sents:
                    # Find person in the current sentence
                    current_persons = [ent.text for ent in sent.ents if ent.label_ == "PERSON"]
                    
                    sent_text = sent.text
                    
                    # Enhanced pronoun replacement
                    if not current_persons and last_person:
                        # Replace various pronouns with the last known person
                        sent_text = re.sub(r'\bhe\b', last_person, sent_text, flags=re.IGNORECASE)
                        sent_text = re.sub(r'\bshe\b', last_person, sent_text, flags=re.IGNORECASE)
                        sent_text = re.sub(r'\bhis\b', f"{last_person}'s", sent_text, flags=re.IGNORECASE)
                        sent_text = re.sub(r'\bher\b', f"{last_person}'s", sent_text, flags=re.IGNORECASE)
                        sent_text = re.sub(r'\bhim\b', last_person, sent_text, flags=re.IGNORECASE)
                        sent_text = re.sub(r'\bhers\b', f"{last_person}'s", sent_text, flags=re.IGNORECASE)

                    resolved_sents.append(sent_text)
                    
                    # Update last_person if a new person is mentioned
                    if current_persons:
                        last_person = current_persons[0]
                
                coref_resolved_content = " ".join(resolved_sents)
                logger.info("Coreference resolved content: '%s'", coref_resolved_content)

                # Restate the fact to be user-centric for the knowledge graph
                restated_content = self._restate_user_fact(coref_resolved_content)
                logger.info("Original content for graph: '%s'", content)
                logger.info("Restated content for graph: '%s'", restated_content)
                
                # --- Extract entities and relationships from the final content ---
                entities = extract_entities(restated_content)
                relationships = extract_relationships(restated_content)
                
                logger.info("Extracted entities: %s", entities)
                logger.info("Extracted relationships: %s", relationships)
                
                graph_edit_results = []
                
                # --- Create all entities first ---
                async with aiohttp.ClientSession() as session:
                    entity_creation_tasks = []
                    for entity in entities:
                        entity_name = entity.get("text")
                        entity_type = entity.get("label")
                        if entity_name and entity_type:
                            payload = {
                                "entity_name": entity_name,
                                "updated_data": {
                                    "type": entity_type,
                                    "description": f"Entity of type {entity_type}"
                                }
                            }
                            url = f"{LIGHTRAG_MEMORY_URL}/graph/entity/edit"
                            
                            async def post_entity(session, url, payload):
                                async with session.post(url, json=payload, timeout=10) as resp:
                                    if resp.status not in [200, 201]:
                                        error_detail = await resp.text()
                                        logger.warning(f"Failed to post entity {payload.get('entity_name')}: {error_detail}")
                                        # Do not raise exception, just log and continue
                                        return {"message": f"Failed: {error_detail}"}
                                    return await resp.json()

                            entity_creation_tasks.append(post_entity(session, url, payload))

                    if entity_creation_tasks:
                        try:
                            entity_results = await asyncio.gather(*entity_creation_tasks)
                            for res in entity_results:
                                graph_edit_results.append(f"Entity added/updated: {res.get('message', 'OK')}")
                        except Exception as e:
                            logger.error(f"Error during entity creation: {e}")
                            graph_edit_results.append(f"Error creating entities: {e}")

                    # --- Then, create all relationships ---
                    relationship_creation_tasks = []
                    for sub, rel, obj in relationships:
                        # More flexible entity validation - allow relationships even if entities aren't perfectly matched
                        entity_names = [e.get("text") for e in entities]
                        
                        # Check if subject and object are valid (not empty, not just pronouns)
                        if not sub or not obj or sub.strip() == "" or obj.strip() == "":
                            logger.warning(f"Skipping relationship {sub}-{rel}-{obj}: empty subject or object")
                            graph_edit_results.append(f"Relation skipped: {sub}-{rel}-{obj} (empty subject/object)")
                            continue
                        
                        # Skip relationships with unresolved pronouns
                        if sub.lower() in ['he', 'she', 'it', 'they', 'him', 'her', 'them']:
                            logger.warning(f"Skipping relationship {sub}-{rel}-{obj}: unresolved pronoun as subject")
                            graph_edit_results.append(f"Relation skipped: {sub}-{rel}-{obj} (unresolved pronoun)")
                            continue
                            
                        # Create entities for subject and object if they don't exist
                        for entity_text in [sub, obj]:
                            if entity_text not in entity_names:
                                # Add missing entity
                                entity_payload = {
                                    "entity_name": entity_text,
                                    "updated_data": {
                                        "type": "MISC",  # Default type for missing entities
                                        "description": f"Auto-created entity: {entity_text}"
                                    }
                                }
                                entity_url = f"{LIGHTRAG_MEMORY_URL}/graph/entity/edit"
                                
                                async def post_missing_entity(session, url, payload):
                                    async with session.post(url, json=payload, timeout=10) as resp:
                                        if resp.status not in [200, 201]:
                                            error_detail = await resp.text()
                                            logger.warning(f"Failed to create missing entity {payload.get('entity_name')}: {error_detail}")
                                            return {"message": f"Failed: {error_detail}"}
                                        return await resp.json()
                                
                                try:
                                    missing_entity_result = await post_missing_entity(session, entity_url, entity_payload)
                                    graph_edit_results.append(f"Missing entity created: {entity_text}")
                                    logger.info(f"Created missing entity: {entity_text}")
                                except Exception as e:
                                    logger.warning(f"Failed to create missing entity {entity_text}: {e}")
                        
                        payload = {
                            "source_id": sub,
                            "target_id": obj,
                            "updated_data": { "type": rel.upper().replace(" ", "_") }
                        }
                        url = f"{LIGHTRAG_MEMORY_URL}/graph/relation/edit"

                        async def post_relation(session, url, payload):
                            async with session.post(url, json=payload, timeout=10) as resp:
                                if resp.status not in [200, 201]:
                                    error_detail = await resp.text()
                                    logger.warning(f"Failed to post relation {payload.get('source_id')}-{payload.get('target_id')}: {error_detail}")
                                    # Do not raise exception, just log and continue
                                    return {"message": f"Failed: {error_detail}"}
                                return await resp.json()
                        
                        relationship_creation_tasks.append(post_relation(session, url, payload))

                    if relationship_creation_tasks:
                        try:
                            relation_results = await asyncio.gather(*relationship_creation_tasks)
                            for res in relation_results:
                                graph_edit_results.append(f"Relation added/updated: {res.get('message', 'OK')}")
                        except Exception as e:
                            logger.error(f"Error during relationship creation: {e}")
                            graph_edit_results.append(f"Error creating relationships: {e}")

                final_message = f"✅ Successfully stored graph memory: {restated_content[:50]}...\nGraph Edits: {'; '.join(graph_edit_results)}"
                logger.info(final_message)
                return final_message
            except Exception as e:
                logger.error("Error storing graph memory: %s", e, exc_info=True)
                return f"❌ Error storing graph memory: {str(e)}"

        async def query_graph_memory(
            query: str,
            mode: str = "mix",
            top_k: int = 5,
            response_type: str = "Multiple Paragraphs",
        ) -> dict:
            """
            Query the LightRAG memory graph to explore relationships between memories.

            :param query: The query to search for.
            :param mode: Query mode (default: "mix"). Options: "local", "global", "hybrid", "naive", "mix", "bypass".
            :param top_k: The number of top items to retrieve.
            :param response_type: The desired format for the response.
            :return: Dictionary with query results (consistent with query_lightrag_knowledge).
            """
            try:
                url = f"{LIGHTRAG_MEMORY_URL}/query"
                payload = {
                    "query": query,
                    "mode": mode,
                    "top_k": top_k,
                    "response_type": response_type,
                }
                async with aiohttp.ClientSession() as session:
                    async with session.post(url, json=payload, timeout=120) as resp:
                        resp.raise_for_status()
                        return await resp.json()
            except Exception as e:
                logger.error("Error querying graph memory: %s", e)
                return {"error": f"Error querying graph memory: {str(e)}"}

        async def get_memory_graph_labels() -> str:
            """
            Get the list of all entity and relation labels from the memory graph
            by calling the /graph/label/list endpoint.
            """
            try:
                url = f"{LIGHTRAG_MEMORY_URL}/graph/label/list"
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=60) as resp:
                        if resp.status != 200:
                            error_text = await resp.text()
                            logger.error(f"Error fetching graph labels from {url}: {resp.status} {error_text}")
                            resp.raise_for_status()
                        
                        labels_data = await resp.json()
                        
                        # Handle both response formats: direct array or dict with 'labels' key
                        if isinstance(labels_data, list):
                            # Direct array format: ["Eric", "Google", "Mountain View", ...]
                            all_labels = labels_data
                        elif isinstance(labels_data, dict) and "labels" in labels_data:
                            # Dict format: {"labels": ["Eric", "Google", ...]}
                            all_labels = labels_data["labels"]
                        else:
                            # Fallback: try to extract any list-like data
                            all_labels = []
                            logger.warning(f"Unexpected labels response format: {type(labels_data)}")
                        
                        return f"📊 Graph Labels: {sorted(all_labels)}"
            except Exception as e:
                logger.error("Error getting graph labels: %s", e)
                return f"❌ Error getting graph labels: {str(e)}"

        # Set proper function names for tool identification
        store_user_memory_tool.__name__ = "store_user_memory"
        query_memory.__name__ = "query_memory"
        search_memory.__name__ = "search_memory"
        update_memory.__name__ = "update_memory"
        delete_memory.__name__ = "delete_memory"
        delete_memories_by_topic.__name__ = "delete_memories_by_topic"
        clear_memories.__name__ = "clear_memories"
        get_recent_memories.__name__ = "get_recent_memories"
        get_all_memories.__name__ = "get_all_memories"
        get_memory_stats.__name__ = "get_memory_stats"
        get_memories_by_topic.__name__ = "get_memories_by_topic"
        list_memories.__name__ = "list_memories"
        query_knowledge_base.__name__ = "query_knowledge_base"
        query_lightrag_knowledge.__name__ = "query_lightrag_knowledge"
        query_semantic_knowledge.__name__ = "query_semantic_knowledge"
        store_graph_memory.__name__ = "store_graph_memory"
        query_graph_memory.__name__ = "query_graph_memory"
        get_memory_graph_labels.__name__ = "get_memory_graph_labels"

        # Add tools to the list
        tools.extend(
            [
                store_user_memory_tool,
                query_memory,
                update_memory,
                delete_memory,
                delete_memories_by_topic,
                clear_memories,
                get_recent_memories,
                get_all_memories,
                get_memory_stats,
                get_memories_by_topic,
                list_memories,
                query_knowledge_base,  # NEW: Unified knowledge coordinator tool
                query_lightrag_knowledge,  # DEPRECATED: Kept for backward compatibility
                query_semantic_knowledge,  # DEPRECATED: Kept for backward compatibility
                store_graph_memory,
                query_graph_memory,
                get_memory_graph_labels,
            ]
        )

        logger.info(
            "Created %d memory tools using direct SemanticMemoryManager calls",
            len(tools),
        )
        return tools

    async def _get_mcp_tools(self) -> List:
        """Create MCP tools as native async functions compatible with Agno.

        Returns:
            List of MCP tool functions
        """
        logger.info(
            "_get_mcp_tools called - enable_mcp: %s, mcp_servers: %s",
            self.enable_mcp,
            self.mcp_servers,
        )

        if not self.enable_mcp:
            logger.info("MCP disabled - enable_mcp is False")
            return []

        if not self.mcp_servers:
            logger.info(
                "No MCP servers configured - mcp_servers is empty: %s", self.mcp_servers
            )
            return []

        tools = []

        for server_name, config in self.mcp_servers.items():
            logger.info("Setting up MCP tool for server: %s", server_name)

            command = config.get("command", "npx")
            args = config.get("args", [])
            env = config.get("env", {})
            description = config.get(
                "description", f"Access to {server_name} MCP server"
            )

            # Create the actual tool function with closure
            def make_mcp_tool(
                name: str,
                cmd: str,
                tool_args: List[str],
                tool_env: Dict[str, str],
                desc: str,
            ) -> Any:
                """Create MCP tool function with proper closure."""

                async def mcp_tool(query: str) -> str:
                    """MCP tool function that creates session on-demand."""
                    try:
                        # Prepare environment - convert GITHUB_PERSONAL_ACCESS_TOKEN to GITHUB_TOKEN if needed
                        server_env = tool_env.copy() if tool_env else {}
                        if (
                            name == "github"
                            and "GITHUB_PERSONAL_ACCESS_TOKEN" in server_env
                        ):
                            # The GitHub MCP server expects GITHUB_TOKEN
                            server_env["GITHUB_TOKEN"] = server_env[
                                "GITHUB_PERSONAL_ACCESS_TOKEN"
                            ]
                            logger.info(
                                "Converted GITHUB_PERSONAL_ACCESS_TOKEN to GITHUB_TOKEN for GitHub MCP server"
                            )

                        server_params = StdioServerParameters(
                            command=cmd,
                            args=tool_args,
                            env=server_env,
                        )

                        # Create client session using async context manager
                        async with stdio_client(server_params) as (read, write):
                            async with ClientSession(read, write) as session:
                                # Initialize MCP toolkit with session
                                mcp_tools = MCPTools(session=session)
                                await mcp_tools.initialize()

                                # Create specialized instructions based on server type
                                if name == "github":
                                    instructions = dedent(
                                        """\
                                        You are a GitHub assistant. Help users explore repositories and their activity.
                                        - Provide organized, concise insights about the repository
                                        - Focus on facts and data from the GitHub API
                                        - Use markdown formatting for better readability
                                        - Present numerical data in tables when appropriate
                                        - Include links to relevant GitHub pages when helpful
                                    """
                                    )
                                elif name.startswith("filesystem"):
                                    instructions = f"You are a filesystem assistant for {name}. Help with file and directory operations."
                                elif name == "brave-search":
                                    instructions = "You are a web search assistant. Help users find information on the web."
                                elif name == "puppeteer":
                                    instructions = "You are a browser automation assistant. Help with web scraping and automation tasks."
                                else:
                                    instructions = f"You are an assistant using {name} MCP server. Help with the user's request."

                                # Create a temporary agent for this MCP server
                                temp_agent = Agent(
                                    model=self._create_model(),
                                    tools=[mcp_tools],
                                    instructions=instructions,
                                    markdown=True,
                                    show_tool_calls=self.debug,
                                )

                                # Run the query
                                response = await temp_agent.arun(query)
                                return response.content

                    except Exception as e:
                        logger.error("Error running %s MCP server: %s", name, e)
                        return f"Error using {name}: {str(e)}"

                # Set function metadata
                mcp_tool.__name__ = f"use_{name.replace('-', '_')}_server"
                mcp_tool.__doc__ = f"""Use {name} MCP server for: {desc}

Args:
    query: The query or task to execute using {name}

Returns:
    str: Result from the MCP server
"""

                return mcp_tool

            tool_func = make_mcp_tool(server_name, command, args, env, description)
            tools.append(tool_func)
            logger.info("Created MCP tool function for: %s", server_name)

        return tools

    def _create_agent_instructions(self) -> str:
        """Create instructions for the agent based on the sophistication level."""
        level = self.instruction_level

        # Common parts for most levels
        header = self._get_header_instructions()
        identity = self._get_identity_rules()
        personality = self._get_personality_and_tone()
        tool_list = self._get_tool_list()
        principles = self._get_core_principles()
        parts = []

        if level == InstructionLevel.MINIMAL:
            # Minimal just has a basic prompt and the tool list
            parts = [
                header,
                "You are a helpful AI assistant. Use your tools to answer the user's request.",
                tool_list,
            ]

        elif level == InstructionLevel.CONCISE:
            # Concise adds identity, personality, concise rules, and principles
            parts = [
                header,
                identity,
                personality,
                self._get_concise_memory_rules(),
                self._get_concise_tool_rules(),
                tool_list,
                principles,
            ]

        elif level == InstructionLevel.STANDARD:
            # Standard uses the more detailed rules instead of the concise ones
            parts = [
                header,
                identity,
                personality,
                self._get_detailed_memory_rules(),
                self._get_detailed_tool_rules(),
                tool_list,
                principles,
            ]

        elif level == InstructionLevel.EXPLICIT:
            # Explicit is like Standard but adds the anti-hesitation rules
            parts = [
                header,
                identity,
                personality,
                self._get_detailed_memory_rules(),
                self._get_detailed_tool_rules(),
                self._get_anti_hesitation_rules(),  # The extra part
                tool_list,
                principles,
            ]

        return "\n\n".join(dedent(p) for p in parts)

    def _get_header_instructions(self) -> str:
        """Returns the header section of the instructions."""
        mcp_status = "enabled" if self.enable_mcp else "disabled"
        memory_status = (
            "enabled with SemanticMemoryManager" if self.enable_memory else "disabled"
        )
        return f"""
            You are a personal AI friend with comprehensive capabilities and built-in semantic memory. Your purpose is to chat with the user about things and make them feel good.

            ## CURRENT CONFIGURATION
            - **Memory System**: {memory_status}
            - **MCP Servers**: {mcp_status}
            - **User ID**: {self.user_id}
            - **Debug Mode**: {self.debug}
        """

    def _get_identity_rules(self) -> str:
        """Returns the critical identity rules for the agent."""
        return f"""
            ## CRITICAL IDENTITY RULES - ABSOLUTELY MANDATORY
            **YOU ARE AN AI ASSISTANT who is a MEMORY EXPERT**: You are NOT the user. You are a friendly AI that helps and remembers things about the user.

            **GREET THE USER BY NAME**: When the user greets you, greet them back by their name, which is '{self.user_id}'. For example, if they say 'hello', you should say 'Hello {self.user_id}!'

            **NEVER PRETEND TO BE THE USER**:
            - You are NOT the user, you are an AI assistant that knows information ABOUT the user
            - NEVER say "I'm {self.user_id}" or introduce yourself as the user - this is COMPLETELY WRONG
            - NEVER use first person when talking about user information
            - You are an AI assistant that has stored semantic memories about the user

            **FRIENDLY INTRODUCTION**: When meeting someone new, introduce yourself as their personal AI friend and ask about their hobbies, interests, and what they like to talk about. Be warm and conversational!
        """

    def _get_personality_and_tone(self) -> str:
        """Returns the personality and tone guidelines."""
        return """
            ## PERSONALITY & TONE
            - **Be Warm & Friendly**: You're a personal AI friend, not just a tool
            - **Be Conversational**: Chat naturally and show genuine interest
            - **Be Supportive**: Make the user feel good and supported
            - **Be Curious**: Ask follow-up questions about their interests
            - **Be Remembering**: Reference past conversations and show you care
            - **Be Encouraging**: Celebrate their achievements and interests
        """

    def _get_concise_memory_rules(self) -> str:
        """Returns concise rules for the semantic memory system."""
        return """
            ## SEMANTIC MEMORY
            - Use `store_user_memory` to save new information about the user.
            - Use `query_memory` to retrieve information about the user.
            - Use `get_all_memories` or `get_recent_memories` for broad queries.
            - Always check memory first when asked about the user.
        """

    def _get_detailed_memory_rules(self) -> str:
        """Returns detailed, prescriptive memory usage rules."""
        return """
            ## SEMANTIC MEMORY SYSTEM - CRITICAL & IMMEDIATE ACTION REQUIRED - YOUR MAIN ROLE!

            Your primary function is to remember information about the user. You must use your memory tools immediately and correctly.

            **SPECIAL COMMANDS**:
            - **`!`**: When the user starts with `!`, **IMMEDIATELY** call `store_user_memory` with the rest of the input.
            - **`?`**: When the user starts with `?`, **IMMEDIATELY** call `get_memories_by_topic`. If no topic is provided, call `get_all_memories`.

            **IMPERATIVE: ACTION OVER CONVERSATION**
            - **DO NOT** explain how to use tools. **DO NOT** provide code examples for tool usage.
            - When the user asks you to do something that requires a tool, **CALL THE TOOL IMMEDIATELY**.
            - Your response should be the result of the tool call, not a conversation about the tool.
            - **WRONG**: "You can use `store_user_memory` to save that."
            - **CORRECT**: (Tool call to `store_user_memory`)

            **MEMORY STORAGE - NO HESITATION RULE**:
            - When the user provides a new piece of information about themselves (e.g., "I work at...", "My pet's name is..."), or tells you to remember something, **IMMEDIATELY** call `store_user_memory(content="the fact to remember")`.
            - If the user wants to update a fact, find the existing memory with `query_memory` to get its ID, then call `update_memory(memory_id="...", content="...")`. If you cannot find an existing memory, use `store_user_memory`.

            **MEMORY RETRIEVAL - CRITICAL RULES**:
            1.  **For a complete list of ALL memories**: If the user asks "list everything you know", "what do you know about me", "summarize all memories", or any other broad question asking for everything, you **MUST** call `get_all_memories()`.
                - **WRONG**: `query_memory("all")` or `query_memory("everything")`. This will perform a semantic search for the word "all", which is incorrect.
                - **CORRECT**: `get_all_memories()`
            2.  **For SPECIFIC questions about the user**: Use `query_memory("specific keywords")`. For example, for "what is my favorite color?", use `query_memory("favorite color")`.

            **HOW TO RESPOND - CRITICAL IDENTITY RULES**:
            - You are an AI assistant, NOT the user.
            - When you retrieve a memory, present it in the second person.
            - CORRECT: "I remember you told me you enjoy hiking."
            - INCORRECT: "I enjoy hiking."
        """

    def _get_concise_tool_rules(self) -> str:
        """Returns concise rules for general tool usage."""
        return """
            ## TOOL USAGE
            - Use tools to answer questions about finance, news, and files.
            - `YFinanceTools`: For stock prices and financial data.
            - `GoogleSearchTools`: For web and news search.
            - `PersonalAgentFilesystemTools`: For file operations.
            - `PythonTools`: For calculations and code execution.
        """

    def _get_detailed_tool_rules(self) -> str:
        """Returns detailed, prescriptive tool usage rules."""
        return """
            **WEB SEARCH - IMMEDIATE ACTION**:
            - News requests → IMMEDIATELY use GoogleSearchTools
            - Current events → IMMEDIATELY use GoogleSearchTools
            - "what's happening with..." → IMMEDIATELY use GoogleSearchTools
            - "top headlines about..." → IMMEDIATELY use GoogleSearchTools
            - NO analysis paralysis, just SEARCH

            **FINANCE QUERIES - IMMEDIATE ACTION**:
            - Stock analysis requests → IMMEDIATELY use YFinanceTools
            - "analyze [STOCK]" → IMMEDIATELY call get_current_stock_price() and get_stock_info()
            - Financial data requests → IMMEDIATELY use finance tools
            - NO thinking, NO debate, just USE THE TOOLS

            **TOOL DECISION TREE - FOLLOW EXACTLY**:
            - Finance question? → YFinanceTools IMMEDIATELY (get_current_stock_price, get_stock_info, etc.)
            - News/current events? → GoogleSearchTools IMMEDIATELY
            - Code questions? → PythonTools IMMEDIATELY
            - File operations? → PersonalAgentFilesystemTools IMMEDIATELY
            - System commands? → ShellTools IMMEDIATELY
            - Personal info? → Memory tools IMMEDIATELY
            - General knowledge questions? → query_lightrag_knowledge IMMEDIATELY
            - Specific document/fact search? → query_semantic_knowledge IMMEDIATELY
            - MCP server tasks? → Use appropriate MCP server tool (use_github_server, use_filesystem_server, etc.)
        """

    def _get_anti_hesitation_rules(self) -> str:
        """Returns explicit rules to prevent hesitation and overthinking."""
        return """
            ## CRITICAL: NO OVERTHINKING RULE - ELIMINATE HESITATION

            **WHEN USER ASKS ABOUT MEMORIES - IMMEDIATE ACTION REQUIRED**:
            - DO NOT analyze whether you should check memories
            - DO NOT think about what tools to use
            - DO NOT hesitate or debate internally
            - IMMEDIATELY call get_recent_memories() or query_memory()
            - ACT FIRST, then respond based on what you find

            **BANNED BEHAVIORS - NEVER DO THESE**:
            - ❌ "Let me think about whether I should check memories..."
            - ❌ "I should probably use the memory tools but..."
            - ❌ "Maybe I should query memory or maybe I should..."
            - ❌ Any internal debate about memory tool usage
            - ❌ Overthinking simple memory queries
            - ❌ "Let me think about what tools to use..."
            - ❌ "I should probably use [tool] but..."
            - ❌ Fabricating data instead of using tools

            **REQUIRED IMMEDIATE RESPONSES**:
            - ✅ User asks "What do you remember?" → IMMEDIATELY call query_memory("personal information about {self.user_id}")
            - ✅ User asks about preferences → IMMEDIATELY call query_memory("preferences likes interests")
            - ✅ User asks for recent memories → IMMEDIATELY call get_recent_memories()
            - ✅ "Analyze NVDA" → IMMEDIATELY use YFinanceTools
            - ✅ "What's the news about..." → IMMEDIATELY use GoogleSearchTools
            - ✅ "top 5 headlines about..." → IMMEDIATELY use GoogleSearchTools
            - ✅ "Calculate..." → IMMEDIATELY use PythonTools
            - ✅ NO hesitation, just ACTION
        """

    def _get_tool_list(self) -> str:
        """Dynamically returns the list of available tools, including MCP servers."""
        # Start with the static list of built-in tools
        tool_parts = [
            "## CURRENT AVAILABLE TOOLS",
            "- **YFinanceTools**: Stock prices, financial analysis, market data.",
            "- **GoogleSearchTools**: Web search, news searches, current events.",
            "- **PythonTools**: Calculations, data analysis, code execution.",
            "- **ShellTools**: System operations and command execution.",
            "- **PersonalAgentFilesystemTools**: File reading, writing, and management.",
            "- **Local Memory Tools (SQLite)**:",
            "  - `store_user_memory`: Store a simple fact in your local semantic memory.",
            "  - `query_memory`: Quickly search your local semantic memory for a specific fact.",
            "  - `get_recent_memories`: Get recent memories from local storage.",
            "  - `get_all_memories`: Get all stored memories.",
            "  - `get_memories_by_topic`: Get memories filtered by topic, without similarity search.",
            "  - `list_memories`: List all memories in a simple, user-friendly format.",
            "  - `update_memory`: Update an existing memory.",
            "  - `delete_memory`: Delete a specific memory by its ID.",
            "  - `delete_memories_by_topic`: Delete all memories for a given topic.",
            "  - `clear_memories`: Clear all memories for the user from local storage.",
            "  - `get_memory_stats`: Get statistics for the local memory.",
            "- **Graph Memory Tools (LightRAG)**:",
            "  - `store_graph_memory`: Store a complex memory in your knowledge graph to capture relationships.",
            "  - `query_graph_memory`: Explore your knowledge graph to answer complex questions about relationships.",
            "  - `get_memory_graph_labels`: Get all entity and relation labels from the memory graph.",
            "- **Knowledge Base Tools**:",
            "  - `query_knowledge_base`: 🆕 UNIFIED knowledge coordinator with intelligent routing (mode=auto/local/global/hybrid/mix)",
            "  - `query_lightrag_knowledge`: DEPRECATED - Use query_knowledge_base instead",
            "  - `query_semantic_knowledge`: DEPRECATED - Use query_knowledge_base instead",
        ]

        # Dynamically add MCP tools if they are enabled and configured
        if self.enable_mcp and self.mcp_servers:
            tool_parts.append("- **MCP Server Tools**:")
            for server_name, config in self.mcp_servers.items():
                tool_name = f"use_{server_name.replace('-', '_')}_server"
                description = config.get(
                    "description", f"Access to {server_name} MCP server"
                )
                tool_parts.append(f"  - `{tool_name}`: {description}")
        else:
            tool_parts.append("- **MCP Server Tools**: Disabled")

        return "\n".join(tool_parts)

    def _get_core_principles(self) -> str:
        """Returns the core principles and conversation guidelines."""
        return """
            ## CORE PRINCIPLES
            1. **Friendship First**: You're their AI friend who happens to be very capable.
            2. **Remember Everything**: Use your semantic memory to build deeper relationships.
            3. **Be Genuinely Helpful**: Use your tools immediately to assist with real needs.
            4. **Stay Positive**: Focus on making them feel good.
            5. **Be Curious**: Ask about their life, interests, and goals.
            6. **Act Immediately**: When they ask for information, use tools RIGHT NOW.

            Remember: You're not just an assistant - you're a friendly AI companion with semantic memory who genuinely cares about the user and remembers your conversations together! Use your tools immediately when requested - no hesitation!
        """

    def _restate_user_fact(self, content: str) -> str:
        """
        Restate a user fact from first-person to third-person.

        This method converts statements like "I have a PhD" to "{user_id} has a PhD"
        to ensure correct entity mapping in the knowledge graph.

        :param content: The original fact from the user.
        :return: The restated fact.
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

    async def initialize(self, recreate: bool = False) -> bool:
        """Initialize the agno agent with all components.

        :param recreate: Whether to recreate the agent knowledge bases
        :return: True if initialization successful, False otherwise
        """
        logger.info(
            "🚀 AgnoPersonalAgent.initialize() called with recreate=%s", recreate
        )
        try:
            # Create model
            model = self._create_model()
            logger.info("Created model: %s", self.model_name)

            # Prepare tools list
            tools = [
                # Add GoogleSearch tools directly for web search functionality
                GoogleSearchTools(),
                YFinanceTools(
                    stock_price=True,
                    company_info=True,
                    stock_fundamentals=True,
                    key_financial_ratios=True,
                    analyst_recommendations=True,
                ),
                PythonTools(),
                ShellTools(
                    base_dir="."
                ),  # Match Streamlit configuration for consistency
                PersonalAgentFilesystemTools(),
                # Removed PersonalAgentWebTools as it was causing confusion with MCP references
            ]

            # Initialize Agno native storage and knowledge following the working example pattern
            if self.enable_memory:
                self.agno_storage = create_agno_storage(self.storage_dir)
                logger.info("Created Agno storage at: %s", self.storage_dir)

                # Create knowledge base (sync creation)
                self.agno_knowledge = create_combined_knowledge_base(
                    self.storage_dir, self.knowledge_dir, self.agno_storage
                )

                # Load knowledge base content (async loading) - matches working example
                if self.agno_knowledge:
                    await load_combined_knowledge_base(
                        self.agno_knowledge, recreate=recreate
                    )
                    logger.info("Loaded Agno combined knowledge base content")

                    # Add KnowledgeTools for automatic knowledge base search and reasoning
                    try:
                        knowledge_tools = KnowledgeTools(
                            knowledge=self.agno_knowledge,
                            think=True,  # Enable reasoning scratchpad
                            search=True,  # Enable knowledge search
                            analyze=True,  # Enable analysis capabilities
                            add_instructions=True,  # Use built-in instructions
                            add_few_shot=True,  # Add example interactions
                        )
                        # tools.append(knowledge_tools)
                        # logger.info(
                        #    "Added KnowledgeTools for automatic knowledge base search and reasoning"
                        # )
                    except Exception as e:
                        logger.warning("Failed to add KnowledgeTools: %s", e)

                    # Add Lightrag knowledge if enabled
                    if self.enable_memory:
                        try:
                            self.lightrag_knowledge = (
                                await load_lightrag_knowledge_base()
                            )
                            self.lightrag_knowledge_enabled = (
                                self.lightrag_knowledge is not None
                            )
                            logger.info("Loaded Lightrag knowledge base metadata")
                        except Exception as e:
                            logger.warning(
                                "Failed to load Lightrag knowledge base: %s", e
                            )
                            self.lightrag_knowledge = None
                            self.lightrag_knowledge_enabled = False

                # Create memory with SemanticMemoryManager (debug mode passed through)
                self.agno_memory = create_agno_memory(
                    self.storage_dir, debug_mode=self.debug
                )

                if self.agno_memory:
                    logger.info(
                        "Created Agno memory with SemanticMemoryManager at: %s",
                        self.storage_dir,
                    )
                else:
                    logger.error("Failed to create memory system")

                # Create Knowledge Coordinator
                self.knowledge_coordinator = create_knowledge_coordinator(
                    agno_knowledge=self.agno_knowledge,
                    lightrag_url=LIGHTRAG_URL,
                    debug=self.debug,
                )
                logger.info(
                    "Created Knowledge Coordinator for unified knowledge queries"
                )

                logger.info("Initialized Agno storage and knowledge backend")
            else:
                logger.info(
                    "Memory disabled, skipping storage and knowledge initialization"
                )

            # Add ReasoningTools for better reasoning capabilities
            # TEMPORARILY DISABLED to debug tool naming issue
            # try:
            #     from agno.tools.reasoning import ReasoningTools
            #    reasoning_tools = ReasoningTools(add_instructions=True)
            #     tools.append(reasoning_tools)
            #    logger.info("Added ReasoningTools for enhanced reasoning capabilities")
            # except ImportError:
            #    logger.warning(
            #        "ReasoningTools not available, continuing without reasoning capabilities"
            #    )

            # Get MCP tools as function wrappers (no pre-initialization)
            mcp_tool_functions = []
            if self.enable_mcp:
                mcp_tool_functions = await self._get_mcp_tools()
                tools.extend(mcp_tool_functions)
                logger.info("Added %d MCP tools to agent", len(mcp_tool_functions))

            # Manual memory tools are no longer needed.
            # The agent will use its native memory management capabilities.
            memory_tool_functions = []
            if self.enable_memory:
                memory_tool_functions = await self._get_memory_tools()
                tools.extend(memory_tool_functions)
                logger.info(
                    "Added %d memory tools to agent", len(memory_tool_functions)
                )

            # Create the agno agent with direct parameter passing for visibility
            self.agent = Agent(
                model=model,
                tools=tools,
                instructions=self._create_agent_instructions(),
                markdown=True,
                show_tool_calls=self.debug,
                name="Personal AI Agent",
                agent_id="personal_agent",
                user_id=self.user_id,
                enable_agentic_memory=True,  # Enable agno's native memory
                enable_user_memories=False,  # Enable agno's native memory
                add_history_to_messages=True,  # Add conversation history to context
                num_history_responses=3,
                knowledge=self.agno_knowledge if self.enable_memory else None,
                search_knowledge=(
                    True if self.enable_memory and self.agno_knowledge else False
                ),  # Enable automatic knowledge search
                storage=self.agno_storage if self.enable_memory else None,
                memory=None,  # Don't pass memory to avoid auto-storage conflicts
                # Enable telemetry and verbose logging
                debug_mode=self.debug,
                # Enable streaming for intermediate steps
                stream_intermediate_steps=True,  # Required for aprint_response to work correctly
            )

            if self.enable_memory and self.agno_knowledge:
                logger.info("Agent configured with knowledge base search")

            # Calculate tool counts for logging using already-created tool lists
            mcp_tool_count = len(mcp_tool_functions)
            memory_tool_count = len(memory_tool_functions)

            logger.info(
                "Successfully initialized agno agent with native storage: %d total tools (%d MCP, %d memory)",
                len(tools),
                mcp_tool_count,
                memory_tool_count,
            )

            # Display splash screen if enabled
            if SHOW_SPLASH_SCREEN:
                agent_info = self.get_agent_info()
                agent_version = importlib.metadata.version("personal-agent")
                display_splash_screen(agent_info, agent_version)

            return True

        except Exception as e:
            logger.error("Failed to initialize agno agent: %s", e)
            return False

    async def run(
        self, query: str, stream: bool = False, add_thought_callback=None
    ) -> Union[str, Dict[str, Any]]:
        """Run a query through the agno agent, allowing for native tool execution.

        :param query: User query to process
        :param stream: Whether to stream the response
        :param add_thought_callback: Optional callback for adding thoughts during processing
        :return: Agent's final string response
        """
        if not self.agent:
            raise RuntimeError("Agent not initialized. Call initialize() first.")

        try:
            if add_thought_callback:
                add_thought_callback("🚀 Executing agno agent...")

            # The agent will handle the full tool-use loop internally
            response = await self.agent.arun(query, user_id=self.user_id)
            self._last_response = response  # Store for tool call inspection

            if add_thought_callback:
                add_thought_callback("✅ Agent execution complete.")

            return response.content

        except Exception as e:
            logger.error("Error running agno agent: %s", e)
            if add_thought_callback:
                add_thought_callback(f"❌ Error: {str(e)}")
            return f"Error processing request: {str(e)}"

    def _extract_tool_call_info(self, tool_call) -> Optional[Dict[str, Any]]:
        """Extract tool call information from various tool call formats."""
        try:
            logger.info("--- Inspecting tool_call object ---")
            logger.info(f"Type: {type(tool_call)}")
            logger.info(f"Object: {tool_call}")
            logger.info(f"Attributes: {dir(tool_call)}")

            # Handle dict format (Ollama API format)
            if isinstance(tool_call, dict):
                if "function" in tool_call:
                    function_data = tool_call["function"]
                    func_name = function_data.get("name", "unknown")
                    func_args = function_data.get("arguments", {})

                    # Handle arguments as JSON string (Ollama format)
                    if isinstance(func_args, str):
                        try:
                            import json

                            func_args = json.loads(func_args)
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.warning(f"Failed to parse arguments JSON: {e}")
                            func_args = {"raw_arguments": func_args}

                    return {
                        "type": "function",
                        "function_name": func_name,
                        "function_args": func_args,
                        "reasoning": tool_call.get("reasoning", None),
                    }
                else:
                    # Direct dict format
                    func_args = tool_call.get("arguments", {})
                    if isinstance(func_args, str):
                        try:
                            import json

                            func_args = json.loads(func_args)
                        except (json.JSONDecodeError, ValueError) as e:
                            logger.warning(f"Failed to parse arguments JSON: {e}")
                            func_args = {"raw_arguments": func_args}

                    return {
                        "type": "function",
                        "function_name": tool_call.get("name", "unknown"),
                        "function_args": func_args,
                        "reasoning": tool_call.get("reasoning", None),
                    }

            # Handle object format (agno/other frameworks)
            elif hasattr(tool_call, "function"):
                function_obj = tool_call.function
                func_name = "unknown"
                if hasattr(function_obj, "name"):
                    func_name = function_obj.name
                elif hasattr(function_obj, "__name__"):
                    func_name = function_obj.__name__
                elif isinstance(function_obj, str):
                    func_name = function_obj

                func_args = getattr(function_obj, "arguments", {})
                if isinstance(func_args, str):
                    try:
                        import json

                        func_args = json.loads(func_args)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Failed to parse arguments JSON: {e}")
                        func_args = {"raw_arguments": func_args}

                return {
                    "type": "function",
                    "function_name": func_name,
                    "function_args": func_args,
                    "reasoning": getattr(tool_call, "reasoning", None),
                }

            # Handle direct name attribute
            elif hasattr(tool_call, "name"):
                func_args = getattr(tool_call, "arguments", {})
                if isinstance(func_args, str):
                    try:
                        import json

                        func_args = json.loads(func_args)
                    except (json.JSONDecodeError, ValueError) as e:
                        logger.warning(f"Failed to parse arguments JSON: {e}")
                        func_args = {"raw_arguments": func_args}

                return {
                    "type": "function",
                    "function_name": tool_call.name,
                    "function_args": func_args,
                    "reasoning": getattr(tool_call, "reasoning", None),
                }

        except Exception as e:
            logger.warning(f"Failed to extract tool call info: {e}")

        return None

    def get_last_tool_calls(self) -> Dict[str, Any]:
        """Get tool call information from the last response object with enhanced detection.

        :return: Dictionary with tool call details
        """
        if not hasattr(self, "_last_response") or not self._last_response:
            return {
                "tool_calls_count": 0,
                "tool_call_details": [],
                "has_tool_calls": False,
                "response_type": "AgnoNative",
                "metadata": {},
            }

        response = self._last_response
        tool_calls = []
        tool_calls_count = 0

        # Enhanced tool call detection with multiple fallback methods
        logger.debug(f"Analyzing response object: {type(response)}")
        logger.debug(f"Response attributes: {dir(response)}")

        # Method 1: Standard tool_calls attribute
        if hasattr(response, "tool_calls") and response.tool_calls:
            logger.debug(
                f"Found tool_calls attribute with {len(response.tool_calls)} calls"
            )
            tool_calls_count = len(response.tool_calls)
            for tool_call in response.tool_calls:
                tool_info = self._extract_tool_call_info(tool_call)
                if tool_info:
                    tool_calls.append(tool_info)

        # Method 2: Check messages for tool calls
        elif hasattr(response, "messages") and response.messages:
            logger.debug("Checking messages for tool calls")
            for message in response.messages:
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        tool_info = self._extract_tool_call_info(tool_call)
                        if tool_info:
                            tool_calls.append(tool_info)
                            tool_calls_count += 1

        # Method 3: Check run_response for tool usage
        elif hasattr(response, "run_response") and response.run_response:
            logger.debug("Checking run_response for tool calls")
            run_resp = response.run_response
            if hasattr(run_resp, "tool_calls") and run_resp.tool_calls:
                for tool_call in run_resp.tool_calls:
                    tool_info = self._extract_tool_call_info(tool_call)
                    if tool_info:
                        tool_calls.append(tool_call)
                        tool_calls_count += 1

        # Method 4: Check for tools used in response metadata
        elif hasattr(response, "metadata") and response.metadata:
            logger.debug("Checking metadata for tool usage")
            metadata = response.metadata
            if isinstance(metadata, dict) and "tools_used" in metadata:
                tools_used = metadata["tools_used"]
                if isinstance(tools_used, list):
                    tool_calls_count = len(tools_used)
                    for tool_name in tools_used:
                        tool_calls.append(
                            {
                                "type": "function",
                                "function_name": tool_name,
                                "function_args": {},
                                "reasoning": None,
                            }
                        )

        # Method 5: Check for any attribute containing "tool" in the name
        else:
            logger.debug("Checking for any tool-related attributes")
            for attr_name in dir(response):
                if "tool" in attr_name.lower() and not attr_name.startswith("_"):
                    attr_value = getattr(response, attr_name, None)
                    if attr_value:
                        logger.debug(
                            f"Found tool-related attribute: {attr_name} = {attr_value}"
                        )

        # Extract metadata if available
        metadata = {}
        if hasattr(response, "metadata"):
            metadata = response.metadata or {}

        # Get response type information
        response_type = "AgnoNative"
        if hasattr(response, "response_type"):
            response_type = response.response_type
        elif hasattr(response, "type"):
            response_type = response.type

        logger.info(f"Tool call detection complete: {tool_calls_count} calls found")

        return {
            "tool_calls_count": tool_calls_count,
            "tool_call_details": tool_calls,
            "has_tool_calls": tool_calls_count > 0,
            "response_type": response_type,
            "metadata": metadata,
        }

    async def store_user_memory(
        self, content: str = "", topics: Union[List[str], str, None] = None
    ) -> str:
        """Store information as a user memory in BOTH local SQLite and LightRAG graph systems.

        This is a public method that can be called directly.

        Args:
            content: The information to store as a memory
            topics: Optional list of topics/categories for the memory (None = auto-classify)

        Returns:
            str: Success or error message
        """
        # Validate that content is provided
        if not content or not content.strip():
            return "❌ Error: Content is required to store a memory. Please provide the information you want me to remember."
        try:
            import json

            # DON'T set topics to ["general"] here - let the memory manager handle auto-classification
            # if topics is None:
            #     topics = ["general"]

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

            # Don't set a default - let the memory manager handle auto-classification
            # if topics is None:
            #     topics = ["general"]

            # DUAL STORAGE: Store in BOTH local SQLite memory AND LightRAG graph memory
            results = []

            # 1. Store in local SQLite memory system
            (
                success,
                message,
                memory_id,
                generated_topics,
            ) = self.agno_memory.memory_manager.add_memory(
                memory_text=content,
                db=self.agno_memory.db,
                user_id=self.user_id,
                topics=topics,
            )

            if success:
                logger.info(
                    "Stored in local memory: %s... (ID: %s)",
                    content[:50],
                    memory_id,
                )
                results.append(f"✅ Local memory: {content[:50]}... (ID: {memory_id})")
            else:
                logger.info("Local memory rejected: %s", message)
                if "duplicate" in message.lower():
                    results.append(f"✅ Local memory: Already exists")
                else:
                    results.append(f"❌ Local memory error: {message}")

            # 2. Store in LightRAG graph memory system
            try:
                # Find the store_graph_memory tool/method to call it
                store_graph_memory_func = None
                if self.agent and hasattr(self.agent, "tools"):
                    for tool in self.agent.tools:
                        if getattr(tool, "__name__", "") == "store_graph_memory":
                            store_graph_memory_func = tool
                            break
                if store_graph_memory_func:
                    graph_result = await store_graph_memory_func(
                        content, generated_topics
                    )
                    logger.info("Graph memory result: %s", graph_result)
                    results.append(f"Graph memory: {graph_result}")
                else:
                    logger.error("Could not find store_graph_memory tool to call.")
                    results.append("❌ Graph memory error: Tool not found")
            except Exception as e:
                logger.error("Error storing in graph memory: %s", e)
                results.append(f"❌ Graph memory error: {str(e)}")

            # Return combined results
            return " | ".join(results)

        except Exception as e:
            logger.error("Error storing user memory: %s", e)
            return f"❌ Error storing memory: {str(e)}"

    async def cleanup(self) -> None:
        """Clean up resources.

        :return: None
        """
        try:
            # With the new on-demand pattern, MCP tools are created and cleaned up
            # automatically within their async context managers
            logger.info(
                "Agno agent cleanup completed - MCP tools auto-cleaned with context managers"
            )
        except Exception as e:
            logger.error("Error during agno agent cleanup: %s", e)

    async def query_lightrag_knowledge_direct(self, query: str, params: dict) -> str:
        """
        Directly query the LightRAG knowledge base and return the raw response.
        This method is intended for direct calls (e.g., from Streamlit) and is not an agent tool.

        :param query: The query string to search in the knowledge base.
        :param params: A dictionary of query parameters based on the QueryParam class.
        :return: String with query results exactly as LightRAG returns them.
        """
        try:
            url = f"{LIGHTRAG_URL}/query"
            # Start with the mandatory query parameter
            payload = {"query": query}
            # Add optional parameters from the params dict
            payload.update(params)

            logger.info(f"Querying LightRAG: {url} with payload: {payload}")

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, timeout=120) as resp:
                    logger.info(f"LightRAG response status: {resp.status}")

                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(
                            f"LightRAG server error {resp.status}: {error_text}"
                        )
                        return f"LightRAG server error {resp.status}: {error_text}"

                    result = await resp.json()
                    logger.info("LightRAG response received, returning raw content...")

                    # Extract response content - simple and direct, NO FILTERING
                    if isinstance(result, dict) and "response" in result:
                        response_content = result["response"]
                    elif isinstance(result, dict) and "content" in result:
                        response_content = result["content"]
                    elif isinstance(result, dict) and "answer" in result:
                        response_content = result["answer"]
                    else:
                        response_content = str(result)

                    # Return exactly as received - NO PROCESSING OR FILTERING
                    logger.info(
                        f"Returning raw LightRAG response: {len(response_content)} characters"
                    )
                    return response_content

        except aiohttp.ClientConnectorError as e:
            error_msg = f"Cannot connect to LightRAG server at {LIGHTRAG_URL}. Is the server running? Error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except asyncio.TimeoutError as e:
            error_msg = f"Timeout connecting to LightRAG server at {LIGHTRAG_URL}. Error: {str(e)}"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Error querying knowledge base: {str(e)}"
            logger.error(error_msg)
            return error_msg

    def get_agent_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the agent configuration and tools.

        :return: Dictionary containing detailed agent configuration and tool information
        """
        # Get basic tool info
        built_in_tools = []
        mcp_tools = []

        if self.agent and hasattr(self.agent, "tools"):
            for tool in self.agent.tools:
                tool_name = getattr(tool, "__name__", str(type(tool).__name__))
                tool_doc = getattr(tool, "__doc__", "No description available")

                # Clean up docstring for display
                if tool_doc:
                    tool_doc = tool_doc.strip().split("\n")[0]  # First line only

                if tool_name.startswith("use_") and "_server" in tool_name:
                    mcp_tools.append(
                        {
                            "name": tool_name,
                            "description": tool_doc,
                            "type": "MCP Server",
                        }
                    )
                else:
                    built_in_tools.append(
                        {
                            "name": tool_name,
                            "description": tool_doc,
                            "type": "Built-in Tool",
                        }
                    )

        # MCP server details
        mcp_server_details = {}
        if self.enable_mcp and self.mcp_servers:
            for server_name, config in self.mcp_servers.items():
                mcp_server_details[server_name] = {
                    "command": config.get("command", "N/A"),
                    "description": config.get(
                        "description", f"Access to {server_name} MCP server"
                    ),
                    "args_count": len(config.get("args", [])),
                    "env_vars": len(config.get("env", {})),
                }

        return {
            "framework": "agno",
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "memory_enabled": self.enable_memory,
            "knowledge_enabled": self.agno_knowledge is not None,
            "lightrag_knowledge_enabled": self.lightrag_knowledge_enabled,
            "mcp_enabled": self.enable_mcp,
            "debug_mode": self.debug,
            "user_id": self.user_id,
            "initialized": self.agent is not None,
            "storage_dir": self.storage_dir,
            "knowledge_dir": self.knowledge_dir,
            "lightrag_url": LIGHTRAG_URL,
            "lightrag_memory_url": LIGHTRAG_MEMORY_URL,
            "tool_counts": {
                "total": len(built_in_tools) + len(mcp_tools),
                "built_in": len(built_in_tools),
                "mcp": len(mcp_tools),
                "mcp_servers": len(self.mcp_servers) if self.enable_mcp else 0,
            },
            "built_in_tools": built_in_tools,
            "mcp_tools": mcp_tools,
            "mcp_servers": mcp_server_details,
        }

    def print_agent_info(self, console: Optional[Console] = None) -> None:
        """Pretty print comprehensive agent information using Rich.

        :param console: Optional Rich Console instance. If None, creates a new one.
        """
        if console is None:
            console = Console()

        info = self.get_agent_info()

        # Main agent info table
        main_table = Table(
            title="🤖 Personal AI Agent Configuration",
            show_header=True,
            header_style="bold magenta",
        )
        main_table.add_column("Setting", style="cyan", no_wrap=True)
        main_table.add_column("Value", style="green")

        main_table.add_row("Framework", info["framework"])
        main_table.add_row("Model Provider", info["model_provider"])
        main_table.add_row("Model Name", info["model_name"])
        main_table.add_row("Memory Enabled", "✅" if info["memory_enabled"] else "❌")
        main_table.add_row(
            "Knowledge Enabled", "✅" if info["knowledge_enabled"] else "❌"
        )
        main_table.add_row("MCP Enabled", "✅" if info["mcp_enabled"] else "❌")
        main_table.add_row("Debug Mode", "✅" if info["debug_mode"] else "❌")
        main_table.add_row("User ID", info["user_id"])
        main_table.add_row("Initialized", "✅" if info["initialized"] else "❌")
        main_table.add_row("Storage Directory", info["storage_dir"])
        main_table.add_row("Knowledge Directory", info["knowledge_dir"])
        main_table.add_row(
            "LightRAG Knowledge",
            "✅" if info["lightrag_knowledge_enabled"] else "❌",
        )
        main_table.add_row("LightRAG URL", info["lightrag_url"])
        main_table.add_row("LightRAG Memory URL", info["lightrag_memory_url"])

        console.print(main_table)
        console.print()

        # Tool counts table
        tool_table = Table(
            title="🔧 Tool Summary", show_header=True, header_style="bold blue"
        )
        tool_table.add_column("Tool Type", style="cyan")
        tool_table.add_column("Count", style="green", justify="right")

        counts = info["tool_counts"]
        tool_table.add_row("Total Tools", str(counts["total"]))
        tool_table.add_row("Built-in Tools", str(counts["built_in"]))
        tool_table.add_row("MCP Tools", str(counts["mcp"]))
        tool_table.add_row("MCP Servers", str(counts["mcp_servers"]))

        console.print(tool_table)
        console.print()

        # Built-in tools table
        if info["built_in_tools"]:
            builtin_table = Table(
                title="🛠️ Built-in Tools", show_header=True, header_style="bold yellow"
            )
            builtin_table.add_column("Tool Name", style="cyan")
            builtin_table.add_column("Description", style="white")

            for tool in info["built_in_tools"]:
                builtin_table.add_row(tool["name"], tool["description"])

            console.print(builtin_table)
            console.print()

        # MCP tools table
        if info["mcp_tools"]:
            mcp_table = Table(
                title="🌐 MCP Server Tools", show_header=True, header_style="bold red"
            )
            mcp_table.add_column("Tool Name", style="cyan")
            mcp_table.add_column("Description", style="white")

            for tool in info["mcp_tools"]:
                mcp_table.add_row(tool["name"], tool["description"])

            console.print(mcp_table)
            console.print()

        # MCP servers detail table
        if info["mcp_servers"]:
            server_table = Table(
                title="🖥️ MCP Server Details",
                show_header=True,
                header_style="bold purple",
            )
            server_table.add_column("Server Name", style="cyan")
            server_table.add_column("Command", style="yellow")
            server_table.add_column("Description", style="white")
            server_table.add_column("Args", style="green", justify="right")
            server_table.add_column("Env Vars", style="green", justify="right")

            for server_name, details in info["mcp_servers"].items():
                server_table.add_row(
                    server_name,
                    details["command"],
                    details["description"],
                    str(details["args_count"]),
                    str(details["env_vars"]),
                )

            console.print(server_table)

        console.print("\n🎉 Agent information displayed successfully!")

    def quick_agent_summary(self, console: Optional[Console] = None) -> None:
        """Print a quick one-line summary of the agent.

        :param console: Optional Rich Console instance. If None, creates a new one.
        """
        if console is None:
            console = Console()

        info = self.get_agent_info()
        counts = info["tool_counts"]

        status = "✅ Ready" if info["initialized"] else "❌ Not Initialized"
        memory_status = "🧠" if info["memory_enabled"] else "🚫"
        mcp_status = "🌐" if info["mcp_enabled"] else "🚫"

        summary = (
            f"[bold]{info['framework'].upper()}[/bold] Agent: {status} | "
            f"Model: [cyan]{info['model_provider']}:{info['model_name']}[/cyan] | "
            f"Tools: [green]{counts['total']}[/green] "
            f"([yellow]{counts['built_in']}[/yellow] built-in + [red]{counts['mcp']}[/red] MCP) | "
            f"Memory: {memory_status} | MCP: {mcp_status}"
        )

        console.print(summary)


async def create_agno_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    enable_memory: bool = True,
    enable_mcp: bool = True,
    storage_dir: str = "./data/agno",
    knowledge_dir: str = "./data/knowledge",
    debug: bool = True,
    ollama_base_url: str = OLLAMA_URL,
    user_id: str = "default_user",
    recreate: bool = False,
    instruction_level: InstructionLevel = InstructionLevel.STANDARD,
) -> AgnoPersonalAgent:
    """Create and initialize an agno-based personal agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param enable_memory: Whether to enable memory and knowledge features
    :param enable_mcp: Whether to enable MCP tool integration
    :param storage_dir: Directory for Agno storage files
    :param knowledge_dir: Directory containing knowledge files to load
    :param debug: Enable debug mode
    :param ollama_base_url: Base URL for Ollama API
    :param user_id: User identifier for memory operations
    :param instruction_level: The sophistication level for agent instructions
    :return: Initialized agent instance
    """
    agent = AgnoPersonalAgent(
        model_provider=model_provider,
        model_name=model_name,
        enable_memory=enable_memory,
        enable_mcp=enable_mcp,
        storage_dir=storage_dir,
        knowledge_dir=knowledge_dir,  # Pass the user-specific path
        debug=debug,
        ollama_base_url=ollama_base_url,
        user_id=user_id,
        recreate=recreate,
        instruction_level=instruction_level,
    )

    success = await agent.initialize(recreate=recreate)
    if not success:
        raise RuntimeError("Failed to initialize agno agent")

    return agent


# Synchronous wrapper for compatibility
def create_agno_agent_sync(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    enable_memory: bool = True,
    enable_mcp: bool = True,
    storage_dir: str = "./data/agno",
    knowledge_dir: str = "./data/knowledge",
    debug: bool = False,
    ollama_base_url: str = OLLAMA_URL,
    user_id: str = "default_user",
    instruction_level: InstructionLevel = InstructionLevel.EXPLICIT,
) -> AgnoPersonalAgent:
    """
    Synchronous wrapper for creating agno agent.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param enable_memory: Whether to enable memory and knowledge features
    :param enable_mcp: Whether to enable MCP tool integration
    :param storage_dir: Directory for Agno storage files
    :param knowledge_dir: Directory containing knowledge files to load
    :param debug: Enable debug mode
    :param user_id: User identifier for memory operations
    :param instruction_level: The sophistication level for agent instructions
    :return: Initialized agent instance
    """
    return asyncio.run(
        create_agno_agent(
            model_provider=model_provider,
            model_name=model_name,
            enable_memory=enable_memory,
            enable_mcp=enable_mcp,
            storage_dir=storage_dir,
            knowledge_dir=knowledge_dir,
            debug=debug,
            ollama_base_url=ollama_base_url,
            user_id=user_id,
            instruction_level=instruction_level,
        )
    )


def create_simple_personal_agent(
    storage_dir: str = None,
    knowledge_dir: str = None,
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
) -> tuple[Agent, Optional[CombinedKnowledgeBase]]:
    """Create a simple personal agent following the working pattern from knowledge_agent_example.py

    This function creates an agent with knowledge base integration using the simple
    pattern that avoids async initialization complexity.

    :param storage_dir: Directory for storage files (defaults to DATA_DIR/agno)
    :param knowledge_dir: Directory containing knowledge files (defaults to DATA_DIR/knowledge)
    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :return: Tuple of (Agent instance, knowledge_base) or (Agent, None) if no knowledge
    """
    # Create knowledge base (synchronous creation)
    knowledge_base = create_combined_knowledge_base(storage_dir, knowledge_dir)

    # Create the model
    if model_provider == "openai":
        model = OpenAIChat(id=model_name)
    elif model_provider == "ollama":
        model = Ollama(
            id=model_name,
        )
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")

    # Create agent with simple pattern
    agent = Agent(
        name="Personal AI Agent",
        model=model,
        knowledge=knowledge_base,
        search_knowledge=True,  # Enable automatic knowledge search
        show_tool_calls=True,  # Show what tools the agent uses
        markdown=True,  # Format responses in markdown
        instructions=[
            "You are a personal AI assistant with access to the user's knowledge base.",
            "Always search your knowledge base when asked about personal information.",
            "Provide detailed responses based on the information you find.",
            "If you can't find specific information, say so clearly.",
            "Include relevant details from the knowledge base in your responses.",
        ],
    )

    logger.info("✅ Created simple personal agent")
    if knowledge_base:
        logger.info("   Knowledge base: Enabled")
        logger.info("   Search enabled: %s", agent.search_knowledge)
    else:
        logger.info("   Knowledge base: None (no knowledge files found)")

    return agent, knowledge_base


async def load_agent_knowledge(
    knowledge_base: CombinedKnowledgeBase, recreate: bool = False
) -> None:
    """Load knowledge base content asynchronously.

    This should be called after creating the agent to load the knowledge content.

    :param knowledge_base: Knowledge base instance to load
    :param recreate: Whether to recreate the knowledge base from scratch
    :return: None
    """
    if knowledge_base:
        await load_combined_knowledge_base(knowledge_base, recreate=recreate)
        logger.info("✅ Knowledge base loaded successfully")
    else:
        logger.info("No knowledge base to load")
