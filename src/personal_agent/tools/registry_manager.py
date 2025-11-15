"""
User Registry Manager - Recovery and Nuclear Options

Provides tools for managing the user registry including:
- Automatic discovery and recovery from filesystem
- Intelligent merging of existing registry with discovered users
- Nuclear option for complete data destruction

This module provides both programmatic API and CLI interface for
registry management operations.

Author: Eric G. Suchanek, PhD
Revision Date: 2025-11-15
License: Apache 2.0
"""

import shutil
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Optional

from personal_agent.config.runtime_config import get_config
from personal_agent.core.user_registry import UserRegistry


# ANSI colors for CLI output
RED = "\033[0;31m"
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
MAGENTA = "\033[0;35m"
NC = "\033[0m"  # No Color


def print_header(title: str, color: str = BLUE):
    """Print a formatted header.
    
    Args:
        title: Header title text
        color: ANSI color code (default: BLUE)
    """
    print()
    print("━" * 80)
    print(f"{color}{title}{NC}")
    print("━" * 80)
    print()


def print_success(msg: str):
    """Print success message.
    
    Args:
        msg: Success message text
    """
    print(f"{GREEN}✓{NC} {msg}")


def print_error(msg: str):
    """Print error message.
    
    Args:
        msg: Error message text
    """
    print(f"{RED}✗{NC} {msg}")


def print_warning(msg: str):
    """Print warning message.
    
    Args:
        msg: Warning message text
    """
    print(f"{YELLOW}⚠{NC} {msg}")


def print_info(msg: str):
    """Print info message.
    
    Args:
        msg: Info message text
    """
    print(f"{BLUE}ℹ{NC} {msg}")


def show_status(quiet: bool = False) -> Dict[str, Any]:
    """Show current registry status.
    
    Args:
        quiet: If True, return data without printing (default: False)
    
    Returns:
        Dictionary with status information
    """
    if not quiet:
        print_header("User Registry Status")
    
    config = get_config()
    registry = UserRegistry()
    
    status_data = {
        "registry_file": str(registry.registry_file),
        "data_root": config.persag_root,
        "registry_exists": registry.registry_file.exists(),
        "registered_users": [],
        "filesystem_users": [],
    }
    
    if not quiet:
        print(f"Registry file: {CYAN}{registry.registry_file}{NC}")
        print(f"Data root:     {CYAN}{config.persag_root}{NC}")
        print(f"Agno dir:      {CYAN}{config.persag_root}/agno{NC}")
        print()
    
    # Check if registry exists
    if not registry.registry_file.exists():
        if not quiet:
            print_warning("Registry file does not exist")
            print()
    else:
        # Load and show users
        users = registry.get_all_users()
        status_data["registered_users"] = users
        
        if not quiet:
            print(f"Registered users: {len(users)}")
            print()
            
            if users:
                print(f"{CYAN}User ID{NC:20} {CYAN}User Name{NC:25} {CYAN}Created{NC}")
                print("-" * 80)
                for user in users:
                    user_id = user.get("user_id", "?")
                    user_name = user.get("user_name", "?")
                    created = user.get("created_at", "unknown")[:10]
                    print(f"{user_id:20} {user_name:25} {created}")
                print()
    
    # Show filesystem users
    fs_users = registry.discover_filesystem_users()
    status_data["filesystem_users"] = fs_users
    
    if not quiet:
        print(f"Filesystem users: {len(fs_users)}")
        print()
        
        if fs_users:
            print(f"{CYAN}User ID{NC:20} {CYAN}Directory Modified{NC}")
            print("-" * 80)
            for user in fs_users:
                user_id = user.get("user_id", "?")
                last_seen = user.get("last_seen", "unknown")[:10]
                print(f"{user_id:20} {last_seen}")
            print()
    
    return status_data


def show_discovery(quiet: bool = False) -> Dict[str, Any]:
    """Show discovered users without rebuilding.
    
    Args:
        quiet: If True, return data without printing (default: False)
    
    Returns:
        Dictionary with discovery information
    """
    if not quiet:
        print_header("User Discovery")
    
    registry = UserRegistry()
    config = get_config()
    
    # Show what would be discovered
    fs_users = registry.discover_filesystem_users()
    existing_users = {u["user_id"]: u for u in registry.get_all_users()}
    
    discovery_data = {
        "scan_path": f"{config.persag_root}/agno",
        "in_both": [],
        "only_filesystem": [],
        "orphaned": [],
    }
    
    if not quiet:
        print(f"Scanning: {CYAN}{config.persag_root}/agno{NC}")
        print()
    
    if not fs_users:
        if not quiet:
            print_warning("No user directories found in filesystem")
        return discovery_data
    
    # Categorize users
    in_both = []
    only_filesystem = []
    
    for fs_user in fs_users:
        user_id = fs_user["user_id"]
        if user_id in existing_users:
            in_both.append((user_id, existing_users[user_id], fs_user))
        else:
            only_filesystem.append(fs_user)
    
    discovery_data["in_both"] = [(uid, reg_u) for uid, reg_u, _ in in_both]
    discovery_data["only_filesystem"] = only_filesystem
    
    # Show users in both
    if in_both and not quiet:
        print(f"{GREEN}Users with existing profiles ({len(in_both)}):{NC}")
        for user_id, reg_user, fs_user in in_both:
            user_name = reg_user.get("user_name", "?")
            print(f"  • {user_id:20} → {user_name}")
        print()
    
    # Show users only in filesystem
    if only_filesystem and not quiet:
        print(f"{YELLOW}Users to be added ({len(only_filesystem)}):{NC}")
        for fs_user in only_filesystem:
            user_id = fs_user["user_id"]
            user_name = fs_user["user_name"]
            print(f"  • {user_id:20} → {user_name} (inferred)")
        print()
    
    # Show orphaned users (in registry but not filesystem)
    fs_user_ids = {u["user_id"] for u in fs_users}
    orphaned = [u for u in existing_users.values() if u["user_id"] not in fs_user_ids]
    discovery_data["orphaned"] = orphaned
    
    if orphaned and not quiet:
        print(f"{RED}Orphaned users (no directory) ({len(orphaned)}):{NC}")
        for user in orphaned:
            user_id = user.get("user_id", "?")
            user_name = user.get("user_name", "?")
            print(f"  • {user_id:20} → {user_name}")
        print()
    
    return discovery_data


def rebuild_registry(dry_run: bool = False, quiet: bool = False) -> Dict[str, Any]:
    """Rebuild registry from filesystem and existing data.
    
    Args:
        dry_run: If True, preview changes without modifying registry (default: False)
        quiet: If True, return data without printing (default: False)
    
    Returns:
        Dictionary with rebuild results
    """
    if not quiet:
        print_header(f"Rebuilding Registry {'(DRY RUN)' if dry_run else ''}")
    
    registry = UserRegistry()
    
    # Run rebuild
    results = registry.rebuild_registry(merge_existing=True, dry_run=dry_run)
    
    if not results["success"]:
        if not quiet:
            print_error(f"Rebuild failed: {results.get('error', 'Unknown error')}")
        return results
    
    # Show results
    if not quiet:
        print(f"Total users: {CYAN}{results['total_users']}{NC}")
        print()
        
        if results["preserved_users"]:
            print(f"{GREEN}Preserved users with existing profiles ({len(results['preserved_users'])}):{NC}")
            for user_id in results["preserved_users"]:
                print(f"  • {user_id}")
            print()
        
        if results["discovered_users"]:
            print(f"{YELLOW}Newly discovered users ({len(results['discovered_users'])}):{NC}")
            for user_id in results["discovered_users"]:
                print(f"  • {user_id}")
            print()
        
        if results["orphaned_users"]:
            print(f"{RED}Orphaned users (removed from registry) ({len(results['orphaned_users'])}):{NC}")
            for user_id in results["orphaned_users"]:
                print(f"  • {user_id}")
            print()
        
        if results.get("registry_backup"):
            print(f"Backup created: {CYAN}{results['registry_backup']}{NC}")
            print()
        
        if dry_run:
            print_info("This was a dry run - no changes were made")
            print_info("Run without --dry-run to apply changes")
        else:
            print_success("Registry rebuilt successfully!")
    
    return results


def nuke_all_data(confirm: bool = False, quiet: bool = False) -> Dict[str, Any]:
    """Nuclear option - destroy all user data.
    
    Args:
        confirm: If True, skip confirmation prompt (default: False)
        quiet: If True, minimize output (default: False)
    
    Returns:
        Dictionary with destruction results
    """
    if not quiet:
        print_header("☢️  NUCLEAR OPTION - COMPLETE DATA DESTRUCTION ☢️", RED)
    
    config = get_config()
    registry = UserRegistry()
    
    if not quiet:
        print(f"{RED}WARNING: This will permanently delete ALL user data!{NC}")
        print()
        print("This includes:")
        print(f"  • All user directories: {CYAN}{config.persag_root}/agno/*{NC}")
        print(f"  • User registry:        {CYAN}{registry.registry_file}{NC}")
        print(f"  • LightRAG configs:     {CYAN}{config.persag_home}/lightrag_*{NC}")
        print(f"  • Current user file:    {CYAN}{config.persag_home}/env.userid{NC}")
        print()
    
    if not confirm:
        if not quiet:
            print_error("Nuclear option requires --nuke-confirm flag")
            print_info("Run with both --nuke and --nuke-confirm to proceed")
        return {"success": False, "error": "Not confirmed"}
    
    # Final confirmation (unless quiet mode)
    if not quiet:
        print(f"{YELLOW}This action CANNOT be undone!{NC}")
        print()
        response = input(f"Type '{RED}DELETE EVERYTHING{NC}' to confirm: ")
        
        if response != "DELETE EVERYTHING":
            print()
            print_error("Nuclear option cancelled")
            return {"success": False, "error": "User cancelled"}
        
        # Countdown
        print()
        print_warning("Destroying all user data in 5 seconds... (Ctrl+C to cancel)")
        for i in range(5, 0, -1):
            print(f"  {i}...")
            time.sleep(1)
        
        print()
        print_warning("Initiating data destruction...")
        print()
    
    # Destroy data
    destroyed = []
    errors = []
    
    # 1. Stop LightRAG services
    try:
        if not quiet:
            print_info("Stopping LightRAG services...")
        subprocess.run(["./restart-lightrag.sh", "stop"], capture_output=True)
        destroyed.append("LightRAG services stopped")
    except Exception as e:
        errors.append(f"Failed to stop services: {e}")
    
    # 2. Delete user directories
    agno_dir = Path(config.persag_root) / "agno"
    if agno_dir.exists():
        try:
            if not quiet:
                print_info(f"Deleting user directories: {agno_dir}")
            for user_dir in agno_dir.iterdir():
                if user_dir.is_dir():
                    shutil.rmtree(user_dir)
                    destroyed.append(f"Deleted {user_dir.name}/")
        except Exception as e:
            errors.append(f"Failed to delete user directories: {e}")
    
    # 3. Delete registry file
    if registry.registry_file.exists():
        try:
            if not quiet:
                print_info(f"Deleting registry: {registry.registry_file}")
            registry.registry_file.unlink()
            destroyed.append("Deleted users_registry.json")
        except Exception as e:
            errors.append(f"Failed to delete registry: {e}")
    
    # 4. Delete LightRAG configs
    lightrag_dirs = [
        Path(config.persag_home) / "lightrag_server",
        Path(config.persag_home) / "lightrag_memory_server",
    ]
    for lightrag_dir in lightrag_dirs:
        if lightrag_dir.exists():
            try:
                if not quiet:
                    print_info(f"Deleting LightRAG config: {lightrag_dir}")
                shutil.rmtree(lightrag_dir)
                destroyed.append(f"Deleted {lightrag_dir.name}/")
            except Exception as e:
                errors.append(f"Failed to delete {lightrag_dir}: {e}")
    
    # 5. Delete current user file
    userid_file = Path(config.persag_home) / "env.userid"
    if userid_file.exists():
        try:
            if not quiet:
                print_info(f"Deleting current user: {userid_file}")
            userid_file.unlink()
            destroyed.append("Deleted env.userid")
        except Exception as e:
            errors.append(f"Failed to delete userid file: {e}")
    
    # Show results
    if not quiet:
        print()
        print_header("Destruction Complete", RED if not errors else YELLOW)
        
        if destroyed:
            print(f"{RED}Destroyed:{NC}")
            for item in destroyed:
                print(f"  • {item}")
            print()
        
        if errors:
            print(f"{YELLOW}Errors:{NC}")
            for error in errors:
                print(f"  • {error}")
            print()
        
        if not errors:
            print_success("All user data destroyed successfully")
            print()
            print_info("System is now in pristine state")
            print_info("Run ./first-run-setup.sh to create a new user")
        else:
            print_warning("Some items could not be destroyed")
    
    return {
        "success": len(errors) == 0,
        "destroyed": destroyed,
        "errors": errors,
    }
