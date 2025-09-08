"""
Streamlit Helper Classes for Agent Memory and Knowledge Management

This module provides helper classes that bridge agent-based memory and knowledge systems
with Streamlit user interfaces. It enables seamless integration of complex agent operations
within Streamlit applications by handling async operations, error management, and UI feedback.

Classes:
    StreamlitMemoryHelper: Manages memory operations including search, storage, updates,
                          deletion, and synchronization with graph-based memory systems.
    StreamlitKnowledgeHelper: Manages knowledge operations including document search
                             and RAG (Retrieval-Augmented Generation) queries.

Key Features:
    - Dynamic property access to agent components with lazy initialization
    - Async operation handling within Streamlit's synchronous context
    - Comprehensive error handling with user-friendly Streamlit error messages
    - Memory-graph synchronization capabilities
    - Support for both semantic memory and knowledge base operations

Usage:
    # Memory operations
    memory_helper = StreamlitMemoryHelper(agent)
    memories = memory_helper.search_memories("query", limit=10)
    success, msg, id, topics = memory_helper.add_memory("content", ["topic1"])

    # Knowledge operations
    knowledge_helper = StreamlitKnowledgeHelper(agent)
    results = knowledge_helper.search_knowledge("query", limit=5)
    rag_result = knowledge_helper.search_rag("query", params={})

Dependencies:
    - asyncio: For handling async agent operations
    - streamlit: For UI integration and error display
    - Agent system with memory and knowledge management capabilities

Note:
    These helpers are designed to work with agents that have agno_memory and
    agno_knowledge components, providing a consistent interface for Streamlit
    applications to interact with complex agent architectures.

Author:
    Eric G. Suchanek, PhD.
    Last Revision: 2025-08-19 15:22:58
"""

import asyncio
import logging

import streamlit as st

# Import MemoryStorageResult for type checking
try:
    from personal_agent.core.semantic_memory_manager import MemoryStorageResult
except ImportError:
    # Fallback if import fails
    MemoryStorageResult = None

# Set up logger
logger = logging.getLogger(__name__)


class StreamlitMemoryHelper:
    """Simplified StreamlitMemoryHelper using the new agent memory function interfaces."""

    def __init__(self, agent):
        self.agent = agent

    def _ensure_agent_available(self):
        """Ensure agent is available and has basic memory access."""
        if not self.agent:
            return False, "Agent not available"

        # Check for basic memory access - either through direct functions or memory system
        has_memory_access = (
            # Direct memory functions (single agent)
            hasattr(self.agent, "store_user_memory")
            or
            # Memory system access (both single agent and team wrapper)
            (hasattr(self.agent, "agno_memory") and self.agent.agno_memory)
            or (hasattr(self.agent, "memory_manager") and self.agent.memory_manager)
        )

        if not has_memory_access:
            return False, "Agent has no memory access"

        return True, "Agent ready"

    def search_memories(
        self, query: str, limit: int = 10, similarity_threshold: float = 0.3
    ):
        """Search memories using the agent's query_memory function."""
        available, message = self._ensure_agent_available()
        if not available:
            st.error(f"Memory search not available: {message}")
            return []

        try:
            # For UI compatibility, we need to return memory objects, not formatted strings
            # Access the memory manager directly through the agent's initialized components

            # Ensure agent is initialized first
            if hasattr(self.agent, "_ensure_initialized"):
                self._run_async(self.agent._ensure_initialized())

            # Access the memory manager directly for raw memory objects
            if (
                hasattr(self.agent, "memory_manager")
                and self.agent.memory_manager
                and hasattr(self.agent.memory_manager, "agno_memory")
                and self.agent.memory_manager.agno_memory
            ):

                # Use the SemanticMemoryManager's search method directly
                raw_memories = self.agent.memory_manager.agno_memory.memory_manager.search_memories(
                    query=query,
                    db=self.agent.memory_manager.agno_memory.db,
                    user_id=self.agent.user_id,
                    limit=limit,
                    similarity_threshold=similarity_threshold,
                )
                return raw_memories

            # Fallback: try to access through different paths for team wrappers
            elif hasattr(self.agent, "agno_memory") and self.agent.agno_memory:
                raw_memories = self.agent.agno_memory.memory_manager.search_memories(
                    query=query,
                    db=self.agent.agno_memory.db,
                    user_id=self.agent.user_id,
                    limit=limit,
                    similarity_threshold=similarity_threshold,
                )
                return raw_memories

            return []

        except Exception as e:
            st.error(f"Error searching memories: {e}")
            return []

    def get_all_memories(self):
        """Get all memories using the agent's memory system."""
        available, message = self._ensure_agent_available()
        if not available:
            st.error(f"Get all memories not available: {message}")
            return []

        try:
            # For UI compatibility, we need to return memory objects, not formatted strings
            # Access the memory manager directly through the agent's initialized components

            # Ensure agent is initialized first
            if hasattr(self.agent, "_ensure_initialized"):
                self._run_async(self.agent._ensure_initialized())

            # Access the memory manager directly for raw memory objects
            if (
                hasattr(self.agent, "memory_manager")
                and self.agent.memory_manager
                and hasattr(self.agent.memory_manager, "agno_memory")
                and self.agent.memory_manager.agno_memory
            ):

                raw_memories = self.agent.memory_manager.agno_memory.memory_manager.get_all_memories(
                    self.agent.memory_manager.agno_memory.db, self.agent.user_id
                )
                return raw_memories

            # Fallback: try to access through different paths for team wrappers
            elif hasattr(self.agent, "agno_memory") and self.agent.agno_memory:
                raw_memories = self.agent.agno_memory.memory_manager.get_all_memories(
                    self.agent.agno_memory.db, self.agent.user_id
                )
                return raw_memories

            return []

        except Exception as e:
            st.error(f"Error getting all memories: {e}")
            return []

    def list_all_memories(self):
        """List all memories using the agent's list_all_memories function.

        This method provides a simplified, user-friendly listing of all memories
        by calling the agent's list_all_memories method which returns a formatted string.
        """
        available, message = self._ensure_agent_available()
        if not available:
            return f"List memories not available: {message}"

        try:
            # Check if the agent has the list_all_memories function
            if hasattr(self.agent, "list_all_memories"):
                # Check if the function returns a coroutine or a direct result
                list_func = self.agent.list_all_memories
                if asyncio.iscoroutinefunction(list_func):
                    result = self._run_async(list_func())
                else:
                    # Function is already sync (like in TeamWrapper)
                    result = list_func()
                return result
            else:
                # Fallback: use get_all_memories and format the result
                memories = self.get_all_memories()
                if not memories:
                    return "🔍 No memories found. Try storing some information first!"

                # Format memories in a simple list format
                result = f"📝 MEMORY LIST ({len(memories)} total):\n\n"
                for i, memory in enumerate(memories, 1):
                    result += f"{i}. {memory.memory}\n"

                return result

        except Exception as e:
            return f"❌ Error listing memories: {str(e)}"

    def add_memory(self, memory_text: str, topics: list = None, input_text: str = None):
        """Add a memory using the agent's store_user_memory function."""
        available, message = self._ensure_agent_available()
        if not available:
            return False, f"Memory storage not available: {message}", None, None

        try:
            # Check if the function returns a coroutine or a direct result
            store_func = self.agent.store_user_memory
            if asyncio.iscoroutinefunction(store_func):
                # Agent method is async - use _run_async
                result = self._run_async(store_func(content=memory_text, topics=topics))
            else:
                # TeamWrapper method is already sync - call directly
                result = store_func(content=memory_text, topics=topics)

            # Handle MemoryStorageResult object
            if (MemoryStorageResult and isinstance(result, MemoryStorageResult)) or (
                hasattr(result, "is_success") and hasattr(result, "message")
            ):
                success = result.is_success
                message = result.message
                memory_id = getattr(result, "memory_id", None)
                generated_topics = getattr(result, "topics", topics)
                return success, message, memory_id, generated_topics
            else:
                # Fallback for unexpected result format
                return False, f"Unexpected result format: {result}", None, None

        except Exception as e:
            return False, f"Error adding memory: {e}", None, None

    def _run_async(self, coro):
        """Helper to run async functions, handling existing event loops."""
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we're in a running loop, we need to use a different approach
            import concurrent.futures
            import threading

            # Create a new event loop in a separate thread
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()

        except RuntimeError:
            # No running event loop, safe to use asyncio.run()
            return asyncio.run(coro)

    def clear_memories(self):
        """Clear all memories using the agent's clear_all_memories function."""
        available, message = self._ensure_agent_available()
        if not available:
            return False, f"Clear memories not available: {message}"

        try:
            # Check if the function returns a coroutine or a direct result
            clear_func = self.agent.clear_all_memories
            if asyncio.iscoroutinefunction(clear_func):
                result = self._run_async(clear_func())
            else:
                # Function is already sync (like in TeamWrapper)
                result = clear_func()

            # Parse the result string to determine success
            if "✅" in result:
                return True, result
            else:
                return False, result

        except Exception as e:
            return False, f"Error clearing memories: {e}"

    def get_memory_stats(self):
        """Get memory statistics using the agent's memory system directly."""
        available, message = self._ensure_agent_available()
        if not available:
            return {"error": f"Memory stats not available: {message}"}

        try:
            # Ensure agent is initialized first
            if hasattr(self.agent, "_ensure_initialized"):
                self._run_async(self.agent._ensure_initialized())

            # Access the memory manager directly to get raw memory data
            memories = []

            if (
                hasattr(self.agent, "memory_manager")
                and self.agent.memory_manager
                and hasattr(self.agent.memory_manager, "agno_memory")
                and self.agent.memory_manager.agno_memory
            ):

                # Use the SemanticMemoryManager's get_all_memories method directly
                memories = self.agent.memory_manager.agno_memory.memory_manager.get_all_memories(
                    self.agent.memory_manager.agno_memory.db, self.agent.user_id
                )
            elif hasattr(self.agent, "agno_memory") and self.agent.agno_memory:
                # Fallback: try to access through different paths for team wrappers
                memories = self.agent.agno_memory.memory_manager.get_all_memories(
                    self.agent.agno_memory.db, self.agent.user_id
                )

            if not memories:
                return {
                    "total_memories": 0,
                    "recent_memories_24h": 0,
                    "average_memory_length": 0,
                    "topic_distribution": {},
                }

            # Calculate statistics from raw memory data
            total_memories = len(memories)

            # Calculate recent memories (24h)
            import time

            current_time = time.time()
            twenty_four_hours_ago = current_time - (24 * 60 * 60)
            recent_memories_24h = sum(
                1
                for memory in memories
                if hasattr(memory, "timestamp")
                and memory.timestamp
                and memory.timestamp > twenty_four_hours_ago
            )

            # Calculate average memory length
            total_length = sum(len(memory.memory) for memory in memories)
            average_memory_length = (
                total_length / total_memories if total_memories > 0 else 0
            )

            # Calculate topic distribution
            topic_distribution = {}
            for memory in memories:
                if hasattr(memory, "topics") and memory.topics:
                    for topic in memory.topics:
                        topic_distribution[topic] = topic_distribution.get(topic, 0) + 1

            return {
                "total_memories": total_memories,
                "recent_memories_24h": recent_memories_24h,
                "average_memory_length": average_memory_length,
                "topic_distribution": topic_distribution,
            }

        except Exception as e:
            return {"error": f"Error getting memory stats: {e}"}

    def delete_memory(self, memory_id: str):
        """Delete a memory using the agent's delete_memory function."""
        available, message = self._ensure_agent_available()
        if not available:
            return False, f"Memory deletion not available: {message}"

        try:
            logger.info(f"🗑️ Deleting memory using agent.delete_memory(): {memory_id}")

            # Check if the function returns a coroutine or a direct result
            delete_func = self.agent.delete_memory
            if asyncio.iscoroutinefunction(delete_func):
                result = self._run_async(delete_func(memory_id))
            else:
                # Function is already sync (like in TeamWrapper)
                result = delete_func(memory_id)

            # Parse the result string to determine success
            if isinstance(result, str):
                if "✅" in result or "Successfully deleted" in result:
                    logger.info(f"✅ Memory deletion successful: {result}")
                    return True, result
                else:
                    logger.warning(f"❌ Memory deletion failed: {result}")
                    return False, result
            else:
                logger.error(f"Unexpected result type: {type(result)}")
                return False, f"Unexpected result type: {type(result)}"

        except Exception as e:
            logger.error(f"Exception in delete_memory: {e}", exc_info=True)
            return False, f"Error deleting memory: {e}"

    def update_memory(
        self,
        memory_id: str,
        memory_text: str,
        topics: list = None,
        input_text: str = None,
    ):
        """Update a memory using the agent's update_memory function."""
        available, message = self._ensure_agent_available()
        if not available:
            return False, f"Memory update not available: {message}"

        try:
            # Check if the function returns a coroutine or a direct result
            update_func = self.agent.update_memory
            if asyncio.iscoroutinefunction(update_func):
                result = self._run_async(update_func(memory_id, memory_text, topics))
            else:
                # Function is already sync (like in TeamWrapper)
                result = update_func(memory_id, memory_text, topics)

            # Parse the result string to determine success
            if "✅" in result:
                return True, result
            else:
                return False, result

        except Exception as e:
            return False, f"Error updating memory: {e}"

    def sync_memory_to_graph(self, memory_text: str, topics: list = None):
        """Sync a memory to the LightRAG graph system."""
        # This functionality is now handled automatically by store_user_memory
        # which stores in both local SQLite and LightRAG graph systems
        try:
            result = self._run_async(
                self.agent.store_user_memory(content=memory_text, topics=topics)
            )
            if hasattr(result, "graph_success") and result.graph_success:
                return True, "Memory synced to graph successfully"
            else:
                return False, "Graph sync failed"
        except Exception as e:
            return False, f"Error syncing to graph: {e}"

    def get_memory_sync_status(self):
        """Get memory sync status by checking both local and graph memory systems."""
        available, message = self._ensure_agent_available()
        if not available:
            return {
                "error": f"Memory sync status not available: {message}",
                "local_memory_count": 0,
                "graph_entity_count": 0,
                "sync_ratio": 0,
                "status": "error",
            }

        try:
            # Ensure agent is initialized first
            if hasattr(self.agent, "_ensure_initialized"):
                self._run_async(self.agent._ensure_initialized())

            # Get local memory count
            local_memories = []
            if (
                hasattr(self.agent, "memory_manager")
                and self.agent.memory_manager
                and hasattr(self.agent.memory_manager, "agno_memory")
                and self.agent.memory_manager.agno_memory
            ):

                local_memories = self.agent.memory_manager.agno_memory.memory_manager.get_all_memories(
                    self.agent.memory_manager.agno_memory.db, self.agent.user_id
                )
            elif hasattr(self.agent, "agno_memory") and self.agent.agno_memory:
                local_memories = self.agent.agno_memory.memory_manager.get_all_memories(
                    self.agent.agno_memory.db, self.agent.user_id
                )

            local_memory_count = len(local_memories)

            # Get graph entity count using the agent's new method
            graph_entity_count = 0
            try:
                # Check if agent has the get_graph_entity_count method
                if hasattr(self.agent, "get_graph_entity_count"):
                    if asyncio.iscoroutinefunction(self.agent.get_graph_entity_count):
                        graph_entity_count = self._run_async(
                            self.agent.get_graph_entity_count()
                        )
                    else:
                        graph_entity_count = self.agent.get_graph_entity_count()
                else:
                    # Fallback: try to access through team wrapper's knowledge agent
                    if (
                        hasattr(self.agent, "team")
                        and hasattr(self.agent.team, "members")
                        and self.agent.team.members
                    ):
                        knowledge_agent = self.agent.team.members[0]
                        if hasattr(knowledge_agent, "get_graph_entity_count"):
                            if asyncio.iscoroutinefunction(
                                knowledge_agent.get_graph_entity_count
                            ):
                                graph_entity_count = self._run_async(
                                    knowledge_agent.get_graph_entity_count()
                                )
                            else:
                                graph_entity_count = (
                                    knowledge_agent.get_graph_entity_count()
                                )

                logger.debug(f"Retrieved graph entity count: {graph_entity_count}")

            except Exception as e:
                logger.warning(f"Error getting graph entity count: {e}")
                graph_entity_count = 0

            # Calculate sync ratio
            if local_memory_count == 0 and graph_entity_count == 0:
                sync_ratio = 1.0  # Both empty = synced
                status = "synced"
            elif local_memory_count == 0:
                sync_ratio = 0.0
                status = "out_of_sync"
            elif graph_entity_count == 0:
                sync_ratio = 0.0
                status = "out_of_sync"
            else:
                sync_ratio = min(local_memory_count, graph_entity_count) / max(
                    local_memory_count, graph_entity_count
                )
                status = "synced" if sync_ratio > 0.9 else "out_of_sync"

            return {
                "local_memory_count": local_memory_count,
                "graph_entity_count": graph_entity_count,
                "sync_ratio": sync_ratio,
                "status": status,
            }

        except Exception as e:
            return {
                "error": f"Error checking sync status: {e}",
                "local_memory_count": 0,
                "graph_entity_count": 0,
                "sync_ratio": 0,
                "status": "error",
            }


class StreamlitKnowledgeHelper:
    def __init__(self, agent):
        self.agent = agent
        # Don't cache knowledge_manager - get it fresh each time
        self._knowledge_manager = None

    def _run_async(self, coro):
        """Helper to run async functions, handling existing event loops."""
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # If we're in a running loop, we need to use a different approach
            import concurrent.futures
            import threading

            # Create a new event loop in a separate thread
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()

        except RuntimeError:
            # No running event loop, safe to use asyncio.run()
            return asyncio.run(coro)

    def _get_knowledge_manager(self):
        """Get knowledge manager, ensuring agent is initialized first."""
        if not self.agent:
            return None

        # Check if agent is already initialized to avoid redundant initialization
        is_initialized = getattr(self.agent, "_initialized", False)

        # Only initialize if not already initialized
        if not is_initialized and hasattr(self.agent, "_ensure_initialized"):
            try:
                logger.info(
                    "Agent not initialized, triggering lazy initialization for knowledge..."
                )
                self._run_async(self.agent._ensure_initialized())
            except Exception as e:
                logger.error(f"Failed to initialize agent: {e}")
                return None
        elif is_initialized:
            logger.info("Agent already initialized, skipping knowledge initialization")

        # Now check for knowledge manager
        if hasattr(self.agent, "agno_knowledge") and self.agent.agno_knowledge:
            return self.agent.agno_knowledge
        return None

    @property
    def knowledge_manager(self):
        """Dynamic property that always gets fresh knowledge manager."""
        return self._get_knowledge_manager()

    def search_knowledge(self, query: str, limit: int = 10):
        km = self.knowledge_manager  # This will trigger initialization
        if not km:
            return []
        try:
            return km.search(query=query, num_documents=limit)
        except Exception as e:
            st.error(f"Error in knowledge search: {e}")
            return []

    def search_rag(self, query: str, params: dict):
        # Check if agent exists and has the query method
        if not self.agent or not hasattr(self.agent, "query_lightrag_knowledge_direct"):
            st.error(
                "LightRAG knowledge base not available - agent missing query method"
            )
            return None

        # Force agent initialization if needed
        try:
            if hasattr(self.agent, "_ensure_initialized"):
                self._run_async(self.agent._ensure_initialized())
        except Exception as e:
            st.error(f"Failed to initialize agent: {e}")
            return None

        # LightRAG is available if the agent has the query method - no need for additional checks
        # The agent initialization ensures all components are properly set up

        try:
            result = self._run_async(
                self.agent.query_lightrag_knowledge_direct(query, params=params)
            )
            return result
        except Exception as e:
            st.error(f"Error querying LightRAG knowledge base: {e}")
            import traceback

            st.error(f"Full traceback: {traceback.format_exc()}")
            return None
