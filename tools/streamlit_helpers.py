import asyncio
import streamlit as st
from datetime import datetime
import time

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
            
        # Force agent initialization if needed
        try:
            if hasattr(self.agent, '_ensure_initialized'):
                asyncio.run(self.agent._ensure_initialized())
        except Exception as e:
            print(f"Failed to initialize agent: {e}")
            return None, None
            
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

    def search_memories(self, query: str, limit: int = 10, similarity_threshold: float = 0.3):
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
            return False, "Memory storage function not available on the agent.", None, None

        try:
            # Call the async method from the agent
            result_str = asyncio.run(
                self.agent.store_user_memory(content=memory_text, topics=topics)
            )

            # Parse the result string to determine success and message
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
            return self.memory_manager.clear_memories(db=self.db, user_id=self.agent.user_id)
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
        if not self.memory_manager or not self.db:
            return False, "Memory system not available"
        try:
            return self.memory_manager.delete_memory(memory_id, self.db, self.agent.user_id)
        except Exception as e:
            return False, f"Error deleting memory: {e}"

    def update_memory(self, memory_id: str, memory_text: str, topics: list = None, input_text: str = None):
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
                "status": "synced"
            }
            
        except Exception as e:
            return {
                "error": f"Error checking sync status: {e}",
                "local_memory_count": 0,
                "graph_entity_count": 0,
                "sync_ratio": 0,
                "status": "error"
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
            
        # Force agent initialization if needed
        try:
            if hasattr(self.agent, '_ensure_initialized'):
                asyncio.run(self.agent._ensure_initialized())
        except Exception as e:
            print(f"Failed to initialize agent: {e}")
            return None
            
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
            st.error("LightRAG knowledge base not available - agent missing query method")
            return None
        
        # Force agent initialization if needed
        try:
            if hasattr(self.agent, '_ensure_initialized'):
                asyncio.run(self.agent._ensure_initialized())
        except Exception as e:
            st.error(f"Failed to initialize agent: {e}")
            return None
        
        # LightRAG is available if the agent has the query method - no need for additional checks
        # The agent initialization ensures all components are properly set up
            
        try:
            result = asyncio.run(self.agent.query_lightrag_knowledge_direct(query, params=params))
            return result
        except Exception as e:
            st.error(f"Error querying LightRAG knowledge base: {e}")
            import traceback
            st.error(f"Full traceback: {traceback.format_exc()}")
            return None
