#!/usr/bin/env python3
"""
Simplified main entry point for the Personal AI Agent.

This script provides a unified entry point with clear argument parsing for all
operational modes: CLI, web interface, and direct queries.
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import the functions directly
try:
    from personal_agent.agno_main import run_agno_cli, run_agno_web
except ImportError:
    # Fallback import path
    import personal_agent.agno_main as agno_main
    run_agno_cli = agno_main.run_agno_cli
    run_agno_web = agno_main.run_agno_web


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Personal AI Agent - Unified entry point",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --web                    # Start web interface
  %(prog)s --cli                    # Start CLI mode
  %(prog)s --query "Hello world"    # Run single query
  %(prog)s --web --remote-ollama    # Web with remote Ollama
  %(prog)s --cli --remote-ollama    # CLI with remote Ollama
        """,
    )

    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument(
        "--web", action="store_true", help="Start web interface on port 5003"
    )
    mode_group.add_argument("--cli", action="store_true", help="Start CLI mode")
    mode_group.add_argument("--query", type=str, help="Run a single query and exit")

    # Options
    parser.add_argument(
        "--remote-ollama",
        action="store_true",
        help="Use remote Ollama server (tesla.local:11434) instead of local",
    )

    args = parser.parse_args()

    # Print startup banner
    print("\n🤖 Personal AI Agent")
    print("=" * 50)

    if args.web:
        print("🌐 Starting web interface...")
        if args.remote_ollama:
            print("🖥️  Using remote Ollama at: http://tesla.local:11434")
        else:
            print("🖥️  Using local Ollama at: http://localhost:11434")
        print("📍 Access at: http://127.0.0.1:5003")
        print("=" * 50)
        run_agno_web(use_remote_ollama=args.remote_ollama)

    elif args.cli:
        print("💬 Starting CLI mode...")
        if args.remote_ollama:
            print("🖥️  Using remote Ollama at: http://tesla.local:11434")
        else:
            print("🖥️  Using local Ollama at: http://localhost:11434")
        print("=" * 50)
        asyncio.run(run_agno_cli(use_remote_ollama=args.remote_ollama))

    elif args.query:
        print(f"❓ Running query: {args.query}")
        if args.remote_ollama:
            print("🖥️  Using remote Ollama at: http://tesla.local:11434")
        else:
            print("🖥️  Using local Ollama at: http://localhost:11434")
        print("=" * 50)
        asyncio.run(
            run_agno_cli(query=args.query, use_remote_ollama=args.remote_ollama)
        )


if __name__ == "__main__":
    main()
