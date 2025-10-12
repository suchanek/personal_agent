#!/usr/bin/env python3
"""
Test script to verify model context size detection for Q6_K model.
"""

import os
import sys

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from personal_agent.config.model_contexts import (
    get_model_config_dict,
    get_model_config_summary,
    get_model_context_size_sync,
    get_model_parameters,
)


def test_q6k_model():
    """Test the Q6_K model configuration."""
    model_name = "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K"

    print(f"Testing model: {model_name}")
    print("=" * 80)

    # Test context size detection
    context_size, detection_method = get_model_context_size_sync(model_name)
    print(f"Context Size: {context_size:,} tokens")
    print(f"Detection Method: {detection_method}")
    print()

    # Test model parameters
    parameters, param_method = get_model_parameters(model_name)
    print("Model Parameters:")
    print(f"  Temperature: {parameters.temperature}")
    print(f"  Top P: {parameters.top_p}")
    print(f"  Top K: {parameters.top_k}")
    print(f"  Repetition Penalty: {parameters.repetition_penalty}")
    print(f"  Context Size: {parameters.context_size:,} tokens")
    print(f"  Parameter Detection Method: {param_method}")
    print()

    # Test complete config
    config_dict = get_model_config_dict(model_name)
    print("Complete Configuration Dictionary:")
    for key, value in config_dict.items():
        if key == "parameters":
            print(f"  {key}:")
            for param_key, param_value in value.items():
                if param_key == "context_size":
                    print(f"    {param_key}: {param_value:,}")
                else:
                    print(f"    {param_key}: {param_value}")
        else:
            if key == "context_size":
                print(f"  {key}: {value:,}")
            else:
                print(f"  {key}: {value}")
    print()

    # Test summary
    print("Model Configuration Summary:")
    print("-" * 40)
    summary = get_model_config_summary(model_name)
    print(summary)

    # Validation
    print("\n" + "=" * 80)
    print("VALIDATION:")
    expected_context = 12232
    if context_size == expected_context:
        print(f"✅ PASS: Context size is correct ({context_size:,} tokens)")
    else:
        print(f"❌ FAIL: Expected {expected_context:,} tokens, got {context_size:,}")

    if parameters.context_size == expected_context:
        print(
            f"✅ PASS: Parameters context size is correct ({parameters.context_size:,} tokens)"
        )
    else:
        print(
            f"❌ FAIL: Expected {expected_context:,} tokens in parameters, got {parameters.context_size:,}"
        )


if __name__ == "__main__":
    test_q6k_model()
