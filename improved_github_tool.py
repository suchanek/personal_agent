#!/usr/bin/env python3
"""
Improved GitHub tool that properly uses available MCP server tools.
Based on the debug results showing 26 available tools.
"""

from smolagents import tool


@tool
def github_repository_info(repository: str) -> str:
    """
    Get comprehensive information about a GitHub repository.

    This tool provides detailed information about a repository including:
    - Basic repository details from search
    - README content
    - Recent commits and activity
    - Issues and pull requests

    Args:
        repository: Repository in format "owner/repo" (e.g., "microsoft/vscode")

    Returns:
        str: Comprehensive repository information
    """
    if not _mcp_client:
        return "Error: MCP client not initialized"

    try:
        # Parse repository
        if "/" not in repository:
            return "Error: Repository must be in format 'owner/repo'"

        owner, repo = repository.split("/", 1)

        # Start GitHub server if not already running
        server_name = "github"
        if server_name not in _mcp_client.active_servers:
            start_result = _mcp_client.start_server_sync(server_name)
            if not start_result:
                return "Failed to start MCP GitHub server. Make sure GITHUB_PERSONAL_ACCESS_TOKEN is set."

        info_parts = []

        # 1. Get repository search results for basic info
        try:
            search_result = _mcp_client.call_tool_sync(
                server_name, "search_repositories", {"query": f"repo:{repository}"}
            )
            info_parts.append(f"## Repository Search Results\n{search_result}\n")
        except Exception as e:
            info_parts.append(f"⚠️ Could not get repository search info: {e}\n")

        # 2. Get README content
        try:
            readme_result = _mcp_client.call_tool_sync(
                server_name,
                "get_file_contents",
                {"owner": owner, "repo": repo, "path": "README.md"},
            )
            info_parts.append(f"## README Content\n{readme_result}\n")
        except Exception as e:
            # Try other common README formats
            for readme_name in ["readme.md", "README.rst", "readme.txt", "README"]:
                try:
                    readme_result = _mcp_client.call_tool_sync(
                        server_name,
                        "get_file_contents",
                        {"owner": owner, "repo": repo, "path": readme_name},
                    )
                    info_parts.append(
                        f"## README Content ({readme_name})\n{readme_result}\n"
                    )
                    break
                except:
                    continue
            else:
                info_parts.append("⚠️ No README file found\n")

        # 3. Get recent commits
        try:
            commits_result = _mcp_client.call_tool_sync(
                server_name,
                "list_commits",
                {"owner": owner, "repo": repo, "perPage": 10},
            )
            info_parts.append(f"## Recent Commits\n{commits_result}\n")
        except Exception as e:
            info_parts.append(f"⚠️ Could not get recent commits: {e}\n")

        # 4. Get recent issues
        try:
            issues_result = _mcp_client.call_tool_sync(
                server_name,
                "list_issues",
                {"owner": owner, "repo": repo, "per_page": 5, "state": "open"},
            )
            info_parts.append(f"## Recent Open Issues\n{issues_result}\n")
        except Exception as e:
            info_parts.append(f"⚠️ Could not get issues: {e}\n")

        # 5. Get recent pull requests
        try:
            prs_result = _mcp_client.call_tool_sync(
                server_name,
                "list_pull_requests",
                {"owner": owner, "repo": repo, "per_page": 5, "state": "open"},
            )
            info_parts.append(f"## Recent Open Pull Requests\n{prs_result}\n")
        except Exception as e:
            info_parts.append(f"⚠️ Could not get pull requests: {e}\n")

        # 6. Get root directory structure
        try:
            root_contents = _mcp_client.call_tool_sync(
                server_name,
                "get_file_contents",
                {"owner": owner, "repo": repo, "path": ""},
            )
            info_parts.append(f"## Repository Structure\n{root_contents}\n")
        except Exception as e:
            info_parts.append(f"⚠️ Could not get repository structure: {e}\n")

        # 7. Try to get package.json, setup.py, or other config files
        config_files = [
            "package.json",
            "setup.py",
            "pyproject.toml",
            "Cargo.toml",
            "go.mod",
        ]
        for config_file in config_files:
            try:
                config_result = _mcp_client.call_tool_sync(
                    server_name,
                    "get_file_contents",
                    {"owner": owner, "repo": repo, "path": config_file},
                )
                info_parts.append(f"## {config_file}\n{config_result}\n")
                break  # Only get the first config file found
            except:
                continue

        return "\n".join(info_parts)

    except Exception as e:
        return f"Error getting repository info for {repository}: {str(e)}"


@tool
def github_search_repositories(query: str, repo: str = "") -> str:
    """
    Search GitHub repositories using the correct available tools.

    Args:
        query: Search query
        repo: Optional specific repository to search within

    Returns:
        str: Search results or error description
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

        # Use the correct tools based on what's actually available
        if repo:
            # If specific repo provided, search within that repo
            if any(
                keyword in query.lower()
                for keyword in ["code", "function", "class", "import"]
            ):
                # Use search_code for code-specific queries
                result = _mcp_client.call_tool_sync(
                    server_name, "search_code", {"q": f"repo:{repo} {query}"}
                )
            elif any(
                keyword in query.lower()
                for keyword in ["issue", "bug", "feature", "pull request"]
            ):
                # Use search_issues for issue-related queries
                result = _mcp_client.call_tool_sync(
                    server_name, "search_issues", {"q": f"repo:{repo} {query}"}
                )
            else:
                # Default to repository search
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

        return result

    except Exception as e:
        return f"Error searching GitHub: {str(e)}"


# Global MCP client reference (will be set by the system)
_mcp_client = None


def set_mcp_client(client):
    """Set the global MCP client."""
    global _mcp_client
    _mcp_client = client


if __name__ == "__main__":
    # Example usage
    print("This is an improved GitHub tool based on available MCP server capabilities")
    print("Available tools:")
    print("1. github_repository_info(repository) - Get comprehensive info about a repo")
    print(
        "2. github_search_repositories(query, repo='') - Search repositories or within a repo"
    )
