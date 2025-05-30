"""Web-related tools for the Personal Agent using MCP."""

import json
import subprocess
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
logger = None


@tool
def mcp_github_search(query: str, repo: str = "") -> str:
    """Search GitHub repositories or specific repo for code, issues, or documentation."""
    # Handle case where parameters might be JSON strings from LangChain
    if isinstance(query, str) and query.startswith("{"):
        try:
            params = json.loads(query)
            query = params.get("query", query)
            repo = params.get("repo", repo)
        except (json.JSONDecodeError, TypeError):
            pass

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot search GitHub."

    try:
        server_name = "github"

        # Start GitHub server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP GitHub server. Make sure GITHUB_PERSONAL_ACCESS_TOKEN is set."

        # Determine which search tool to use based on query characteristics
        tool_name = "search_repositories"  # Default
        params = {}

        # If searching within a specific repo, use search_code for code-specific queries
        if repo and any(
            keyword in query.lower()
            for keyword in [
                "language:",
                "def ",
                "class ",
                "function",
                "import ",
                "const ",
                "var ",
            ]
        ):
            tool_name = "search_code"
            # For search_code, we need to format the query differently
            if repo:
                params = {"q": f"repo:{repo} {query}"}
            else:
                params = {"q": query}
        elif any(
            keyword in query.lower()
            for keyword in ["issue", "bug", "feature", "pull request", "pr"]
        ):
            tool_name = "search_issues"
            if repo:
                params = {"q": f"repo:{repo} {query}"}
            else:
                params = {"q": query}
        else:
            # Default repository search
            if repo:
                params = {"query": f"repo:{repo} {query}"}
            else:
                params = {"query": query}

        logger.debug("Using GitHub tool: %s with params: %s", tool_name, params)

        # Call the appropriate GitHub search tool
        result = mcp_client.call_tool_sync(server_name, tool_name, params)

        # Store the GitHub search operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = (
                f"GitHub search: {query}"
                + (f" in {repo}" if repo else "")
                + f"\nResults: {result[:300]}..."
            )
            store_interaction.invoke(
                {"text": interaction_text, "topic": "github_search"}
            )

        logger.info("GitHub search completed: %s", query)
        return result

    except Exception as e:
        logger.error("Error searching GitHub via MCP: %s", str(e))
        return f"Error searching GitHub: {str(e)}"


@tool
def mcp_brave_search(query: str, count: int = 5) -> str:
    """Search the web using Brave Search for research and technical information."""
    # Handle case where parameters might be JSON strings from LangChain
    if isinstance(query, str) and query.startswith("{"):
        try:
            params = json.loads(query)
            query = params.get("query", query)
            count = params.get("count", count)
        except (json.JSONDecodeError, TypeError):
            pass

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot search web."

    try:
        server_name = "brave-search"

        # Start Brave Search server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP Brave Search server. Make sure BRAVE_API_KEY is set."

        # Call Brave search tool
        result = mcp_client.call_tool_sync(
            server_name, "brave_web_search", {"query": query, "count": count}
        )

        # Store the web search operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = (
                f"Web search: {query}\nResults preview: {result[:300]}..."
            )
            store_interaction.invoke({"text": interaction_text, "topic": "web_search"})

        logger.info("Web search completed: %s", query)
        return result

    except Exception as e:
        logger.error("Error searching web via MCP: %s", str(e))
        return f"Error searching web: {str(e)}"


@tool
def mcp_fetch_url(url: str, method: str = "GET") -> str:
    """Fetch content from web URLs using MCP puppeteer server for browser automation."""
    # Handle case where parameters might be JSON strings from LangChain
    if isinstance(url, str) and url.startswith("{"):
        try:
            params = json.loads(url)
            url = params.get("url", url)
            method = params.get("method", method)
        except (json.JSONDecodeError, TypeError):
            pass

    if not USE_MCP or mcp_client is None:
        return "MCP is disabled, cannot fetch URLs."

    try:
        server_name = "puppeteer"

        # Start puppeteer server if not already running
        if server_name not in mcp_client.active_servers:
            start_result = mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP puppeteer server."

        # Call puppeteer goto tool to fetch page content
        result = mcp_client.call_tool_sync(server_name, "puppeteer_goto", {"url": url})

        # Store the fetch operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = f"Fetched URL: {url}\nContent preview: {result[:300]}..."
            store_interaction.invoke({"text": interaction_text, "topic": "web_fetch"})

        logger.info("Fetched URL: %s", url)
        return result

    except Exception as e:
        logger.error("Error fetching URL via MCP puppeteer: %s", str(e))
        return f"Error fetching URL: {str(e)}"
