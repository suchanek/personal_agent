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
        if not self.agent or not hasattr(self.agent, "agno_memory"):
            return []
        try:
            return self.agent.agno_memory.get_user_memories(user_id=self.agent.user_id)
        except Exception as e:
            st.error(f"Error getting all memories: {e}")
            return []

    def add_memory(self, memory_text: str, topics: list = None, input_text: str = None):
        if not self.memory_manager or not self.db:
            return False, "Memory system not available", None
        try:
            return self.memory_manager.add_memory(
                memory_text=memory_text,
                db=self.db,
                user_id=self.agent.user_id,
                topics=topics,
                input_text=input_text,
            )
        except Exception as e:
            return False, f"Error adding memory: {e}", None

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

    def search_rag(self, query: str, search_type: str = "naive"):
        if not self.agent or not (hasattr(self.agent, "lightrag_knowledge")):
            return None
        try:
            return asyncio.run(self.agent.query_knowledge_base(query, mode=search_type))
        except Exception as e:
            st.error(f"Error querying knowledge base: {e}")
            return None