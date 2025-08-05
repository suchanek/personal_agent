"""
Agno agent initialization module.

This module handles the complex initialization logic for the Agno framework,
extracted from agno_main.py for better organization.
"""

import logging
import os
from typing import Optional, Tuple

from ..config import settings
from ..utils import inject_dependencies, setup_logging
from .agent_instruction_manager import InstructionLevel
from .agno_agent import AgnoPersonalAgent, create_agno_agent


async def initialize_agno_system(
    use_remote_ollama: bool = False,
    recreate: bool = False,
    instruction_level: str = "STANDARD",
) -> Tuple[AgnoPersonalAgent, callable, callable, callable, str]:
    """
    Initialize all system components for agno framework.

    :param use_remote_ollama: Whether to use the remote Ollama server instead of local
    :param recreate: Whether to recreate the knowledge base
    :return: Tuple of (agno_agent, query_kb_func, store_int_func, clear_kb_func, ollama_url)
    """
    from ..utils.pag_logging import configure_all_rich_logging
    from .agno_agent import create_agno_agent
    from .docker_integration import ensure_docker_user_consistency

    # Set up Rich logging for all components including agno
    configure_all_rich_logging()
    logger = setup_logging(level=settings.LOG_LEVEL)
    logger.info("Starting Personal AI Agent with agno framework...")

    # CRITICAL: Ensure Docker and user synchronization BEFORE any agent creation
    logger.info("🐳 Performing system-level Docker and user synchronization...")
    docker_ready, docker_message = ensure_docker_user_consistency(
        user_id=settings.get_userid(), auto_fix=True, force_restart=False
    )

    if docker_ready:
        logger.info("✅ Docker synchronization successful: %s", docker_message)
    else:
        logger.warning("⚠️ Docker synchronization failed: %s", docker_message)
        logger.warning(
            "Proceeding with agent initialization, but Docker services may be inconsistent"
        )

    # Update Ollama URL if requested
    ollama_url = settings.OLLAMA_URL
    if use_remote_ollama:
        ollama_url = settings.REMOTE_OLLAMA_URL
        os.environ["OLLAMA_URL"] = ollama_url
        logger.info("Using remote Ollama server at: %s", ollama_url)
    else:
        logger.info("Using local Ollama server at: %s", ollama_url)

    # Create agno agent with native storage
    logger.info("Creating agno agent with native storage...")

    # Convert string instruction level to enum
    try:
        instruction_level_enum = InstructionLevel[instruction_level.upper()]
        logger.info(f"Using instruction level: {instruction_level_enum.name}")
    except KeyError:
        logger.warning(
            f"Invalid instruction level '{instruction_level}', defaulting to STANDARD"
        )
        instruction_level_enum = InstructionLevel.STANDARD

    agno_agent = await create_agno_agent(
        model_provider=settings.PROVIDER,  # Use configured provider from .env
        model_name=settings.LLM_MODEL,  # Use configured model
        enable_memory=True,  # Enable native Agno memory
        enable_mcp=settings.USE_MCP,  # Use configured MCP setting
        storage_dir=settings.AGNO_STORAGE_DIR,  # Pass the user-specific path
        knowledge_dir=settings.AGNO_KNOWLEDGE_DIR,  # Pass the user-specific path
        debug=True,
        user_id=settings.get_userid(),
        ollama_base_url=ollama_url,  # Pass the selected Ollama URL
        recreate=recreate,
        instruction_level=instruction_level_enum,
    )

    agent_info = agno_agent.get_agent_info()
    logger.info(
        "Agno agent created successfully: %s servers, memory=%s",
        agent_info["mcp_servers"],
        agent_info["memory_enabled"],
    )

    # Legacy compatibility functions (Agno handles memory automatically)
    async def query_knowledge_base(query: str) -> str:
        """Query the knowledge base (legacy compatibility - not used)."""
        logger.info("Legacy memory function called - Agno handles this automatically")
        return "Memory is handled automatically by Agno"

    async def store_interaction(query: str, response: str) -> bool:
        """Store interaction (legacy compatibility - not used)."""
        logger.info("Legacy memory function called - Agno handles this automatically")
        return True

    async def clear_knowledge_base() -> bool:
        """Clear the knowledge base (legacy compatibility - not used)."""
        logger.info("Legacy memory function called - Agno handles this automatically")
        return True

    # Inject dependencies for cleanup (simplified for Agno)
    inject_dependencies(None, None, None, logger)

    return (
        agno_agent,
        query_knowledge_base,
        store_interaction,
        clear_knowledge_base,
        ollama_url,
    )
