"""Centralized Query Handler

This module provides a unified query dispatcher that routes queries to
appropriate handlers based on intent classification. It includes:

- Query classification using QueryClassifier
- Dispatch to fast paths or full team inference
- Graceful fallback on errors
- Built-in logging and metrics collection

Classes:
    QueryHandler: Main query dispatcher

Author: Claude Code
Date: 2025-11-18
"""

import asyncio
import logging
import time
from typing import Optional

from personal_agent.core.query_classifier import QueryClassifier, QueryIntent
from personal_agent.core.response_types import ResponseBuilder, UnifiedResponse

logger = logging.getLogger(__name__)


class QueryHandler:
    """Centralized query dispatcher with fast path support.

    Routes queries to appropriate handlers based on intent classification:
    - MEMORY_LIST → Fast path (direct memory retrieval)
    - MEMORY_SEARCH → Fast path (semantic memory search)
    - KNOWLEDGE_SEARCH → Fast path (knowledge base search)
    - GENERAL → Full team inference

    Includes graceful fallback to team inference if fast paths fail.

    :param agent: Agent or team instance for query handling
    :param classifier: Optional QueryClassifier instance
    """

    def __init__(
        self,
        agent,
        classifier: Optional[QueryClassifier] = None,
    ):
        """Initialize the query handler.

        :param agent: Agent or team instance (must have arun method)
        :param classifier: Optional QueryClassifier (creates default if None)
        """
        self.agent = agent
        self.classifier = classifier or QueryClassifier()

    async def handle_query(self, query: str, user_id: Optional[str] = None) -> UnifiedResponse:
        """Route and handle a query asynchronously.

        :param query: User query text
        :param user_id: Optional user ID for team.arun
        :return: UnifiedResponse with content and metadata
        """
        # Classify the query
        classification = self.classifier.classify(query)

        logger.info(
            f"Query classified as {classification.intent.value} "
            f"(confidence: {classification.confidence:.2f}, "
            f"reason: {classification.reason})"
        )

        # Route to appropriate handler based on intent
        try:
            if classification.intent == QueryIntent.MEMORY_LIST:
                return await self._handle_memory_list(query)
            elif classification.intent == QueryIntent.MEMORY_SEARCH:
                return await self._handle_memory_search(query)
            else:
                # General query or default: use full team inference
                return await self._handle_general_query(query, user_id)

        except Exception as e:
            logger.error(f"Query handler error: {e}", exc_info=True)
            return ResponseBuilder.error(f"Query handling failed: {str(e)}", e)

    async def _handle_memory_list(self, query: str) -> UnifiedResponse:
        """Handle memory list query with fast path.

        :param query: User query
        :return: UnifiedResponse with memory list
        """
        start_time = time.time()

        try:
            from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper

            logger.info("⚡ FAST PATH: Handling memory list query")

            # Get appropriate agent for memory helper
            memory_agent = self._get_memory_agent()

            # Create memory helper and retrieve memories
            memory_helper = StreamlitMemoryHelper(memory_agent)
            content = memory_helper.list_all_memories()

            elapsed = time.time() - start_time
            logger.info(f"⚡ Memory list retrieved in {elapsed:.3f}s via fast path")

            return ResponseBuilder.memory_fast_path(content, elapsed)

        except Exception as e:
            elapsed = time.time() - start_time
            logger.warning(
                f"Memory fast path failed after {elapsed:.3f}s: {e}, "
                f"falling back to team inference"
            )

            # Graceful fallback to team inference
            return await self._handle_general_query(query)

    async def _handle_memory_search(self, query: str) -> UnifiedResponse:
        """Handle memory search query.

        :param query: User query
        :return: UnifiedResponse with search results
        """
        start_time = time.time()

        try:
            from personal_agent.tools.streamlit_helpers import StreamlitMemoryHelper

            logger.info("⚡ FAST PATH: Handling memory search query")

            memory_agent = self._get_memory_agent()
            memory_helper = StreamlitMemoryHelper(memory_agent)

            # Extract search terms from query
            # Simple heuristic: remove common phrases
            search_query = query.lower()
            for phrase in ["do you remember", "what do you know about", "search memories for"]:
                search_query = search_query.replace(phrase, "").strip()

            if not search_query:
                search_query = query

            # Search memories
            results = memory_helper.search_memories(search_query, limit=10)

            # Format results
            if results:
                content = f"🔍 Found {len(results)} memories matching '{search_query}':\n\n"
                for i, (memory, score) in enumerate(results, 1):
                    content += f"{i}. {memory.memory} (score: {score:.2f})\n"
            else:
                content = f"❌ No memories found matching '{search_query}'"

            elapsed = time.time() - start_time
            logger.info(f"⚡ Memory search completed in {elapsed:.3f}s via fast path")

            return ResponseBuilder.memory_search_fast_path(content, elapsed)

        except Exception as e:
            elapsed = time.time() - start_time
            logger.warning(
                f"Memory search fast path failed after {elapsed:.3f}s: {e}, "
                f"falling back to team inference"
            )

            # Graceful fallback to team inference
            return await self._handle_general_query(query)

    async def _handle_general_query(
        self,
        query: str,
        user_id: Optional[str] = None,
    ) -> UnifiedResponse:
        """Handle general query with full team inference.

        :param query: User query
        :param user_id: Optional user ID for team.arun
        :return: UnifiedResponse from team inference
        """
        start_time = time.time()

        try:
            logger.info("Running full team inference for query")

            # Check if agent has arun method (async) or run method (sync)
            if hasattr(self.agent, "arun"):
                # Async team method
                if user_id:
                    response_obj = await self.agent.arun(query, user_id=user_id)
                else:
                    response_obj = await self.agent.arun(query)
            else:
                # Fall back to sync method wrapped in executor
                loop = asyncio.get_event_loop()
                response_obj = await loop.run_in_executor(
                    None,
                    lambda: self.agent.run(query),
                )

            # Extract content from response
            content = (
                response_obj.content
                if hasattr(response_obj, "content")
                else str(response_obj)
            )

            # Extract messages if available
            messages = []
            if hasattr(response_obj, "messages"):
                messages = response_obj.messages

            elapsed = time.time() - start_time
            logger.info(f"Team inference completed in {elapsed:.3f}s")

            return ResponseBuilder.team_inference(content, elapsed, messages=messages)

        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Team inference failed after {elapsed:.3f}s: {e}", exc_info=True)

            return ResponseBuilder.error(
                f"Team inference failed: {str(e)}",
                e,
            )

    def _get_memory_agent(self):
        """Get the appropriate agent for memory operations.

        Handles both single agents and teams with multiple members.

        :return: Agent with memory capabilities
        """
        # If it's a team with members, get first member (usually memory agent)
        if hasattr(self.agent, "members") and self.agent.members:
            return self.agent.members[0]

        # Otherwise, return the agent itself
        return self.agent
