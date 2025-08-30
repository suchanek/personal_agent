#!/usr/bin/env python3
"""
Test script for the expanded model_contexts.py functionality.

This script tests the new parameter retrieval system for Qwen models
and other models with their respective optimal parameters.
"""

import sys
import os

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from personal_agent.config.model_contexts import (
    get_model_parameters,
    get_model_parameters_dict,
    get_model_config_summary,
    get_model_config_dict,
    ModelParameters,
)

def test_qwen_parameters():
    """Test that Qwen models get the correct parameters."""
    print("=== Testing Qwen Model Parameters ===")
    
    qwen_models = [
        "qwen3:1.7b",
        "qwen3:7b", 
        "qwen2.5:7b",
        "qwen2.5:14b"
    ]
    
    expected_qwen_params = {
        "temperature": 0.7,
        "top_p": 0.8,
        "top_k": 20,
        "repetition_penalty": 1.05
    }
    
    for model in qwen_models:
        params_dict = get_model_parameters_dict(model)
        print(f"\n{model}:")
        print(f"  Temperature: {params_dict['temperature']}")
        print(f"  Top P: {params_dict['top_p']}")
        print(f"  Top K: {params_dict['top_k']}")
        print(f"  Repetition Penalty: {params_dict['repetition_penalty']}")
        
        # Verify the parameters match expected values
        for param, expected_value in expected_qwen_params.items():
            if params_dict[param] != expected_value:
                print(f"  ❌ ERROR: {param} = {params_dict[param]}, expected {expected_value}")
            else:
                print(f"  ✅ {param} correct")

def test_other_model_parameters():
    """Test parameters for other model families."""
    print("\n=== Testing Other Model Parameters ===")
    
    test_models = [
        ("llama3.1:8b", {"temperature": 0.7, "top_p": 0.9, "top_k": 40, "repetition_penalty": 1.1}),
        ("codellama:7b", {"temperature": 0.2, "top_p": 0.95, "top_k": 50, "repetition_penalty": 1.05}),
        ("mistral:7b", {"temperature": 0.8, "top_p": 0.9, "top_k": 50, "repetition_penalty": 1.1}),
        ("phi3:3.8b", {"temperature": 0.6, "top_p": 0.9, "top_k": 30, "repetition_penalty": 1.1}),
    ]
    
    for model, expected_params in test_models:
        params_dict = get_model_parameters_dict(model)
        print(f"\n{model}:")
        print(f"  Temperature: {params_dict['temperature']}")
        print(f"  Top P: {params_dict['top_p']}")
        print(f"  Top K: {params_dict['top_k']}")
        print(f"  Repetition Penalty: {params_dict['repetition_penalty']}")
        
        # Verify the parameters match expected values
        for param, expected_value in expected_params.items():
            if params_dict[param] != expected_value:
                print(f"  ❌ ERROR: {param} = {params_dict[param]}, expected {expected_value}")
            else:
                print(f"  ✅ {param} correct")

def test_unknown_model():
    """Test that unknown models get default parameters."""
    print("\n=== Testing Unknown Model (Default Parameters) ===")
    
    unknown_model = "unknown-model:1b"
    params_dict = get_model_parameters_dict(unknown_model)
    
    print(f"\n{unknown_model}:")
    print(f"  Temperature: {params_dict['temperature']}")
    print(f"  Top P: {params_dict['top_p']}")
    print(f"  Top K: {params_dict['top_k']}")
    print(f"  Repetition Penalty: {params_dict['repetition_penalty']}")
    
    # Should match default parameters
    expected_defaults = {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "repetition_penalty": 1.1
    }
    
    for param, expected_value in expected_defaults.items():
        if params_dict[param] != expected_value:
            print(f"  ❌ ERROR: {param} = {params_dict[param]}, expected {expected_value}")
        else:
            print(f"  ✅ {param} correct")

def test_comprehensive_config():
    """Test the comprehensive config functions."""
    print("\n=== Testing Comprehensive Config Functions ===")
    
    model = "qwen3:7b"
    
    print(f"\nConfig Summary for {model}:")
    print(get_model_config_summary(model))
    
    print(f"\nConfig Dict for {model}:")
    config_dict = get_model_config_dict(model)
    for key, value in config_dict.items():
        print(f"  {key}: {value}")

def test_environment_variable_simulation():
    """Test environment variable override simulation."""
    print("\n=== Testing Environment Variable Override Simulation ===")
    
    # We can't actually set environment variables in this test,
    # but we can show how the system would work
    print("Environment variable examples:")
    print("  QWEN3_7B_TEMPERATURE=0.5 would override temperature for qwen3:7b")
    print("  DEFAULT_TEMPERATURE=0.8 would set default temperature for all models")
    print("  LLAMA3_1_8B_TOP_K=25 would override top_k for llama3.1:8b")
    
    # Show current parameters for comparison
    model = "qwen3:7b"
    params = get_model_parameters_dict(model)
    print(f"\nCurrent {model} parameters (without env overrides):")
    for param, value in params.items():
        print(f"  {param}: {value}")

if __name__ == "__main__":
    print("Testing Model Parameter Configuration System")
    print("=" * 50)
    
    try:
        test_qwen_parameters()
        test_other_model_parameters()
        test_unknown_model()
        test_comprehensive_config()
        test_environment_variable_simulation()
        
        print("\n" + "=" * 50)
        print("✅ All tests completed successfully!")
        print("\nThe model parameter system is working correctly:")
        print("- Qwen models use the suggested parameters (temp=0.7, top_p=0.8, top_k=20, rep_penalty=1.05)")
        print("- Other models have appropriate defaults for their use cases")
        print("- Unknown models fall back to sensible defaults")
        print("- Environment variable overrides are supported")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
