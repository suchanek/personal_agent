#!/usr/bin/env python3
"""
Test script to verify OllamaTools integration is working correctly.

This script tests the basic functionality of the updated AgentModelManager
and AgnoPersonalAgent with OllamaTools integration.
"""

import asyncio
import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.config.settings import LLM_MODEL, OLLAMA_URL
from personal_agent.core.agent_model_manager import AgentModelManager
from personal_agent.core.agno_agent import AgnoPersonalAgent


async def test_model_manager():
    """Test that the AgentModelManager creates OllamaTools correctly."""
    print("🧪 Testing AgentModelManager with OllamaTools...")

    try:
        # Create model manager
        model_manager = AgentModelManager(
            model_provider="ollama",
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            seed=42,
        )

        # Create model
        model = model_manager.create_model()

        # Verify it's an OllamaTools instance
        from agno.models.ollama.tools import OllamaTools

        if isinstance(model, OllamaTools):
            print("✅ AgentModelManager successfully created OllamaTools instance")
            print(f"   Model ID: {model.id}")
            print(f"   Model Name: {model.name}")
            print(f"   Provider: {model.provider}")
            print(f"   Host: {model.host}")
            return True
        else:
            print(f"❌ Expected OllamaTools, got {type(model)}")
            return False

    except Exception as e:
        print(f"❌ Error testing AgentModelManager: {e}")
        return False


async def test_agent_initialization():
    """Test that the AgnoPersonalAgent initializes with OllamaTools."""
    print("\n🧪 Testing AgnoPersonalAgent initialization...")

    try:
        # Create agent with minimal configuration
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name=LLM_MODEL,
            enable_memory=False,  # Disable memory for simple test
            enable_mcp=False,  # Disable MCP for simple test
            debug=True,
        )

        # Initialize agent
        success = await agent.initialize()

        if success:
            print("✅ AgnoPersonalAgent initialized successfully")

            # Check that the model is OllamaTools
            if hasattr(agent.agent, "model"):
                from agno.models.ollama.tools import OllamaTools

                if isinstance(agent.agent.model, OllamaTools):
                    print("✅ Agent is using OllamaTools model")
                    return True
                else:
                    print(
                        f"❌ Agent is using {type(agent.agent.model)} instead of OllamaTools"
                    )
                    return False
            else:
                print("❌ Agent doesn't have a model attribute")
                return False
        else:
            print("❌ AgnoPersonalAgent initialization failed")
            return False

    except Exception as e:
        print(f"❌ Error testing AgnoPersonalAgent: {e}")
        return False


async def test_simple_query():
    """Test a simple query to verify OllamaTools response handling."""
    print("\n🧪 Testing simple query with OllamaTools...")

    try:
        # Create agent with minimal configuration
        agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name=LLM_MODEL,
            enable_memory=True,  # Disable memory for simple test
            enable_mcp=False,  # Disable MCP for simple test
            debug=True,
        )

        # Initialize agent
        success = await agent.initialize()
        if not success:
            print("❌ Failed to initialize agent for query test")
            return False

        # Test simple query
        print("   Sending test query: 'Hello, how are you?'")
        response = await agent.run("Hello, how are you?")

        if response and len(response.strip()) > 0:
            print("✅ Query successful!")
            print(
                f"   Response: {response[:100]}{'...' if len(response) > 100 else ''}"
            )
            return True
        else:
            print("❌ Query returned empty response")
            return False

    except Exception as e:
        print(f"❌ Error testing simple query: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Testing OllamaTools Integration")
    print("=" * 50)

    tests = [
        ("Model Manager", test_model_manager),
        ("Agent Initialization", test_agent_initialization),
        ("Simple Query", test_simple_query),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")

    passed = 0
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! OllamaTools integration is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the output above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
