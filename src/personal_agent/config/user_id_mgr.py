"""User ID management and user-specific configuration functions."""

import logging
import os
import shutil
import sys
from pathlib import Path

# Define the project's base directory.
# This file is at src/personal_agent/config/user_id_mgr.py, so we go up 4 levels for the root.
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
# Default: ~/.persag, overridable via environment variable PERSAG_HOME
PERSAG_HOME = os.getenv("PERSAG_HOME", str(Path.home() / ".persag"))


if __name__ == "__main__":
    # When run directly, use absolute imports
    sys.path.insert(0, str(BASE_DIR))

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)


def load_user_from_file():
    """Initialize PERSAG environment and load user configuration.

    Creates the ~/.persag directory structure if it doesn't exist, copies default
    LightRAG server configurations from the project root, and manages the user ID
    file (env.userid). Sets up the complete user environment on first run.

    Directory Setup:
        - Creates ~/.persag/ if missing
        - Copies lightrag_server/ and lightrag_memory_server/ directories
        - Creates/manages env.userid file with USER_ID configuration

    Returns:
        str: The current user ID (loaded from file or default 'default_user')

    Side Effects:
        - Sets USER_ID in os.environ
        - Creates directory structure and config files
        - Logs setup progress and errors
    """
    try:

        persag_dir = Path(os.getenv("PERSAG_HOME", str(Path.home() / ".persag")))
        userid_file = persag_dir / "env.userid"

        # Create ~/.persag and copy default configs if it doesn't exist
        if not persag_dir.exists():
            _logger.info(f"PERSAG directory not found. Creating at: {persag_dir}")
            persag_dir.mkdir(parents=True, exist_ok=True)

            # Copy lightrag server directories from project root
            project_root = Path(__file__).resolve().parent.parent.parent.parent
            source_server_dir = project_root / "lightrag_server"
            source_memory_dir = project_root / "lightrag_memory_server"
            dest_server_dir = persag_dir / "lightrag_server"
            dest_memory_dir = persag_dir / "lightrag_memory_server"

            try:
                if source_server_dir.exists() and not dest_server_dir.exists():
                    shutil.copytree(source_server_dir, dest_server_dir)
                    _logger.info(f"Copied default lightrag_server to {dest_server_dir}")
                if source_memory_dir.exists() and not dest_memory_dir.exists():
                    shutil.copytree(source_memory_dir, dest_memory_dir)
                    _logger.info(
                        f"Copied default lightrag_memory_server to {dest_memory_dir}"
                    )
            except Exception as copy_e:
                _logger.critical(
                    f"Failed to copy LightRAG directories to {persag_dir}: {copy_e}"
                )

        # Now, manage the env.userid file
        if userid_file.exists():
            with open(userid_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content.startswith("USER_ID="):
                    user_id = content.split("=", 1)[1].strip().strip("'\"")
                    if user_id:
                        os.environ["USER_ID"] = user_id
                        return user_id

        # If file doesn't exist or is empty, create/set a default user
        default_user_id = "default_user"
        with open(userid_file, "w", encoding="utf-8") as f:
            f.write(f'USER_ID="{default_user_id}"\n')
        os.environ["USER_ID"] = default_user_id
        _logger.info(f"Created default USER_ID in {userid_file}")
        return default_user_id

    except Exception as e:
        _logger.warning(f"Failed to load user ID from ~/.persag: {e}")
        fallback_user_id = os.getenv("USER_ID", "default_user")
        os.environ["USER_ID"] = fallback_user_id
        return fallback_user_id


def get_userid() -> str:
    """Retrieve the current USER_ID dynamically from ~/.persag/env.userid.

    Always reads from the filesystem to ensure the most current user ID is returned,
    supporting dynamic user switching without requiring module reload.

    Returns:
        str: Current user ID from ~/.persag/env.userid or 'default_user' fallback
    """
    return load_user_from_file()


def get_current_user_id():
    """Get the current USER_ID dynamically from ~/.persag/env.userid.

    This function always reads from ~/.persag/env.userid to ensure we get the latest value
    after user switching, rather than the cached value from module import time.

    Returns:
        Current USER_ID from ~/.persag/env.userid or default fallback
    """
    return get_userid()


def get_user_storage_paths():
    """Generate user-specific storage directory paths for current user.

    Creates a complete mapping of storage directories customized for the current
    user ID, incorporating the configured storage backend and root paths.
    All paths use environment variable expansion for flexibility.

    Returns:
        dict: Dictionary mapping storage types to their full directory paths:
            - DATA_DIR: General data storage
            - AGNO_STORAGE_DIR: AGNO agent storage root
            - AGNO_KNOWLEDGE_DIR: AGNO knowledge base
            - LIGHTRAG_STORAGE_DIR: LightRAG document storage
            - LIGHTRAG_INPUTS_DIR: LightRAG input files
            - LIGHTRAG_MEMORY_STORAGE_DIR: LightRAG memory storage
            - LIGHTRAG_MEMORY_INPUTS_DIR: LightRAG memory input files
    """
    # Import here to avoid circular imports
    from .settings import PERSAG_ROOT, STORAGE_BACKEND

    current_user_id = get_userid()
    return {
        "USER_DATA_DIR": os.path.expandvars(
            f"{PERSAG_ROOT}/{STORAGE_BACKEND}/{current_user_id}/data"
        ),
        "DATA_DIR": os.path.expandvars(f"{PERSAG_ROOT}"),
        "AGNO_STORAGE_DIR": os.path.expandvars(
            f"{PERSAG_ROOT}/{STORAGE_BACKEND}/{current_user_id}"
        ),
        "AGNO_KNOWLEDGE_DIR": os.path.expandvars(
            f"{PERSAG_ROOT}/{STORAGE_BACKEND}/{current_user_id}/knowledge"
        ),
        "LIGHTRAG_STORAGE_DIR": os.path.expandvars(
            f"{PERSAG_ROOT}/{STORAGE_BACKEND}/{current_user_id}/rag_storage"
        ),
        "LIGHTRAG_INPUTS_DIR": os.path.expandvars(
            f"{PERSAG_ROOT}/{STORAGE_BACKEND}/{current_user_id}/inputs"
        ),
        "LIGHTRAG_MEMORY_STORAGE_DIR": os.path.expandvars(
            f"{PERSAG_ROOT}/{STORAGE_BACKEND}/{current_user_id}/memory_rag_storage"
        ),
        "LIGHTRAG_MEMORY_INPUTS_DIR": os.path.expandvars(
            f"{PERSAG_ROOT}/{STORAGE_BACKEND}/{current_user_id}/memory_inputs"
        ),
    }


def refresh_user_dependent_settings(user_id: str = None):
    """Refresh all USER_ID-dependent settings after user switching.

    This function recalculates all storage paths and settings that depend on USER_ID
    to ensure they reflect the current user after switching.

    Args:
        user_id: Optional user_id to refresh settings for. If not provided,
                 the current user_id from ~/.persag will be used.

    Returns:
        Dictionary with updated settings
    """
    # Import here to avoid circular imports
    from .settings import PERSAG_ROOT, STORAGE_BACKEND

    current_user_id = user_id or get_userid()

    # Recalculate storage directories with current USER_ID using os.path.expandvars
    # to match the behavior of get_user_storage_paths()
    data_dir = os.path.expandvars(
        f"{PERSAG_ROOT}/{STORAGE_BACKEND}/{current_user_id}/data"
    )
    agno_storage_dir = os.path.expandvars(
        f"{PERSAG_ROOT}/{STORAGE_BACKEND}/{current_user_id}"
    )
    agno_knowledge_dir = os.path.expandvars(
        f"{PERSAG_ROOT}/{STORAGE_BACKEND}/{current_user_id}/knowledge"
    )
    lightrag_storage_dir = os.path.expandvars(
        f"{PERSAG_ROOT}/{STORAGE_BACKEND}/{current_user_id}/rag_storage"
    )
    lightrag_inputs_dir = os.path.expandvars(
        f"{PERSAG_ROOT}/{STORAGE_BACKEND}/{current_user_id}/inputs"
    )
    lightrag_memory_storage_dir = os.path.expandvars(
        f"{PERSAG_ROOT}/{STORAGE_BACKEND}/{current_user_id}/memory_rag_storage"
    )
    lightrag_memory_inputs_dir = os.path.expandvars(
        f"{PERSAG_ROOT}/{STORAGE_BACKEND}/{current_user_id}/memory_inputs"
    )

    return {
        "USER_ID": current_user_id,
        "DATA_DIR": data_dir,
        "AGNO_STORAGE_DIR": agno_storage_dir,
        "AGNO_KNOWLEDGE_DIR": agno_knowledge_dir,
        "LIGHTRAG_STORAGE_DIR": lightrag_storage_dir,
        "LIGHTRAG_INPUTS_DIR": lightrag_inputs_dir,
        "LIGHTRAG_MEMORY_STORAGE_DIR": lightrag_memory_storage_dir,
        "LIGHTRAG_MEMORY_INPUTS_DIR": lightrag_memory_inputs_dir,
    }
