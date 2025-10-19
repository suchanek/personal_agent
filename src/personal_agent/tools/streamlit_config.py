"""
Streamlit Configuration and Argument Parsing
============================================

This module handles configuration management and command line argument parsing
for the Personal Agent Streamlit application.

It centralizes configuration logic and provides utilities for managing
application settings.
"""

import argparse
import os

# Import the centralized config system
from personal_agent.config.runtime_config import get_config


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Personal Agent Streamlit App")
    parser.add_argument(
        "--remote", action="store_true", help="Use remote Ollama URL instead of local"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Set debug mode",
        default=False,
    )

    parser.add_argument(
        "--recreate",
        action="store_true",
        help="Recreate the knowledge base and clear all memories",
        default=False,
    )

    parser.add_argument(
        "--single",
        action="store_true",
        help="Launch the single-agent mode (default is team mode)",
        default=False,
    )

    parser.add_argument(
        "--provider",
        type=str,
        choices=["ollama", "lm-studio", "openai"],
        help="Set the LLM provider (ollama, lm-studio, or openai). Overrides PROVIDER environment variable.",
        default=None,
    )

    return parser.parse_known_args()  # Use parse_known_args to ignore Streamlit's args


def detect_provider_from_model_name(model_name):
    """Detect the appropriate provider based on model name patterns.

    Args:
        model_name: The model name to analyze

    Returns:
        str: The detected provider ('ollama', 'lm-studio', 'openai')
    """
    if not model_name:
        return "ollama"

    model_lower = model_name.lower()

    # LM Studio / MLX model patterns
    if any(pattern in model_lower for pattern in ["-mlx", "lm-studio", "lmstudio"]):
        return "lm-studio"

    # OpenAI model patterns
    if model_lower.startswith(("gpt-", "o1-", "o3-")):
        return "openai"

    # Default to ollama for most other models
    return "ollama"


def get_appropriate_base_url(provider, use_remote=False):
    """Get the appropriate base URL for the given provider.

    Args:
        provider: The provider name ('ollama', 'lm-studio', 'openai')
        use_remote: Whether to use remote endpoints

    Returns:
        str: The base URL for the provider
    """
    from personal_agent.config import settings

    if provider == "lm-studio":
        base_url = (
            settings.REMOTE_LMSTUDIO_URL if use_remote else settings.LMSTUDIO_BASE_URL
        )
        # Ensure LM Studio URL doesn't end with /v1 for model fetching
        return base_url.rstrip("/v1").rstrip("/")
    elif provider == "openai":
        return "https://api.openai.com"
    else:  # ollama
        return settings.REMOTE_OLLAMA_URL if use_remote else settings.OLLAMA_URL


def update_provider_and_reinitialize(new_provider, model_name, use_remote=False):
    """Update the provider using PersonalAgentConfig and reinitialize agent/team.

    Args:
        new_provider: The new provider to use ('ollama', 'lm-studio', 'openai')
        model_name: The model name to use with the new provider
        use_remote: Whether to use remote endpoints

    Returns:
        tuple: (success: bool, message: str, base_url: str)
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Get the configuration instance
        config = get_config()

        # Get the old provider for logging
        old_provider = config.provider

        # Update provider (this automatically updates environment variables)
        config.set_provider(new_provider, auto_set_model=False)
        config.set_model(model_name)

        logger.info(
            "🔄 Provider switched from '%s' to '%s'", old_provider, new_provider
        )
        logger.info("🔄 Model updated to '%s'", model_name)

        # Update remote setting if needed
        if use_remote != config.use_remote:
            config.set_use_remote(use_remote)
            logger.info("🔄 Remote setting updated to '%s'", use_remote)

        # Get the effective base URL from config
        base_url = config.get_effective_base_url()

        return True, f"Successfully switched to {new_provider} provider", base_url

    except (OSError, ValueError) as e:
        logger.error("Failed to update provider: %s", e)
        return False, f"Failed to update provider: {str(e)}", ""


def get_available_models(base_url, provider=None):
    """Query API to get available models - supports Ollama, LM Studio, and OpenAI."""
    import requests

    if provider is None:
        provider = os.getenv("PROVIDER", "ollama")

    try:
        if provider == "openai":
            # OpenAI uses /v1/models endpoint with API key authentication
            # Load API key from environment
            import os

            from dotenv import load_dotenv

            load_dotenv()

            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                import streamlit as st

                st.error("OPENAI_API_KEY not found in environment")
                return []

            headers = {"Authorization": f"Bearer {api_key}"}
            # OpenAI API base URL should end with /v1
            if not base_url.endswith("/v1"):
                base_url = base_url.rstrip("/") + "/v1"

            response = requests.get(f"{base_url}/models", headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # OpenAI returns models in data array
                if "data" in data:
                    # Filter to only chat-capable models
                    all_models = [model["id"] for model in data["data"]]
                    chat_models = [
                        m
                        for m in all_models
                        if any(prefix in m.lower() for prefix in ["gpt", "o1", "o3"])
                    ]
                    return sorted(chat_models)
                return []
            else:
                import streamlit as st

                st.warning(
                    f"Failed to fetch models from OpenAI: {response.status_code}"
                )
                # Return common OpenAI models as fallback
                return [
                    "gpt-4.1",
                    "gpt-4.1-mini",
                    "gpt-4o",
                    "gpt-4o-mini",
                    "gpt-4-turbo",
                ]
        elif provider == "lm-studio":
            # LM Studio uses OpenAI-compatible /v1/models endpoint
            response = requests.get(f"{base_url}/v1/models", timeout=5)
            if response.status_code == 200:
                data = response.json()
                # LM Studio returns models in a different format
                models = []
                if "data" in data:
                    models = [model["id"] for model in data["data"]]
                elif isinstance(data, dict) and "models" in data:
                    models = [model["id"] for model in data.get("models", [])]
                return models
            else:
                import streamlit as st

                st.warning(
                    f"Failed to fetch models from LM Studio: {response.status_code}"
                )
                # Return a default model list for LM Studio
                from personal_agent.config import LLM_MODEL

                return ["qwen3-4b-mlx", LLM_MODEL]
        else:
            # Ollama uses /api/tags endpoint
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                models = [model["name"] for model in data.get("models", [])]
                return models
            else:
                import streamlit as st

                st.error(f"Failed to fetch models from Ollama: {response.status_code}")
                return []
    except requests.exceptions.RequestException as e:
        import streamlit as st

        provider_name = (
            "OpenAI"
            if provider == "openai"
            else ("LM Studio" if provider == "lm-studio" else "Ollama")
        )
        st.error(f"Error connecting to {provider_name} at {base_url}: {str(e)}")
        return []


# Parse arguments and determine configuration
args, unknown = parse_args()

# Get the global configuration instance
config = get_config()

# Apply command line arguments to configuration
if args.provider:
    print(f"🔧 Provider set via command line: {args.provider}")
    # Set provider with auto_set_model=True to use provider's default model
    config.set_provider(args.provider, auto_set_model=True)
    print(f"🔧 Model set to provider default: {config.model}")

if args.remote:
    config.set_use_remote(True)
    print(f"🔧 Remote endpoints enabled")

if args.debug:
    config.set_debug_mode(True)
    print(f"🔧 Debug mode enabled")

if args.single:
    config.set_agent_mode("single")
    print(f"🔧 Agent mode set to: single")
else:
    config.set_agent_mode("team")

# Export configuration to module-level variables for backward compatibility
EFFECTIVE_OLLAMA_URL = config.get_effective_base_url()
RECREATE_FLAG = args.recreate
DEBUG_FLAG = args.debug
SINGLE_FLAG = args.single

# For backward compatibility, also import from legacy config
# These will be gradually phased out
from personal_agent.config import OLLAMA_URL, REMOTE_OLLAMA_URL
