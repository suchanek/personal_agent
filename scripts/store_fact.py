#!/usr/bin/env python3
"""Store facts in the Personal AI Agent knowledge base.

This script allows you to store facts directly in the Weaviate vector database
that powers the Personal AI Agent's memory system.

Usage:
    python store_fact.py "Your fact here"
    python store_fact.py "Your fact here" --topic "science"

Examples:
    python store_fact.py "Python was created by Guido van Rossum"
    python store_fact.py "The speed of light is 299,792,458 m/s" --topic "physics"
    python store_fact.py "My favorite coffee shop is on Main Street" --topic "personal"

Requirements:
- Weaviate must be running (docker-compose up -d)
- The .venv environment should be activated
"""

import sys
from pathlib import Path

# Add the src directory to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from personal_agent.utils.store_fact import main
except ImportError as e:
    print("❌ Error importing Personal AI Agent modules:")
    print(f"   {e}")
    print()
    print("Make sure you:")
    print("1. Have activated the virtual environment: source .venv/bin/activate")
    print("2. Are running from the project root directory")
    print("3. Have Weaviate running: docker-compose up -d")
    sys.exit(1)

if __name__ == "__main__":
    main()
