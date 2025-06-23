"""
Basic Memory Agent - A simplified version of AgnoPersonalAgent for team use.

This creates a basic memory agent with just the memory tools properly initialized,
following the working pattern from AgnoPersonalAgent.
"""

import asyncio
from textwrap import dedent
from typing import Any, Dict, List, Optional, Union

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat

from ..config import LLM_MODEL, OLLAMA_URL
from ..config.model_contexts import get_model_context_size_sync
from ..core.agno_storage import create_agno_memory
from ..utils import setup_logging

logger = setup_logging(__name__)


def create_basic_memory_agent(
    model_provider: str = "ollama",
    model_name: str = LLM_MODEL,
    ollama_base_url: str = OLLAMA_URL,
    storage_dir: str = "./data/agno",
    user_id: str = "default_user",
    debug: bool = False,
) -> Agent:
    """Create a basic memory agent with just memory tools.

    This follows the working pattern from AgnoPersonalAgent but simplified
    for use as a team member.

    :param model_provider: LLM provider ('ollama' or 'openai')
    :param model_name: Model name to use
    :param ollama_base_url: Base URL for Ollama API
    :param storage_dir: Directory for storage files
    :param user_id: User identifier for memory operations
    :param debug: Enable debug mode
    :return: Configured Agent instance with memory tools
    """
    logger.info("Creating basic memory agent with AgnoPersonalAgent pattern")

    # Create model
    if model_provider == "openai":
        model = OpenAIChat(id=model_name)
    elif model_provider == "ollama":
        # Get dynamic context size for this model
        context_size, detection_method = get_model_context_size_sync(
            model_name, ollama_base_url
        )

        logger.info(
            "Basic memory agent using context size %d for model %s (detected via: %s)",
            context_size,
            model_name,
            detection_method,
        )

        model = Ollama(
            id=model_name,
            host=ollama_base_url,
            options={
                "num_ctx": context_size,
                "temperature": 0.7,
            },
        )
    else:
        raise ValueError(f"Unsupported model provider: {model_provider}")

    # Create memory system
    agno_memory = create_agno_memory(storage_dir, debug_mode=debug)
    
    # Create memory tools following AgnoPersonalAgent pattern
    def create_memory_tools():
        """Create memory tools as native async functions."""
        tools = []

        async def store_user_memory(
            content: str, topics: Union[List[str], str, None] = None
        ) -> str:
            """Store information as a user memory."""
            try:
                import json
                from agno.memory.v2.memory import UserMemory

                if topics is None:
                    topics = ["general"]

                if isinstance(topics, str):
                    try:
                        topics = json.loads(topics)
                    except (json.JSONDecodeError, ValueError):
                        topics = [topics]

                if not isinstance(topics, list):
                    topics = [str(topics)]

                memory_obj = UserMemory(memory=content, topics=topics)
                memory_id = agno_memory.add_user_memory(
                    memory=memory_obj, user_id=user_id
                )

                if memory_id == "duplicate-detected-fake-id":
                    return f"✅ Memory already exists: {content[:50]}..."
                elif memory_id is None:
                    return f"❌ Error storing memory: {content[:50]}..."
                else:
                    return f"✅ Successfully stored memory: {content[:50]}... (ID: {memory_id})"

            except Exception as e:
                return f"❌ Error storing memory: {str(e)}"

        async def query_memory(query: str, limit: Union[int, None] = None) -> str:
            """Search user memories using semantic search."""
            try:
                if not query or not query.strip():
                    return "❌ Error: Query cannot be empty."

                all_memories = agno_memory.get_user_memories(user_id=user_id)
                if not all_memories:
                    return "🔍 No memories found - you haven't shared any information with me yet!"

                # Search through memories
                query_terms = query.strip().lower().split()
                matching_memories = []

                for memory in all_memories:
                    memory_content = getattr(memory, "memory", "").lower()
                    memory_topics = getattr(memory, "topics", [])
                    topic_text = " ".join(memory_topics).lower()

                    if any(
                        term in memory_content or term in topic_text
                        for term in query_terms
                    ):
                        matching_memories.append(memory)

                # Also try semantic search
                try:
                    semantic_memories = agno_memory.search_user_memories(
                        user_id=user_id,
                        query=query.strip(),
                        retrieval_method="agentic",
                        limit=20,
                    )
                    for sem_memory in semantic_memories:
                        if sem_memory not in matching_memories:
                            matching_memories.append(sem_memory)
                except Exception:
                    pass

                if not matching_memories:
                    return f"🔍 No memories found for '{query}' (searched through {len(all_memories)} total memories). Try different keywords!"

                if limit and len(matching_memories) > limit:
                    display_memories = matching_memories[:limit]
                    result_note = f"🧠 Found {len(matching_memories)} matches, showing top {limit}:"
                else:
                    display_memories = matching_memories
                    result_note = f"🧠 Found {len(matching_memories)} memories about '{query}':"

                result = f"{result_note}\n\n"
                for i, memory in enumerate(display_memories, 1):
                    result += f"{i}. {memory.memory}\n"
                    if memory.topics:
                        result += f"   Topics: {', '.join(memory.topics)}\n"
                    result += "\n"

                return result

            except Exception as e:
                return f"❌ Error searching memories: {str(e)}"

        async def get_recent_memories(limit: int = 10) -> str:
            """Get the most recent user memories."""
            try:
                memories = agno_memory.search_user_memories(
                    user_id=user_id, limit=limit, retrieval_method="last_n"
                )

                if not memories:
                    return "📝 No memories found - you haven't shared any information with me yet!"

                result = f"📝 Your most recent {len(memories)} memories:\n\n"
                for i, memory in enumerate(memories, 1):
                    result += f"{i}. {memory.memory}\n"
                    if memory.topics:
                        result += f"   Topics: {', '.join(memory.topics)}\n"
                    result += "\n"

                return result

            except Exception as e:
                return f"❌ Error getting recent memories: {str(e)}"

        # Set proper function names
        store_user_memory.__name__ = "store_user_memory"
        query_memory.__name__ = "query_memory"
        get_recent_memories.__name__ = "get_recent_memories"

        tools.extend([store_user_memory, query_memory, get_recent_memories])
        return tools

    # Get memory tools
    memory_tools = create_memory_tools()

    # Create agent instructions
    instructions = dedent(
        f"""\
        You are a warm, friendly personal AI assistant with memory capabilities.
        
        ## YOUR IDENTITY
        - You ARE the user's personal AI friend
        - You have direct access to memory tools to remember conversations
        - You should be conversational, warm, and genuinely interested in the user
        
        ## YOUR MEMORY TOOLS (use these directly):
        - store_user_memory(content, topics): Store new information about the user
        - query_memory(query): Search through stored memories about the user  
        - get_recent_memories(limit): Get the user's most recent memories
        
        ## BEHAVIOR RULES:
        1. **Memory Questions**: Use your memory tools DIRECTLY
           - "What do you remember about me?" → get_recent_memories()
           - "Do you know my preferences?" → query_memory("preferences")
           - Store new personal info with store_user_memory()
        
        2. **General Conversation**: Respond directly as a friendly AI
           - Be warm, conversational, and supportive
           - Reference memories to personalize responses
           - Ask follow-up questions to show interest
        
        ## CRITICAL: ALWAYS USE YOUR MEMORY TOOLS
        - When asked about memories, IMMEDIATELY use get_recent_memories() or query_memory()
        - When given new personal information, store it with store_user_memory()
        - You ARE the memory agent - use your tools directly
        """
    )

    # Create the agent
    agent = Agent(
        name="Basic Memory Agent",
        model=model,
        tools=memory_tools,
        instructions=instructions,
        markdown=True,
        show_tool_calls=debug,
        user_id=user_id,
    )

    logger.info("Created basic memory agent with %d memory tools", len(memory_tools))
    return agent
