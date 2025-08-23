#!/usr/bin/env python3
"""Test script to verify Qwen model configuration settings."""

import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from personal_agent.config.settings import (
    LLM_MODEL,
    QWEN_INSTRUCT_TEMPERATURE,
    QWEN_INSTRUCT_MIN_P,
    QWEN_INSTRUCT_TOP_P,
    QWEN_INSTRUCT_TOP_K,
    QWEN_THINKING_TEMPERATURE,
    QWEN_THINKING_MIN_P,
    QWEN_THINKING_TOP_P,
    get_qwen_instruct_settings,
    get_qwen_thinking_settings,
)

def test_qwen_configuration():
    """Test and display Qwen model configuration."""
    print("=" * 60)
    print("QWEN MODEL CONFIGURATION TEST")
    print("=" * 60)
    
    print(f"\nModel Path: {LLM_MODEL}")
    
    print("\n--- INSTRUCT MODEL SETTINGS ---")
    print(f"Temperature: {QWEN_INSTRUCT_TEMPERATURE}")
    print(f"Min_P: {QWEN_INSTRUCT_MIN_P}")
    print(f"Top_P: {QWEN_INSTRUCT_TOP_P}")
    print(f"Top_K: {QWEN_INSTRUCT_TOP_K}")
    
    print("\n--- THINKING MODEL SETTINGS ---")
    print(f"Temperature: {QWEN_THINKING_TEMPERATURE}")
    print(f"Min_P: {QWEN_THINKING_MIN_P}")
    print(f"Top_P: {QWEN_THINKING_TOP_P}")
    
    print("\n--- HELPER FUNCTIONS TEST ---")
    instruct_settings = get_qwen_instruct_settings()
    thinking_settings = get_qwen_thinking_settings()
    
    print("Instruct Settings Dictionary:")
    for key, value in instruct_settings.items():
        print(f"  {key}: {value} (type: {type(value).__name__})")
    
    print("Thinking Settings Dictionary:")
    for key, value in thinking_settings.items():
        print(f"  {key}: {value} (type: {type(value).__name__})")
    
    print("\n--- VERIFICATION ---")
    # Verify the values match the requirements
    expected_instruct = {
        "temperature": 0.7,
        "min_p": 0.0,
        "top_p": 0.8,
        "top_k": 20
    }
    
    expected_thinking = {
        "temperature": 0.6,
        "min_p": 0.0,
        "top_p": 0.95
    }
    
    instruct_match = all(
        instruct_settings[key] == expected_instruct[key] 
        for key in expected_instruct
    )
    
    thinking_match = all(
        thinking_settings[key] == expected_thinking[key] 
        for key in expected_thinking
    )
    
    print(f"✅ Instruct settings match requirements: {instruct_match}")
    print(f"✅ Thinking settings match requirements: {thinking_match}")
    print(f"✅ Model path configured: {LLM_MODEL == 'hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M'}")
    
    if instruct_match and thinking_match:
        print("\n🎉 ALL QWEN CONFIGURATION TESTS PASSED!")
    else:
        print("\n❌ Some configuration tests failed!")
        return False
    
    return True

if __name__ == "__main__":
    success = test_qwen_configuration()
    sys.exit(0 if success else 1)
