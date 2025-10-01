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

# Import configuration
from personal_agent.config import (
    OLLAMA_URL,
    REMOTE_OLLAMA_URL,
)


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
        default=True,
    )

    parser.add_argument(
        "--single",
        action="store_true",
        help="Launch the single-agent mode (default is team mode)",
        default=False,
    )

    return parser.parse_known_args()  # Use parse_known_args to ignore Streamlit's args


def get_available_models(base_url):
    """Query API to get available models - supports both Ollama and LM Studio."""
    import requests

    provider = os.getenv("PROVIDER", "ollama")

    try:
        if provider == "lm-studio":
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
        provider_name = "LM Studio" if provider == "lm-studio" else "Ollama"
        st.error(f"Error connecting to {provider_name} at {base_url}: {str(e)}")
        return []


# Parse arguments and determine configuration
args, unknown = parse_args()
EFFECTIVE_OLLAMA_URL = REMOTE_OLLAMA_URL if args.remote else OLLAMA_URL
RECREATE_FLAG = args.recreate
DEBUG_FLAG = args.debug
SINGLE_FLAG = args.single
