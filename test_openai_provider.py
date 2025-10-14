#!/usr/bin/env python3
"""Test script for OpenAI provider configuration."""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Load environment
load_dotenv()

print("=" * 60)
print("OpenAI Provider Test")
print("=" * 60)

# Test 1: Check API key
print("\n1. Checking OPENAI_API_KEY...")
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"   ✅ API key found (length: {len(api_key)})")
else:
    print("   ❌ API key NOT found")
    sys.exit(1)

# Test 2: Test AgentModelManager
print("\n2. Testing AgentModelManager...")
try:
    from personal_agent.core.agent_model_manager import AgentModelManager

    # Create model manager for OpenAI
    manager = AgentModelManager(
        model_provider="openai",
        model_name="gpt-4o",
        openai_base_url=None  # Should use default URL
    )
    print(f"   ✅ Created AgentModelManager")
    print(f"   Provider: {manager.model_provider}")
    print(f"   Model: {manager.model_name}")

    # Create the model
    model = manager.create_model(use_remote=False)
    print(f"   ✅ Created OpenAI model")
    print(f"   Model ID: {model.id}")
    print(f"   Base URL: {model.base_url}")

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 3: Test get_available_models
print("\n3. Testing get_available_models...")
try:
    from personal_agent.tools.streamlit_config import get_available_models

    models = get_available_models("https://api.openai.com/v1", provider="openai")
    print(f"   ✅ Retrieved {len(models)} models from OpenAI")
    print(f"   First 5 models: {models[:5]}")

except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 60)
print("✅ All tests passed!")
print("=" * 60)
