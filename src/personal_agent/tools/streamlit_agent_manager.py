"""
Streamlit Agent Manager
=======================

This module handles agent and team initialization and management for the
Personal Agent Streamlit application.

It provides functions to create, configure, and manage both single agents
and multi-agent teams.
"""

import asyncio
import logging
import os

from personal_agent.config import AGNO_KNOWLEDGE_DIR, AGNO_STORAGE_DIR, USER_DATA_DIR
from personal_agent.core.agno_agent import AgnoPersonalAgent
from personal_agent.team.reasoning_team import create_team as create_personal_agent_team

logger = logging.getLogger(__name__)


async def initialize_agent_async(recreate: bool = False):
    """Initialize AgnoPersonalAgent using the central configuration.

    Args:
        recreate (bool): Flag to recreate knowledge bases.

    Returns:
        An initialized AgnoPersonalAgent instance.
    """
    # The agent's provider, model, user_id, etc., are now read directly from
    # the get_config() singleton within the agent's constructor.
    return await AgnoPersonalAgent.create_with_init(recreate=recreate)


def initialize_agent(recreate: bool = False):
    """Sync wrapper for agent initialization."""
    # The UI or CLI is responsible for setting the config state before this is called.
    # For example: `get_config().set_model("new-model-name")`
    logger.info("Initializing agent based on central configuration...")
    return asyncio.run(initialize_agent_async(recreate=recreate))


def _run_async_team_init(coro):
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


def initialize_team(recreate: bool = False):
    """Initialize the team using the central configuration."""
    try:
        from personal_agent.tools.streamlit_config import args

        logger.info("Initializing team based on central configuration...")

        # The create_personal_agent_team function now reads directly from the
        # get_config() singleton, so we no longer need to pass model, provider, etc.
        team = _run_async_team_init(
            create_personal_agent_team(use_remote=args.remote, single=args.single)
        )

        if not team or not hasattr(team, "members") or not team.members:
            logger.error("Team creation failed or resulted in an empty team.")
            st.error("❌ Team creation failed.")
            return None

        logger.info(f"Team created successfully with {len(team.members)} members")

        # The knowledge agent (first member) should have the memory system.
        knowledge_agent = team.members[0]
        if hasattr(knowledge_agent, "agno_memory"):
            team.agno_memory = knowledge_agent.agno_memory
            logger.info("Exposed knowledge agent's memory to team object.")
        else:
            logger.error("Knowledge agent lacks 'agno_memory', memory features will fail.")

        logger.info("Team initialization completed successfully")
        return team

    except Exception as e:
        logger.error(f"Exception during team initialization: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        import streamlit as st
        st.error(f"❌ Failed to initialize team: {str(e)}")
        return None


def create_team_wrapper(team):
    """Create a wrapper that makes the team look like an agent for the helpers."""

    class TeamWrapper:
        def __init__(self, team):
            from personal_agent.config import get_current_user_id

            self.team = team
            self.user_id = get_current_user_id()
            # Force initialization of the knowledge agent first
            self._force_knowledge_agent_init()
            # Now get memory and tools after initialization
            self.agno_memory = self._get_team_memory()
            self.memory_tools = self._get_memory_tools()

            # Add memory_manager attribute for StreamlitMemoryHelper compatibility
            self.memory_manager = self._create_memory_manager_wrapper()

            # Add debugging info
            logger.info(f"TeamWrapper initialized:")
            logger.info(f"  - Team available: {self.team is not None}")
            logger.info(f"  - Team members: {len(getattr(self.team, 'members', []))}")
            logger.info(f"  - Memory available: {self.agno_memory is not None}")
            logger.info(f"  - Memory tools available: {self.memory_tools is not None}")
            logger.info(
                f"  - Memory manager wrapper: {self.memory_manager is not None}"
            )

        def _force_knowledge_agent_init(self):
            """Force initialization of the knowledge agent (first team member)."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                logger.info(f"Knowledge agent type: {type(knowledge_agent).__name__}")
                # Force initialization if not already done
                if hasattr(knowledge_agent, "_ensure_initialized"):
                    try:
                        self._run_async_safely(knowledge_agent._ensure_initialized())
                        logger.info("Knowledge agent initialized successfully")
                    except Exception as e:
                        logger.error(f"Failed to initialize knowledge agent: {e}")
                else:
                    logger.warning("Knowledge agent has no _ensure_initialized method")
            else:
                logger.error("No team members available for initialization")

        def _get_team_memory(self):
            """Get memory system from the knowledge agent in the team."""
            if hasattr(self.team, "members") and self.team.members:
                # The first member should be the knowledge agent (PersonalAgnoAgent)
                knowledge_agent = self.team.members[0]
                logger.info(
                    f"Getting memory from knowledge agent: {type(knowledge_agent).__name__}"
                )

                if hasattr(knowledge_agent, "agno_memory"):
                    logger.info("Found agno_memory on knowledge agent")
                    return knowledge_agent.agno_memory
                elif hasattr(knowledge_agent, "memory"):
                    logger.info("Found memory on knowledge agent")
                    return knowledge_agent.memory
                else:
                    logger.warning("No memory found on knowledge agent")

            # Fallback: check if team has direct memory access
            team_memory = getattr(self.team, "agno_memory", None)
            if team_memory:
                logger.info("Found memory on team directly")
            else:
                logger.warning("No memory found on team")
            return team_memory

        def _get_memory_tools(self):
            """Get memory tools from the knowledge agent in the team."""
            if hasattr(self.team, "members") and self.team.members:
                # The first member should be the knowledge agent (PersonalAgnoAgent)
                knowledge_agent = self.team.members[0]
                logger.info(
                    f"Getting memory tools from knowledge agent: {type(knowledge_agent).__name__}"
                )

                if hasattr(knowledge_agent, "memory_tools"):
                    logger.info("Found memory_tools on knowledge agent")
                    return knowledge_agent.memory_tools
                else:
                    logger.warning("No memory_tools found on knowledge agent")
                    # Try to get tools from the agent's tools list
                    if hasattr(knowledge_agent, "agent") and hasattr(
                        knowledge_agent.agent, "tools"
                    ):
                        for tool in knowledge_agent.agent.tools:
                            if hasattr(
                                tool, "__class__"
                            ) and "PersagMemoryTools" in str(tool.__class__):
                                logger.info("Found PersagMemoryTools in agent tools")
                                return tool
                        logger.warning("No PersagMemoryTools found in agent tools")
            else:
                logger.error("No team members available for memory tools")
            return None

        def _ensure_initialized(self):
            """Ensure the knowledge agent is initialized."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "_ensure_initialized"):
                    return knowledge_agent._ensure_initialized()
            return None

        def _create_memory_manager_wrapper(self):
            """Create a memory manager wrapper for StreamlitMemoryHelper compatibility."""
            if self.agno_memory:
                # Create a wrapper that exposes the agno_memory for StreamlitMemoryHelper
                class MemoryManagerWrapper:
                    def __init__(self, agno_memory):
                        self.agno_memory = agno_memory

                return MemoryManagerWrapper(self.agno_memory)
            return None

        def store_user_memory(self, content, topics=None):
            # Use the knowledge agent (first team member) for memory storage with fact restating
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[
                    0
                ]  # First member is the knowledge agent
                if hasattr(knowledge_agent, "store_user_memory"):
                    # This will properly restate facts and process them through the LLM
                    # The knowledge agent now properly handles delta_year through the fixed memory_functions.py
                    return self._run_async_safely(
                        knowledge_agent.store_user_memory(
                            content=content, topics=topics
                        )
                    )

            raise Exception(
                "Team memory not available - knowledge agent not properly initialized"
            )

        # Helper method to safely run async functions in Streamlit environment
        def _run_async_safely(self, coro):
            """Safely run async coroutines in Streamlit environment."""
            try:
                # Try to get the current event loop
                loop = asyncio.get_running_loop()
                # If we're in a running loop, create a new thread to run the coroutine
                import concurrent.futures
                import threading

                def run_in_thread():
                    # Create a new event loop for this thread
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(coro)
                    finally:
                        new_loop.close()

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result(timeout=30)  # 30 second timeout

            except RuntimeError:
                # No running event loop, safe to use asyncio.run()
                return asyncio.run(coro)

        # Expose all memory functions from the knowledge agent
        def list_all_memories(self):
            """List all memories using the knowledge agent."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "list_all_memories"):
                    return self._run_async_safely(knowledge_agent.list_all_memories())
            raise Exception("Team memory not available")

        def query_memory(self, query, limit=None):
            """Query memories using the knowledge agent."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "query_memory"):
                    return self._run_async_safely(
                        knowledge_agent.query_memory(query, limit)
                    )
            raise Exception("Team memory not available")

        def update_memory(self, memory_id, content, topics=None):
            """Update a memory using the knowledge agent."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "update_memory"):
                    return self._run_async_safely(
                        knowledge_agent.update_memory(memory_id, content, topics)
                    )
            raise Exception("Team memory not available")

        def delete_memory(self, memory_id):
            """Delete a memory using the knowledge agent."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "delete_memory"):
                    return self._run_async_safely(
                        knowledge_agent.delete_memory(memory_id)
                    )
            raise Exception("Team memory not available")

        def get_recent_memories(self, limit=10):
            """Get recent memories using the knowledge agent."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "get_recent_memories"):
                    return self._run_async_safely(
                        knowledge_agent.get_recent_memories(limit)
                    )
            raise Exception("Team memory not available")

        def get_all_memories(self):
            """Get all memories using the knowledge agent."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "get_all_memories"):
                    return self._run_async_safely(knowledge_agent.get_all_memories())
            raise Exception("Team memory not available")

        def get_memory_stats(self):
            """Get memory statistics using the knowledge agent."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "get_memory_stats"):
                    return self._run_async_safely(knowledge_agent.get_memory_stats())
            raise Exception("Team memory not available")

        def get_memories_by_topic(self, topics=None, limit=None):
            """Get memories by topic using the knowledge agent."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "get_memories_by_topic"):
                    return self._run_async_safely(
                        knowledge_agent.get_memories_by_topic(topics, limit)
                    )
            raise Exception("Team memory not available")

        def delete_memories_by_topic(self, topics):
            """Delete memories by topic using the knowledge agent."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "delete_memories_by_topic"):
                    return self._run_async_safely(
                        knowledge_agent.delete_memories_by_topic(topics)
                    )
            raise Exception("Team memory not available")

        def get_memory_graph_labels(self):
            """Get memory graph labels using the knowledge agent."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "get_memory_graph_labels"):
                    return self._run_async_safely(
                        knowledge_agent.get_memory_graph_labels()
                    )
            raise Exception("Team memory not available")

        def clear_all_memories(self):
            """Clear all memories using the knowledge agent."""
            if hasattr(self.team, "members") and self.team.members:
                knowledge_agent = self.team.members[0]
                if hasattr(knowledge_agent, "clear_all_memories"):
                    return self._run_async_safely(knowledge_agent.clear_all_memories())
            raise Exception("Team memory not available")

    return TeamWrapper(team)
