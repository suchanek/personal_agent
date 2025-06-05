"""Web-related tools for the Personal Agent using MCP."""

import json
import logging
from typing import TYPE_CHECKING

from agno.tools import tool

if TYPE_CHECKING:
    from ..core.mcp_client import SimpleMCPClient
    from ..core.memory import WeaviateVectorStore

# Get logger for this module
logger = logging.getLogger(__name__)

# These will be injected by the main module
USE_WEAVIATE = False
mcp_client: "SimpleMCPClient" = None
vector_store: "WeaviateVectorStore" = None
store_interaction = None


def _sanitize_github_output(result: str) -> str:
    """Sanitize GitHub search output to prevent agno parsing issues."""
    if not result:
        return result

    try:
        # If it's valid JSON, parse and summarize to prevent large output issues
        if result.strip().startswith("{") and result.strip().endswith("}"):
            parsed = json.loads(result)

            # Create a more concise summary for agno
            if isinstance(parsed, dict) and "items" in parsed:
                total_count = parsed.get("total_count", 0)
                items = parsed.get("items", [])

                summary = {"total_count": total_count, "found_repositories": []}

                # Track unique repositories to avoid duplicates
                seen_repos = set()

                # Limit to first 10 results to prevent output size issues
                for item in items[:10]:
                    # Extract repository information from various possible fields
                    repo_name = "Unknown"
                    repo_url = ""

                    # For issues/pull requests, extract repo from repository_url
                    if "repository_url" in item:
                        repo_api_url = item["repository_url"]
                        # Extract repo name from API URL like "https://api.github.com/repos/owner/repo"
                        if "/repos/" in repo_api_url:
                            repo_name = repo_api_url.split("/repos/")[-1]
                            repo_url = f"https://github.com/{repo_name}"

                    # Fallback: try to extract from html_url
                    elif "html_url" in item:
                        html_url = item["html_url"]
                        if "github.com/" in html_url:
                            # Extract repo from URLs like https://github.com/owner/repo/issues/123
                            parts = html_url.replace("https://github.com/", "").split(
                                "/"
                            )
                            if len(parts) >= 2:
                                repo_name = f"{parts[0]}/{parts[1]}"
                                repo_url = f"https://github.com/{repo_name}"

                    # For direct repository results
                    elif "full_name" in item:
                        repo_name = item["full_name"]
                        repo_url = item.get(
                            "html_url", f"https://github.com/{repo_name}"
                        )

                    # Avoid duplicate repositories
                    if repo_name != "Unknown" and repo_name not in seen_repos:
                        seen_repos.add(repo_name)

                        repo_info = {
                            "name": repo_name,
                            "description": (
                                item.get("description", "")[:200]
                                if item.get("description")
                                else ""
                            ),
                            "url": repo_url,
                            "stars": item.get("stargazers_count", 0),
                            "language": item.get("language", ""),
                            "updated": item.get("updated_at", ""),
                            "type": "issue" if "number" in item else "repository",
                        }
                        summary["found_repositories"].append(repo_info)

                # Return formatted summary instead of raw JSON
                result_text = f"Found {total_count} results"
                if seen_repos:
                    result_text += f" from {len(seen_repos)} repositories:\n\n"
                else:
                    result_text += ":\n\n"

                for repo in summary["found_repositories"]:
                    result_text += f"• {repo['name']}\n"
                    if repo["description"]:
                        result_text += f"  Description: {repo['description']}\n"
                    if repo["stars"]:
                        result_text += f"  Stars: {repo['stars']}\n"
                    if repo["language"]:
                        result_text += f"  Language: {repo['language']}\n"
                    result_text += f"  URL: {repo['url']}\n"
                    if repo["type"] == "issue":
                        result_text += f"  (Found via issues/PRs)\n"
                    result_text += "\n"

                return result_text.strip()

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        if logger:
            logger.debug("Could not parse GitHub result as JSON: %s", e)

    # Fallback: truncate if too long and remove problematic characters
    if len(result) > 10000:
        result = result[:10000] + "... (truncated)"

    # Remove or escape problematic characters that might confuse agno
    result = result.replace("\r\n", "\n").replace("\r", "\n")

    return result


@tool
def github_search(query: str, repo: str = "") -> str:
    """
    Search GitHub repositories or specific repo for code, issues, or documentation.

    Args:
        query: Search query terms
        repo: Optional specific repository to search within (format: owner/repo)

    Returns:
        str: Search results or error message
    """
    # Handle case where parameters might be JSON strings from agno
    if isinstance(query, str) and query.startswith("{"):
        try:
            params = json.loads(query)
            query = params.get("query", query)
            repo = params.get("repo", repo)
        except (json.JSONDecodeError, TypeError):
            pass

    # Get MCP client - try module variable first, then global import
    client = mcp_client
    if client is None:
        try:
            from .. import mcp_client as global_mcp_client

            client = global_mcp_client
        except ImportError:
            return "MCP client not available, cannot search GitHub."

    if client is None:
        return "MCP client not initialized, cannot search GitHub."

    try:
        server_name = "github"

        # Start GitHub server if not already running
        if server_name not in client.active_servers:
            start_result = client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP GitHub server. Make sure GITHUB_PERSONAL_ACCESS_TOKEN is set."

        # GitHub MCP server appears to only have search_issues and search_code tools
        # Use search_issues for general searches since it can find repositories too

        # Set parameters based on the search type
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
            # For code search, try search_code tool
            try:
                if repo:
                    params = {"q": f"repo:{repo} {query}"}
                else:
                    params = {"q": query}
                result = client.call_tool_sync(server_name, "search_code", params)
            except Exception:
                # Fallback to search_issues
                if repo:
                    params = {"q": f"repo:{repo} {query}"}
                else:
                    params = {"q": query}
                result = client.call_tool_sync(server_name, "search_issues", params)
        else:
            # For both issue search and repository search, use search_issues
            # GitHub's issue search can find repositories and issues
            if repo:
                params = {"q": f"repo:{repo} {query}"}
            else:
                params = {"q": query}
            result = client.call_tool_sync(server_name, "search_issues", params)

        # Sanitize the result to prevent agno parsing issues
        result = _sanitize_github_output(result)

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
def web_search(query: str, count: int = 5) -> str:
    """
    Search the web using Brave Search for research and technical information.

    Args:
        query: Search query terms
        count: Number of results to return (default: 5)

    Returns:
        str: Search results or error message
    """
    # Handle case where parameters might be JSON strings from agno
    if isinstance(query, str) and query.startswith("{"):
        try:
            params = json.loads(query)
            query = params.get("query", query)
            count = params.get("count", count)
        except (json.JSONDecodeError, TypeError):
            pass

    # Get MCP client - try module variable first, then global import
    client = mcp_client
    if client is None:
        try:
            from .. import mcp_client as global_mcp_client

            client = global_mcp_client
        except ImportError:
            return "MCP client not available, cannot search web."

    if client is None:
        return "MCP client not initialized, cannot search web."

    try:
        server_name = "brave-search"

        # Start Brave Search server if not already running
        if server_name not in client.active_servers:
            start_result = client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP Brave Search server. Make sure BRAVE_API_KEY is set."

        # Call Brave search tool
        result = client.call_tool_sync(
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
def fetch_url(url: str, method: str = "GET") -> str:
    """Fetch content from web URLs using MCP puppeteer server for browser automation.

    Args:
        url: The URL to fetch content from
        method: HTTP method to use (default: GET)

    Returns:
        str: Page content or error message
    """
    # Handle case where parameters might be JSON strings from agno
    if isinstance(url, str) and url.startswith("{"):
        try:
            params = json.loads(url)
            url = params.get("url", url)
            method = params.get("method", method)
        except (json.JSONDecodeError, TypeError):
            pass

    # Get MCP client - try module variable first, then global import
    client = mcp_client
    if client is None:
        try:
            from .. import mcp_client as global_mcp_client

            client = global_mcp_client
        except ImportError:
            return "MCP client not available, cannot fetch URLs."

    if client is None:
        return "MCP client not initialized, cannot fetch URLs."

    try:
        server_name = "puppeteer"

        # Start puppeteer server if not already running
        if server_name not in client.active_servers:
            start_result = client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP puppeteer server."

        # Call puppeteer goto tool to fetch page content
        result = client.call_tool_sync(server_name, "puppeteer_goto", {"url": url})

        # Store the fetch operation in memory for context
        if USE_WEAVIATE and vector_store is not None:
            interaction_text = f"Fetched URL: {url}\nContent preview: {result[:300]}..."
            store_interaction.invoke({"text": interaction_text, "topic": "web_fetch"})

        logger.info("Fetched URL: %s", url)
        return result

    except Exception as e:
        logger.error("Error fetching URL via MCP puppeteer: %s", str(e))
        return f"Error fetching URL: {str(e)}"
