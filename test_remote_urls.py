#!/usr/bin/env python3
"""
Test script to check URL handling with --remote flag.
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import REMOTE_LMSTUDIO_URL, settings
from personal_agent.tools.streamlit_config import args, get_appropriate_base_url


def test_url_handling():
    """Test URL handling for different providers and remote flags."""

    print("🌐 Testing URL Handling")
    print("=" * 60)

    # Show current args state
    print(f"**Current Args State:**")
    print(f"  - args.remote: {args.remote}")
    print()

    # Show environment and settings
    print(f"**Environment & Settings:**")
    print(f"  - REMOTE_LMSTUDIO_URL: {REMOTE_LMSTUDIO_URL}")
    print(
        f"  - settings.LMSTUDIO_BASE_URL: {getattr(settings, 'LMSTUDIO_BASE_URL', 'NOT_SET')}"
    )
    print(
        f"  - settings.REMOTE_LMSTUDIO_URL: {getattr(settings, 'REMOTE_LMSTUDIO_URL', 'NOT_SET')}"
    )
    print()

    # Test different provider/remote combinations
    test_cases = [
        ("lm-studio", False),
        ("lm-studio", True),
        ("ollama", False),
        ("ollama", True),
    ]

    print(f"**URL Resolution Tests:**")
    for provider, use_remote in test_cases:
        url = get_appropriate_base_url(provider, use_remote=use_remote)
        remote_text = "REMOTE" if use_remote else "LOCAL"
        print(f"  {provider:12} + {remote_text:6} → {url}")

    print()

    # Show what LM Studio should use based on current args
    lm_studio_url = get_appropriate_base_url("lm-studio", use_remote=args.remote)
    print(f"**LM Studio will use:** {lm_studio_url}")
    print(f"  (based on args.remote = {args.remote})")

    return True


if __name__ == "__main__":
    success = test_url_handling()
    sys.exit(0 if success else 1)
