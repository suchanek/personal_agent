#!/usr/bin/env python3
"""Test the new configuration structure."""

import sys

from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.config import (
    DATA_DIR,
    LLM_MODEL,
    MCP_SERVERS,
    OLLAMA_URL,
    ROOT_DIR,
    USE_MCP,
    USE_WEAVIATE,
    WEAVIATE_URL,
    get_env_var,
)


def test_config():
    """Test that configuration is properly loaded."""
    print("Testing configuration extraction...")

    print(f"ROOT_DIR: {ROOT_DIR}")
    print(f"DATA_DIR: {DATA_DIR}")
    print(f"WEAVIATE_URL: {WEAVIATE_URL}")
    print(f"OLLAMA_URL: {OLLAMA_URL}")
    print(f"LLM_MODEL: {LLM_MODEL}")
    print(f"USE_WEAVIATE: {USE_WEAVIATE}")
    print(f"USE_MCP: {USE_MCP}")

    print(f"MCP_SERVERS keys: {list(MCP_SERVERS.keys())}")

    # Test environment variable function
    test_var = get_env_var("NONEXISTENT_VAR", "default_value")
    print(f"get_env_var test: {test_var}")

    print("✅ Configuration extraction test passed!")


if __name__ == "__main__":
    test_config()
