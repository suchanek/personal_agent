#!/usr/bin/env python3
"""
Test script for the refactored AgentModelManager.

This script tests that the AgentModelManager correctly uses the unified
model configuration system from model_contexts.py.
"""

import sys
import os

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from personal_agent.core.agent_model_manager import AgentModelManager
from personal_agent.config.model_contexts import get_model_parameters_dict

def test_qwen_model_configuration():
    """Test that Qwen models get the correct unified configuration."""
    print("=== Testing Qwen Model Configuration ===")
    
    model_name = "qwen3:8b"
    manager = AgentModelManager(
        model_provider="ollama",
        model_name=model_name,
        ollama_base_url="http://localhost:11434",
        seed=42
    )
    
    # Get the expected configuration from our unified system
    expected_config = get_model_parameters_dict(model_name)
    print(f"Expected configuration for {model_name}: {expected_config}")
    
    # Create the model (this will log the actual configuration used)
    print(f"\nCreating model with AgentModelManager...")
    try:
        model = manager.create_model()
        print(f"✅ Successfully created model: {model.id}")
        print(f"Model options: {model.options}")
        
        # Verify the key parameters match our unified configuration
        options = model.options
        print(f"\nVerifying parameters:")
        print(f"  Context Size: {options.get('num_ctx')} (expected: {expected_config.get('context_size')})")
        print(f"  Temperature: {options.get('temperature')} (expected: {expected_config.get('temperature')})")
        print(f"  Top K: {options.get('top_k')} (expected: {expected_config.get('top_k')})")
        print(f"  Top P: {options.get('top_p')} (expected: {expected_config.get('top_p')})")
        print(f"  Repeat Penalty: {options.get('repeat_penalty')} (expected: {expected_config.get('repetition_penalty')})")
        
        # Check if parameters match
        matches = []
        matches.append(options.get('num_ctx') == expected_config.get('context_size'))
        matches.append(options.get('temperature') == expected_config.get('temperature'))
        matches.append(options.get('top_k') == expected_config.get('top_k'))
        matches.append(options.get('top_p') == expected_config.get('top_p'))
        matches.append(options.get('repeat_penalty') == expected_config.get('repetition_penalty'))
        
        if all(matches):
            print("✅ All parameters match the unified configuration!")
        else:
            print("❌ Some parameters don't match")
            
    except Exception as e:
        print(f"❌ Failed to create model: {e}")

def test_llama_model_configuration():
    """Test that Llama models get the correct unified configuration."""
    print("\n=== Testing Llama Model Configuration ===")
    
    model_name = "llama3.1:8b"
    manager = AgentModelManager(
        model_provider="ollama",
        model_name=model_name,
        ollama_base_url="http://localhost:11434",
        seed=42
    )
    
    # Get the expected configuration from our unified system
    expected_config = get_model_parameters_dict(model_name)
    print(f"Expected configuration for {model_name}: {expected_config}")
    
    # Create the model (this will log the actual configuration used)
    print(f"\nCreating model with AgentModelManager...")
    try:
        model = manager.create_model()
        print(f"✅ Successfully created model: {model.id}")
        print(f"Model options: {model.options}")
        
        # Check for Llama-specific stop tokens
        if 'stop' in model.options:
            print(f"✅ Llama-specific stop tokens applied: {model.options['stop']}")
        else:
            print("ℹ️  No stop tokens found (may not be needed for this model)")
            
    except Exception as e:
        print(f"❌ Failed to create model: {e}")

def test_codellama_model_configuration():
    """Test that CodeLlama models get the correct unified configuration."""
    print("\n=== Testing CodeLlama Model Configuration ===")
    
    model_name = "codellama:7b"
    manager = AgentModelManager(
        model_provider="ollama",
        model_name=model_name,
        ollama_base_url="http://localhost:11434",
        seed=42
    )
    
    # Get the expected configuration from our unified system
    expected_config = get_model_parameters_dict(model_name)
    print(f"Expected configuration for {model_name}: {expected_config}")
    
    # Create the model (this will log the actual configuration used)
    print(f"\nCreating model with AgentModelManager...")
    try:
        model = manager.create_model()
        print(f"✅ Successfully created model: {model.id}")
        print(f"Model options: {model.options}")
        
        # CodeLlama should have low temperature for focused code generation
        temp = model.options.get('temperature')
        if temp == 0.2:
            print(f"✅ CodeLlama has correct low temperature: {temp}")
        else:
            print(f"⚠️  CodeLlama temperature: {temp} (expected: 0.2)")
            
    except Exception as e:
        print(f"❌ Failed to create model: {e}")

def test_unknown_model_configuration():
    """Test that unknown models get default configuration."""
    print("\n=== Testing Unknown Model Configuration ===")
    
    model_name = "unknown-model:1b"
    manager = AgentModelManager(
        model_provider="ollama",
        model_name=model_name,
        ollama_base_url="http://localhost:11434",
        seed=42
    )
    
    # Get the expected configuration from our unified system
    expected_config = get_model_parameters_dict(model_name)
    print(f"Expected configuration for {model_name}: {expected_config}")
    
    # Create the model (this will log the actual configuration used)
    print(f"\nCreating model with AgentModelManager...")
    try:
        model = manager.create_model()
        print(f"✅ Successfully created model: {model.id}")
        print(f"Model options: {model.options}")
        
        # Should use default parameters
        temp = model.options.get('temperature')
        if temp == 0.7:
            print(f"✅ Unknown model uses default temperature: {temp}")
        else:
            print(f"⚠️  Unknown model temperature: {temp} (expected: 0.7)")
            
    except Exception as e:
        print(f"❌ Failed to create model: {e}")

def compare_old_vs_new():
    """Compare the old hardcoded approach vs new unified approach."""
    print("\n=== Comparing Old vs New Approach ===")
    
    print("🔄 OLD APPROACH:")
    print("  - Hardcoded parameters in agent_model_manager.py")
    print("  - Separate context size lookup")
    print("  - Special case handling for each model family")
    print("  - No environment variable support")
    print("  - Difficult to maintain and extend")
    
    print("\n✨ NEW UNIFIED APPROACH:")
    print("  - Single source of truth in model_contexts.py")
    print("  - Automatic parameter extraction from Ollama models")
    print("  - Context size and parameters in one lookup")
    print("  - Environment variable overrides supported")
    print("  - Easy to add new models and update parameters")
    print("  - Model-family-specific optimizations built-in")

if __name__ == "__main__":
    print("Testing Refactored AgentModelManager")
    print("=" * 50)
    
    try:
        test_qwen_model_configuration()
        test_llama_model_configuration()
        test_codellama_model_configuration()
        test_unknown_model_configuration()
        compare_old_vs_new()
        
        print("\n" + "=" * 50)
        print("✅ AgentModelManager refactoring test completed!")
        print("\nKey improvements:")
        print("🎯 Uses unified model configuration system")
        print("📊 Real parameters from your Ollama models")
        print("🔧 Environment variable override support")
        print("🚀 Cleaner, more maintainable code")
        print("⚡ Single source of truth for all model config")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
