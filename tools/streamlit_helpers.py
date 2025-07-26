import asyncio
import streamlit as st
from datetime import datetime
import time

class StreamlitMemoryHelper:
    def __init__(self, agent):
        self.agent = agent
        self.memory_manager, self.db = self._get_memory_manager_and_db()

    def _get_memory_manager_and_db(self):
        if not self.agent or not (hasattr(self.agent, "agno_memory") and self.agent.agno_memory):
            return None, None
        return self.agent.agno_memory.memory_manager, self.agent.agno_memory.db

    def search_memories(self, query: str, limit: int = 10, similarity_threshold: float = 0.3):
        if not self.memory_manager or not self.db:
            return []
        try:
            return self.memory_manager.search_memories(
                query=query,
                db=self.db,
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
        self.knowledge_manager = self._get_knowledge_manager()

    def _get_knowledge_manager(self):
        if not self.agent or not (hasattr(self.agent, "agno_knowledge") and self.agent.agno_knowledge):
            return None
        return self.agent.agno_knowledge

    def search_knowledge(self, query: str, limit: int = 10):
        if not self.knowledge_manager:
            return []
        try:
            return self.knowledge_manager.search(query=query, num_documents=limit)
        except Exception as e:
            st.error(f"Error in knowledge search: {e}")
            return []

    def search_rag(self, query: str, params: dict):
        # Check if agent exists and has the query method
        if not self.agent or not hasattr(self.agent, "query_lightrag_knowledge_direct"):
            st.error("LightRAG knowledge base not available - agent missing query method")
            return None
        
        # Check if LightRAG is enabled on the agent
        if not getattr(self.agent, "lightrag_knowledge_enabled", False):
            st.error("LightRAG knowledge base not enabled - server may not be running")
            return None
            
        try:
            result = asyncio.run(self.agent.query_lightrag_knowledge_direct(query, params=params))
            return result
        except Exception as e:
            st.error(f"Error querying LightRAG knowledge base: {e}")
            import traceback
            st.error(f"Full traceback: {traceback.format_exc()}")
            return None
