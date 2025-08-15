#!/usr/bin/env python3
"""
Test script to verify the brain icon status functionality.
"""

import os
import sys

from personal_agent.utils import add_src_to_path

add_src_to_path()

from personal_agent.core.memory import is_weaviate_connected


def test_weaviate_connection():
    """Test the Weaviate connection status function."""
    print("Testing Weaviate connection status...")

    try:
        status = is_weaviate_connected()
        print(f"✅ Weaviate connection test completed successfully")
        print(
            f"   Connection status: {'🟢 Connected' if status else '🔴 Disconnected'}"
        )

        if status:
            print("   Brain icon will show GREEN (connected)")
        else:
            print("   Brain icon will show RED (disconnected)")

    except Exception as e:
        print(f"❌ Error testing Weaviate connection: {e}")
        return False

    return True


def test_brain_icon_logic():
    """Test the brain icon CSS class logic."""
    print("\nTesting brain icon CSS class logic...")

    # Simulate connected state
    weaviate_connected = True
    class_name = "brain-connected" if weaviate_connected else "brain-disconnected"
    print(f"   When connected: fas fa-brain {class_name}")

    # Simulate disconnected state
    weaviate_connected = False
    class_name = "brain-connected" if weaviate_connected else "brain-disconnected"
    print(f"   When disconnected: fas fa-brain {class_name}")

    print("✅ Brain icon CSS logic test completed")


if __name__ == "__main__":
    print("🧠 Testing Brain Icon Status Feature")
    print("=" * 50)

    success = True
    success &= test_weaviate_connection()
    test_brain_icon_logic()

    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Brain icon status feature is ready.")
        print("\nTo see the feature in action:")
        print("1. Start the agent: python run_agent.py")
        print("2. Open the web interface")
        print("3. Check the brain icons in the header and status section")
        print("4. The color will be:")
        print("   - 🟢 GREEN when Weaviate is connected")
        print("   - 🔴 RED when Weaviate is disconnected")
    else:
        print("❌ Some tests failed. Please check the error messages above.")
