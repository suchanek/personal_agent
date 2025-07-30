#!/usr/bin/env python3
"""
Debug script to test the LMStudio connection fix.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.core.agent_model_manager import AgentModelManager
from personal_agent.config.settings import LLM_MODEL, LMSTUDIO_URL

def debug_lmstudio_connection():
    """Debug the LMStudio connection configuration."""
    print("🔍 Debugging LMStudio Connection")
    print("=" * 50)
    print(f"LLM_MODEL: {LLM_MODEL}")
    print(f"LMSTUDIO_URL: {LMSTUDIO_URL}")
    print(f"Provider: openai")
    print()
    
    # Create model manager
    model_manager = AgentModelManager(
        model_provider="openai",
        model_name=LLM_MODEL,
        ollama_base_url=LMSTUDIO_URL,
        seed=None,
    )
    
    print("🔧 Model Manager Configuration:")
    print(f"  model_provider: {model_manager.model_provider}")
    print(f"  model_name: {model_manager.model_name}")
    print(f"  ollama_base_url: {model_manager.ollama_base_url}")
    print()
    
    # Check if LMStudio detection works
    is_lmstudio = "localhost:1234" in model_manager.ollama_base_url or "1234" in model_manager.ollama_base_url
    print(f"🎯 LMStudio Detection: {is_lmstudio}")
    print()
    
    try:
        print("📡 Creating model...")
        model = model_manager.create_model()
        print(f"✅ Model created: {type(model).__name__}")
        print(f"   Model ID: {model.id}")
        
        # Check if it has the right base_url
        if hasattr(model, 'base_url'):
            print(f"   Base URL: {model.base_url}")
        if hasattr(model, 'api_key'):
            print(f"   API Key: {model.api_key}")
            
        # Try a simple test
        print("\n🧪 Testing connection...")
        try:
            # This should work if properly configured
            response = model.invoke("Hello, respond with just 'TEST'")
            print(f"✅ Connection successful! Response: {response}")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            
    except Exception as e:
        print(f"❌ Model creation failed: {e}")

if __name__ == "__main__":
    debug_lmstudio_connection()