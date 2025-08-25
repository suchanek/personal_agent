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
"""

import sys
import json
import argparse
from pathlib import Path
import yaml

# Import settings from the config module
try:
    from ..config import settings, get_userid
    from ..config.mcp_servers import get_mcp_servers
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent.parent
    src_dir = project_root / "src"
    sys.path.insert(0, str(src_dir))
    from personal_agent.config import settings, get_userid, get_mcp_servers


def get_project_root():
    """Get the project root directory."""
    # This file is at src/personal_agent/tools/show_config.py
    # So we go up 3 levels to get to project root
    return Path(__file__).resolve().parent.parent.parent.parent


def output_json():
    """Output configuration as JSON."""
    project_root = get_project_root()
    
    config_data = {
        "version": settings.get_package_version(),
        "environment_file": {
            "loaded": settings.dotenv_loaded,
            "path": str(settings.dotenv_path)
        },
        "environment_variables": dict(settings._env_vars) if settings._env_vars else {},
        "docker_environment_variables": get_docker_env_variables(),
        "docker_environment_variables_by_server": get_docker_env_variables_by_server(),
        "server_configuration": {
            "lightrag_url": settings.LIGHTRAG_URL,
            "lightrag_memory_url": settings.LIGHTRAG_MEMORY_URL,
            "weaviate_url": settings.WEAVIATE_URL,
            "ollama_url": settings.OLLAMA_URL,
            "remote_ollama_url": settings.REMOTE_OLLAMA_URL,
        },
        "mcp_servers": get_mcp_servers(),
        "feature_flags": {
            "use_weaviate": settings.USE_WEAVIATE,
            "use_mcp": settings.USE_MCP,
            "show_splash_screen": settings.SHOW_SPLASH_SCREEN,
        },
        "directories": {
            "root_dir": settings.ROOT_DIR,
            "home_dir": settings.HOME_DIR,
            "persag_env_home": settings.PERSAG_HOME,
            "persag_data_root": settings.PERSAG_ROOT,
            "user_data_dir": settings.USER_DATA_DIR,
            "repo_dir": settings.REPO_DIR,
            "lightrag_server_dir": settings.LIGHTRAG_SERVER_DIR,
            "lightrag_memory_dir": settings.LIGHTRAG_MEMORY_DIR,
            "agno_storage_dir": settings.AGNO_STORAGE_DIR,
            "agno_knowledge_dir": settings.AGNO_KNOWLEDGE_DIR,
            "lightrag_storage_dir": settings.LIGHTRAG_STORAGE_DIR,
            "lightrag_inputs_dir": settings.LIGHTRAG_INPUTS_DIR,
            "lightrag_memory_storage_dir": settings.LIGHTRAG_MEMORY_STORAGE_DIR,
            "lightrag_memory_inputs_dir": settings.LIGHTRAG_MEMORY_INPUTS_DIR,
        },
        "ai_storage": {
            "storage_backend": settings.STORAGE_BACKEND,
            "llm_model": settings.LLM_MODEL,
            "user_id": get_userid(),
            "log_level": settings.LOG_LEVEL_STR,
        },
        "agentic_tools": get_agentic_tools(),
        "docker_compose_summary": get_docker_compose_summary(),
        "current_user": get_userid()
    }
    
    return json.dumps(config_data, indent=2)


def load_env_file(env_path):
    """Load environment variables from a .env file."""
    env_vars = {}
    if env_path.exists():
        try:
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        # Remove quotes if present
                        value = value.strip('"\'')
                        env_vars[key] = value
        except Exception as e:
            print(f"Error reading {env_path}: {e}")
    return env_vars


def get_docker_env_variables_by_server():
    """Get environment variables from Docker env files organized by server."""
    persag_home = settings.PERSAG_HOME
    
    servers = {
        "lightrag_server": {
            "env_file": Path(persag_home) / "lightrag_server" / "env.server",
            "mounted_env": Path(persag_home) / "lightrag_server" / ".env"
        },
        "lightrag_memory_server": {
            "env_file": Path(persag_home) / ".env",
            "mounted_env": Path(persag_home) / "lightrag_memory_server" / "env.memory_server"
        }
    }
    
    docker_vars_by_server = {}
    for server_name, files in servers.items():
        docker_vars_by_server[server_name] = {}
        
        # Load env_file variables
        if files["env_file"].exists():
            env_vars = load_env_file(files["env_file"])
            docker_vars_by_server[server_name]["env_file"] = {
                "path": str(files["env_file"]),
                "variables": env_vars
            }
        
        # Load mounted .env variables
        if files["mounted_env"].exists():
            env_vars = load_env_file(files["mounted_env"])
            docker_vars_by_server[server_name]["mounted_env"] = {
                "path": str(files["mounted_env"]),
                "variables": env_vars
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
        "lightrag_memory_server": project_root / "lightrag_memory_server" / "docker-compose.yml",
    }
    
    summary = {}
    for name, path in docker_compose_files.items():
        if path.exists():
            with open(path, 'r') as f:
                try:
                    data = yaml.safe_load(f)
                    service_config = next(iter(data.get('services', {}).values()), {})
                    summary[name] = {
                        "image": service_config.get('image'),
                        "ports": service_config.get('ports'),
                        "volumes": service_config.get('volumes'),
                        "environment": service_config.get('environment'),
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
                    "name": "GoogleSearchTools",
                    "description": "Web search functionality using Google Search API",
                    "category": "web"
                },
                {
                    "name": "YFinanceTools", 
                    "description": "Financial data and stock market information",
                    "category": "finance",
                    "features": ["stock_price", "company_info", "stock_fundamentals", "key_financial_ratios", "analyst_recommendations"]
                },
                {
                    "name": "PythonTools",
                    "description": "Execute Python code and scripts",
                    "category": "development"
                }
            ]
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
                        "intelligent_file_search - Search files by name and content"
                    ]
                },
                {
                    "name": "PersonalAgentSystemTools", 
                    "description": "System command execution with safety controls",
                    "category": "system",
                    "functions": [
                        "shell_command - Execute shell commands safely"
                    ]
                }
            ]
        },
        "memory_tools": {
            "description": "Memory management tools for storing and retrieving user information",
            "tools": [
                {
                    "name": "store_user_memory",
                    "description": "Store information as user memory in both SQLite and LightRAG systems",
                    "category": "memory"
                },
                {
                    "name": "direct_search_memories",
                    "description": "Direct semantic search in local memory (bypasses agentic pipeline)",
                    "category": "memory"
                },
                {
                    "name": "query_memory",
                    "description": "Search user memories using semantic search",
                    "category": "memory"
                },
                {
                    "name": "update_memory",
                    "description": "Update existing memory content",
                    "category": "memory"
                },
                {
                    "name": "delete_memory",
                    "description": "Delete memory from both storage systems",
                    "category": "memory"
                },
                {
                    "name": "get_recent_memories",
                    "description": "Retrieve recent memories sorted by date",
                    "category": "memory"
                },
                {
                    "name": "get_all_memories",
                    "description": "Get all user memories",
                    "category": "memory"
                },
                {
                    "name": "get_memory_stats",
                    "description": "Get memory usage statistics",
                    "category": "memory"
                },
                {
                    "name": "get_memories_by_topic",
                    "description": "Filter memories by topic/category",
                    "category": "memory"
                },
                {
                    "name": "list_memories",
                    "description": "List all memories in simplified format",
                    "category": "memory"
                },
                {
                    "name": "store_graph_memory",
                    "description": "Store memory in LightRAG graph database for relationship capture (requires LIGHTRAG_MEMORY_URL)",
                    "category": "memory"
                },
                {
                    "name": "query_graph_memory",
                    "description": "Query LightRAG memory graph to explore relationships (requires LIGHTRAG_MEMORY_URL)",
                    "category": "memory"
                },
                {
                    "name": "get_memory_graph_labels",
                    "description": "Get entity and relation labels from memory graph (requires LIGHTRAG_MEMORY_URL)",
                    "category": "memory"
                },
                {
                    "name": "seed_entity_in_graph",
                    "description": "Seed an entity into the graph by uploading a synthetic document (requires LIGHTRAG_MEMORY_URL)",
                    "category": "memory"
                },
                {
                    "name": "check_entity_exists",
                    "description": "Check if an entity exists in the memory graph (requires LIGHTRAG_MEMORY_URL)",
                    "category": "memory"
                },
                {
                    "name": "delete_memories_by_topic",
                    "description": "Delete memories by topic/category",
                    "category": "memory"
                },
                {
                    "name": "clear_all_memories",
                    "description": "Clear all memories from both SQLite and LightRAG systems",
                    "category": "memory"
                }
            ]
        },
        "mcp_tools": {
            "description": "Model Context Protocol (MCP) server tools for external integrations",
            "tools": []
        }
    }
    
    # Add MCP tools from configuration
    mcp_servers = get_mcp_servers()
    for server_name, config in mcp_servers.items():
        tools["mcp_tools"]["tools"].append({
            "name": f"use_{server_name.replace('-', '_')}_server",
            "description": config.get("description", f"Access to {server_name} MCP server"),
            "category": "mcp",
            "server": server_name,
            "command": config.get("command", ""),
            "args_count": len(config.get("args", [])),
            "env_vars": len(config.get("env", {}))
        })
    
    return tools


def print_config_colored():
    """Print configuration with ANSI colors (fancy output)."""
    # ANSI color codes
    RESET = '\033[0m'
    BOLD = '\033[1m'
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    MAGENTA = '\033[95m'
    
    version = settings.get_package_version()
    print(f"{CYAN}{BOLD}{'=' * 60}{RESET}")
    print(f"{CYAN}{BOLD}  Personal Agent Configuration Status{RESET}")
    print(f"{CYAN}{BOLD}  Version: {YELLOW}{version}{RESET}")
    print(f"{CYAN}{BOLD}{'=' * 60}{RESET}")
    
    # Environment file status
    print(f"\n{BLUE}{BOLD}📁 Environment File Status:{RESET}")
    if settings.dotenv_loaded:
        print(f"  {GREEN}✓{RESET} Successfully loaded .env from: {CYAN}{settings.dotenv_path}{RESET}")
    else:
        print(f"  {RED}✗{RESET} Failed to load .env file")
    
    # Environment variables section
    if settings._env_vars:
        print(f"\n{BLUE}{BOLD}🔧 Main Environment Variables (.env):{RESET}")
        print(f"  {BOLD}Variable{' '*20}Value{RESET}")
        for key, value in sorted(settings._env_vars.items()):
            # Mask sensitive values
            display_value = value
            if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                display_value = f"{RED}{'*' * len(value) if value else ''}{RESET}"
            else:
                display_value = f"{GREEN}{value}{RESET}"
            print(f"  {YELLOW}{key:<28}{RESET} {display_value}")
    
    # Docker environment variables section organized by server
    docker_servers = get_docker_env_variables_by_server()
    if docker_servers:
        print(f"\n{BLUE}{BOLD}🐳 Docker Environment Variables by Server:{RESET}")
        for server_name, server_data in docker_servers.items():
            print(f"\n  {MAGENTA}{BOLD}📦 {server_name.replace('_', ' ').title()}:{RESET}")
            
            for env_type, env_info in server_data.items():
                env_type_display = "Environment File" if env_type == "env_file" else "Mounted Environment"
                print(f"    {CYAN}{env_type_display}{RESET} ({YELLOW}{env_info['path']}{RESET}):")
                
                if env_info['variables']:
                    for key, value in sorted(env_info['variables'].items()):
                        # Mask sensitive values
                        display_value = value
                        if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                            display_value = f"{RED}{'*' * len(value) if value else ''}{RESET}"
                        else:
                            display_value = f"{GREEN}{value}{RESET}"
                        print(f"      {YELLOW}{key:<26}{RESET} {display_value}")
                else:
                    print(f"      {RED}(No variables found){RESET}")
    
    # Configuration sections
    sections = [
        {
            'title': f'{BLUE}{BOLD}🌐 Server Configuration{RESET}',
            'items': [
                ('LightRAG URL', settings.LIGHTRAG_URL),
                ('LightRAG Memory URL', settings.LIGHTRAG_MEMORY_URL),
                ('Weaviate URL', settings.WEAVIATE_URL),
                ('Ollama URL', settings.OLLAMA_URL),
                ('Remote Ollama URL', settings.REMOTE_OLLAMA_URL),
            ]
        },
        {
            'title': f'{BLUE}{BOLD}⚙️  Feature Flags{RESET}',
            'items': [
                ('Use Weaviate', f"{GREEN}✓{RESET}" if settings.USE_WEAVIATE else f"{RED}✗{RESET}"),
                ('Use MCP', f"{GREEN}✓{RESET}" if settings.USE_MCP else f"{RED}✗{RESET}"),
                ('Show Splash Screen', f"{GREEN}✓{RESET}" if settings.SHOW_SPLASH_SCREEN else f"{RED}✗{RESET}"),
            ]
        },
        {
            'title': f'{BLUE}{BOLD}📂 Directory Configuration{RESET}',
            'items': [
                ('Root Directory', settings.ROOT_DIR),
                ('Home Directory', settings.HOME_DIR),
                ('Persag Env Home', settings.PERSAG_HOME),
                ('Persag Data Root', settings.PERSAG_ROOT),
                ('User Data Directory', settings.USER_DATA_DIR),
                ('Repository Directory', settings.REPO_DIR),
                ('LightRAG Server Dir', settings.LIGHTRAG_SERVER_DIR),
                ('LightRAG Memory Dir', settings.LIGHTRAG_MEMORY_DIR),
                ('Agno Storage Directory', settings.AGNO_STORAGE_DIR),
                ('Agno Knowledge Directory', settings.AGNO_KNOWLEDGE_DIR),
                ('LightRAG Storage Directory', settings.LIGHTRAG_STORAGE_DIR),
                ('LightRAG Inputs Directory', settings.LIGHTRAG_INPUTS_DIR),
                ('LightRAG Memory Storage Directory', settings.LIGHTRAG_MEMORY_STORAGE_DIR),
                ('LightRAG Memory Inputs Directory', settings.LIGHTRAG_MEMORY_INPUTS_DIR),
            ]
        },
        {
            'title': f'{BLUE}{BOLD}🤖 AI & Storage Configuration{RESET}',
            'items': [
                ('Storage Backend', settings.STORAGE_BACKEND),
                ('LLM Model', settings.LLM_MODEL),
                ('User ID', get_userid()),
                ('Log Level', settings.LOG_LEVEL_STR),
            ]
        }
    ]
    
    # MCP Servers section
    print(f"\n{BLUE}{BOLD}🔌 MCP Servers{RESET}:")
    mcp_servers = get_mcp_servers()
    if mcp_servers:
        print(f"  {BOLD}Server Name{' '*15}Description{RESET}")
        for name, config in mcp_servers.items():
            description = config.get('description', 'No description available')
            print(f"  {YELLOW}{name:<25}{RESET} {GREEN}{description}{RESET}")
    else:
        print(f"  {RED}No MCP servers configured{RESET}")
    
    # Agentic Tools section
    print(f"\n{BLUE}{BOLD}🛠️ Agentic Tools{RESET}:")
    agentic_tools = get_agentic_tools()
    
    for category_name, category_info in agentic_tools.items():
        category_display = category_name.replace('_', ' ').title()
        print(f"\n  {MAGENTA}{BOLD}📦 {category_display}:{RESET}")
        print(f"    {CYAN}{category_info['description']}{RESET}")
        
        if category_info['tools']:
            for tool in category_info['tools']:
                tool_name = tool['name']
                tool_desc = tool['description']
                tool_category = tool.get('category', 'general')
                
                print(f"    {YELLOW}• {tool_name}{RESET} ({GREEN}{tool_category}{RESET})")
                print(f"      {tool_desc}")
                
                # Show additional details for specific tool types
                if 'functions' in tool:
                    print(f"      {CYAN}Functions:{RESET}")
                    for func in tool['functions']:
                        print(f"        - {func}")
                elif 'features' in tool:
                    print(f"      {CYAN}Features:{RESET} {', '.join(tool['features'])}")
                elif 'server' in tool:
                    print(f"      {CYAN}Server:{RESET} {tool['server']} | {CYAN}Args:{RESET} {tool['args_count']} | {CYAN}Env:{RESET} {tool['env_vars']}")
                
                print()  # Empty line between tools
        else:
            print(f"    {RED}No tools available in this category{RESET}")
    
    for section in sections:
        print(f"\n{section['title']}:")
        print(f"  {BOLD}Setting{' '*22}Value{RESET}")
        for name, value in section['items']:
            # Color the values based on type for better readability
            if isinstance(value, bool):
                colored_value = f"{GREEN}{value}{RESET}" if value else f"{RED}{value}{RESET}"
            elif value and ('http://' in str(value) or 'https://' in str(value)):
                colored_value = f"{CYAN}{value}{RESET}"
            elif value and str(value).startswith('/'):
                colored_value = f"{YELLOW}{value}{RESET}"
            else:
                colored_value = f"{GREEN}{value}{RESET}" if value else f"{RED}None{RESET}"
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
        
        if config.get('image'):
            print(f"  {BLUE}Image:{RESET} {GREEN}{config['image']}{RESET}")
        if config.get('ports'):
            print(f"  {BLUE}Ports:{RESET} {YELLOW}{', '.join(config['ports'])}{RESET}")
        if config.get('volumes'):
            print(f"  {BLUE}Volumes:{RESET}")
            for v in config['volumes']:
                print(f"    {CYAN}- {v}{RESET}")
        if config.get('environment'):
            print(f"  {BLUE}Environment:{RESET}")
            for e in config['environment']:
                print(f"    {CYAN}- {e}{RESET}")

    # Footer
    print(f"\n{CYAN}{BOLD}{'=' * 60}{RESET}")
    print(f"{GREEN}{BOLD}Configuration loaded successfully!{RESET}")
    print(f"{CYAN}{BOLD}Current User: {YELLOW}{get_userid()}{RESET}")
    print(f"{CYAN}{BOLD}{'=' * 60}{RESET}")


def print_config_no_color():
    """Print configuration without ANSI colors."""
    version = settings.get_package_version()
    print("=" * 60)
    print("  Personal Agent Configuration Status")
    print(f"  Version: {version}")
    print("=" * 60)
    
    # Environment file status
    print("\n📁 Environment File Status:")
    if settings.dotenv_loaded:
        print(f"  ✓ Successfully loaded .env from: {settings.dotenv_path}")
    else:
        print("  ✗ Failed to load .env file")
    
    # Environment variables section
    if settings._env_vars:
        print("\n🔧 Main Environment Variables (.env):")
        print(f"  Variable{' '*20}Value")
        for key, value in sorted(settings._env_vars.items()):
            # Mask sensitive values
            display_value = value
            if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                display_value = '*' * len(value) if value else ''
            print(f"  {key:<28} {display_value}")
    
    # Docker environment variables section organized by server
    docker_servers = get_docker_env_variables_by_server()
    if docker_servers:
        print("\n🐳 Docker Environment Variables by Server:")
        for server_name, server_data in docker_servers.items():
            print(f"\n  📦 {server_name.replace('_', ' ').title()}:")
            
            for env_type, env_info in server_data.items():
                env_type_display = "Environment File" if env_type == "env_file" else "Mounted Environment"
                print(f"    {env_type_display} ({env_info['path']}):")
                
                if env_info['variables']:
                    for key, value in sorted(env_info['variables'].items()):
                        # Mask sensitive values
                        display_value = value
                        if any(sensitive in key.lower() for sensitive in ['password', 'secret', 'key', 'token']):
                            display_value = '*' * len(value) if value else ''
                        print(f"      {key:<26} {display_value}")
                else:
                    print("      (No variables found)")
    
    # Configuration sections
    sections = [
        {
            'title': '🌐 Server Configuration',
            'items': [
                ('LightRAG URL', settings.LIGHTRAG_URL),
                ('LightRAG Memory URL', settings.LIGHTRAG_MEMORY_URL),
                ('Weaviate URL', settings.WEAVIATE_URL),
                ('Ollama URL', settings.OLLAMA_URL),
                ('Remote Ollama URL', settings.REMOTE_OLLAMA_URL),
            ]
        },
        {
            'title': '⚙️  Feature Flags',
            'items': [
                ('Use Weaviate', "✓" if settings.USE_WEAVIATE else "✗"),
                ('Use MCP', "✓" if settings.USE_MCP else "✗"),
                ('Show Splash Screen', "✓" if settings.SHOW_SPLASH_SCREEN else "✗"),
            ]
        },
        {
            'title': '📂 Directory Configuration',
            'items': [
                ('Root Directory', settings.ROOT_DIR),
                ('Home Directory', settings.HOME_DIR),
                ('Persag Env Home', settings.PERSAG_HOME),
                ('Persag Data Root', settings.PERSAG_ROOT),
                ('User Data Directory', settings.USER_DATA_DIR),
                ('Repository Directory', settings.REPO_DIR),
                ('LightRAG Server Dir', settings.LIGHTRAG_SERVER_DIR),
                ('LightRAG Memory Dir', settings.LIGHTRAG_MEMORY_DIR),
                ('Agno Storage Directory', settings.AGNO_STORAGE_DIR),
                ('Agno Knowledge Directory', settings.AGNO_KNOWLEDGE_DIR),
                ('LightRAG Storage Directory', settings.LIGHTRAG_STORAGE_DIR),
                ('LightRAG Inputs Directory', settings.LIGHTRAG_INPUTS_DIR),
                ('LightRAG Memory Storage Directory', settings.LIGHTRAG_MEMORY_STORAGE_DIR),
                ('LightRAG Memory Inputs Directory', settings.LIGHTRAG_MEMORY_INPUTS_DIR),
            ]
        },
        {
            'title': '🤖 AI & Storage Configuration',
            'items': [
                ('Storage Backend', settings.STORAGE_BACKEND),
                ('LLM Model', settings.LLM_MODEL),
                ('User ID', get_userid()),
                ('Log Level', settings.LOG_LEVEL_STR),
            ]
        }
    ]
    
    # MCP Servers section
    print("\n🔌 MCP Servers:")
    mcp_servers = get_mcp_servers()
    if mcp_servers:
        print(f"  Server Name{' '*15}Description")
        for name, config in mcp_servers.items():
            description = config.get('description', 'No description available')
            print(f"  {name:<25} {description}")
    else:
        print("  No MCP servers configured")
    
    # Agentic Tools section
    print("\n🛠️ Agentic Tools:")
    agentic_tools = get_agentic_tools()
    
    for category_name, category_info in agentic_tools.items():
        category_display = category_name.replace('_', ' ').title()
        print(f"\n  📦 {category_display}:")
        print(f"    {category_info['description']}")
        
        if category_info['tools']:
            for tool in category_info['tools']:
                tool_name = tool['name']
                tool_desc = tool['description']
                tool_category = tool.get('category', 'general')
                
                print(f"    • {tool_name} ({tool_category})")
                print(f"      {tool_desc}")
                
                # Show additional details for specific tool types
                if 'functions' in tool:
                    print(f"      Functions:")
                    for func in tool['functions']:
                        print(f"        - {func}")
                elif 'features' in tool:
                    print(f"      Features: {', '.join(tool['features'])}")
                elif 'server' in tool:
                    print(f"      Server: {tool['server']} | Args: {tool['args_count']} | Env: {tool['env_vars']}")
                
                print()  # Empty line between tools
        else:
            print(f"    No tools available in this category")
    
    for section in sections:
        print(f"\n{section['title']}:")
        print(f"  Setting{' '*22}Value")
        for name, value in section['items']:
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
        
        if config.get('image'):
            print(f"  Image: {config['image']}")
        if config.get('ports'):
            print(f"  Ports: {', '.join(config['ports'])}")
        if config.get('volumes'):
            print("  Volumes:")
            for v in config['volumes']:
                print(f"    - {v}")
        if config.get('environment'):
            print("  Environment:")
            for e in config['environment']:
                print(f"    - {e}")

    # Footer
    print("\n" + "=" * 60)
    print("Configuration loaded successfully!")
    print(f"Current User: {get_userid()}")
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
        epilog=__doc__
    )
    
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="Personal Agent Config Tool v1.0"
    )
    
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output configuration as JSON"
    )
    
    args = parser.parse_args()
    
    result = show_config(no_color=args.no_color, json_output=args.json)
    if args.json and result:
        print(result)


if __name__ == "__main__":
    main()
