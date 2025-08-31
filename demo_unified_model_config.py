#!/usr/bin/env python3
"""
Demonstration of the unified model configuration system.

This script shows how the new system provides both parameters and context size
in a single, unified ModelParameters object.
"""

import sys
import os

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from personal_agent.config.model_contexts import (
    get_model_parameters,
    get_model_parameters_dict,
    get_model_config_summary,
    ModelParameters,
)

def demo_unified_config():
    """Demonstrate the unified model configuration system."""
    print("🚀 Unified Model Configuration System Demo")
    print("=" * 60)
    
    # Test models from different families
    test_models = [
        "qwen3:8b",           # Your actual Qwen model
        "llama3.1:8b",        # Llama model with large context
        "codellama:7b",       # Code-focused model
        "phi3:3.8b",          # Reasoning-optimized model
        "unknown-model:1b",   # Unknown model (fallback)
    ]
    
    for model in test_models:
        print(f"\n📋 Configuration for {model}:")
        print("-" * 40)
        
        # Get the unified parameters object
        params, detection_method = get_model_parameters(model)
        
        # Show all parameters including context size
        print(f"🌡️  Temperature: {params.temperature}")
        print(f"🎯 Top P: {params.top_p}")
        print(f"🔢 Top K: {params.top_k}")
        print(f"🔄 Repetition Penalty: {params.repetition_penalty}")
        print(f"📏 Context Size: {params.context_size:,} tokens" if params.context_size else "📏 Context Size: Not specified")
        print(f"🔍 Detection Method: {detection_method}")
        
        # Show as dictionary (useful for API calls)
        params_dict = params.to_dict()
        print(f"📦 As Dictionary: {params_dict}")

def demo_comprehensive_summary():
    """Show the comprehensive summary feature."""
    print(f"\n\n🎯 Comprehensive Model Summary")
    print("=" * 60)
    
    model = "qwen3:8b"
    summary = get_model_config_summary(model)
    print(summary)

def demo_environment_overrides():
    """Show how environment variable overrides would work."""
    print(f"\n\n🔧 Environment Variable Override Examples")
    print("=" * 60)
    
    print("You can override any parameter using environment variables:")
    print("• QWEN3_8B_TEMPERATURE=0.5        # Override temperature for qwen3:8b")
    print("• QWEN3_8B_TOP_P=0.9              # Override top_p for qwen3:8b")
    print("• QWEN3_8B_CTX_SIZE=32768          # Override context size for qwen3:8b")
    print("• DEFAULT_TEMPERATURE=0.8          # Set default temperature for all models")
    print("• DEFAULT_TOP_K=50                 # Set default top_k for all models")
    
    print("\nEnvironment variables take precedence over database values!")

def demo_model_families():
    """Show how different model families have optimized parameters."""
    print(f"\n\n🏷️  Model Family Optimizations")
    print("=" * 60)
    
    families = {
        "Qwen Models": ["qwen3:8b", "qwen2.5:7b"],
        "Code Models": ["codellama:7b", "qwen2.5-coder:3b"],
        "Reasoning Models": ["phi3:3.8b"],
        "Large Context Models": ["llama3.1:8b", "myaniu/qwen2.5-1m"],
    }
    
    for family_name, models in families.items():
        print(f"\n{family_name}:")
        for model in models:
            params = get_model_parameters_dict(model)
            ctx_size = params.get('context_size', 'Unknown')
            ctx_display = f"{ctx_size:,}" if isinstance(ctx_size, int) else ctx_size
            print(f"  • {model}: temp={params['temperature']}, ctx={ctx_display}")

if __name__ == "__main__":
    demo_unified_config()
    demo_comprehensive_summary()
    demo_environment_overrides()
    demo_model_families()
    
    print(f"\n\n✨ Key Benefits of the Unified System:")
    print("=" * 60)
    print("✅ Single source of truth for all model configuration")
    print("✅ Context size and parameters in one object")
    print("✅ Automatic parameter extraction from your Ollama models")
    print("✅ Environment variable overrides for flexibility")
    print("✅ Model-family-specific optimizations")
    print("✅ Backward compatibility with existing code")
    print("✅ Easy integration with any LLM framework")
