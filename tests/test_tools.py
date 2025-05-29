#!/usr/bin/env python3
"""Test script to check if all tools are properly loaded."""

import sys

sys.path.append(".")

from personal_agent import (
    clear_knowledge_base,
    comprehensive_research,
    intelligent_file_search,
    mcp_brave_search,
    mcp_fetch_url,
    mcp_github_search,
    mcp_list_directory,
    mcp_read_file,
    mcp_shell_command,
    mcp_write_file,
    query_knowledge_base,
    store_interaction,
)


def main():
    print("Checking all tool functions...")

    tools = [
        store_interaction,
        query_knowledge_base,
        clear_knowledge_base,
        mcp_read_file,
        mcp_write_file,
        mcp_list_directory,
        intelligent_file_search,
        mcp_github_search,
        mcp_brave_search,
        mcp_shell_command,
        mcp_fetch_url,
        comprehensive_research,
    ]

    print(f"Total tools found: {len(tools)}")
    print("\nTool names and descriptions:")
    for i, tool in enumerate(tools, 1):
        print(f"{i:2d}. {tool.name}: {tool.description}")

    print("\nAll tools are properly loaded!")


if __name__ == "__main__":
    main()
