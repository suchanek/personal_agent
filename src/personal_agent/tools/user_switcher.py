#!/usr/bin/env python3
"""
User Switching Tool for Personal Agent

This module provides a complete user switching solution that:
1. Creates new users if they don't exist
2. Switches the current USER_ID environment variable
3. Refreshes all user-dependent configuration settings
4. Restarts Docker services with the new user context
5. Ensures proper user isolation and data directory setup

Usage:
    from personal_agent.tools.user_switcher import main as switch_user_main
    switch_user_main()

Command-line arguments:
    user_id (positional, optional)         User ID or full name to switch to (optional with --status)
    --user-name                           Display name for new users (defaults to formatted user_id)
    --user-type {Standard,Admin,Guest}    User type for new users (default: Standard)
    --birth-date <YYYY-MM-DD>             Birth date for new users (e.g., 1990-05-15)
    --gender {Male,Female,N/A}            Gender for new users (Male, Female, or N/A)
    --cognitive-state <0-100>             Cognitive state for new users (0-100, default: 100)
    --npc                                 Mark user as NPC (Non-Player Character)
    --no-restart                          Don't restart LightRAG services after switching
    --no-system-restart                   Don't restart the agent/team system after switching
    --status                              Display user status instead of switching
    --create-only                         Only create the user, don't switch to them
    -y, --yes                             Automatically confirm user creation without prompting
    --list                                Display a list of all users

Examples:
    ./switch-user.py "Alice Smith"                                              # Switch to existing user (prompts if new)
    ./switch-user.py alice.smith --no-restart                                   # Switch without restarting services
    ./switch-user.py "Charlie Brown" --user-type Admin --yes                    # Create admin without prompt
    ./switch-user.py "Bob" --birth-date 1985-06-20 --cognitive-state 85 --yes   # Create with specific profile
    ./switch-user.py --status alice.smith                                       # Display user status
    ./switch-user.py --list                                                     # Display all users in the system
"""
# pylint: disable=import-outside-toplevel
# (Imports are inside functions to avoid circular dependencies and lazy-load heavy modules)

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from personal_agent.config.user_id_mgr import (
    get_current_user_id,
    load_user_from_file,
    refresh_user_dependent_settings,
)

# Ensure the USER_ID context is initialized using the canonical loader
load_user_from_file()


@dataclass
class UserCreateOptions:
    """Options for creating a new user.

    :param user_id: User ID or full name for the new user
    :param user_name: Display name (defaults to formatted user_id)
    :param user_type: User type (Standard, Admin, Guest)
    :param birth_date: Birth date for the user in YYYY-MM-DD format (optional)
    :param gender: Gender for the user (Male, Female, or N/A)
    :param cognitive_state: Cognitive state (0-100 scale, default 100)
    :param npc: Whether this is an NPC/bot user
    :param auto_confirm: Skip confirmation prompt for new user creation
    """

    user_id: str
    user_name: Optional[str] = None
    user_type: str = "Standard"
    birth_date: Optional[str] = None
    gender: Optional[str] = None
    cognitive_state: int = 100
    npc: bool = False
    auto_confirm: bool = False

    def get_display_name(self) -> str:
        """Get display name, using formatted user_id if not provided.

        :return: The display name for the user
        """
        if self.user_name:
            return self.user_name
        return self.user_id.replace("_", " ").replace("-", " ").title()

    def get_gender(self) -> str:
        """Get gender, defaulting to N/A.

        :return: The gender value
        """
        return self.gender if self.gender else "N/A"


# Colors for output
class Colors:  # pylint: disable=too-few-public-methods
    """ANSI color codes for terminal output formatting."""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    CYAN = "\033[0;36m"
    MAGENTA = "\033[0;35m"
    WHITE = "\033[1;37m"
    NC = "\033[0m"  # No Color
    BOLD = "\033[1m"


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {title}{Colors.NC}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.NC}")


def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.GREEN}✓{Colors.NC} {message}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.NC} {message}")


def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.RED}✗{Colors.NC} {message}")


def print_info(message: str):
    """Print an info message."""
    print(f"{Colors.CYAN}ℹ{Colors.NC} {message}")


def print_step(step: str, message: str):
    """Print a step message."""
    print(f"{Colors.MAGENTA}[{step}]{Colors.NC} {message}")


def validate_user_id(user_id: str) -> bool:
    """Validate that the user ID is acceptable."""
    if not user_id:
        print_error("User ID cannot be empty")
        return False

    if len(user_id) < 2:
        print_error("User ID must be at least 2 characters long")
        return False

    # Allow dots and spaces for full names like "Eric Suchanek"
    cleaned = (
        user_id.replace("_", "").replace("-", "").replace(".", "").replace(" ", "")
    )
    if not cleaned.isalnum():
        print_error(
            "User ID can only contain letters, numbers, spaces, dots, hyphens, and underscores"
        )
        return False

    return True


def get_current_user_info() -> Dict[str, Any]:
    """Get information about the current user."""
    try:
        current_user_id = get_current_user_id()
        current_settings = refresh_user_dependent_settings()

        return {"user_id": current_user_id, "settings": current_settings}
    except Exception as e:
        print_error(f"Failed to get current user info: {e}")
        return {"user_id": "unknown", "settings": {}}


def _prompt_for_user_creation(opts: UserCreateOptions) -> bool:
    """Prompt user to confirm new user creation.

    :param opts: User creation options
    :return: True if user confirmed, False otherwise
    """
    print_warning(f"User '{opts.user_id}' does not exist.")
    print_info(f"  User Name: {opts.get_display_name()}")
    print_info(f"  User Type: {opts.user_type}")
    if opts.birth_date:
        print_info(f"  Birth Date: {opts.birth_date}")
    if opts.gender and opts.gender != "N/A":
        print_info(f"  Gender: {opts.gender}")
    if opts.cognitive_state != 100:
        print_info(f"  Cognitive State: {opts.cognitive_state}/100")
    if opts.npc:
        print_info("  NPC: Yes")

    response = (
        input(f"\n{Colors.YELLOW}Create this user? [y/N]: {Colors.NC}").strip().lower()
    )
    return response in ["y", "yes"]


def create_user_if_needed(  # pylint: disable=too-many-arguments,too-many-locals,too-many-positional-arguments
    user_id: str,
    user_name: Optional[str] = None,
    user_type: str = "Standard",
    birth_date: Optional[str] = None,
    gender: Optional[str] = None,
    cognitive_state: int = 100,
    npc: bool = False,
    auto_confirm: bool = False,
) -> tuple:
    """Create a user if they don't exist.

    :param user_id: User ID or full name for the new user
    :param user_name: Display name (defaults to formatted user_id)
    :param user_type: User type (Standard, Admin, Guest)
    :param birth_date: Birth date for the user in YYYY-MM-DD format (optional)
    :param gender: Gender for the user (Male, Female, or N/A)
    :param cognitive_state: Cognitive state (0-100 scale, default 100)
    :param npc: Whether this is an NPC/bot user
    :param auto_confirm: Skip confirmation prompt for new user creation
    :return: Tuple of (success: bool, normalized_user_id: str)
    """
    try:
        from personal_agent.core.user_manager import UserManager

        opts = UserCreateOptions(
            user_id=user_id,
            user_name=user_name,
            user_type=user_type,
            birth_date=birth_date,
            gender=gender,
            cognitive_state=cognitive_state,
            npc=npc,
            auto_confirm=auto_confirm,
        )

        user_manager = UserManager()

        # Check if user already exists
        existing_user = user_manager.get_user(opts.user_id)
        if existing_user:
            print_info(f"User '{opts.user_id}' already exists")
            return True, existing_user.get("user_id", opts.user_id)

        # User doesn't exist - prompt for confirmation
        if not opts.auto_confirm and not _prompt_for_user_creation(opts):
            print_info("User creation cancelled")
            return False, opts.user_id

        # Create new user
        print_step("CREATE", f"Creating new user '{opts.user_id}'")

        result = user_manager.create_user(
            user_id=opts.user_id,
            user_name=opts.get_display_name(),
            user_type=opts.user_type,
            birth_date=opts.birth_date,
            gender=opts.get_gender(),
            cognitive_state=opts.cognitive_state,
            npc=opts.npc,
        )

        if result["success"]:
            normalized_user_id = result.get("user_id", opts.user_id)
            user_display_name = result.get("user_name", opts.get_display_name())
            print_success(
                f"Created user '{normalized_user_id}' with name '{user_display_name}' (type: {opts.user_type})"
            )
            return True, normalized_user_id

        error_msg = result.get("error", result.get("message", "Unknown error"))
        print_error(f"Failed to create user: {error_msg}")
        return False, opts.user_id

    except Exception as e:
        print_error(f"Error creating user: {e}")
        return False, user_id


def _restart_lightrag_services(user_id: str) -> bool:
    """Restart LightRAG services for the new user.

    :param user_id: The user ID to restart services for
    :return: True if successful, False otherwise
    """
    from personal_agent.core.docker_integration import ensure_docker_user_consistency

    print_step("SYNC", "Ensuring Docker services are synchronized...")
    success, message = ensure_docker_user_consistency(
        user_id=user_id, auto_fix=True, force_restart=True
    )
    if success:
        print_success("Docker services synchronized successfully.")
        return True
    print_error(f"Docker synchronization failed: {message}")
    return False


def _display_switch_results(result: Dict[str, Any]) -> None:
    """Display results of the user switch operation.

    :param result: Result dictionary from switch_user operation
    """
    print_success(f"Successfully switched to user '{result.get('user_id', 'N/A')}'")

    if result.get("actions_performed"):
        print_info("Actions performed:")
        for action in result["actions_performed"]:
            print(f"  • {action}")

    if result.get("config_refresh"):
        _display_config_refresh(result["config_refresh"])

    if result.get("warnings"):
        for warning in result["warnings"]:
            print_warning(warning)


def _display_config_refresh(config_refresh: Dict[str, Any]) -> None:
    """Display configuration refresh details.

    :param config_refresh: Configuration refresh data
    """
    print_info("Configuration refreshed:")
    print(f"  • USER_ID: {config_refresh.get('USER_ID', 'N/A')}")
    print(f"  • Storage Directory: {config_refresh.get('AGNO_STORAGE_DIR', 'N/A')}")
    print(f"  • LightRAG Storage: {config_refresh.get('LIGHTRAG_STORAGE_DIR', 'N/A')}")
    print(
        f"  • Memory Storage: {config_refresh.get('LIGHTRAG_MEMORY_STORAGE_DIR', 'N/A')}"
    )


def _setup_team_helpers(team: Any, global_state: Any) -> None:
    """Setup memory and knowledge helpers for team.

    :param team: The team object
    :param global_state: Global state manager
    """
    from personal_agent.tools.streamlit_helpers import (
        StreamlitKnowledgeHelper,
        StreamlitMemoryHelper,
    )

    if hasattr(team, "members") and team.members:
        knowledge_agent = team.members[0]
        memory_helper = StreamlitMemoryHelper(knowledge_agent)
        knowledge_helper_obj = StreamlitKnowledgeHelper(knowledge_agent)
        global_state.set("memory_helper", memory_helper)
        global_state.set("knowledge_helper", knowledge_helper_obj)


def _setup_agent_helpers(agent: Any, global_state: Any) -> None:
    """Setup memory and knowledge helpers for agent.

    :param agent: The agent object
    :param global_state: Global state manager
    """
    from personal_agent.tools.streamlit_helpers import (
        StreamlitKnowledgeHelper,
        StreamlitMemoryHelper,
    )

    memory_helper = StreamlitMemoryHelper(agent)
    knowledge_helper_obj = StreamlitKnowledgeHelper(agent)
    global_state.set("memory_helper", memory_helper)
    global_state.set("knowledge_helper", knowledge_helper_obj)


def _restart_team_system(
    global_state: Any, current_model: str, current_ollama_url: str
) -> Dict[str, Any]:
    """Reinitialize team system after user switch.

    :param global_state: Global state manager
    :param current_model: Current LLM model
    :param current_ollama_url: Current Ollama URL
    :return: Restart result dictionary
    """
    from personal_agent.tools.streamlit_agent_manager import initialize_team

    restart_success = False
    restart_message = ""

    try:
        team = initialize_team(recreate=True)
        if team:
            global_state.set("agent_mode", "team")
            global_state.set("team", team)
            global_state.set("llm_model", current_model)
            global_state.set("ollama_url", current_ollama_url)
            _setup_team_helpers(team, global_state)
            restart_success = True
            restart_message = "System restarted successfully in team mode"
            print_success(restart_message)
        else:
            restart_message = "Failed to initialize team during restart"
            print_error(restart_message)
    except Exception as e:
        restart_message = f"Error restarting team: {str(e)}"
        print_error(restart_message)

    return {
        "restart_performed": True,
        "restart_success": restart_success,
        "restart_message": restart_message,
        "agent_mode": "team",
        "model": current_model,
    }


def _restart_agent_system(
    global_state: Any, current_model: str, current_ollama_url: str
) -> Dict[str, Any]:
    """Reinitialize agent system after user switch.

    :param global_state: Global state manager
    :param current_model: Current LLM model
    :param current_ollama_url: Current Ollama URL
    :return: Restart result dictionary
    """
    from personal_agent.tools.streamlit_agent_manager import initialize_agent

    restart_success = False
    restart_message = ""

    try:
        agent = initialize_agent(recreate=True)
        if agent:
            global_state.set("agent_mode", "single")
            global_state.set("agent", agent)
            global_state.set("llm_model", current_model)
            global_state.set("ollama_url", current_ollama_url)
            _setup_agent_helpers(agent, global_state)
            restart_success = True
            restart_message = "System restarted successfully in single agent mode"
            print_success(restart_message)
        else:
            restart_message = "Failed to initialize agent during restart"
            print_error(restart_message)
    except Exception as e:
        restart_message = f"Error restarting agent: {str(e)}"
        print_error(restart_message)

    return {
        "restart_performed": True,
        "restart_success": restart_success,
        "restart_message": restart_message,
        "agent_mode": "single",
        "model": current_model,
    }


def _perform_system_restart(
    global_state: Any,
    current_agent_mode: str,
    current_model: str,
    current_ollama_url: str,
) -> Dict[str, Any]:
    """Perform system restart after user switch.

    :param global_state: Global state manager
    :param current_agent_mode: Current agent mode (team or single)
    :param current_model: Current LLM model
    :param current_ollama_url: Current Ollama URL
    :return: System restart result
    """
    global_state.clear()

    if current_agent_mode == "team":
        return _restart_team_system(global_state, current_model, current_ollama_url)
    return _restart_agent_system(global_state, current_model, current_ollama_url)


def _handle_switch_error(error_msg: str) -> bool:
    """Handle user switch errors.

    :param error_msg: Error message from switch_user
    :return: True if already logged in (recoverable), False otherwise
    """
    if "Already logged in" in error_msg:
        print_warning(error_msg)
        print_info("User is already active - configuration is up to date")
        return True
    print_error(f"Failed to switch user: {error_msg}")
    return False


def switch_user_context(  # pylint: disable=too-many-locals
    user_id: str, restart_services: bool = True, restart_system: bool = True
) -> bool:
    """Switch the user context and refresh all settings.

    :param user_id: The user ID to switch to
    :param restart_services: Whether to restart Docker services
    :param restart_system: Whether to restart the agent/team system
    :return: True if successful, False otherwise
    """
    try:
        from personal_agent.core.docker_integration import stop_lightrag_services
        from personal_agent.core.user_manager import UserManager

        # Shut down services before switching user to ensure a clean restart
        if restart_services:
            print_step("SHUTDOWN", "Stopping LightRAG services before user switch...")
            success, message = stop_lightrag_services()
            if success:
                print_success("LightRAG services stopped successfully.")
            else:
                print_warning(f"Could not stop all LightRAG services: {message}")

        user_manager = UserManager()
        print_step("SWITCH", f"Switching to user '{user_id}'")

        result = user_manager.switch_user(
            user_id=user_id,
            restart_lightrag=False,
            update_global_config=True,
        )

        if not result["success"]:
            return _handle_switch_error(result.get("error", "Unknown error"))

        _display_switch_results(result)

        if restart_services and not _restart_lightrag_services(user_id):
            return False

        system_restart_result = None
        if restart_system:
            print_step("RESTART", "Performing system restart after user switch...")
            try:
                from personal_agent.tools.global_state import get_global_state

                global_state = get_global_state()
                current_agent_mode = global_state.get("agent_mode", "single")
                current_model = global_state.get(
                    "llm_model",
                    os.getenv(
                        "LLM_MODEL",
                        "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:q8_0",
                    ),
                )
                current_ollama_url = global_state.get(
                    "ollama_url",
                    os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                )

                system_restart_result = _perform_system_restart(
                    global_state, current_agent_mode, current_model, current_ollama_url
                )
            except Exception as restart_error:
                print_error(
                    f"Error during system restart after user switch: {restart_error}"
                )
                system_restart_result = {
                    "restart_performed": True,
                    "restart_success": False,
                    "restart_message": str(restart_error),
                }

        if system_restart_result:
            if system_restart_result["restart_success"]:
                print_info("System restart completed successfully")
            else:
                print_warning(
                    f"System restart had issues: {system_restart_result['restart_message']}"
                )

        return True

    except Exception as e:
        print_error(f"Error switching user: {e}")
        return False


def _get_expected_directories(settings: Dict[str, Any], base_path: str) -> list:
    """Get the list of expected user directories.

    :param settings: User settings dictionary
    :param base_path: Base storage path for the user
    :return: List of expected directory paths
    """
    if base_path:
        return [
            base_path,
            f"{base_path}/knowledge",
            f"{base_path}/rag_storage",
            f"{base_path}/inputs",
            f"{base_path}/memory_rag_storage",
            f"{base_path}/memory_inputs",
        ]
    # Fallback to settings if base_path couldn't be determined
    return [
        settings.get("AGNO_STORAGE_DIR"),
        settings.get("AGNO_KNOWLEDGE_DIR"),
        settings.get("LIGHTRAG_STORAGE_DIR"),
        settings.get("LIGHTRAG_INPUTS_DIR"),
        settings.get("LIGHTRAG_MEMORY_STORAGE_DIR"),
        settings.get("LIGHTRAG_MEMORY_INPUTS_DIR"),
    ]


def _verify_and_create_directories(
    dir_paths: list,
) -> tuple:
    """Verify existing directories and create missing ones.

    :param dir_paths: List of directory paths to verify/create
    :return: Tuple of (created_dirs, existing_dirs)
    """
    directories_created = []
    directories_existing = []

    for dir_path in dir_paths:
        if not dir_path:
            continue
        if Path(dir_path).exists():
            directories_existing.append(dir_path)
        else:
            try:
                Path(dir_path).mkdir(parents=True, exist_ok=True)
                directories_created.append(dir_path)
            except Exception as e:
                print_warning(f"Could not create directory {dir_path}: {e}")

    return directories_created, directories_existing


def _display_directory_results(created: list, existing: list) -> None:
    """Display results of directory creation/verification.

    :param created: List of newly created directories
    :param existing: List of existing directories
    """
    if created:
        print_success(f"Created {len(created)} new user directories:")
        for dir_path in created:
            print(f"  • {dir_path}")

    if existing:
        print_info(f"Verified {len(existing)} existing user directories:")
        for dir_path in existing:
            print(f"  • {dir_path}")


def _get_corrected_base_path(
    base_path: str, original_user_id: Optional[str], new_user_id: str
) -> str:
    """Correct base path if it contains the original user ID.

    :param base_path: The base storage path
    :param original_user_id: The original user ID (if any)
    :param new_user_id: The new user ID
    :return: Corrected base path
    """
    if original_user_id and original_user_id in base_path:
        return base_path.replace(original_user_id, new_user_id)
    return base_path


def create_user_directories(user_id: str) -> bool:  # pylint: disable=too-many-locals
    """Create necessary directories for the user.

    :param user_id: The user ID to create directories for
    :return: True if successful, False otherwise
    """
    try:
        from personal_agent.config.runtime_config import get_config
        from personal_agent.core.agno_agent import AgnoPersonalAgent

        print_step("SETUP", f"Creating directories for user '{user_id}'")

        # Temporarily set the USER_ID environment variable
        original_user_id = os.getenv("USER_ID")
        os.environ["USER_ID"] = user_id

        # Update the config singleton with the new user_id
        config = get_config()
        config.set_user_id(user_id, persist=False)

        try:
            # Initialize AgnoPersonalAgent with the new user ID
            AgnoPersonalAgent(user_id=user_id)

            # Refresh settings to get the correct paths for the new user
            settings = refresh_user_dependent_settings(user_id=user_id)

            # Get and correct the base storage path
            base_path = settings.get("AGNO_STORAGE_DIR", "")
            base_path = _get_corrected_base_path(base_path, original_user_id, user_id)

            # Get expected directories and verify/create them
            expected_dirs = _get_expected_directories(settings, base_path)
            created, existing = _verify_and_create_directories(expected_dirs)

            # Display results
            _display_directory_results(created, existing)

            return True

        finally:
            # Restore original USER_ID in both environment and config
            if original_user_id:
                os.environ["USER_ID"] = original_user_id
                config.set_user_id(original_user_id, persist=False)

    except Exception as e:
        print_error(f"Error creating user directories: {e}")
        return False


def display_user_status(user_id: str):
    """Display the current status of the user."""
    try:
        from personal_agent.core.user_manager import UserManager

        user_manager = UserManager()
        user_details = user_manager.get_user_details(user_id)

        # Show summary line with user name and ID
        if user_details:
            print_header(
                f"User Status: {user_details.get('user_name', 'N/A')} ({user_details.get('user_id', 'N/A')})"
            )
        else:
            print_header(f"User Status: {user_id}")

        current_user = get_current_user_id()

        if user_details:
            print(f"{Colors.CYAN}User Information:{Colors.NC}")
            print(f"  • User ID: {user_details.get('user_id', 'N/A')}")
            print(f"  • User Name: {user_details.get('user_name', 'N/A')}")
            print(f"  • User Type: {user_details.get('user_type', 'N/A')}")
            print(f"  • Created: {user_details.get('created_at', 'N/A')}")
            print(f"  • Last Seen: {user_details.get('last_seen', 'N/A')}")
            print(
                f"  • Is Current: {Colors.GREEN if user_details.get('is_current') else Colors.RED}{user_details.get('is_current', False)}{Colors.NC}"
            )

            # Display LightRAG status if available
            if user_details.get("lightrag_status"):
                lightrag_status = user_details["lightrag_status"]
                print(f"\n{Colors.CYAN}LightRAG Status:{Colors.NC}")
                if lightrag_status.get("error"):
                    print(f"  • Status: {Colors.RED}Error{Colors.NC}")
                    print(f"  • Error: {lightrag_status['error']}")
                else:
                    print(f"  • Status: {Colors.GREEN}Available{Colors.NC}")
        else:
            print_error(f"User '{user_id}' not found")

        # Display current environment
        print(f"\n{Colors.CYAN}Environment:{Colors.NC}")
        print(f"  • Current USER_ID: {current_user}")
        print(f"  • Environment USER_ID: {os.getenv('USER_ID', 'Not set')}")

    except Exception as e:
        print_error(f"Error displaying user status: {e}")


def _create_argument_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser.

    :return: Configured argument parser
    """
    parser = argparse.ArgumentParser(
        description="Switch users in the Personal Agent system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  switch-user.py "Alice Smith"              # Switch to existing user (prompts if new)
  switch-user.py alice.smith --no-restart   # Switch without restarting services
  switch-user.py "Charlie Brown" --user-type Admin --yes  # Create admin without prompt
  switch-user.py --status alice.smith       # Display user status
  switch-user.py --list                     # Display all users in the system
        """,
    )

    parser.add_argument(
        "user_id",
        nargs="?",
        help="User ID or full name to switch to (optional with --status)",
    )
    parser.add_argument(
        "--user-name", help="Display name for new users (defaults to formatted user_id)"
    )
    parser.add_argument(
        "--user-type",
        choices=["Standard", "Admin", "Guest"],
        default="Standard",
        help="User type for new users (default: Standard)",
    )
    parser.add_argument(
        "--birth-date", help="Birth date for new users in YYYY-MM-DD format (e.g., 1990-05-15)"
    )
    parser.add_argument(
        "--gender",
        choices=["Male", "Female", "N/A"],
        help="Gender for new users (Male, Female, or N/A)",
    )
    parser.add_argument(
        "--cognitive-state",
        type=int,
        default=100,
        help="Cognitive state for new users (0-100 scale, default: 100)",
    )
    parser.add_argument(
        "--npc",
        action="store_true",
        help="Mark user as NPC (Non-Player Character) for bot/knowledge consolidation users",
    )
    parser.add_argument(
        "--no-restart",
        action="store_true",
        help="Don't restart LightRAG services after switching",
    )
    parser.add_argument(
        "--no-system-restart",
        action="store_true",
        help="Don't restart the agent/team system after switching",
    )
    parser.add_argument(
        "--status", action="store_true", help="Display user status instead of switching"
    )
    parser.add_argument(
        "--create-only",
        action="store_true",
        help="Only create the user, don't switch to them",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Automatically confirm user creation without prompting",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Display a list of all users",
    )
    return parser


def _format_user_row(
    user: Dict[str, Any], current_user_id: str, col_widths: Dict[str, int]
) -> str:
    """Format a single user row for table display.

    :param user: User dictionary
    :param current_user_id: Current active user ID
    :param col_widths: Dictionary of column names to widths
    :return: Formatted row string
    """
    is_current = user.get("is_current", False)
    current_marker = "→" if is_current else " "

    user_id = user.get("user_id", "N/A")[: col_widths["User ID"]]
    user_name = user.get("user_name", "N/A")[: col_widths["Name"]]
    user_type = user.get("user_type", "Standard")[: col_widths["Type"]]
    created = user.get("created_at", "N/A")[: col_widths["Created"]]
    last_seen = user.get("last_seen", "N/A")[: col_widths["Last Seen"]]

    row = f"{current_marker} "
    row += f"{user_id:<{col_widths['User ID']}}  "
    row += f"{user_name:<{col_widths['Name']}}  "
    row += f"{user_type:<{col_widths['Type']}}  "
    row += f"{created:<{col_widths['Created']}}  "
    row += f"{last_seen:<{col_widths['Last Seen']}}"

    if is_current:
        row = f"{Colors.GREEN}{row}{Colors.NC}"

    return row


def _handle_list_mode() -> None:
    """Handle --list mode to display all users in a formatted table."""
    try:
        from personal_agent.core.user_manager import UserManager

        user_manager = UserManager()
        users = user_manager.get_all_users()

        if not users:
            print_info("No users found in the system")
            return

        print_header("All Users")

        # Calculate column widths
        col_widths = {
            "User ID": max(10, max(len(u.get("user_id", "N/A")) for u in users)),
            "Name": max(15, max(len(u.get("user_name", "N/A")) for u in users)),
            "Type": 10,
            "Created": 19,
            "Last Seen": 19,
        }

        # Print header
        header = "  "
        header += f"{'User ID':<{col_widths['User ID']}}  "
        header += f"{'Name':<{col_widths['Name']}}  "
        header += f"{'Type':<{col_widths['Type']}}  "
        header += f"{'Created':<{col_widths['Created']}}  "
        header += f"{'Last Seen':<{col_widths['Last Seen']}}"
        print(f"{Colors.BOLD}{Colors.CYAN}{header}{Colors.NC}")
        print(f"{Colors.CYAN}{'-' * (len(header) + 20)}{Colors.NC}")

        # Print rows
        current_user_id = get_current_user_id()
        for user in users:
            row = _format_user_row(user, current_user_id, col_widths)
            print(row)

        # Print legend
        print(f"\n{Colors.CYAN}Legend:{Colors.NC}")
        print(f"  {Colors.GREEN}→{Colors.NC} = Current user")
        print(f"  Total users: {len(users)}")

    except Exception as e:
        print_error(f"Error listing users: {e}")


def _handle_status_mode(args: argparse.Namespace) -> None:
    """Handle --status mode to display user information.

    :param args: Parsed command-line arguments
    """
    if args.user_id:
        display_user_status(args.user_id)
    else:
        current_info = get_current_user_info()
        display_user_status(current_info["user_id"])


def _validate_and_get_current_user(args: argparse.Namespace) -> str:
    """Validate user input and get current user.

    :param args: Parsed command-line arguments
    :return: Current user ID
    """
    if not args.user_id:
        print_error("User ID is required unless --status is used.")
        sys.exit(1)
    if not validate_user_id(args.user_id):
        sys.exit(1)

    current_info = get_current_user_info()
    return current_info["user_id"]


def _display_success_message(normalized_user_id: str, restart_services: bool) -> None:
    """Display the success message after user switch.

    :param normalized_user_id: The normalized user ID
    :param restart_services: Whether services were restarted
    """
    print_header("Switch Complete")
    display_user_status(normalized_user_id)

    print(
        f"\n{Colors.GREEN}{Colors.BOLD}🎉 Successfully switched to user '{normalized_user_id}'!{Colors.NC}"
    )
    print(
        f"{Colors.CYAN}You can now use the Personal Agent system as '{normalized_user_id}'.{Colors.NC}"
    )

    if restart_services:
        print(
            f"{Colors.CYAN}LightRAG services have been restarted with the new user context.{Colors.NC}"
        )
    else:
        print(
            f"{Colors.YELLOW}Note: LightRAG services were not restarted. You may need to restart them manually.{Colors.NC}"
        )


def main():
    """Main function for user switching."""
    parser = _create_argument_parser()
    args = parser.parse_args()

    print_header("Personal Agent User Switcher")

    # Handle --list mode
    if args.list:
        _handle_list_mode()
        return

    # Handle --status mode
    if args.status:
        _handle_status_mode(args)
        return

    # Validate and get current user
    current_user = _validate_and_get_current_user(args)
    print_info(f"Current user: {current_user}")
    print_info(f"Target user: {args.user_id}")

    # Check if already logged in
    if current_user == args.user_id and not args.create_only:
        print_warning(f"Already logged in as '{args.user_id}'")
        display_user_status(args.user_id)
        return

    # Step 1: Create user if needed
    success, normalized_user_id = create_user_if_needed(
        args.user_id,
        args.user_name,
        args.user_type,
        birth_date=getattr(args, "birth_date", None),
        gender=getattr(args, "gender", None),
        cognitive_state=getattr(args, "cognitive_state", 100),
        npc=getattr(args, "npc", False),
        auto_confirm=args.yes,
    )
    if not success:
        print_error("Failed to create user")
        sys.exit(1)

    print_info(f"Using normalized user ID: {normalized_user_id}")

    # Step 2: Create user directories
    if not create_user_directories(normalized_user_id):
        print_warning("Some user directories could not be created")

    # Step 3: Early exit if create-only
    if args.create_only:
        print_success(f"User '{normalized_user_id}' created successfully")
        return

    # Step 4: Switch user context
    restart_services = not args.no_restart
    restart_system = not args.no_system_restart
    if not switch_user_context(normalized_user_id, restart_services, restart_system):
        print_error("Failed to switch user context")
        sys.exit(1)

    # Step 5: Display success
    _display_success_message(normalized_user_id, restart_services)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Operation cancelled by user{Colors.NC}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
