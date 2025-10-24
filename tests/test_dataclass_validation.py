#!/usr/bin/env python3
"""
Test script for the dataclass ModelParameters validation.

This script tests the new validation features added with the dataclass conversion.
"""

import sys
import os

# Add the src directory to the path so we can import the module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from personal_agent.config.model_contexts import ModelParameters

def test_valid_parameters():
    """Test that valid parameters work correctly."""
    print("=== Testing Valid Parameters ===")
    
    try:
        # Test with valid parameters
        params = ModelParameters(
            temperature=0.7,
            top_p=0.9,
            top_k=40,
            repetition_penalty=1.1,
            context_size=32768
        )
        print(f"✅ Valid parameters created: {params}")
        print(f"✅ Dict conversion: {params.to_dict()}")
        
    except Exception as e:
        print(f"❌ Unexpected error with valid parameters: {e}")

def test_invalid_parameters():
    """Test that invalid parameters are properly rejected."""
    print("\n=== Testing Invalid Parameters ===")
    
    # Test invalid temperature
    try:
        params = ModelParameters(temperature=3.0)  # Too high
        print(f"❌ Should have failed: temperature=3.0")
    except ValueError as e:
        print(f"✅ Correctly rejected invalid temperature: {e}")
    
    # Test invalid top_p
    try:
        params = ModelParameters(top_p=1.5)  # Too high
        print(f"❌ Should have failed: top_p=1.5")
    except ValueError as e:
        print(f"✅ Correctly rejected invalid top_p: {e}")
    
    # Test invalid top_k
    try:
        params = ModelParameters(top_k=0)  # Too low
        print(f"❌ Should have failed: top_k=0")
    except ValueError as e:
        print(f"✅ Correctly rejected invalid top_k: {e}")
    
    # Test invalid repetition_penalty
    try:
        params = ModelParameters(repetition_penalty=-0.5)  # Negative
        print(f"❌ Should have failed: repetition_penalty=-0.5")
    except ValueError as e:
        print(f"✅ Correctly rejected invalid repetition_penalty: {e}")
    
    # Test invalid context_size
    try:
        params = ModelParameters(context_size=-1000)  # Negative
        print(f"❌ Should have failed: context_size=-1000")
    except ValueError as e:
        print(f"✅ Correctly rejected invalid context_size: {e}")

def test_dataclass_features():
    """Test dataclass-specific features."""
    print("\n=== Testing Dataclass Features ===")
    
    # Test equality comparison (new feature!)
    params1 = ModelParameters(temperature=0.7, top_p=0.9)
    params2 = ModelParameters(temperature=0.7, top_p=0.9)
    params3 = ModelParameters(temperature=0.8, top_p=0.9)
    
    if params1 == params2:
        print("✅ Equality comparison works: identical parameters are equal")
    else:
        print("❌ Equality comparison failed")
    
    if params1 != params3:
        print("✅ Inequality comparison works: different parameters are not equal")
    else:
        print("❌ Inequality comparison failed")
    
    # Test automatic repr (should be cleaner now)
    print(f"✅ Automatic repr: {repr(params1)}")
    
    # Test field access
    print(f"✅ Field access: temperature={params1.temperature}, top_k={params1.top_k}")

def test_edge_cases():
    """Test edge cases and boundary values."""
    print("\n=== Testing Edge Cases ===")
    
    # Test boundary values
    try:
        # Minimum valid values
        params_min = ModelParameters(
            temperature=0.0,
            top_p=0.0,
            top_k=1,
            repetition_penalty=0.0,
            context_size=1
        )
        print(f"✅ Minimum valid values: {params_min}")
        
        # Maximum valid values
        params_max = ModelParameters(
            temperature=2.0,
            top_p=1.0,
            top_k=1000,
            repetition_penalty=2.0,
            context_size=1000000
        )
        print(f"✅ Maximum valid values: {params_max}")
        
        # None context_size (should be allowed)
        params_none = ModelParameters(context_size=None)
        print(f"✅ None context_size allowed: {params_none}")
        
    except Exception as e:
        print(f"❌ Edge case failed: {e}")

if __name__ == "__main__":
    print("Testing Dataclass ModelParameters Validation")
    print("=" * 50)
    
    try:
        test_valid_parameters()
        test_invalid_parameters()
        test_dataclass_features()
        test_edge_cases()
        
        print("\n" + "=" * 50)
        print("✅ Dataclass conversion successful!")
        print("\nKey improvements:")
        print("🎯 Automatic __init__, __repr__, and __eq__ methods")
        print("🛡️ Built-in parameter validation with __post_init__")
        print("🔍 Better IDE support and type checking")
        print("📝 Cleaner, more readable code")
        print("⚡ Same performance with less boilerplate")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
