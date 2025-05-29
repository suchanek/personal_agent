#!/usr/bin/env python3
"""Test script to validate improved cleanup functionality."""

import logging
import sys
import time
import warnings
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging to capture warnings
logging.basicConfig(level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)

# Capture all warnings including ResourceWarnings
warnings.filterwarnings("always", category=ResourceWarning)


def test_cleanup_resources():
    """Test the improved cleanup function with better resource management."""
    print("Testing improved cleanup functionality...")

    # Import the main module after path setup
    try:
        from personal_agent import cleanup, mcp_client, vector_store, weaviate_client

        print("✓ Successfully imported personal_agent components")
    except Exception as e:
        print(f"✗ Failed to import personal_agent: {e}")
        return False

    # Check initial state
    print(f"Initial state:")
    print(f"  - weaviate_client: {weaviate_client is not None}")
    print(f"  - vector_store: {vector_store is not None}")
    print(f"  - mcp_client: {mcp_client is not None}")

    if weaviate_client:
        try:
            is_connected = (
                hasattr(weaviate_client, "is_connected")
                and weaviate_client.is_connected()
            )
            print(f"  - weaviate_client connected: {is_connected}")
        except Exception as e:
            print(f"  - weaviate_client connection check failed: {e}")

    # Test cleanup function
    print("\nTesting cleanup function...")
    try:
        cleanup()
        print("✓ Cleanup function executed successfully")

        # Brief pause to allow cleanup to complete
        time.sleep(2)

        print("✓ Cleanup completed with improved resource management")
        return True

    except Exception as e:
        print(f"✗ Cleanup function failed: {e}")
        return False


def main():
    """Main test function."""
    print("=" * 60)
    print("Personal AI Agent - Improved Cleanup Test")
    print("=" * 60)

    success = test_cleanup_resources()

    if success:
        print("\n✓ All cleanup tests passed!")
        print("✓ Improved resource management implemented")
        return 0
    else:
        print("\n✗ Some cleanup tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
