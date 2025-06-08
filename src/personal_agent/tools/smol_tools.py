"""Smolagents-compatible tools wrapping MCP functionality."""

import json
import logging
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

from smolagents import tool
from weaviate.util import generate_uuid5

logger = logging.getLogger(__name__)

# Global references - will be set during initialization
_mcp_client = None
_weaviate_client = None
_vector_store = None

# Configuration flags
USE_WEAVIATE = False
USE_MCP = False


def set_mcp_client(client) -> None:
    """
    Set the global MCP client reference.

    :param client: MCP client instance
    """
    global _mcp_client, USE_MCP
    _mcp_client = client
    USE_MCP = client is not None


def set_memory_components(
    weaviate_client, vector_store, use_weaviate: bool = False
) -> None:
    """
    Set the global memory components.

    :param weaviate_client: Weaviate client instance
    :param vector_store: Vector store instance
    :param use_weaviate: Whether to use Weaviate functionality
    """
    global _weaviate_client, _vector_store, USE_WEAVIATE
    _weaviate_client = weaviate_client
    _vector_store = vector_store
    USE_WEAVIATE = use_weaviate


# MCP Filesystem Tools
@tool
def mcp_write_file(file_path: str, content: str) -> str:
    """
    Write content to a file via MCP filesystem server.

    Args:
        file_path: Path where to write the file
        content: Content to write to the file

    Returns:
        str: Success message or error description
    """
    if not _mcp_client:
        return "Error: MCP client not initialized"

    try:
        result = _mcp_client.call_tool_sync(
            "filesystem-data", "write_file", {"path": file_path, "content": content}
        )
        return result
    except Exception as e:
        logger.error("Error in mcp_write_file: %s", e)
        return f"Error writing file: {str(e)}"


@tool
def mcp_read_file(file_path: str) -> str:
    """
    Read content from a file via MCP filesystem server.

    Args:
        file_path: Path to the file to read

    Returns:
        str: File content or error description
    """
    if not _mcp_client:
        return "Error: MCP client not initialized"

    try:
        result = _mcp_client.call_tool_sync(
            "filesystem-data", "read_file", {"path": file_path}
        )
        return result
    except Exception as e:
        logger.error("Error in mcp_read_file: %s", e)
        return f"Error reading file: {str(e)}"


@tool
def mcp_list_directory(directory_path: str) -> str:
    """
    List contents of a directory via MCP filesystem server.

    Args:
        directory_path: Path to the directory to list

    Returns:
        str: Directory contents listing or error description
    """
    if not _mcp_client:
        return "Error: MCP client not initialized"

    try:
        result = _mcp_client.call_tool_sync(
            "filesystem-data", "list_directory", {"path": directory_path}
        )
        return result
    except Exception as e:
        logger.error("Error in mcp_list_directory: %s", e)
        return f"Error listing directory: {str(e)}"


@tool
def mcp_create_directory(directory_path: str) -> str:
    """
    Create a directory via MCP filesystem server.

    Args:
        directory_path: Path to the directory to create

    Returns:
        str: Success message or error description
    """
    if not _mcp_client:
        return "Error: MCP client not initialized"

    try:
        result = _mcp_client.call_tool_sync(
            "filesystem-data", "create_directory", {"path": directory_path}
        )
        return result
    except Exception as e:
        logger.error("Error in mcp_create_directory: %s", e)
        return f"Error creating directory: {str(e)}"


# Web Search Tools
@tool
def web_search(query: str, count: int = 5) -> str:
    """
    Search the web using Brave Search for research and technical information.

    Args:
        query: Search query
        count: Number of results to return (default 5)

    Returns:
        str: Search results or error description
    """
    if not _mcp_client:
        return "Error: MCP client not initialized"

    try:
        server_name = "brave-search"

        # Start Brave Search server if not already running
        if server_name not in _mcp_client.active_servers:
            start_result = _mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP Brave Search server. Make sure BRAVE_API_KEY is set."

        result = _mcp_client.call_tool_sync(
            server_name, "brave_web_search", {"query": query, "count": count}
        )

        # Store the web search operation in memory for context
        if USE_WEAVIATE and _vector_store is not None:
            interaction_text = f"Web search: {query}\nResults: {result[:300]}..."
            store_interaction(interaction_text, "web_search")

        logger.info("Web search completed: %s", query)
        return result

    except Exception as e:
        logger.error("Error in web_search: %s", e)
        return f"Error searching web: {str(e)}"


def _sanitize_github_output(result: str) -> str:
    """
    Sanitize GitHub search output to prevent parsing issues.

    :param result: Raw GitHub search result
    :return: Sanitized and formatted result
    """
    if not result:
        return result

    try:
        # If it's valid JSON, parse and summarize to prevent large output issues
        if result.strip().startswith("{") and result.strip().endswith("}"):
            parsed = json.loads(result)

            # Create a more concise summary
            if isinstance(parsed, dict) and "items" in parsed:
                total_count = parsed.get("total_count", 0)
                items = parsed.get("items", [])

                # Limit to first 5 results to prevent output size issues
                result_text = f"Found {total_count} repositories:\n\n"
                for item in items[:5]:
                    name = item.get("full_name", item.get("name", "Unknown"))
                    description = (
                        item.get("description", "")[:200]
                        if item.get("description")
                        else ""
                    )
                    url = item.get("html_url", item.get("url", ""))
                    stars = item.get("stargazers_count", 0)
                    language = item.get("language", "")

                    result_text += f"• {name}\n"
                    if description:
                        result_text += f"  Description: {description}\n"
                    if stars:
                        result_text += f"  Stars: {stars}\n"
                    if language:
                        result_text += f"  Language: {language}\n"
                    result_text += f"  URL: {url}\n\n"

                return result_text.strip()

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.debug(f"Could not parse GitHub result as JSON: {e}")

    # Fallback: truncate if too long
    if len(result) > 10000:
        result = result[:10000] + "... (truncated)"

    return result.replace("\r\n", "\n").replace("\r", "\n")


@tool
def github_search_repositories(query: str, repo: str = "") -> str:
    """
    Search GitHub repositories or get detailed repository information.

    This tool can:
    - Search for repositories globally
    - Get comprehensive information about a specific repository
    - Search within a specific repository for code, issues, or PRs

    Args:
        query: Search query or "info" for repository details
        repo: Optional specific repository in format "owner/repo"

    Returns:
        str: Search results or repository information
    """
    if not _mcp_client:
        return "Error: MCP client not initialized"

    try:
        server_name = "github"

        # Start GitHub server if not already running
        if server_name not in _mcp_client.active_servers:
            start_result = _mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP GitHub server. Make sure GITHUB_PERSONAL_ACCESS_TOKEN is set."

        # If query is "info" or similar, provide comprehensive repository info
        if repo and query.lower() in [
            "info",
            "information",
            "about",
            "details",
            "tell me about",
        ]:
            return _get_repository_info(server_name, repo)

        # Use the correct tools based on available MCP server capabilities
        if repo:
            # Search within specific repository
            if any(
                keyword in query.lower()
                for keyword in [
                    "code",
                    "function",
                    "class",
                    "import",
                    "def ",
                    "const ",
                    "var ",
                ]
            ):
                # Use search_code for code-specific queries
                result = _mcp_client.call_tool_sync(
                    server_name, "search_code", {"q": f"repo:{repo} {query}"}
                )
            elif any(
                keyword in query.lower()
                for keyword in ["issue", "bug", "feature", "pull request", "pr"]
            ):
                # Use search_issues for issue-related queries
                result = _mcp_client.call_tool_sync(
                    server_name, "search_issues", {"q": f"repo:{repo} {query}"}
                )
            else:
                # Default to repository search with repo filter
                result = _mcp_client.call_tool_sync(
                    server_name,
                    "search_repositories",
                    {"query": f"repo:{repo} {query}"},
                )
        else:
            # General repository search
            result = _mcp_client.call_tool_sync(
                server_name, "search_repositories", {"query": query}
            )

        # Sanitize the result
        result = _sanitize_github_output(result)

        # Store the GitHub search operation in memory for context
        if USE_WEAVIATE and _vector_store is not None:
            interaction_text = (
                f"GitHub search: {query}"
                + (f" in {repo}" if repo else "")
                + f"\nResults: {result[:300]}..."
            )
            store_interaction(interaction_text, "github_search")

        logger.info("GitHub search completed: %s", query)
        return result

    except Exception as e:
        logger.error("Error in github_search_repositories: %s", e)
        return f"Error searching GitHub: {str(e)}"


@tool
def github_repository_info(repository: str) -> str:
    """
    Get comprehensive information about a GitHub repository.

    This tool provides detailed information about a repository including:
    - Basic repository details from search
    - README content
    - Repository structure
    - Recent commits and activity

    Args:
        repository: Repository in format "owner/repo" (e.g., "microsoft/vscode")

    Returns:
        str: Comprehensive repository information
    """
    if not _mcp_client:
        return "Error: MCP client not initialized"

    try:
        server_name = "github"

        # Start GitHub server if not already running
        if server_name not in _mcp_client.active_servers:
            start_result = _mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP GitHub server. Make sure GITHUB_PERSONAL_ACCESS_TOKEN is set."

        return _get_repository_info(server_name, repository)

    except Exception as e:
        logger.error("Error in github_repository_info: %s", e)
        return f"Error getting repository info for {repository}: {str(e)}"


def _get_repository_info(server_name: str, repository: str) -> str:
    """
    Get comprehensive information about a GitHub repository.

    :param server_name: MCP server name
    :param repository: Repository in format "owner/repo"
    :return: Comprehensive repository information
    """
    try:
        # Parse repository
        if "/" not in repository:
            return "Error: Repository must be in format 'owner/repo'"

        owner, repo = repository.split("/", 1)
        info_parts = []

        # 1. Get repository search results for basic info
        try:
            search_result = _mcp_client.call_tool_sync(
                server_name, "search_repositories", {"query": f"repo:{repository}"}
            )
            info_parts.append(f"## Repository Info\n{search_result}\n")
        except Exception as e:
            info_parts.append(f"⚠️ Could not get repository info: {e}\n")

        # 2. Get README content
        try:
            readme_result = _mcp_client.call_tool_sync(
                server_name,
                "get_file_contents",
                {"owner": owner, "repo": repo, "path": "README.md"},
            )
            info_parts.append(f"## README\n{readme_result}\n")
        except Exception:
            # Try other README formats
            for readme_name in ["readme.md", "README.rst", "readme.txt", "README"]:
                try:
                    readme_result = _mcp_client.call_tool_sync(
                        server_name,
                        "get_file_contents",
                        {"owner": owner, "repo": repo, "path": readme_name},
                    )
                    info_parts.append(f"## README ({readme_name})\n{readme_result}\n")
                    break
                except:
                    continue
            else:
                info_parts.append("⚠️ No README file found\n")

        # 3. Get root directory structure
        try:
            root_contents = _mcp_client.call_tool_sync(
                server_name,
                "get_file_contents",
                {"owner": owner, "repo": repo, "path": ""},
            )
            info_parts.append(f"## Repository Structure\n{root_contents}\n")
        except Exception as e:
            info_parts.append(f"⚠️ Could not get repository structure: {e}\n")

        # 4. Get recent commits (optional, for activity info)
        try:
            commits_result = _mcp_client.call_tool_sync(
                server_name,
                "list_commits",
                {"owner": owner, "repo": repo, "perPage": 5},
            )
            info_parts.append(f"## Recent Activity\n{commits_result}\n")
        except Exception:
            # Don't fail if commits can't be retrieved
            pass

        return "\n".join(info_parts)

    except Exception as e:
        return f"Error getting repository info: {str(e)}"


# Memory Tools
@tool
def store_interaction(text: str, topic: str = "general") -> str:
    """
    Store user interaction in Weaviate vector database.

    Args:
        text: Text content to store
        topic: Topic category for the interaction

    Returns:
        str: Success message or error description
    """
    if not USE_WEAVIATE or _vector_store is None:
        logger.warning("Weaviate is disabled, interaction not stored.")
        return "Weaviate is disabled, interaction not stored."

    try:
        # Format timestamp as RFC3339 (with 'Z' for UTC)
        timestamp = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        _vector_store.add_texts(
            texts=[text],
            metadatas=[{"timestamp": timestamp, "topic": topic}],
            ids=[generate_uuid5(text)],
        )
        logger.info("Stored interaction: %s...", text[:50])
        return "Interaction stored successfully."
    except Exception as e:
        logger.error("Error storing interaction: %s", str(e))
        return f"Error storing interaction: {str(e)}"


@tool
def query_knowledge_base(query: str, limit: int = 5) -> str:
    """
    Query Weaviate for relevant context from stored interactions.

    Args:
        query: Search query
        limit: Maximum number of results to return

    Returns:
        str: Relevant context or error description
    """
    if not USE_WEAVIATE or _vector_store is None:
        logger.warning("Weaviate is disabled, no context available.")
        return "Weaviate is disabled, no context available."

    try:
        results = _vector_store.similarity_search(query, k=limit)
        context_list = []
        for doc in results:
            metadata = doc.metadata if hasattr(doc, "metadata") else {}
            timestamp = metadata.get("timestamp", "unknown")
            topic = metadata.get("topic", "general")
            context_list.append(f"[{timestamp}] [{topic}] {doc.page_content}")

        logger.info("Found %d relevant items for query: %s", len(context_list), query)
        return "\n".join(context_list) if context_list else "No relevant context found."
    except Exception as e:
        logger.error("Error querying knowledge base: %s", str(e))
        return f"Error querying knowledge base: {str(e)}"


@tool
def clear_knowledge_base() -> str:
    """
    Clear all data from Weaviate vector database.

    Returns:
        str: Success message or error description
    """
    if not USE_WEAVIATE or _weaviate_client is None:
        logger.warning("Weaviate is disabled, cannot clear.")
        return "Weaviate is disabled, cannot clear."

    try:
        collection_name = "UserKnowledgeBase"
        if _weaviate_client.collections.exists(collection_name):
            collection = _weaviate_client.collections.get(collection_name)
            collection.data.delete_many({})
            logger.info("Cleared all data from Weaviate")
            return "Successfully cleared all data from knowledge base."
        else:
            logger.warning("Collection %s does not exist", collection_name)
            return "Collection does not exist."
    except Exception as e:
        logger.error("Error clearing knowledge base: %s", str(e))
        return f"Error clearing knowledge base: {str(e)}"


# System Tools
@tool
def shell_command(command: str, timeout: int = 30) -> str:
    """
    Execute shell commands safely using subprocess.

    Args:
        command: Shell command to execute
        timeout: Timeout in seconds (default 30)

    Returns:
        str: Command output including return code, stdout, and stderr
    """
    try:
        # Use subprocess for safe shell command execution
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        output = f"Command: {command}\nReturn code: {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}"

        # Store the shell command operation in memory for context
        if USE_WEAVIATE and _vector_store is not None:
            interaction_text = f"Shell command: {command}\nOutput: {output[:300]}..."
            store_interaction(interaction_text, "shell_commands")

        logger.info("Shell command executed: %s", command)
        return output

    except subprocess.TimeoutExpired:
        error_msg = f"Command timed out after {timeout} seconds"
        logger.error("Shell command timeout: %s", command)
        return error_msg
    except Exception as e:
        logger.error("Error executing shell command: %s", str(e))
        return f"Error executing shell command: {str(e)}"


# Research Tools
@tool
def comprehensive_research(topic: str, max_results: int = 10) -> str:
    """
    Perform comprehensive research combining memory, web search, GitHub, and file operations.

    Args:
        topic: Research topic
        max_results: Maximum number of results per search type

    Returns:
        str: Comprehensive research results
    """
    if not USE_MCP or _mcp_client is None:
        return "MCP is disabled, cannot perform comprehensive research."

    try:
        research_results = []

        # 1. Search memory for existing knowledge
        if USE_WEAVIATE and _vector_store is not None:
            memory_results = query_knowledge_base(topic, 5)
            if memory_results and memory_results != "No relevant context found.":
                research_results.append("=== MEMORY CONTEXT ===")
                research_results.append(memory_results)

        # 2. Web search for current information
        try:
            web_results = web_search(topic, min(5, max_results))
            research_results.append("=== WEB SEARCH RESULTS ===")
            research_results.append(web_results)
        except Exception as e:
            research_results.append(f"Web search failed: {str(e)}")

        # 3. GitHub search for code and technical documentation
        try:
            github_results = github_search_repositories(topic)
            research_results.append("=== GITHUB SEARCH RESULTS ===")
            research_results.append(github_results)
        except Exception as e:
            research_results.append(f"GitHub search failed: {str(e)}")

        # 4. Search local files for relevant information
        try:
            file_search_results = mcp_list_directory(".")
            research_results.append("=== LOCAL FILE SEARCH ===")
            research_results.append(file_search_results)
        except Exception as e:
            research_results.append(f"File search failed: {str(e)}")

        # Combine all results
        comprehensive_result = "\n\n".join(research_results)

        # Store the comprehensive research in memory
        if USE_WEAVIATE and _vector_store is not None:
            interaction_text = f"Comprehensive research on: {topic}\nSummary: Combined memory, web, GitHub, and file search results"
            store_interaction(interaction_text, "research")

            # Also store the research results for future reference
            store_interaction(
                comprehensive_result[:2000],  # Truncate to avoid too large storage
                f"research_{topic.replace(' ', '_')}",
            )

        logger.info("Comprehensive research completed for: %s", topic)
        return comprehensive_result

    except Exception as e:
        logger.error("Error in comprehensive_research: %s", str(e))
        return f"Error performing comprehensive research: {str(e)}"


# Additional Web Tools
@tool
def intelligent_file_search(search_query: str, directory: str = ".") -> str:
    """
    Search for files containing specific content or patterns.

    Args:
        search_query: Text or pattern to search for
        directory: Directory to search in (default current directory)

    Returns:
        str: Search results showing matching files and content
    """
    try:
        # List directory contents first
        dir_contents = mcp_list_directory(directory)

        # For now, return directory listing as basic file search
        # Could be extended to search file contents using grep or similar
        result = f"File search in {directory} for '{search_query}':\n\n{dir_contents}"

        # Store the file search operation in memory
        if USE_WEAVIATE and _vector_store is not None:
            interaction_text = f"File search: {search_query} in {directory}\nResults: {result[:300]}..."
            store_interaction(interaction_text, "file_search")

        return result

    except Exception as e:
        logger.error("Error in intelligent_file_search: %s", str(e))
        return f"Error searching files: {str(e)}"


# List of all tools for easy import
ALL_TOOLS = [
    mcp_write_file,
    mcp_read_file,
    mcp_list_directory,
    mcp_create_directory,
    web_search,
    github_search_repositories,
    github_repository_info,
    store_interaction,
    query_knowledge_base,
    clear_knowledge_base,
    shell_command,
    comprehensive_research,
    intelligent_file_search,
]
