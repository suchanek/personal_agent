"""
Core utilities for the Personal Agent package.
"""
import sys
from pathlib import Path

def add_src_to_path():
    """
    Adds the project's 'src' directory to the Python path to allow for absolute imports.
    This is useful for scripts in subdirectories like tests/ or scripts/ that need to
    import from the `personal_agent` package before it might be installed.
    """
    # The file is in src/personal_agent/ so .parents[2] is the project root.
    project_root = Path(__file__).resolve().parents[2]
    src_dir = project_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))
