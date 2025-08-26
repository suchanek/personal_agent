#!/usr/bin/env python3
"""
User Switching Script for Personal Agent

This script provides a complete user switching solution that:
1. Creates new users if they don't exist
2. Switches the current USER_ID environment variable
3. Refreshes all user-dependent configuration settings
4. Restarts Docker services with the new user context
5. Ensures proper user isolation and data directory setup

Usage:
    python switch-user.py <user_id> [options]

Examples:
    python switch-user.py alice
    python switch-user.py bob --no-restart
    python switch-user.py charlie --user-name "Charlie Brown" --user-type Admin
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))


# Colors for output
class Colors:
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

    if not user_id.replace("_", "").replace("-", "").isalnum():
        print_error(
            "User ID can only contain letters, numbers, hyphens, and underscores"
        )
        return False

    return True


def get_current_user_info() -> Dict[str, Any]:
    """Get information about the current user."""
    try:
        from personal_agent.config import (
            get_current_user_id,
            refresh_user_dependent_settings,
        )

        current_user_id = get_current_user_id()
        current_settings = refresh_user_dependent_settings()

        return {"user_id": current_user_id, "settings": current_settings}
    except Exception as e:
        print_error(f"Failed to get current user info: {e}")
        return {"user_id": "unknown", "settings": {}}


def create_user_if_needed(
    user_id: str, user_name: str = None, user_type: str = "Standard"
) -> bool:
    """Create a user if they don't exist."""
    try:
        from personal_agent.core.user_manager import UserManager

        user_manager = UserManager()

        # Check if user already exists
        existing_user = user_manager.get_user(user_id)
        if existing_user:
            print_info(f"User '{user_id}' already exists")
            return True

        # Create new user
        print_step("CREATE", f"Creating new user '{user_id}'")

        if not user_name:
            user_name = user_id.replace("_", " ").replace("-", " ").title()

        result = user_manager.create_user(user_id, user_name, user_type)

        if result["success"]:
            print_success(
                f"Created user '{user_id}' with name '{user_name}' (type: {user_type})"
            )
            return True
        else:
            error_msg = result.get("error", result.get("message", "Unknown error"))
            print_error(f"Failed to create user: {error_msg}")
            return False

    except Exception as e:
        print_error(f"Error creating user: {e}")
        return False


def switch_user_context(user_id: str, restart_services: bool = True) -> bool:
    """Switch the user context and refresh all settings."""
    try:
        from personal_agent.config import DATA_DIR, PERSAG_HOME
        from personal_agent.core.user_manager import UserManager
        from personal_agent.core.docker_integration import ensure_docker_user_consistency

        user_manager = UserManager(data_dir=DATA_DIR, project_root=PERSAG_HOME)

        print_step("SWITCH", f"Switching to user '{user_id} using {PERSAG_HOME}'")

        # Perform the user switch
        result = user_manager.switch_user(
            user_id=user_id,
            restart_lightrag=False, # We will handle this with the more robust docker_integration module
            update_global_config=True,
        )

        if result["success"]:
            print_success(f"Successfully switched to user '{user_id}'")

            # Display actions performed
            if result.get("actions_performed"):
                print_info("Actions performed:")
                for action in result["actions_performed"]:
                    print(f"  • {action}")

            # Display configuration refresh info
            if result.get("config_refresh"):
                config_refresh = result["config_refresh"]
                print_info("Configuration refreshed:")
                print(f"  • USER_ID: {config_refresh.get('USER_ID', 'N/A')}")
                print(
                    f"  • Storage Directory: {config_refresh.get('AGNO_STORAGE_DIR', 'N/A')}"
                )
                print(
                    f"  • LightRAG Storage: {config_refresh.get('LIGHTRAG_STORAGE_DIR', 'N/A')}"
                )
                print(
                    f"  • Memory Storage: {config_refresh.get('LIGHTRAG_MEMORY_STORAGE_DIR', 'N/A')}"
                )

            # Restart services using the robust docker_integration module
            if restart_services:
                print_step("SYNC", "Ensuring Docker services are synchronized...")
                success, message = ensure_docker_user_consistency(user_id=user_id, auto_fix=True, force_restart=True)
                if success:
                    print_success("Docker services synchronized successfully.")
                else:
                    print_error(f"Docker synchronization failed: {message}")
                    return False

            # Display warnings if any
            if result.get("warnings"):
                for warning in result["warnings"]:
                    print_warning(warning)

            return True
        else:
            error_msg = result.get("error", "Unknown error")

            # Handle the case where user is already logged in
            if "Already logged in" in error_msg:
                print_warning(error_msg)
                print_info("User is already active - configuration is up to date")
                return True
            else:
                print_error(f"Failed to switch user: {error_msg}")
                return False

    except Exception as e:
        print_error(f"Error switching user: {e}")
        return False


def create_user_directories(user_id: str) -> bool:
    """Create necessary directories for the user."""
    try:
        import os

        from personal_agent.core.agno_agent import AgnoPersonalAgent

        print_step("SETUP", f"Creating directories for user '{user_id}'")

        # Temporarily set the USER_ID environment variable
        original_user_id = os.getenv("USER_ID")
        os.environ["USER_ID"] = user_id

        try:
            # Initialize AgnoPersonalAgent with the new user ID to ensure proper directory creation
            agent = AgnoPersonalAgent(user_id=user_id)

            # Get the agent's storage directories
            directories_created = []

            # Check if directories were created by examining the agent's configuration
            from personal_agent.config import refresh_user_dependent_settings

            # Refresh settings to get the correct paths for the new user
            settings = refresh_user_dependent_settings(user_id=user_id)

            # Get the base storage path for the new user
            base_path = settings.get("AGNO_STORAGE_DIR", "")

            # If the base path still contains the original user ID, replace it with the new user ID
            if original_user_id and original_user_id in base_path:
                base_path = base_path.replace(original_user_id, user_id)

            # Create the expected directory paths using the new user's base path
            expected_dirs = []
            if base_path:
                expected_dirs = [
                    base_path,  # Main user directory
                    f"{base_path}/knowledge",
                    f"{base_path}/rag_storage",
                    f"{base_path}/inputs",
                    f"{base_path}/memory_rag_storage",
                    f"{base_path}/memory_inputs",
                ]
            else:
                # Fallback to settings if base_path couldn't be determined
                expected_dirs = [
                    settings.get("AGNO_STORAGE_DIR"),
                    settings.get("AGNO_KNOWLEDGE_DIR"),
                    settings.get("LIGHTRAG_STORAGE_DIR"),
                    settings.get("LIGHTRAG_INPUTS_DIR"),
                    settings.get("LIGHTRAG_MEMORY_STORAGE_DIR"),
                    settings.get("LIGHTRAG_MEMORY_INPUTS_DIR"),
                ]

            # Verify and create any missing directories
            directories_created = []
            directories_existing = []

            for dir_path in expected_dirs:
                if dir_path and Path(dir_path).exists():
                    directories_existing.append(dir_path)
                elif dir_path:
                    try:
                        Path(dir_path).mkdir(parents=True, exist_ok=True)
                        directories_created.append(dir_path)
                    except Exception as e:
                        print_warning(f"Could not create directory {dir_path}: {e}")

            if directories_created:
                print_success(
                    f"Created {len(directories_created)} new user directories:"
                )
                for dir_path in directories_created:
                    print(f"  • {dir_path}")

            if directories_existing:
                print_info(
                    f"Verified {len(directories_existing)} existing user directories:"
                )
                for dir_path in directories_existing:
                    print(f"  • {dir_path}")

            return True

        finally:
            # Restore original USER_ID
            if original_user_id:
                os.environ["USER_ID"] = original_user_id

    except Exception as e:
        print_error(f"Error creating user directories: {e}")
        return False


def display_user_status(user_id: str):
    """Display the current status of the user."""
    try:
        from personal_agent.config import get_current_user_id
        from personal_agent.core.user_manager import UserManager

        print_header(f"User Status: {user_id}")

        user_manager = UserManager()
        current_user = get_current_user_id()

        # Get user details
        user_details = user_manager.get_user_details(user_id)

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


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Switch users in the Personal Agent system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python switch-user.py alice
  python switch-user.py bob --no-restart
  python switch-user.py charlie --user-name "Charlie Brown" --user-type Admin
  python switch-user.py --status alice
        """,
    )

    parser.add_argument("user_id", help="User ID to switch to")

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
        "--no-restart",
        action="store_true",
        help="Don't restart LightRAG services after switching",
    )

    parser.add_argument(
        "--status", action="store_true", help="Display user status instead of switching"
    )

    parser.add_argument(
        "--create-only",
        action="store_true",
        help="Only create the user, don't switch to them",
    )

    args = parser.parse_args()

    # Validate user ID
    if not validate_user_id(args.user_id):
        sys.exit(1)

    print_header("Personal Agent User Switcher")

    # Display status only
    if args.status:
        display_user_status(args.user_id)
        return

    # Get current user info
    current_info = get_current_user_info()
    current_user = current_info["user_id"]

    print_info(f"Current user: {current_user}")
    print_info(f"Target user: {args.user_id}")

    # Check if we're already the target user
    if current_user == args.user_id and not args.create_only:
        print_warning(f"Already logged in as '{args.user_id}'")
        display_user_status(args.user_id)
        return

    # Step 1: Create user if needed
    if not create_user_if_needed(args.user_id, args.user_name, args.user_type):
        print_error("Failed to create user")
        sys.exit(1)

    # Step 2: Create user directories
    if not create_user_directories(args.user_id):
        print_warning("Some user directories could not be created")

    # If create-only mode, stop here
    if args.create_only:
        print_success(f"User '{args.user_id}' created successfully")
        return

    # Step 3: Switch user context
    restart_services = not args.no_restart
    if not switch_user_context(args.user_id, restart_services):
        print_error("Failed to switch user context")
        sys.exit(1)

    # Step 4: Display final status
    print_header("Switch Complete")
    display_user_status(args.user_id)

    print(
        f"\n{Colors.GREEN}{Colors.BOLD}🎉 Successfully switched to user '{args.user_id}'!{Colors.NC}"
    )
    print(
        f"{Colors.CYAN}You can now use the Personal Agent system as '{args.user_id}'.{Colors.NC}"
    )

    if restart_services:
        print(
            f"{Colors.CYAN}LightRAG services have been restarted with the new user context.{Colors.NC}"
        )
    else:
        print(
            f"{Colors.YELLOW}Note: LightRAG services were not restarted. You may need to restart them manually.{Colors.NC}"
        )


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
