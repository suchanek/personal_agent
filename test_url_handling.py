#!/usr/bin/env python3
"""
Test script to verify URL handling in agent/team initialization.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.tools.streamlit_config import (
    args,
    detect_provider_from_model_name,
    get_appropriate_base_url,
)


def test_url_handling():
    """Test URL handling for different providers."""

    print("🧪 Testing URL Handling for Provider Switching")
    print("=" * 60)

    test_cases = [
        # (model_name, session_url, expected_provider)
        ("qwen3-4b-instruct-2507-mlx", "http://localhost:1234", "lm-studio"),
        ("qwen3:8b", "http://localhost:11434", "ollama"),
        ("gpt-4o", "https://api.openai.com", "openai"),
    ]

    for model_name, session_url, expected_provider in test_cases:
        print(f"\n📋 Test Case: {model_name}")
        print(f"   Session URL: {session_url}")

        # Test provider detection
        detected_provider = detect_provider_from_model_name(model_name)
        provider_match = detected_provider == expected_provider
        print(
            f"   Detected Provider: {detected_provider} {'✅' if provider_match else '❌'}"
        )

        # Test URL generation
        appropriate_url = get_appropriate_base_url(
            detected_provider, use_remote=args.remote
        )
        print(f"   Appropriate URL: {appropriate_url}")

        # Check if session URL matches expected
        url_match = session_url in appropriate_url or appropriate_url in session_url
        print(f"   URL Match: {'✅' if url_match else '❌'}")

        print(f"   Overall: {'✅ PASS' if provider_match and url_match else '❌ FAIL'}")

    print("\n" + "=" * 60)
    print(
        "🎯 Key Insight: When session URL != appropriate URL, we need dynamic override!"
    )


if __name__ == "__main__":
    test_url_handling()
