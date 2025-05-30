"""Research tools for the Personal Agent."""

import json
from typing import TYPE_CHECKING

from langchain.tools import tool

if TYPE_CHECKING:
    from ..core.mcp_client import SimpleMCPClient
    from ..core.memory import WeaviateVectorStore

# These will be injected by the main module
USE_MCP = False
USE_WEAVIATE = False
mcp_client: "SimpleMCPClient" = None
vector_store: "WeaviateVectorStore" = None
store_interaction = None
query_knowledge_base = None
mcp_brave_search = None
mcp_github_search = None
intelligent_file_search = None
logger = None
logger = None


@tool
def comprehensive_research(topic: str, max_results: int = 10) -> str:
    """Perform comprehensive research combining memory, web search, GitHub, and file operations."""
    # Handle case where parameters might be JSON strings from LangChain
    if isinstance(topic, str) and topic.startswith("{"):
        try:
            params = json.loads(topic)
            topic = params.get("topic", topic)
            max_results = params.get("max_results", max_results)
        except (json.JSONDecodeError, TypeError):
            pass

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot perform comprehensive research."

    try:
        research_results = []

        # 1. Search memory for existing knowledge
        if (
            USE_WEAVIATE
            and vector_store is not None
            and query_knowledge_base is not None
        ):
            memory_results = query_knowledge_base.invoke({"query": topic, "limit": 5})
            if memory_results and memory_results != ["No relevant context found."]:
                research_results.append("=== MEMORY CONTEXT ===")
                research_results.extend(memory_results)

        # 2. Web search for current information
        try:
            if mcp_brave_search is not None:
                web_results = mcp_brave_search.invoke(
                    {"query": topic, "count": min(5, max_results)}
                )
                research_results.append("=== WEB SEARCH RESULTS ===")
                research_results.append(web_results)
        except Exception as e:
            research_results.append(f"Web search failed: {str(e)}")

        # 3. GitHub search for code and technical documentation
        try:
            if mcp_github_search is not None:
                github_results = mcp_github_search.invoke({"query": topic})
                research_results.append("=== GITHUB SEARCH RESULTS ===")
                research_results.append(github_results)
        except Exception as e:
            research_results.append(f"GitHub search failed: {str(e)}")

        # 4. Search local files for relevant information
        try:
            if intelligent_file_search is not None:
                file_search_results = intelligent_file_search.invoke(
                    {"search_query": topic, "directory": "."}
                )
                research_results.append("=== LOCAL FILE SEARCH ===")
                research_results.append(file_search_results)
        except Exception as e:
            research_results.append(f"File search failed: {str(e)}")

        # Combine all results
        comprehensive_result = "\n\n".join(research_results)

        # Store the comprehensive research in memory
        if USE_WEAVIATE and vector_store is not None and store_interaction is not None:
            interaction_text = f"Comprehensive research on: {topic}\nSummary: Combined memory, web, GitHub, and file search results"
            store_interaction.invoke({"text": interaction_text, "topic": "research"})

            # Also store the research results for future reference
            store_interaction.invoke(
                {
                    "text": comprehensive_result[:2000],
                    "topic": f"research_{topic.replace(' ', '_')}",
                }
            )

        logger.info("Comprehensive research completed for: %s", topic)
        return comprehensive_result

    except Exception as e:
        logger.error("Error in comprehensive research: %s", str(e))
        return f"Error performing comprehensive research: {str(e)}"
