"""
Main entry point for Streamlit Personal AI Agent.

This module provides the main entry point for running the Streamlit version
of the Personal AI Agent application.
"""

import logging
import sys
from pathlib import Path

# Add the src directory to sys.path to enable imports
repo_root = Path(__file__).parent.parent.parent.parent
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from personal_agent.streamlit.app import main as app_main
    from personal_agent.utils import setup_logging
except ImportError:
    # Fallback for relative imports
    from ..utils import setup_logging
    from .app import main as app_main

# Setup logging for the Streamlit application
logger = setup_logging(name=__name__, level=logging.INFO)


def main() -> None:
    """
    Main entry point for the Streamlit Personal AI Agent application.

    This function initializes logging and starts the Streamlit application.
    """
    try:
        logger.info("Starting Streamlit Personal AI Agent")
        app_main()
    except Exception as e:
        logger.error(f"Failed to start Streamlit application: {e}")
        raise


if __name__ == "__main__":
    main()
