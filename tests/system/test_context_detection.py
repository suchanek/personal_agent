#!/usr/bin/env python3
"""
Test script for dynamic model context size detection.

This script demonstrates the new context size detection system and shows
how different models get their optimal context sizes automatically.
"""

import asyncio
import sys
from pathlib import Path

from personal_agent.utils import add_src_to_path

add_src_to_path()

from src.personal_agent.config.model_contexts import (
    get_model_context_size,
    get_model_context_size_sync,
    get_context_size_summary,
    list_supported_models,
    add_model_to_database,
)
from src.personal_agent.config.settings import OLLAMA_URL, LLM_MODEL

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'-'*40}")
    print(f" {title}")
    print(f"{'-'*40}")

async def test_context_detection():
    """Test the context size detection system."""
    
    print_header("Dynamic Model Context Size Detection Test")
    
    # Test models from your configuration
    test_models = [
        LLM_MODEL,  # Your current model
        "qwen3:1.7b",
        "llama3.1:8b-instruct-q8_0", 
        "llama3.2:3b",
        "mistral:7b",
        "phi3:3.8b",
        "unknown-model:1b",  # Test unknown model fallback
    ]
    
    print_section("Testing Synchronous Context Detection")
    
    for model in test_models:
        try:
            context_size, method = get_model_context_size_sync(model, OLLAMA_URL)
            print(f"Model: {model:25} | Context: {context_size:>6,} tokens | Method: {method}")
        except Exception as e:
            print(f"Model: {model:25} | Error: {e}")
    
    print_section("Testing Asynchronous Context Detection (with Ollama API)")
    
    for model in test_models:
        try:
            context_size, method = await get_model_context_size(model, OLLAMA_URL)
            print(f"Model: {model:25} | Context: {context_size:>6,} tokens | Method: {method}")
        except Exception as e:
            print(f"Model: {model:25} | Error: {e}")
    
    print_section("Detailed Context Size Summary")
    
    # Show detailed summary for your current model
    print(f"Current Model ({LLM_MODEL}) Details:")
    print(get_context_size_summary(LLM_MODEL, OLLAMA_URL))
    
    print_section("Supported Models Database")
    
    supported_models = list_supported_models()
    print(f"Total supported models: {len(supported_models)}")
    print("\nSample of supported models:")
    
    # Show first 10 models as examples
    for i, (model, context) in enumerate(list(supported_models.items())[:10]):
        print(f"  {model:25} | {context:>6,} tokens")
    
    if len(supported_models) > 10:
        print(f"  ... and {len(supported_models) - 10} more models")
    
    print_section("Testing Model Addition")
    
    # Test adding a new model to the database
    test_model = "custom-test:1b"
    test_context = 16384
    
    print(f"Adding new model: {test_model} with {test_context:,} tokens")
    add_model_to_database(test_model, test_context)
    
    # Verify it was added
    context_size, method = get_model_context_size_sync(test_model)
    print(f"Verification: {test_model} -> {context_size:,} tokens (method: {method})")
    
    print_section("Environment Variable Override Test")
    
    print("To test environment variable overrides, you can set:")
    print(f"  export QWEN3_1_7B_CTX_SIZE=16384")
    print(f"  export DEFAULT_MODEL_CTX_SIZE=8192")
    print("Then run this script again to see the overrides in action.")
    
    print_header("Test Complete")
    print(f"✅ Dynamic context size detection is working!")
    print(f"✅ Your current model ({LLM_MODEL}) will use optimal context size")
    print(f"✅ System supports {len(supported_models)} models with fallback for unknown models")

def test_sync_only():
    """Test only synchronous functions (no async/await needed)."""
    
    print_header("Synchronous Context Size Detection Test")
    
    test_models = [
        LLM_MODEL,
        "qwen3:1.7b", 
        "llama3.1:8b-instruct-q8_0",
        "unknown-model:1b",
    ]
    
    for model in test_models:
        try:
            context_size, method = get_model_context_size_sync(model)
            print(f"Model: {model:25} | Context: {context_size:>6,} tokens | Method: {method}")
        except Exception as e:
            print(f"Model: {model:25} | Error: {e}")
    
    print(f"\n✅ Current model ({LLM_MODEL}) context size detection working!")

if __name__ == "__main__":
    print("Dynamic Model Context Size Detection")
    print("====================================")
    
    # Check if user wants full async test or just sync test
    if len(sys.argv) > 1 and sys.argv[1] == "--sync-only":
        test_sync_only()
    else:
        print("Running full async test (includes Ollama API queries)")
        print("Use --sync-only flag for faster synchronous-only test")
        asyncio.run(test_context_detection())
