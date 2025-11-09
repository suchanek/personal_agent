#!/usr/bin/env python3
"""
Personal Agent Configuration Display Tool

This script provides a pretty-printed view of the personal agent's configuration
including environment variables, server settings, feature flags, and directory paths.

Usage:
    from personal_agent.tools.show_config import show_config
    show_config()

Options:
    show_config(no_color=False, json_output=False)

Last revision: 2025-10-15 00:05:13
Author: Eric G. Suchanek, PhD
License: Apache-2.0
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

# Import centralized configuration system
try:
    from ..config.mcp_servers import get_mcp_servers
    from ..config.runtime_config import get_config
except ImportError:
    # Fallback for direct execution
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent.parent
    src_dir = project_root / "src"
    sys.path.insert(0, str(src_dir))
    from personal_agent.config.mcp_servers import get_mcp_servers
    from personal_agent.config.runtime_config import get_config


def get_project_root():
    """Get the project root directory."""
    # This file is at src/personal_agent/tools/show_config.py
    # So we go up 3 levels to get to project root
    return Path(__file__).resolve().parent.parent.parent.parent


def get_package_version():
    """Retrieve package version from the package's __init__.py file.

    Returns:
        str: Package version string or 'unknown' if import fails
    """
    try:
        from personal_agent import __version__

        return __version__
    except ImportError:
        return "unknown"


def output_json():
    """Output configuration as JSON using centralized config system."""
    config = get_config()
    snapshot = config.snapshot()

    config_data = {
        "version": get_package_version(),
        "runtime_configuration": {
            "user_id": snapshot.user_id,
            "provider": snapshot.provider,
            "model": snapshot.model,
            "agent_mode": snapshot.agent_mode,
            "debug_mode": snapshot.debug_mode,
            "use_remote": snapshot.use_remote,
        },
        "docker_environment_variables": get_docker_env_variables(),
        "docker_environment_variables_by_server": get_docker_env_variables_by_server(),
        "server_configuration": {
            "lightrag_url": snapshot.lightrag_url,
            "lightrag_memory_url": snapshot.lightrag_memory_url,
            "ollama_url": snapshot.ollama_url,
            "remote_ollama_url": snapshot.remote_ollama_url,
            "lmstudio_url": snapshot.lmstudio_url,
            "remote_lmstudio_url": snapshot.remote_lmstudio_url,
            "openai_url": snapshot.openai_url,
        },
        "mcp_servers": get_mcp_servers(),
        "feature_flags": {
            "use_mcp": snapshot.use_mcp,
            "enable_memory": snapshot.enable_memory,
        },
        "directories": {
            "root_dir": snapshot.root_dir,
            "home_dir": snapshot.home_dir,
            "persag_env_home": snapshot.persag_home,
            "persag_data_root": snapshot.persag_root,
            "user_data_dir": snapshot.user_data_dir,
            "user_storage_dir": snapshot.user_storage_dir,
            "user_knowledge_dir": snapshot.user_knowledge_dir,
            "repo_dir": snapshot.repo_dir,
            "agno_storage_dir": snapshot.agno_storage_dir,
            "agno_knowledge_dir": snapshot.agno_knowledge_dir,
            "lightrag_storage_dir": snapshot.lightrag_storage_dir,
            "lightrag_inputs_dir": snapshot.lightrag_inputs_dir,
            "lightrag_memory_storage_dir": snapshot.lightrag_memory_storage_dir,
            "lightrag_memory_inputs_dir": snapshot.lightrag_memory_inputs_dir,
        },
        "ai_storage": {
            "storage_backend": snapshot.storage_backend,
            "llm_model": snapshot.model,
            "user_id": snapshot.user_id,
            "seed": snapshot.seed,
        },
        "ports": {
            "lightrag_port": snapshot.lightrag_port,
            "lightrag_memory_port": snapshot.lightrag_memory_port,
        },
        "agentic_tools": get_agentic_tools(),
        "docker_compose_summary": get_docker_compose_summary(),
        "current_user": snapshot.user_id,
    }

    return json.dumps(config_data, indent=2)


def load_env_file(env_path):
    """Load environment variables from a .env file."""
    env_vars = {}
    if env_path.exists():
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        # Remove quotes if present
                        value = value.strip("\"'")
                        env_vars[key] = value
        except Exception as e:
            print(f"Error reading {env_path}: {e}")
    return env_vars


def get_docker_env_variables_by_server():
    """Get environment variables from Docker env files organized by server."""
    config = get_config()
    snapshot = config.snapshot()
    persag_home = snapshot.persag_home

    servers = {
        "lightrag_server": {
            "env_file": Path(persag_home) / "lightrag_server" / "env.server",
            "mounted_env": Path(persag_home) / "lightrag_server" / ".env",
        },
        "lightrag_memory_server": {
            "env_file": Path(persag_home)
            / "lightrag_memory_server"
            / "env.memory_server",
            "mounted_env": Path(persag_home)
            / "lightrag_memory_server"
            / "env.memory_server",
        },
    }

    docker_vars_by_server = {}
    for server_name, files in servers.items():
        docker_vars_by_server[server_name] = {}

        # Load env_file variables
        if files["env_file"].exists():
            env_vars = load_env_file(files["env_file"])
            docker_vars_by_server[server_name]["env_file"] = {
                "path": str(files["env_file"]),
                "variables": env_vars,
            }

        # Load mounted .env variables
        if files["mounted_env"].exists():
            env_vars = load_env_file(files["mounted_env"])
            docker_vars_by_server[server_name]["mounted_env"] = {
                "path": str(files["mounted_env"]),
                "variables": env_vars,
            }

    return docker_vars_by_server


def get_docker_env_variables():
    """Get environment variables from Docker env files (flat structure for JSON)."""
    servers_data = get_docker_env_variables_by_server()
    all_docker_vars = {}

    for server_name, server_data in servers_data.items():
        for env_type, env_info in server_data.items():
            for key, value in env_info["variables"].items():
                prefixed_key = f"{server_name.upper()}_{env_type.upper()}_{key}"
                all_docker_vars[prefixed_key] = value

    return all_docker_vars


def get_docker_compose_summary():
    """Get a summary of the docker-compose configurations."""
    project_root = get_project_root()

    docker_compose_files = {
        "lightrag_server": project_root / "lightrag_server" / "docker-compose.yml",
        "lightrag_memory_server": project_root
        / "lightrag_memory_server"
        / "docker-compose.yml",
    }

    summary = {}
    for name, path in docker_compose_files.items():
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                try:
                    data = yaml.safe_load(f)
                    service_config = next(iter(data.get("services", {}).values()), {})
                    summary[name] = {
                        "image": service_config.get("image"),
                        "ports": service_config.get("ports"),
                        "volumes": service_config.get("volumes"),
                        "environment": service_config.get("environment"),
                    }
                except yaml.YAMLError as e:
                    summary[name] = {"error": f"Error parsing YAML: {e}"}
        else:
            summary[name] = {"error": "File not found"}

    return summary


def get_agentic_tools():
    """Get a comprehensive list of all agentic tools available in the system."""
    tools = {
        "built_in_agno_tools": {
            "description": "Built-in Agno framework tools",
            "tools": [
                {
                    "name": "DuckDuckGoTools",
                    "description": "Web search functionality using Google Search API",
                    "category": "web",
                },
                {
                    "name": "YFinanceTools",
                    "description": "Financial data and stock market information",
                    "category": "finance",
                    "features": [
                        "stock_price",
                        "company_info",
                        "stock_fundamentals",
                        "key_financial_ratios",
                        "analyst_recommendations",
                    ],
                },
                {
                    "name": "PythonTools",
                    "description": "Execute Python code and scripts",
                    "category": "development",
                },
            ],
        },
        "personal_agent_tools": {
            "description": "Custom Personal Agent tools implemented as Agno Toolkit classes",
            "tools": [
                {
                    "name": "PersonalAgentFilesystemTools",
                    "description": "File system operations with security controls",
                    "category": "filesystem",
                    "functions": [
                        "read_file - Read content from files",
                        "write_file - Write content to files",
                        "list_directory - List directory contents",
                        "create_and_save_file - Create new files with content",
                        "intelligent_file_search - Search files by name and content",
                    ],
                },
                {
                    "name": "PersonalAgentSystemTools",
                    "description": "System command execution with safety controls",
                    "category": "system",
                    "functions": ["shell_command - Execute shell commands safely"],
                },
            ],
        },
        "memory_tools": {
            "description": "Memory management tools for storing and retrieving user information",
            "tools": [
                {
                    "name": "store_user_memory",
                    "description": "Store information as user memory in both SQLite and LightRAG systems",
                    "category": "memory",
                },
                {
                    "name": "direct_search_memories",
                    "description": "Direct semantic search in local memory (bypasses agentic pipeline)",
                    "category": "memory",
                },
                {
                    "name": "query_memory",
                    "description": "Search user memories using semantic search",
                    "category": "memory",
                },
                {
                    "name": "update_memory",
                    "description": "Update existing memory content",
                    "category": "memory",
                },
                {
                    "name": "delete_memory",
                    "description": "Delete memory from both storage systems",
                    "category": "memory",
                },
                {
                    "name": "get_recent_memories",
                    "description": "Retrieve recent memories sorted by date",
                    "category": "memory",
                },
                {
                    "name": "get_all_memories",
                    "description": "Get all user memories",
                    "category": "memory",
                },
                {
                    "name": "get_memory_stats",
                    "description": "Get memory usage statistics",
                    "category": "memory",
                },
                {
                    "name": "get_memories_by_topic",
                    "description": "Filter memories by topic/category",
                    "category": "memory",
                },
                {
                    "name": "list_memories",
                    "description": "List all memories in simplified format",
                    "category": "memory",
                },
                {
                    "name": "store_graph_memory",
                    "description": "Store memory in LightRAG graph database for relationship capture (requires LIGHTRAG_MEMORY_URL)",
                    "category": "memory",
                },
                {
                    "name": "query_graph_memory",
                    "description": "Query LightRAG memory graph to explore relationships (requires LIGHTRAG_MEMORY_URL)",
                    "category": "memory",
                },
                {
                    "name": "get_memory_graph_labels",
                    "description": "Get entity and relation labels from memory graph (requires LIGHTRAG_MEMORY_URL)",
                    "category": "memory",
                },
                {
                    "name": "seed_entity_in_graph",
                    "description": "Seed an entity into the graph by uploading a synthetic document (requires LIGHTRAG_MEMORY_URL)",
                    "category": "memory",
                },
                {
                    "name": "check_entity_exists",
                    "description": "Check if an entity exists in the memory graph (requires LIGHTRAG_MEMORY_URL)",
                    "category": "memory",
                },
                {
                    "name": "delete_memories_by_topic",
                    "description": "Delete memories by topic/category",
                    "category": "memory",
                },
                {
                    "name": "clear_all_memories",
                    "description": "Clear all memories from both SQLite and LightRAG systems",
                    "category": "memory",
                },
            ],
        },
        "mcp_tools": {
            "description": "Model Context Protocol (MCP) server tools for external integrations",
            "tools": [],
        },
    }

    # Add MCP tools from configuration
    mcp_servers = get_mcp_servers()
    for server_name, config in mcp_servers.items():
        tools["mcp_tools"]["tools"].append(
            {
                "name": f"use_{server_name.replace('-', '_')}_server",
                "description": config.get(
                    "description", f"Access to {server_name} MCP server"
                ),
                "category": "mcp",
                "server": server_name,
                "command": config.get("command", ""),
                "args_count": len(config.get("args", [])),
                "env_vars": len(config.get("env", {})),
            }
        )

    return tools


def print_config_colored():
    """Print configuration with ANSI colors (fancy output) using centralized config."""
    # ANSI color codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    MAGENTA = "\033[95m"

    config = get_config()
    snapshot = config.snapshot()
    version = get_package_version()

    print(f"{CYAN}{BOLD}{'=' * 60}{RESET}")
    print(f"{CYAN}{BOLD}  Personal Agent Configuration Status{RESET}")
    print(f"{CYAN}{BOLD}  Version: {YELLOW}{version}{RESET}")
    print(f"{CYAN}{BOLD}{'=' * 60}{RESET}")

    # Runtime configuration status
    print(f"\n{BLUE}{BOLD}⚙️  Runtime Configuration:{RESET}")
    print(f"  {GREEN}✓{RESET} Using centralized configuration system")
    print(f"  {BOLD}Current User:{RESET} {CYAN}{snapshot.user_id}{RESET}")
    print(f"  {BOLD}Provider:{RESET} {CYAN}{snapshot.provider}{RESET}")
    print(f"  {BOLD}Model:{RESET} {CYAN}{snapshot.model}{RESET}")
    print(f"  {BOLD}Agent Mode:{RESET} {CYAN}{snapshot.agent_mode}{RESET}")
    print(
        f"  {BOLD}Debug Mode:{RESET} {GREEN}✓{RESET}"
        if snapshot.debug_mode
        else f"  {BOLD}Debug Mode:{RESET} {RED}✗{RESET}"
    )

    # Docker environment variables section organized by server
    docker_servers = get_docker_env_variables_by_server()
    if docker_servers:
        print(f"\n{BLUE}{BOLD}🐳 Docker Environment Variables by Server:{RESET}")
        for server_name, server_data in docker_servers.items():
            print(
                f"\n  {MAGENTA}{BOLD}📦 {server_name.replace('_', ' ').title()}:{RESET}"
            )

            for env_type, env_info in server_data.items():
                env_type_display = (
                    "Environment File"
                    if env_type == "env_file"
                    else "Mounted Environment"
                )
                print(
                    f"    {CYAN}{env_type_display}{RESET} ({YELLOW}{env_info['path']}{RESET}):"
                )

                if env_info["variables"]:
                    for key, value in sorted(env_info["variables"].items()):
                        # Mask sensitive values
                        display_value = value
                        if any(
                            sensitive in key.lower()
                            for sensitive in ["password", "secret", "key", "token"]
                        ):
                            display_value = (
                                f"{RED}{'*' * len(value) if value else ''}{RESET}"
                            )
                        else:
                            display_value = f"{GREEN}{value}{RESET}"
                        print(f"      {YELLOW}{key:<26}{RESET} {display_value}")
                else:
                    print(f"      {RED}(No variables found){RESET}")

    # Configuration sections
    sections = [
        {
            "title": f"{BLUE}{BOLD}🌐 Server Configuration{RESET}",
            "items": [
                ("LightRAG URL", snapshot.lightrag_url),
                ("LightRAG Memory URL", snapshot.lightrag_memory_url),
                ("Ollama URL", snapshot.ollama_url),
                ("Remote Ollama URL", snapshot.remote_ollama_url),
                ("LM Studio URL", snapshot.lmstudio_url),
                ("Remote LM Studio URL", snapshot.remote_lmstudio_url),
                ("OpenAI URL", snapshot.openai_url),
            ],
        },
        {
            "title": f"{BLUE}{BOLD}⚙️  Feature Flags{RESET}",
            "items": [
                (
                    "Use MCP",
                    f"{GREEN}✓{RESET}" if snapshot.use_mcp else f"{RED}✗{RESET}",
                ),
                (
                    "Enable Memory",
                    f"{GREEN}✓{RESET}" if snapshot.enable_memory else f"{RED}✗{RESET}",
                ),
                (
                    "Use Remote",
                    f"{GREEN}✓{RESET}" if snapshot.use_remote else f"{RED}✗{RESET}",
                ),
            ],
        },
        {
            "title": f"{BLUE}{BOLD}📂 Directory Configuration{RESET}",
            "items": [
                ("Root Directory", snapshot.root_dir),
                ("Home Directory", snapshot.home_dir),
                ("Persag Env Home", snapshot.persag_home),
                ("Persag Data Root", snapshot.persag_root),
                ("User Data Directory", snapshot.user_data_dir),
                ("User Storage Directory", snapshot.user_storage_dir),
                ("User Knowledge Directory", snapshot.user_knowledge_dir),
                ("Repository Directory", snapshot.repo_dir),
                ("Agno Storage Directory", snapshot.agno_storage_dir),
                ("Agno Knowledge Directory", snapshot.agno_knowledge_dir),
                ("LightRAG Storage Directory", snapshot.lightrag_storage_dir),
                ("LightRAG Inputs Directory", snapshot.lightrag_inputs_dir),
                (
                    "LightRAG Memory Storage Directory",
                    snapshot.lightrag_memory_storage_dir,
                ),
                (
                    "LightRAG Memory Inputs Directory",
                    snapshot.lightrag_memory_inputs_dir,
                ),
            ],
        },
        {
            "title": f"{BLUE}{BOLD}🤖 AI & Storage Configuration{RESET}",
            "items": [
                ("Storage Backend", snapshot.storage_backend),
                ("LLM Model", snapshot.model),
                ("User ID", snapshot.user_id),
                ("Random Seed", str(snapshot.seed) if snapshot.seed else "None"),
            ],
        },
        {
            "title": f"{BLUE}{BOLD}🔌 Ports{RESET}",
            "items": [
                ("LightRAG Port", snapshot.lightrag_port),
                ("LightRAG Memory Port", snapshot.lightrag_memory_port),
            ],
        },
    ]

    # MCP Servers section
    print(f"\n{BLUE}{BOLD}🔌 MCP Servers{RESET}:")
    mcp_servers = get_mcp_servers()
    if mcp_servers:
        print(f"  {BOLD}Server Name{' '*15}Description{RESET}")
        for name, config in mcp_servers.items():
            description = config.get("description", "No description available")
            print(f"  {YELLOW}{name:<25}{RESET} {GREEN}{description}{RESET}")
    else:
        print(f"  {RED}No MCP servers configured{RESET}")

    # Agentic Tools section
    print(f"\n{BLUE}{BOLD}🛠️ Agentic Tools{RESET}:")
    agentic_tools = get_agentic_tools()

    for category_name, category_info in agentic_tools.items():
        category_display = category_name.replace("_", " ").title()
        print(f"\n  {MAGENTA}{BOLD}📦 {category_display}:{RESET}")
        print(f"    {CYAN}{category_info['description']}{RESET}")

        if category_info["tools"]:
            for tool in category_info["tools"]:
                tool_name = tool["name"]
                tool_desc = tool["description"]
                tool_category = tool.get("category", "general")

                print(
                    f"    {YELLOW}• {tool_name}{RESET} ({GREEN}{tool_category}{RESET})"
                )
                print(f"      {tool_desc}")

                # Show additional details for specific tool types
                if "functions" in tool:
                    print(f"      {CYAN}Functions:{RESET}")
                    for func in tool["functions"]:
                        print(f"        - {func}")
                elif "features" in tool:
                    print(f"      {CYAN}Features:{RESET} {', '.join(tool['features'])}")
                elif "server" in tool:
                    print(
                        f"      {CYAN}Server:{RESET} {tool['server']} | {CYAN}Args:{RESET} {tool['args_count']} | {CYAN}Env:{RESET} {tool['env_vars']}"
                    )

                print()  # Empty line between tools
        else:
            print(f"    {RED}No tools available in this category{RESET}")

    for section in sections:
        print(f"\n{section['title']}:")
        print(f"  {BOLD}Setting{' '*22}Value{RESET}")
        for name, value in section["items"]:
            # Color the values based on type for better readability
            if isinstance(value, bool):
                colored_value = (
                    f"{GREEN}{value}{RESET}" if value else f"{RED}{value}{RESET}"
                )
            elif value and ("http://" in str(value) or "https://" in str(value)):
                colored_value = f"{CYAN}{value}{RESET}"
            elif value and str(value).startswith("/"):
                colored_value = f"{YELLOW}{value}{RESET}"
            else:
                colored_value = (
                    f"{GREEN}{value}{RESET}" if value else f"{RED}None{RESET}"
                )
            print(f"  {MAGENTA}{name:<30}{RESET} {colored_value}")

    # Docker Compose Summary
    docker_summary = get_docker_compose_summary()
    print(f"\n{CYAN}{BOLD}{'=' * 60}{RESET}")
    print(f"{CYAN}{BOLD}  Docker Compose Summary{RESET}")
    print(f"{CYAN}{BOLD}{'=' * 60}{RESET}")
    for name, config in docker_summary.items():
        print(f"\n{MAGENTA}{BOLD}🐳 {name}:{RESET}")
        if "error" in config:
            print(f"  {RED}Error: {config['error']}{RESET}")
            continue

        if config.get("image"):
            print(f"  {BLUE}Image:{RESET} {GREEN}{config['image']}{RESET}")
        if config.get("ports"):
            print(f"  {BLUE}Ports:{RESET} {YELLOW}{', '.join(config['ports'])}{RESET}")
        if config.get("volumes"):
            print(f"  {BLUE}Volumes:{RESET}")
            for v in config["volumes"]:
                print(f"    {CYAN}- {v}{RESET}")
        if config.get("environment"):
            print(f"  {BLUE}Environment:{RESET}")
            for e in config["environment"]:
                print(f"    {CYAN}- {e}{RESET}")

    # Footer
    print(f"\n{CYAN}{BOLD}{'=' * 60}{RESET}")
    print(f"{GREEN}{BOLD}Configuration loaded successfully!{RESET}")
    print(f"{CYAN}{BOLD}Current User: {YELLOW}{snapshot.user_id}{RESET}")
    print(f"{CYAN}{BOLD}{'=' * 60}{RESET}")


def print_config_no_color():
    """Print configuration without ANSI colors using centralized config."""
    config = get_config()
    snapshot = config.snapshot()
    version = get_package_version()

    print("=" * 60)
    print("  Personal Agent Configuration Status")
    print(f"  Version: {version}")
    print("=" * 60)

    # Runtime configuration status
    print("\n⚙️  Runtime Configuration:")
    print("  ✓ Using centralized configuration system")
    print(f"  Current User: {snapshot.user_id}")
    print(f"  Provider: {snapshot.provider}")
    print(f"  Model: {snapshot.model}")
    print(f"  Agent Mode: {snapshot.agent_mode}")
    print(f"  Debug Mode: {'✓' if snapshot.debug_mode else '✗'}")

    # Docker environment variables section organized by server
    docker_servers = get_docker_env_variables_by_server()
    if docker_servers:
        print("\n🐳 Docker Environment Variables by Server:")
        for server_name, server_data in docker_servers.items():
            print(f"\n  📦 {server_name.replace('_', ' ').title()}:")

            for env_type, env_info in server_data.items():
                env_type_display = (
                    "Environment File"
                    if env_type == "env_file"
                    else "Mounted Environment"
                )
                print(f"    {env_type_display} ({env_info['path']}):")

                if env_info["variables"]:
                    for key, value in sorted(env_info["variables"].items()):
                        # Mask sensitive values
                        display_value = value
                        if any(
                            sensitive in key.lower()
                            for sensitive in ["password", "secret", "key", "token"]
                        ):
                            display_value = "*" * len(value) if value else ""
                        print(f"      {key:<26} {display_value}")
                else:
                    print("      (No variables found)")

    # Configuration sections
    sections = [
        {
            "title": "🌐 Server Configuration",
            "items": [
                ("LightRAG URL", snapshot.lightrag_url),
                ("LightRAG Memory URL", snapshot.lightrag_memory_url),
                ("Ollama URL", snapshot.ollama_url),
                ("Remote Ollama URL", snapshot.remote_ollama_url),
                ("LM Studio URL", snapshot.lmstudio_url),
                ("Remote LM Studio URL", snapshot.remote_lmstudio_url),
                ("OpenAI URL", snapshot.openai_url),
            ],
        },
        {
            "title": "⚙️  Feature Flags",
            "items": [
                ("Use MCP", "✓" if snapshot.use_mcp else "✗"),
                ("Enable Memory", "✓" if snapshot.enable_memory else "✗"),
                ("Use Remote", "✓" if snapshot.use_remote else "✗"),
            ],
        },
        {
            "title": "📂 Directory Configuration",
            "items": [
                ("Root Directory", snapshot.root_dir),
                ("Home Directory", snapshot.home_dir),
                ("Persag Env Home", snapshot.persag_home),
                ("Persag Data Root", snapshot.persag_root),
                ("User Data Directory", snapshot.user_data_dir),
                ("User Storage Directory", snapshot.user_storage_dir),
                ("User Knowledge Directory", snapshot.user_knowledge_dir),
                ("Repository Directory", snapshot.repo_dir),
                ("Agno Storage Directory", snapshot.agno_storage_dir),
                ("Agno Knowledge Directory", snapshot.agno_knowledge_dir),
                ("LightRAG Storage Directory", snapshot.lightrag_storage_dir),
                ("LightRAG Inputs Directory", snapshot.lightrag_inputs_dir),
                (
                    "LightRAG Memory Storage Directory",
                    snapshot.lightrag_memory_storage_dir,
                ),
                (
                    "LightRAG Memory Inputs Directory",
                    snapshot.lightrag_memory_inputs_dir,
                ),
            ],
        },
        {
            "title": "🤖 AI & Storage Configuration",
            "items": [
                ("Storage Backend", snapshot.storage_backend),
                ("LLM Model", snapshot.model),
                ("User ID", snapshot.user_id),
                ("Random Seed", str(snapshot.seed) if snapshot.seed else "None"),
            ],
        },
        {
            "title": "🔌 Ports",
            "items": [
                ("LightRAG Port", snapshot.lightrag_port),
                ("LightRAG Memory Port", snapshot.lightrag_memory_port),
            ],
        },
    ]

    # MCP Servers section
    print("\n🔌 MCP Servers:")
    mcp_servers = get_mcp_servers()
    if mcp_servers:
        print(f"  Server Name{' '*15}Description")
        for name, config in mcp_servers.items():
            description = config.get("description", "No description available")
            print(f"  {name:<25} {description}")
    else:
        print("  No MCP servers configured")

    # Agentic Tools section
    print("\n🛠️ Agentic Tools:")
    agentic_tools = get_agentic_tools()

    for category_name, category_info in agentic_tools.items():
        category_display = category_name.replace("_", " ").title()
        print(f"\n  📦 {category_display}:")
        print(f"    {category_info['description']}")

        if category_info["tools"]:
            for tool in category_info["tools"]:
                tool_name = tool["name"]
                tool_desc = tool["description"]
                tool_category = tool.get("category", "general")

                print(f"    • {tool_name} ({tool_category})")
                print(f"      {tool_desc}")

                # Show additional details for specific tool types
                if "functions" in tool:
                    print("      Functions:")
                    for func in tool["functions"]:
                        print(f"        - {func}")
                elif "features" in tool:
                    print(f"      Features: {', '.join(tool['features'])}")
                elif "server" in tool:
                    print(
                        f"      Server: {tool['server']} | Args: {tool['args_count']} | Env: {tool['env_vars']}"
                    )

                print()  # Empty line between tools
        else:
            print("    No tools available in this category")

    for section in sections:
        print(f"\n{section['title']}:")
        print(f"  Setting{' '*22}Value")
        for name, value in section["items"]:
            print(f"  {name:<30} {value}")

    # Docker Compose Summary
    docker_summary = get_docker_compose_summary()
    print("\n" + "=" * 60)
    print("  Docker Compose Summary")
    print("=" * 60)
    for name, config in docker_summary.items():
        print(f"\n🐳 {name}:")
        if "error" in config:
            print(f"  Error: {config['error']}")
            continue

        if config.get("image"):
            print(f"  Image: {config['image']}")
        if config.get("ports"):
            print(f"  Ports: {', '.join(config['ports'])}")
        if config.get("volumes"):
            print("  Volumes:")
            for v in config["volumes"]:
                print(f"    - {v}")
        if config.get("environment"):
            print("  Environment:")
            for e in config["environment"]:
                print(f"    - {e}")

    # Footer
    print("\n" + "=" * 60)
    print("Configuration loaded successfully!")
    print(f"Current User: {snapshot.user_id}")
    print("=" * 60)


def show_config(no_color=False, json_output=False):
    """Main function to display configuration.

    Args:
        no_color (bool): If True, disable colored output
        json_output (bool): If True, output as JSON

    Returns:
        str: JSON string if json_output=True, otherwise None
    """
    try:
        if json_output:
            return output_json()
        elif no_color:
            print_config_no_color()
        else:
            # Default to colored fancy output
            print_config_colored()
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None


def main():
    """Main entry point for command line usage."""
    parser = argparse.ArgumentParser(
        description="Display Personal Agent configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "-v", "--version", action="version", version="Personal Agent Config Tool v1.0"
    )

    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    parser.add_argument(
        "--json", action="store_true", help="Output configuration as JSON"
    )

    args = parser.parse_args()

    result = show_config(no_color=args.no_color, json_output=args.json)
    if args.json and result:
        print(result)


if __name__ == "__main__":
    main()
