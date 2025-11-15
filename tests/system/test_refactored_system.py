#!/usr/bin/env python3
"""Test script to verify the refactored system works correctly."""

import logging
import sys
from pathlib import Path

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath()


def test_config_imports():
    """Test that configuration imports work correctly."""
    print("Testing config imports...")
    try:
        from personal_agent.config import (
            USE_MCP,
            USE_WEAVIATE,
            get_mcp_servers,
            get_settings,
        )

        print("✅ Config imports successful")
        print(f"  USE_MCP: {USE_MCP}")
        print(f"  USE_WEAVIATE: {USE_WEAVIATE}")
        print(f"  MCP servers: {len(get_mcp_servers())} configured")
        return True
    except Exception as e:
        print(f"❌ Config imports failed: {e}")
        return False


def test_core_imports():
    """Test that core component imports work correctly."""
    print("\nTesting core imports...")
    try:
        from personal_agent.core import (
            SimpleMCPClient,
            create_agent_executor,
            setup_weaviate,
            vector_store,
            weaviate_client,
        )

        print("✅ Core imports successful")
        return True
    except Exception as e:
        print(f"❌ Core imports failed: {e}")
        return False


def test_tools_imports():
    """Test that tools imports work correctly."""
    print("\nTesting tools imports...")
    try:
        from personal_agent.tools import get_all_tools

        print("✅ Tools imports successful")

        # Test tool creation with None dependencies
        tools = get_all_tools()
        print(f"  Created {len(tools)} tools with no dependencies")
        return True
    except Exception as e:
        print(f"❌ Tools imports failed: {e}")
        return False


def test_web_imports():
    """Test that web interface imports work correctly."""
    print("\nTesting web imports...")
    try:
        from personal_agent.web import create_app, register_routes

        print("✅ Web imports successful")
        return True
    except Exception as e:
        print(f"❌ Web imports failed: {e}")
        return False


def test_utils_imports():
    """Test that utils imports work correctly."""
    print("\nTesting utils imports...")
    try:
        from personal_agent.utils import (
            inject_dependencies,
            register_cleanup_handlers,
            setup_logging,
        )

        print("✅ Utils imports successful")
        return True
    except Exception as e:
        print(f"❌ Utils imports failed: {e}")
        return False


def test_main_import():
    """Test that main module imports work correctly."""
    print("\nTesting main module import...")
    try:
        from personal_agent.main import create_web_app, initialize_system

        print("✅ Main module imports successful")
        return True
    except Exception as e:
        print(f"❌ Main module imports failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🔧 Testing refactored Personal Agent system...\n")

    # Set up basic logging to avoid issues
    logging.basicConfig(level=logging.INFO)

    tests = [
        test_config_imports,
        test_core_imports,
        test_tools_imports,
        test_web_imports,
        test_utils_imports,
        test_main_import,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1

    print(f"\n📊 Test Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The refactored system is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    exit(main())
