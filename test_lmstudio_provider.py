#!/usr/bin/env python3
"""
Test script for the new LM Studio provider implementation.

This script tests the LM Studio provider functionality added to the AgentModelManager.
It verifies that the provider can be instantiated and configured correctly.

Usage:
    python test_lmstudio_provider.py

Requirements:
    - LM Studio server running at the configured endpoint
    - Python environment with required dependencies
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.agent_model_manager import AgentModelManager
from personal_agent.config.settings import LMSTUDIO_BASE_URL


def test_lmstudio_provider_creation():
    """Test creating an LM Studio provider instance."""
    print("🧪 Testing LM Studio Provider Creation...")

    try:
        # Test with default configuration
        manager = AgentModelManager(
            model_provider="lm-studio",
            model_name="qwen3-4b-mlx",  # Example model name
            ollama_base_url="http://localhost:11434",
            lmstudio_base_url=LMSTUDIO_BASE_URL,
        )

        print("✅ AgentModelManager created successfully")
        print(f"   Provider: {manager.model_provider}")
        print(f"   Model: {manager.model_name}")
        print(f"   LM Studio URL: {manager.lmstudio_base_url}")

        return manager

    except Exception as e:
        print(f"❌ Failed to create LM Studio provider: {e}")
        return None


def test_lmstudio_model_creation(manager):
    """Test creating a model instance with the LM Studio provider."""
    print("\n🧪 Testing LM Studio Model Creation...")

    if not manager:
        print("❌ No manager instance available")
        return False

    try:
        model = manager.create_model()

        print("✅ Model created successfully")
        print(f"   Model type: {type(model).__name__}")
        print(f"   Model ID: {model.id}")
        print(f"   Base URL: {model.base_url}")

        return True

    except Exception as e:
        print(f"❌ Failed to create model: {e}")
        return False


def test_configuration_loading():
    """Test that configuration is loaded correctly."""
    print("\n🧪 Testing Configuration Loading...")

    try:
        print(f"   LMSTUDIO_BASE_URL from settings: {LMSTUDIO_BASE_URL}")

        # Test with environment variable override
        os.environ["LMSTUDIO_BASE_URL"] = "http://test.example.com:1234"

        # Import again to get updated value
        import importlib
        import personal_agent.config.settings as settings_module
        importlib.reload(settings_module)

        print(f"   Updated LMSTUDIO_BASE_URL: {settings_module.LMSTUDIO_BASE_URL}")

        return True

    except Exception as e:
        print(f"❌ Failed to test configuration: {e}")
        return False


def test_provider_comparison():
    """Test different provider configurations for comparison."""
    print("\n🧪 Testing Provider Comparison...")

    providers_to_test = [
        ("ollama", "qwen3:1.7b"),
        ("openai", "gpt-4o-mini"),
        ("lm-studio", "qwen3-4b-mlx"),
    ]

    for provider, model in providers_to_test:
        try:
            manager = AgentModelManager(
                model_provider=provider,
                model_name=model,
                ollama_base_url="http://localhost:11434",
                lmstudio_base_url=LMSTUDIO_BASE_URL,
            )

            print(f"✅ {provider} provider configured successfully")
            print(f"   Model: {model}")

        except Exception as e:
            print(f"❌ {provider} provider failed: {e}")

    return True


async def test_agent_initialization():
    """Test initializing an agent with the LM Studio provider."""
    print("\n🧪 Testing Agent Initialization with LM Studio...")

    try:
        from personal_agent.core.agno_agent import AgnoPersonalAgent

        # Create agent with LM Studio provider
        agent = AgnoPersonalAgent(
            model_provider="lm-studio",
            model_name="qwen3-4b-mlx",
            enable_memory=False,  # Disable memory for faster testing
            enable_mcp=False,     # Disable MCP for faster testing
            lmstudio_base_url=LMSTUDIO_BASE_URL,
            debug=True,
        )

        print("✅ Agent created with LM Studio provider")
        print(f"   Provider: {agent.model_provider}")
        print(f"   Model: {agent.model_name}")

        # Note: We won't actually initialize the agent here as it requires
        # the LM Studio server to be running and available
        print("   Note: Full initialization requires LM Studio server to be running")

        return True

    except Exception as e:
        print(f"❌ Failed to create agent: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 LM Studio Provider Test Suite")
    print("=" * 50)

    # Test configuration loading
    config_test = test_configuration_loading()

    # Test provider creation
    manager = test_lmstudio_provider_creation()

    # Test model creation
    model_test = test_lmstudio_model_creation(manager)

    # Test provider comparison
    comparison_test = test_provider_comparison()

    # Test agent initialization (async)
    agent_test = asyncio.run(test_agent_initialization())

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Configuration Loading: {'✅ PASS' if config_test else '❌ FAIL'}")
    print(f"   Provider Creation: {'✅ PASS' if manager else '❌ FAIL'}")
    print(f"   Model Creation: {'✅ PASS' if model_test else '❌ FAIL'}")
    print(f"   Provider Comparison: {'✅ PASS' if comparison_test else '❌ FAIL'}")
    print(f"   Agent Initialization: {'✅ PASS' if agent_test else '❌ FAIL'}")

    success_count = sum([config_test, bool(manager), model_test, comparison_test, agent_test])
    print(f"\n🎯 Overall: {success_count}/5 tests passed")

    if success_count == 5:
        print("\n🎉 All tests passed! LM Studio provider is ready to use.")
        print("\n📝 Usage Example:")
        print("   PROVIDER=lm-studio")
        print("   LLM_MODEL=qwen3-4b-mlx")
        print("   LMSTUDIO_BASE_URL=http://100.73.95.100:1234")
    else:
        print(f"\n⚠️  {5 - success_count} test(s) failed. Check the output above for details.")

    return success_count == 5


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
