#!/usr/bin/env python3
"""Test script to verify the cleanup functionality works properly."""

import logging
import signal
import sys
import time

from personal_agent import cleanup, mcp_client, signal_handler, weaviate_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_cleanup():
    """Test the cleanup functionality."""
    print("🧪 Testing Cleanup Functionality")
    print("=" * 50)

    print("📋 Initial state:")
    print(f"   MCP client available: {mcp_client is not None}")
    print(f"   Weaviate client available: {weaviate_client is not None}")

    if mcp_client:
        print(f"   Active MCP servers: {list(mcp_client.active_servers.keys())}")

    print("\n🔧 Testing cleanup function...")
    try:
        cleanup()
        print("✅ Cleanup function executed successfully")
    except Exception as e:
        print(f"❌ Cleanup function failed: {e}")
        return False

    print("\n🔧 Testing signal handler...")
    try:
        # Test signal handler registration
        original_sigint = signal.signal(signal.SIGINT, signal_handler)
        original_sigterm = signal.signal(signal.SIGTERM, signal_handler)

        # Restore original handlers
        signal.signal(signal.SIGINT, original_sigint)
        signal.signal(signal.SIGTERM, original_sigterm)

        print("✅ Signal handlers registered successfully")
    except Exception as e:
        print(f"❌ Signal handler test failed: {e}")
        return False

    print("\n🎉 All cleanup tests passed!")
    return True


if __name__ == "__main__":
    success = test_cleanup()
    sys.exit(0 if success else 1)
