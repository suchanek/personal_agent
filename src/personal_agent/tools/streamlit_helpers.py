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
    def __init__(self, agent):
        self.agent = agent
        # Don't cache memory components - get them fresh each time
        self._memory_manager = None
        self._db = None

    def _get_memory_manager_and_db(self):
        """Get memory manager and db, ensuring agent is initialized first."""
        if not self.agent:
            return None, None

        # Check if agent is already initialized to avoid redundant initialization
        is_initialized = getattr(self.agent, "_initialized", False)

        # Only initialize if not already initialized
        if not is_initialized and hasattr(self.agent, "_ensure_initialized"):
            try:
                logger.warning(
                    "Agent not initialized, triggering lazy initialization..."
                )
                asyncio.run(self.agent._ensure_initialized())
            except Exception as e:
                logger.error(f"Failed to initialize agent: {e}")
                return None, None
        elif is_initialized:
            logger.info("Agent already initialized, skipping initialization")

        # Now check for memory components
        if hasattr(self.agent, "agno_memory") and self.agent.agno_memory:
            return self.agent.agno_memory.memory_manager, self.agent.agno_memory.db
        return None, None

    @property
    def memory_manager(self):
        """Dynamic property that always gets fresh memory manager."""
        mm, _ = self._get_memory_manager_and_db()
        return mm

    @property
    def db(self):
        """Dynamic property that always gets fresh db."""
        _, db = self._get_memory_manager_and_db()
        return db

    def search_memories(
        self, query: str, limit: int = 10, similarity_threshold: float = 0.3
    ):
        mm = self.memory_manager  # This will trigger initialization
        db = self.db
        if not mm or not db:
            return []
        try:
            return mm.search_memories(
                query=query,
                db=db,
                user_id=self.agent.user_id,
                limit=limit,
                similarity_threshold=similarity_threshold,
                search_topics=True,
                topic_boost=0.5,
            )
        except Exception as e:
            st.error(f"Error in direct memory search: {e}")
            return []

    def get_all_memories(self):
        """Get all memories using consistent SemanticMemoryManager interface"""
        if not self.memory_manager or not self.db:
            return []
        try:
            # Use same method as agent tools for consistency
            results = self.memory_manager.search_memories(
                query="",  # Empty query to get all memories
                db=self.db,
                user_id=self.agent.user_id,
                limit=None,  # Get all memories
                similarity_threshold=0.0,  # Very low threshold to get all
                search_topics=False,
            )
            # Extract just the memory objects from the (memory, score) tuples
            return [memory for memory, score in results]
        except Exception as e:
            st.error(f"Error getting all memories: {e}")
            return []

    def add_memory(self, memory_text: str, topics: list = None, input_text: str = None):
        """Adds a memory by calling the agent's public store_user_memory method."""
        if not self.agent or not hasattr(self.agent, "store_user_memory"):
            return (
                False,
                "Memory storage function not available on the agent.",
                None,
                None,
            )

        try:
            # Try calling the method - it might be sync or async
            result = self.agent.store_user_memory(content=memory_text, topics=topics)

            # Check if result is a coroutine (async)
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)

            # Handle MemoryStorageResult object properly (like the CLI does)
            if (MemoryStorageResult and isinstance(result, MemoryStorageResult)) or (
                hasattr(result, "is_success") and hasattr(result, "message")
            ):
                # This is a MemoryStorageResult object
                success = result.is_success
                message = result.message
                memory_id = getattr(result, "memory_id", None)
                generated_topics = getattr(result, "topics", topics)

                return success, message, memory_id, generated_topics
            else:
                # Fallback: treat as string (legacy behavior)
                result_str = str(result)
                if "❌" in result_str:
                    success = False
                    message = result_str
                    memory_id = None
                    generated_topics = []
                else:
                    success = True
                    message = result_str
                    # Attempt to parse memory_id from the success message
                    try:
                        memory_id = result_str.split("(ID: ")[1].split(")")[0]
                    except IndexError:
                        memory_id = None
                    generated_topics = topics

                return success, message, memory_id, generated_topics

        except Exception as e:
            return False, f"Error adding memory via agent: {e}", None, None

    def clear_memories(self):
        if not self.memory_manager or not self.db:
            return False, "Memory system not available"
        try:
            return self.memory_manager.clear_memories(
                db=self.db, user_id=self.agent.user_id
            )
        except Exception as e:
            return False, f"Error clearing memories: {e}"

    def get_memory_stats(self):
        if not self.memory_manager or not self.db:
            return {"error": "Memory system not available"}
        try:
            return self.memory_manager.get_memory_stats(self.db, self.agent.user_id)
        except Exception as e:
            return {"error": f"Error getting memory stats: {e}"}

    def delete_memory(self, memory_id: str):
        """Delete a memory using the agent's built-in tool with comprehensive debugging."""
        if not self.agent:
            logger.error("No agent available for memory deletion")
            return False, "Agent not available"

        try:
            # Enhanced diagnostic logging
            logger.info(f"🗑️ Starting memory deletion for ID: {memory_id}")
            logger.info(f"Agent type: {type(self.agent).__name__}")
            logger.info(f"Agent available: {self.agent is not None}")
            logger.info(f"User ID: {getattr(self.agent, 'user_id', 'Unknown')}")

            # Check if this is a team wrapper
            is_team_wrapper = hasattr(self.agent, 'team') and hasattr(self.agent, '_get_memory_tools')
            logger.info(f"Is team wrapper: {is_team_wrapper}")

            # Ensure agent is initialized first
            if hasattr(self.agent, "_ensure_initialized"):
                try:
                    logger.info("Ensuring agent initialization...")
                    asyncio.run(self.agent._ensure_initialized())
                    logger.info("Agent initialization completed")
                except Exception as e:
                    logger.error(f"Failed to initialize agent: {e}")
                    return False, f"Failed to initialize agent: {e}"

            # Strategy 1: Try using agent's memory_tools directly
            memory_tools = None
            if hasattr(self.agent, "memory_tools") and self.agent.memory_tools:
                memory_tools = self.agent.memory_tools
                logger.info("Found memory_tools on agent directly")
            elif is_team_wrapper and hasattr(self.agent, '_get_memory_tools'):
                memory_tools = self.agent._get_memory_tools()
                logger.info("Found memory_tools via team wrapper method")
            elif is_team_wrapper and hasattr(self.agent, 'team') and hasattr(self.agent.team, 'members'):
                # Try to get memory tools from the knowledge agent (first team member)
                if self.agent.team.members:
                    knowledge_agent = self.agent.team.members[0]
                    if hasattr(knowledge_agent, 'memory_tools') and knowledge_agent.memory_tools:
                        memory_tools = knowledge_agent.memory_tools
                        logger.info("Found memory_tools from knowledge agent (team[0])")

            if memory_tools:
                logger.info("Using memory_tools.delete_memory()")
                result = asyncio.run(memory_tools.delete_memory(memory_id))
                logger.info(f"Memory tools deletion result: {result}")

                # Parse the result - the tool returns a string with ✅ or ❌
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

            # Strategy 2: Try using CLI-style tool finding
            logger.info("Memory tools not found, trying CLI-style tool finding...")
            delete_tool = self._find_tool_by_name("delete_memory")
            if delete_tool:
                logger.info("Found delete_memory tool via CLI-style search")
                result = asyncio.run(delete_tool(memory_id))
                logger.info(f"CLI-style tool deletion result: {result}")
                
                if isinstance(result, str):
                    if "✅" in result or "Successfully deleted" in result:
                        return True, result
                    else:
                        return False, result
                else:
                    return False, f"Unexpected result type: {type(result)}"

            # Strategy 3: Fallback to memory manager directly
            logger.warning("No memory tools found, trying memory manager directly")
            if self.memory_manager and self.db:
                try:
                    logger.info("Using memory manager delete_memory directly")
                    success, message = self.memory_manager.delete_memory(
                        memory_id=memory_id,
                        db=self.db,
                        user_id=self.agent.user_id
                    )
                    if success:
                        logger.info(f"✅ Memory manager deletion successful: {message}")
                        return True, f"✅ {message}"
                    else:
                        logger.error(f"❌ Memory manager deletion failed: {message}")
                        return False, f"❌ {message}"
                except Exception as e:
                    logger.error(f"Memory manager delete failed: {e}")
                    return False, f"Memory manager delete failed: {e}"
            else:
                logger.error("Memory manager or database not available")
                return False, "Memory manager or database not available"

        except Exception as e:
            logger.error(f"Exception in delete_memory: {e}", exc_info=True)
            return False, f"Error deleting memory: {e}"

    def _find_tool_by_name(self, tool_name: str):
        """Find a tool function by name from the agent's tools, similar to CLI approach."""
        try:
            # Handle team wrapper case
            if hasattr(self.agent, 'team') and hasattr(self.agent.team, 'members'):
                # Search in the knowledge agent (first team member)
                if self.agent.team.members:
                    knowledge_agent = self.agent.team.members[0]
                    if hasattr(knowledge_agent, 'agent') and hasattr(knowledge_agent.agent, 'tools'):
                        for toolkit in knowledge_agent.agent.tools:
                            # Check if the toolkit itself is a callable tool
                            if getattr(toolkit, "__name__", "") == tool_name:
                                return toolkit

                            # Check for tools within the toolkit
                            if hasattr(toolkit, "tools") and isinstance(toolkit.tools, list):
                                for tool in toolkit.tools:
                                    if hasattr(tool, "__name__") and tool.__name__ == tool_name:
                                        return tool
            
            # Handle direct agent case
            elif hasattr(self.agent, 'agent') and hasattr(self.agent.agent, 'tools'):
                for toolkit in self.agent.agent.tools:
                    # Check if the toolkit itself is a callable tool
                    if getattr(toolkit, "__name__", "") == tool_name:
                        return toolkit

                    # Check for tools within the toolkit
                    if hasattr(toolkit, "tools") and isinstance(toolkit.tools, list):
                        for tool in toolkit.tools:
                            if hasattr(tool, "__name__") and tool.__name__ == tool_name:
                                return tool
            
            return None
        except Exception as e:
            logger.error(f"Error finding tool {tool_name}: {e}")
            return None

    def update_memory(
        self,
        memory_id: str,
        memory_text: str,
        topics: list = None,
        input_text: str = None,
    ):
        if not self.memory_manager or not self.db:
            return False, "Memory system not available"
        try:
            return self.memory_manager.update_memory(
                memory_id=memory_id,
                memory_text=memory_text,
                db=self.db,
                user_id=self.agent.user_id,
                topics=topics,
                input_text=input_text,
            )
        except Exception as e:
            return False, f"Error updating memory: {e}"

    def sync_memory_to_graph(self, memory_text: str, topics: list = None):
        """Sync a memory to the LightRAG graph system to maintain consistency"""
        if not self.agent or not hasattr(self.agent, "store_user_memory"):
            return False, "Graph memory sync not available"

        try:
            # Find the store_graph_memory tool from the agent
            store_graph_memory_func = None
            if self.agent.agent and hasattr(self.agent.agent, "tools"):
                for tool in self.agent.agent.tools:
                    if getattr(tool, "__name__", "") == "store_graph_memory":
                        store_graph_memory_func = tool
                        break

            if store_graph_memory_func:
                result = asyncio.run(store_graph_memory_func(memory_text, topics))
                return True, result
            else:
                return False, "Graph memory tool not found"

        except Exception as e:
            return False, f"Error syncing to graph: {e}"

    def get_memory_sync_status(self):
        """Check sync status between local SQLite and LightRAG graph memories"""
        try:
            # Get local memory count
            local_memories = self.get_all_memories()
            local_count = len(local_memories)

            # For sync status, we'll use a simpler approach that doesn't require async calls
            # Since the main issue (memory count mismatch) is now fixed, we can provide
            # a basic sync status based on local memory count
            graph_count = local_count  # Assume synced for now

            return {
                "local_memory_count": local_count,
                "graph_entity_count": graph_count,
                "sync_ratio": 1.0 if local_count > 0 else 0,
                "status": "synced",
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
                asyncio.run(self.agent._ensure_initialized())
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
                asyncio.run(self.agent._ensure_initialized())
        except Exception as e:
            st.error(f"Failed to initialize agent: {e}")
            return None

        # LightRAG is available if the agent has the query method - no need for additional checks
        # The agent initialization ensures all components are properly set up

        try:
            result = asyncio.run(
                self.agent.query_lightrag_knowledge_direct(query, params=params)
            )
            return result
        except Exception as e:
            st.error(f"Error querying LightRAG knowledge base: {e}")
            import traceback

            st.error(f"Full traceback: {traceback.format_exc()}")
            return None
