"""
Docker Integration Module

This module provides integration between the personal agent system and Docker-based
LightRAG servers, ensuring USER_ID consistency across all components.

Author: Personal Agent Development Team
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, Tuple

# Import DockerUserSync from the proper module
try:
    from .docker import DockerUserSync
except ImportError:
    # Try absolute import when running as script
    try:
        from personal_agent.core.docker import DockerUserSync
    except ImportError as e:
        logging.warning(f"Could not import DockerUserSync: {e}")
        DockerUserSync = None

# Handle relative imports when running as script vs module
try:
    from ..config.user_id_mgr import get_userid
    from ..utils.pag_logging import setup_logging
except ImportError:
    # Running as script, use absolute imports
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from personal_agent.config import get_userid
    from personal_agent.utils.pag_logging import setup_logging

logger = setup_logging()

class DockerIntegrationManager:
    """Manages Docker integration for the personal agent system."""
    
    def __init__(self, user_id: Optional[str] = None):
        """Initialize the Docker integration manager.
        
        Args:
            user_id: User ID to ensure consistency for (defaults to system USER_ID)
        """
        self.user_id = user_id or get_userid()
        
        # Fix: Use the same robust project root detection as DockerUserSync
        current_path = Path(__file__).resolve()
        project_root = None
        
        # Walk up the directory tree looking for project markers
        for parent in current_path.parents:
            # Look for common project root indicators
            if any((parent / marker).exists() for marker in [
                'pyproject.toml', 'setup.py', '.git',
                'lightrag_server', 'lightrag_memory_server'
            ]):
                project_root = parent
                break
        
        if project_root is None:
            # Fallback to the old method if no markers found
            project_root = Path(__file__).parent.parent.parent.parent.resolve()
            logger.warning("DockerIntegrationManager: Using fallback path detection")
        
        self.base_dir = project_root
        
        # Initialize Docker sync manager if available
        self.docker_sync = None
        if DockerUserSync:
            try:
                self.docker_sync = DockerUserSync(dry_run=False)
                logger.debug("Docker sync manager initialized successfully")
            except Exception as e:
                logger.warning(f"Failed to initialize Docker sync manager: {e}")
        else:
            logger.warning("DockerUserSync not available - Docker integration disabled")

    def check_docker_consistency(self) -> Tuple[bool, str]:
        """Check if Docker configurations are consistent with system USER_ID.
        
        Returns:
            Tuple of (is_consistent, message)
        """
        if not self.docker_sync:
            return True, "Docker sync not available - skipping consistency check"
        
        try:
            results = self.docker_sync.check_user_id_consistency()
            all_consistent = all(result['consistent'] for result in results.values())
            
            if all_consistent:
                return True, f"All Docker configurations consistent with USER_ID: {self.user_id}"
            else:
                inconsistent_servers = [
                    name for name, result in results.items() 
                    if not result['consistent']
                ]
                return False, f"Inconsistent Docker servers: {', '.join(inconsistent_servers)}"
                
        except Exception as e:
            logger.error(f"Error checking Docker consistency: {e}")
            return False, f"Error checking Docker consistency: {e}"

    def ensure_docker_consistency(self, force_restart: bool = False) -> Tuple[bool, str]:
        """Ensure Docker configurations are consistent with system USER_ID.
        
        Args:
            force_restart: If True, restart containers even if not running
            
        Returns:
            Tuple of (success, message)
        """
        if not self.docker_sync:
            return True, "Docker sync not available - skipping consistency enforcement"
        
        try:
            # First check if sync is needed
            is_consistent, check_message = self.check_docker_consistency()
            
            if is_consistent and not force_restart:
                logger.info("Docker configurations already consistent")
                return True, check_message
            elif is_consistent and force_restart:
                logger.info("Docker configurations consistent, but force restart requested")
                # Perform synchronization with force restart even if consistent
                success = self.docker_sync.sync_user_ids(force_restart=True)
                if success:
                    message = f"Successfully force restarted Docker containers with USER_ID: {self.user_id}"
                    logger.info(message)
                    return True, message
                else:
                    message = "Failed to force restart Docker containers"
                    logger.error(message)
                    return False, message
            else:
                logger.info(f"Docker inconsistency detected: {check_message}")
                logger.info("Attempting to synchronize Docker configurations...")
                
                # Perform synchronization
                success = self.docker_sync.sync_user_ids(force_restart=force_restart)
                
                if success:
                    message = f"Successfully synchronized Docker configurations with USER_ID: {self.user_id}"
                    logger.info(message)
                    return True, message
                else:
                    message = "Failed to synchronize Docker configurations"
                    logger.error(message)
                    return False, message
                
        except Exception as e:
            error_msg = f"Error ensuring Docker consistency: {e}"
            logger.error(error_msg)
            return False, error_msg

    def validate_system_consistency(self) -> Tuple[bool, str]:
        """Perform comprehensive validation of system consistency.
        
        Returns:
            Tuple of (is_consistent, message)
        """
        if not self.docker_sync:
            return True, "Docker sync not available - skipping validation"
        
        try:
            is_consistent = self.docker_sync.validate_system_consistency()
            
            if is_consistent:
                return True, f"System is fully consistent with USER_ID: {self.user_id}"
            else:
                return False, "System inconsistencies detected - check logs for details"
                
        except Exception as e:
            error_msg = f"Error validating system consistency: {e}"
            logger.error(error_msg)
            return False, error_msg

    def pre_initialization_check(self, auto_fix: bool = True, force_restart: bool = False) -> Tuple[bool, str]:
        """Perform pre-initialization consistency check and optional auto-fix.
        
        This method should be called before initializing the personal agent system
        to ensure Docker configurations are consistent.
        
        Args:
            auto_fix: If True, automatically fix inconsistencies
            force_restart: If True, restart containers even if not running
            
        Returns:
            Tuple of (ready_to_proceed, message)
        """
        logger.info(f"Performing pre-initialization Docker consistency check for USER_ID: {self.user_id}")
        
        # Check current consistency
        is_consistent, check_message = self.check_docker_consistency()
        
        if is_consistent and not force_restart:
            logger.info("Pre-initialization check passed - Docker configurations consistent")
            return True, check_message
        elif is_consistent and force_restart:
            logger.info("Docker configurations consistent, but force restart requested")
            # Even if consistent, we need to restart if force_restart is True
            if auto_fix:
                logger.info("Performing force restart of Docker containers...")
                fix_success, fix_message = self.ensure_docker_consistency(force_restart=True)
                if fix_success:
                    return True, f"Force restart completed: {fix_message}"
                else:
                    return False, f"Force restart failed: {fix_message}"
            else:
                return True, f"Consistent but force restart requested (auto-fix disabled): {check_message}"
        
        logger.warning(f"Pre-initialization check failed: {check_message}")
        
        if not auto_fix:
            return False, f"Docker inconsistency detected (auto-fix disabled): {check_message}"
        
        logger.info("Attempting to auto-fix Docker inconsistencies...")
        
        # Attempt to fix inconsistencies
        fix_success, fix_message = self.ensure_docker_consistency(force_restart=force_restart)
        
        if fix_success:
            logger.info("Auto-fix successful - system ready for initialization")
            return True, f"Auto-fixed Docker inconsistencies: {fix_message}"
        else:
            logger.error("Auto-fix failed - manual intervention required")
            return False, f"Failed to auto-fix Docker inconsistencies: {fix_message}"


def ensure_docker_user_consistency(user_id: Optional[str] = None, auto_fix: bool = True, force_restart: bool = False) -> Tuple[bool, str]:
    """Convenience function to ensure Docker USER_ID consistency.
    
    This function can be called from agent initialization code to ensure
    Docker configurations are consistent before proceeding.
    
    Args:
        user_id: User ID to ensure consistency for (defaults to system USER_ID)
        auto_fix: If True, automatically fix inconsistencies
        force_restart: If True, restart containers even if not running
        
    Returns:
        Tuple of (ready_to_proceed, message)
    """
    try:
        manager = DockerIntegrationManager(user_id=user_id)
        return manager.pre_initialization_check(auto_fix=auto_fix, force_restart=force_restart)
    except Exception as e:
        error_msg = f"Error in Docker consistency check: {e}"
        logger.error(error_msg)
        return False, error_msg


def stop_lightrag_services() -> Tuple[bool, str]:
    """Convenience function to stop all LightRAG Docker services.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # We don't need a user_id to stop services, but manager needs it.
        manager = DockerIntegrationManager()
        if not manager.docker_sync:
            return True, "Docker sync not available - skipping stop services"
            
        success = manager.docker_sync.stop_all_services()
        if success:
            return True, "All LightRAG services stopped successfully."
        else:
            return False, "Failed to stop one or more LightRAG services."
            
    except Exception as e:
        error_msg = f"Error stopping LightRAG services: {e}"
        logger.error(error_msg)
        return False, error_msg


def check_docker_user_consistency(user_id: Optional[str] = None) -> Tuple[bool, str]:
    """Convenience function to check Docker USER_ID consistency without fixing.
    
    Args:
        user_id: User ID to check consistency for (defaults to system USER_ID)
        
    Returns:
        Tuple of (is_consistent, message)
    """
    try:
        manager = DockerIntegrationManager(user_id=user_id)
        return manager.check_docker_consistency()
    except Exception as e:
        error_msg = f"Error checking Docker consistency: {e}"
        logger.error(error_msg)
        return False, error_msg


if __name__ == "__main__":
    # Test the integration
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Docker integration")
    parser.add_argument('--user-id', help='User ID to test with')
    parser.add_argument('--check-only', action='store_true', help='Only check, do not fix')
    args = parser.parse_args()
    
    user_id = args.user_id or get_userid()
    
    if args.check_only:
        is_consistent, message = check_docker_user_consistency(user_id)
        print(f"Consistency check: {'PASS' if is_consistent else 'FAIL'}")
        print(f"Message: {message}")
    else:
        ready, message = ensure_docker_user_consistency(user_id, auto_fix=True)
        print(f"Ready to proceed: {'YES' if ready else 'NO'}")
        print(f"Message: {message}")
