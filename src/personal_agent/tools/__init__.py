"""Tools package for Personal Agent."""

from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from langchain.tools import BaseTool

from .filesystem import (
    create_and_save_file,
    intelligent_file_search,
    mcp_list_directory,
    mcp_read_file,
    mcp_write_file,
)
from .memory_tools import (
    clear_knowledge_base,
    create_memory_tools,
    query_knowledge_base,
    store_interaction,
)
from .knowledge_ingestion_tools import KnowledgeIngestionTools
from .knowledge_tools import KnowledgeTools
from .lightrag_document_manager import LightRAGDocumentManager
from .memory_cleaner import MemoryClearingManager
from .research import comprehensive_research
from .show_config import show_config
from .system import mcp_shell_command
from .web import mcp_brave_search, mcp_fetch_url, mcp_github_search

__all__ = [
    # Memory tools
    "store_interaction",
    "query_knowledge_base",
    "clear_knowledge_base",
    "create_memory_tools",
    # Knowledge ingestion tools
    "KnowledgeIngestionTools",
    # Knowledge tools
    "KnowledgeTools",
    # Filesystem tools
    "mcp_read_file",
    "mcp_write_file",
    "mcp_list_directory",
    "intelligent_file_search",
    "create_and_save_file",
    # Web tools
    "mcp_github_search",
    "mcp_brave_search",
    "mcp_fetch_url",
    # System tools
    "mcp_shell_command",
    # Research tools
    "comprehensive_research",
    # Document management tools
    "LightRAGDocumentManager",
    # Memory management tools
    "MemoryClearingManager",
    # Configuration tools
    "show_config",
    # Tool collection
    "get_all_tools",
]


def get_all_tools(
    mcp_client: Optional[object] = None,
    weaviate_client: Optional[object] = None,
    vector_store: Optional[object] = None,
    logger: Optional[object] = None,
) -> List["BaseTool"]:
    """
    Get all available tools with injected dependencies.

    Args:
        mcp_client: MCP client for file operations and external tools
        weaviate_client: Weaviate client for vector operations
        vector_store: Vector store for knowledge base operations
        logger: Logger instance for tool operations

    Returns:
        List of initialized tools
    """
    tools = []

    # Import tools modules and inject dependencies
    from ..config import DATA_DIR, ROOT_DIR
    from . import filesystem, memory_tools, research, system, web

    # Inject global dependencies into each module that needs them
    if mcp_client:
        filesystem.mcp_client = mcp_client
        filesystem.USE_MCP = True
        filesystem.ROOT_DIR = ROOT_DIR
        filesystem.DATA_DIR = DATA_DIR

        web.mcp_client = mcp_client
        web.USE_MCP = True

        system.mcp_client = mcp_client
        system.USE_MCP = True

        research.mcp_client = mcp_client
        research.USE_MCP = True

    # Inject logger into all modules
    if logger:
        filesystem.logger = logger
        web.logger = logger
        system.logger = logger
        research.logger = logger
        memory_tools.logger = logger

    if weaviate_client and vector_store:
        memory_tools.weaviate_client = weaviate_client
        memory_tools.vector_store = vector_store
        memory_tools.USE_WEAVIATE = True

        # Inject Weaviate dependencies into other modules
        filesystem.vector_store = vector_store
        filesystem.USE_WEAVIATE = True
        filesystem.store_interaction = memory_tools.store_interaction

        web.vector_store = vector_store
        web.USE_WEAVIATE = True
        web.store_interaction = memory_tools.store_interaction

        system.vector_store = vector_store
        system.USE_WEAVIATE = True
        system.store_interaction = memory_tools.store_interaction

        research.vector_store = vector_store
        research.USE_WEAVIATE = True
        research.store_interaction = memory_tools.store_interaction

    # Memory tools (require Weaviate)
    if weaviate_client and vector_store:
        memory_tools_list = create_memory_tools(weaviate_client, vector_store)
        tools.extend(memory_tools_list)

    # MCP-based tools (require MCP client)
    if mcp_client:
        tools.extend(
            [
                # Filesystem tools
                filesystem.mcp_read_file,
                filesystem.mcp_write_file,
                filesystem.mcp_list_directory,
                filesystem.intelligent_file_search,
                filesystem.create_and_save_file,
                # Web tools
                web.mcp_github_search,
                web.mcp_brave_search,
                web.mcp_fetch_url,
                # System tools
                system.mcp_shell_command,
                # Research tools
                research.comprehensive_research,
            ]
        )

    return tools
