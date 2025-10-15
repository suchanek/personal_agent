"""
Agno agent initialization module.

This module handles the complex initialization logic for the Agno framework,
extracted from agno_main.py for better organization.
"""

import logging
from typing import Optional, Tuple

from ..config.runtime_config import get_config
from ..config.user_id_mgr import get_userid
from ..utils import setup_logging
from .agent_instruction_manager import InstructionLevel
from .agno_agent import AgnoPersonalAgent


async def initialize_agno_system(
    use_remote_ollama: bool = False,
    recreate: bool = False,
    instruction_level: Optional[str] = None,
) -> Tuple[AgnoPersonalAgent, str]:
    """
    Initialize all system components for agno framework.

    :param use_remote_ollama: Whether to use the remote Ollama server instead of local
    :param recreate: Whether to recreate the knowledge base
    :param instruction_level: Instruction level override (None uses config default)
    :return: Tuple of (agno_agent, ollama_url)
    """
    from ..utils.pag_logging import configure_all_rich_logging
    from .agno_agent import create_agno_agent
    from .docker_integration import ensure_docker_user_consistency

    # Get global configuration
    config = get_config()

    # Set up Rich logging for all components including agno
    configure_all_rich_logging()
    logger = setup_logging(level=logging.INFO)  # Use standard logging level
    logger.info("Starting Personal AI Agent...")

    # CRITICAL: Ensure Docker and user synchronization BEFORE any agent creation
    logger.info("🐳 Performing system-level Docker and user synchronization...")
    docker_ready, docker_message = ensure_docker_user_consistency(
        user_id=get_userid(), auto_fix=True, force_restart=False
    )

    if docker_ready:
        logger.info("✅ Docker synchronization successful: %s", docker_message)
    else:
        logger.warning("⚠️ Docker synchronization failed: %s", docker_message)
        logger.warning(
            "Proceeding with agent initialization, but Docker services may be inconsistent"
        )

    # Update use_remote in config if requested
    if use_remote_ollama:
        config.set_use_remote(True)
        logger.info(
            "Using remote Ollama server at: %s", config.get_effective_ollama_url()
        )
    else:
        logger.info(
            "Using local Ollama server at: %s", config.get_effective_ollama_url()
        )

    # Get the effective Ollama URL from config
    ollama_url = config.get_effective_ollama_url()

    # Create agno agent with native storage
    logger.info("Creating agno agent with native storage...")

    # Use provided instruction level or fall back to config default
    effective_instruction_level = (
        instruction_level if instruction_level is not None else config.instruction_level
    )

    # Convert string instruction level to enum
    try:
        instruction_level_enum = InstructionLevel[effective_instruction_level.upper()]
        logger.info("Using instruction level: %s", instruction_level_enum.name)
    except KeyError:
        logger.warning(
            "Invalid instruction level '%s', defaulting to STANDARD",
            effective_instruction_level,
        )
        instruction_level_enum = InstructionLevel.STANDARD

    agno_agent = await create_agno_agent(
        model_provider=config.provider,  # Use configured provider
        model_name=config.model,  # Use configured model
        enable_memory=True,  # Enable native Agno memory
        enable_mcp=config.use_mcp,  # Use configured MCP setting
        storage_dir=config.agno_storage_dir,  # Pass the user-specific path
        knowledge_dir=config.agno_knowledge_dir,  # Pass the user-specific path
        debug=True,
        user_id=get_userid(),
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

    return (agno_agent, ollama_url)
