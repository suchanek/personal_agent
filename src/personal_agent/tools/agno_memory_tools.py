"""Agno-compatible memory management tools for storing and retrieving knowledge."""

from datetime import datetime
from typing import List

from weaviate.util import generate_uuid5

from ..config import USE_WEAVIATE
from ..utils import setup_logging

logger = setup_logging()


def create_agno_memory_tools(weaviate_client_instance, vector_store_instance):
    """Create Agno-compatible memory tools with injected dependencies."""

    async def store_interaction_weaviate(text: str, topic: str = "general") -> str:
        """Store user interaction in Weaviate.

        Args:
            text: The text content to store
            topic: The topic/category for the interaction

        Returns:
            str: Success or error message
        """
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
                    from ..core.memory import reset_weaviate

                    logger.info("Attempting to reset Weaviate...")
                    reset_weaviate()

                    # Retry the operation
                    timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
                    vector_store_instance.add_texts(
                        texts=[text],
                        metadatas=[{"timestamp": timestamp, "topic": topic}],
                        ids=[generate_uuid5(text)],
                    )
                    logger.info("Stored interaction after reset: %s...", text[:50])
                    return "Interaction stored successfully after database reset."

                except Exception as reset_error:
                    logger.error("Failed to reset Weaviate: %s", reset_error)
                    return f"Error storing interaction and reset failed: {reset_error}"
            else:
                logger.error("Error storing interaction: %s", e)
                return f"Error storing interaction: {e}"

    async def query_knowledge_base_weaviate(query: str, limit: int = 3) -> str:
        """Query Weaviate for relevant context.

        Args:
            query: The search query
            limit: Maximum number of results to return

        Returns:
            str: Search results or error message
        """
        if not USE_WEAVIATE or vector_store_instance is None:
            return "Weaviate is disabled, no context available."

        try:
            # Use similarity search to find relevant content
            docs = vector_store_instance.similarity_search(query, k=limit)

            if not docs:
                return "No relevant context found."

            # Format results with metadata
            results = []
            for i, doc in enumerate(docs):
                content = doc.page_content
                metadata = doc.metadata
                timestamp = metadata.get("timestamp", "Unknown time")
                topic = metadata.get("topic", "general")

                result = f"[{timestamp}] ({topic}): {content}"
                results.append(result)

            return "\n\n".join(results)

        except Exception as e:
            logger.error("Error querying knowledge base: %s", e)
            return f"Error querying knowledge base: {e}"

    async def clear_knowledge_base_weaviate() -> str:
        """Clear all data from Weaviate.

        Returns:
            str: Success or error message
        """
        if not USE_WEAVIATE or weaviate_client_instance is None:
            return "Weaviate is disabled, cannot clear."

        try:
            # Clear the knowledge schema
            if weaviate_client_instance.schema.exists("Knowledge"):
                weaviate_client_instance.schema.delete_class("Knowledge")
                logger.info("Cleared Knowledge schema from Weaviate")

                # Recreate the schema
                from ..core.memory import setup_weaviate

                setup_weaviate()

                return "Knowledge base cleared and recreated successfully."
            else:
                return "Knowledge base was already empty."

        except Exception as e:
            logger.error("Error clearing weaviate knowledge base: %s", e)
            return f"Error clearing knowledge base: {e}"

    # Set function metadata for Agno compatibility
    store_interaction.__name__ = "store_interaction_weaviate"
    store_interaction.__doc__ = """Store user interaction in Weaviate.
    
    Args:
        text: The text content to store
        topic: The topic/category for the interaction
        
    Returns:
        str: Success or error message"""

    query_knowledge_base.__name__ = "query_knowledge_base_weaviate"
    query_knowledge_base.__doc__ = """Query Weaviate for relevant context.
    
    Args:
        query: The search query
        limit: Maximum number of results to return
        
    Returns:
        str: Search results or error message"""

    clear_knowledge_base.__name__ = "clear_knowledge_base"
    clear_knowledge_base.__doc__ = """Clear all data from Weaviate.
    
    Returns:
        str: Success or error message"""

    return (
        store_interaction_weaviate,
        query_knowledge_base_weaviate,
        clear_knowledge_base_weaviate,
    )
