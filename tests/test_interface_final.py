#!/usr/bin/env python3
"""
Test script to verify the interface.py fixes work correctly.
"""

import os
import sys

sys.path.append("src")


def test_interface_imports():
    """Test that all imports work correctly."""
    try:
        from personal_agent.core.memory import is_weaviate_connected as memory_check
        from personal_agent.web.interface import index, is_weaviate_connected

        print("✅ All imports successful")
        return True
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def test_weaviate_connection():
    """Test the Weaviate connection check."""
    try:
        from personal_agent.core.memory import is_weaviate_connected

        status = is_weaviate_connected()
        print(f"✅ Weaviate connection status: {status}")
        return True
    except Exception as e:
        print(f"❌ Weaviate connection check error: {e}")
        return False


def test_interface_function():
    """Test the interface index function."""
    try:
        from unittest.mock import Mock

        from flask import Flask

        from personal_agent.web.interface import index

        # Mock the Flask app and request
        app = Flask(__name__)

        # Mock the global variables
        import personal_agent.web.interface as interface_module

        interface_module.app = app
        interface_module.agent_executor = Mock()
        interface_module.logger = Mock()
        interface_module.query_knowledge_base_func = None
        interface_module.store_interaction_func = None

        # Test GET request
        with app.test_request_context(method="GET"):
            result = index()
            print("✅ GET request handled successfully")

        # Test POST request
        with app.test_request_context(
            method="POST",
            data={"query": "test query", "topic": "test", "session_id": "test_session"},
        ):
            result = index()
            print("✅ POST request handled successfully")

        return True
    except Exception as e:
        print(f"❌ Interface function error: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("🧪 Testing interface.py functionality...\n")

    tests = [
        ("Imports", test_interface_imports),
        ("Weaviate Connection", test_weaviate_connection),
        ("Interface Function", test_interface_function),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"Running {test_name} test:")
        result = test_func()
        results.append(result)
        print()

    # Summary
    passed = sum(results)
    total = len(results)
    print(f"📊 Test Results: {passed}/{total} passed")

    if passed == total:
        print("🎉 All tests passed! Interface.py is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    main()
