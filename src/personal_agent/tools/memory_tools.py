"""Memory management tools for storing and retrieving knowledge."""

import logging
from datetime import datetime
from typing import List

from langchain_core.tools import tool
from weaviate.util import generate_uuid5

from ..config import USE_WEAVIATE
from ..utils import setup_logging

logger = setup_logging()


def create_memory_tools(weaviate_client_instance, vector_store_instance):
    """Create memory tools with injected dependencies."""

    @tool
    def store_interaction(text: str, topic: str = "general") -> str:
        """Store user interaction in Weaviate."""
        if not USE_WEAVIATE or vector_store_instance is None:
            logger.warning("Weaviate is disabled, interaction not stored.")
            return "Weaviate is disabled, interaction not stored."
        try:
            # Format timestamp as RFC3339 (with 'Z' for UTC)
            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
            vector_store_instance.add_texts(
                texts=[text],
                metadatas=[{"timestamp": timestamp, "topic": topic}],
                ids=[generate_uuid5(text)],
            )
            logger.info("Stored interaction: %s...", text[:50])
            return "Interaction stored successfully."
        except Exception as e:
            error_msg = str(e).lower()

            # Check for corruption indicators and attempt recovery
            corruption_indicators = [
                "no such file or directory",
                "wal",
                "segment-",
                "commit log",
                "failed to send all objects",
                "weaviateinsertmanyallfailederror",
            ]

            if any(indicator in error_msg for indicator in corruption_indicators):
                logger.warning("Database corruption detected during storage: %s", e)

                # Attempt recovery by importing and using the reset function
                try:
                    from ..core.memory import reset_weaviate_if_corrupted

                    if reset_weaviate_if_corrupted():
                        logger.info("Weaviate recovery successful, retrying storage...")
                        # Retry the operation once
                        try:
                            timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                            vector_store_instance.add_texts(
                                texts=[text],
                                metadatas=[{"timestamp": timestamp, "topic": topic}],
                                ids=[generate_uuid5(text)],
                            )
                            logger.info(
                                "Stored interaction after recovery: %s...", text[:50]
                            )
                            return "Interaction stored successfully after database recovery."
                        except Exception as retry_error:
                            logger.error(
                                "Failed to store after recovery: %s", retry_error
                            )
                            return f"Error storing interaction after recovery: {str(retry_error)}"
                    else:
                        logger.error("Weaviate recovery failed")
                        return "Database corruption detected, recovery failed."
                except ImportError:
                    logger.error("Could not import recovery function")
                    return f"Database corruption detected: {str(e)}"

            logger.error("Error storing interaction: %s", str(e))
            return f"Error storing interaction: {str(e)}"

    @tool
    def query_knowledge_base(query: str, limit: int = 5) -> List[str]:
        """Query Weaviate for relevant context."""
        if not USE_WEAVIATE or vector_store_instance is None:
            logger.warning("Weaviate is disabled, no context available.")
            return ["Weaviate is disabled, no context available."]
        try:
            results = vector_store_instance.similarity_search(query, k=limit)
            context_list = []
            for doc in results:
                metadata = doc.metadata if hasattr(doc, "metadata") else {}
                timestamp = metadata.get("timestamp", "unknown")
                topic = metadata.get("topic", "general")
                context_list.append(f"[{timestamp}] [{topic}] {doc.page_content}")
            logger.info(
                "Found %d relevant items for query: %s", len(context_list), query
            )
            return context_list
        except Exception as e:
            error_msg = str(e).lower()

            # Check for corruption indicators and attempt recovery
            corruption_indicators = [
                "no such file or directory",
                "wal",
                "segment-",
                "commit log",
                "failed to send all objects",
                "weaviateinsertmanyallfailederror",
            ]

            if any(indicator in error_msg for indicator in corruption_indicators):
                logger.warning("Database corruption detected during query: %s", e)
                try:
                    from ..core.memory import reset_weaviate_if_corrupted

                    if reset_weaviate_if_corrupted():
                        logger.info("Weaviate recovery successful, retrying query...")
                        return ["Database was recovered, please retry your query."]
                    else:
                        return ["Database corruption detected, recovery failed."]
                except ImportError:
                    return [f"Database corruption detected: {str(e)}"]

            logger.error("Error querying knowledge base: %s", str(e))
            return [f"Error querying knowledge base: {str(e)}"]

    @tool
    def clear_knowledge_base() -> str:
        """Clear all data from Weaviate."""
        if not USE_WEAVIATE or weaviate_client_instance is None:
            logger.warning("Weaviate is disabled, cannot clear.")
            return "Weaviate is disabled, cannot clear."
        try:
            collection_name = "UserKnowledgeBase"
            if weaviate_client_instance.collections.exists(collection_name):
                collection = weaviate_client_instance.collections.get(collection_name)
                collection.data.delete_many({})
                logger.info("Cleared all data from Weaviate")
                return "Successfully cleared all data from knowledge base."
            else:
                logger.warning("Collection %s does not exist", collection_name)
                return "Collection does not exist."
        except Exception as e:
            logger.error("Error clearing knowledge base: %s", str(e))
            return f"Error clearing knowledge base: {str(e)}"

    return [store_interaction, query_knowledge_base, clear_knowledge_base]


# For backward compatibility, create default tools that use imported globals
try:
    from ..core.memory import vector_store, weaviate_client

    _default_tools = create_memory_tools(weaviate_client, vector_store)
    store_interaction = _default_tools[0]
    query_knowledge_base = _default_tools[1]
    clear_knowledge_base = _default_tools[2]
except ImportError:
    # If there's an error creating default tools, create dummy tools
    @tool
    def store_interaction(text: str, topic: str = "general") -> str:
        """Store user interaction in Weaviate."""
        return "Weaviate not available, interaction not stored."

    @tool
    def query_knowledge_base(query: str, limit: int = 5) -> List[str]:
        """Query Weaviate for relevant context."""
        return ["Weaviate not available, no context available."]

    @tool
    def clear_knowledge_base() -> str:
        """Clear all data from Weaviate."""
        return "Weaviate not available, cannot clear."
