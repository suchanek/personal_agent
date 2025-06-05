"""
Main entry point for Streamlit Personal AI Agent.

This module provides the main entry point for running the Streamlit version
of the Personal AI Agent application.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the src directory to sys.path to enable imports
repo_root = Path(__file__).parent.parent.parent.parent
src_path = repo_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from personal_agent.agno_main import initialize_agno_system
    from personal_agent.streamlit.app import main as app_main
    from personal_agent.utils import setup_logging
except ImportError:
    # Fallback for relative imports
    from ..agno_main import initialize_agno_system
    from ..utils import setup_logging
    from .app import main as app_main

# Setup logging for the Streamlit application
logger = setup_logging(name=__name__, level=logging.INFO)


async def run_cli_mode() -> None:
    """
    Run the Personal AI Agent in CLI mode with streaming responses.

    This provides direct command-line interaction with the agent,
    using the same agno system as the Streamlit interface.
    """
    print("\n🤖 Personal AI Agent - CLI Mode")
    print("=" * 50)
    print(
        "💡 Tip: Use 'streamlit run' or 'poetry run personal-agent' for web interface"
    )
    print("=" * 50)

    # Initialize the agno system
    try:
        agent = await initialize_agno_system()
        print(
            f"✅ Agent initialized: memory={agent.memory is not None}, knowledge={agent.knowledge is not None}"
        )
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return

    print("\nEnter your queries (type 'quit', 'exit', or 'bye' to exit):")

    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if user_input.lower() in ["quit", "exit", "bye"]:
                print("👋 Goodbye!")
                break

            if not user_input:
                continue

            print("\n🤖 Assistant:")

            # Use native agno agent run method with streaming
            response_stream = await agent.arun(user_input, stream=True)

            # Handle streaming response
            content_parts = []
            async for response_chunk in response_stream:
                if hasattr(response_chunk, "content") and response_chunk.content:
                    print(response_chunk.content, end="", flush=True)
                    content_parts.append(response_chunk.content)

            print()  # Add newline after streaming completes

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error during CLI interaction: {e}")
            print(f"❌ Error: {e}")


def cli_main() -> None:
    """
    Main entry point for CLI mode (used by poetry scripts).

    This function is called by the CLI script entries in pyproject.toml
    to provide command-line interaction with the Personal AI Agent.
    """
    try:
        asyncio.run(run_cli_mode())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"CLI startup error: {e}")
        print(f"❌ Failed to start CLI mode: {e}")


def streamlit_main() -> None:
    """
    Main entry point for launching Streamlit application with proper command.

    This function uses subprocess to run streamlit properly rather than
    calling the app directly, which avoids ScriptRunContext warnings.
    """
    import subprocess
    import sys

    # Get the path to the streamlit app file
    app_file = Path(__file__).parent / "app.py"

    try:
        # Run streamlit with proper command
        cmd = [sys.executable, "-m", "streamlit", "run", str(app_file)]
        logger.info("Launching Streamlit with command: %s", " ".join(cmd))
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Streamlit: {e}")
        raise
    except KeyboardInterrupt:
        logger.info("Streamlit application interrupted by user")


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
    # Check for CLI argument
    if len(sys.argv) > 1 and sys.argv[1] == "cli":
        cli_main()
    else:
        main()
