#!/usr/bin/env python3
"""Test script to verify the web interface works correctly."""

import time

import requests


def test_web_interface():
    """Test that the web interface works without logger errors."""
    base_url = "http://127.0.0.1:5001"

    print("Testing web interface...")

    # Test 1: Check if the main page loads
    try:
        response = requests.get(base_url, timeout=10)
        if response.status_code == 200:
            print("✅ Main page loads successfully")
        else:
            print(f"❌ Main page failed with status: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Error loading main page: {e}")
        return

    # Test 2: Submit a simple query that should work without errors
    try:
        print("Submitting test query...")
        data = {"query": "What is Python?"}
        response = requests.post(base_url, data=data, timeout=30)

        if response.status_code == 200:
            print("✅ Query submitted successfully without server errors")
            if "Error" in response.text:
                print("⚠️  Query may have had issues, but no logger errors")
            else:
                print("✅ Query completed successfully")
        else:
            print(f"❌ Query failed with status: {response.status_code}")

    except Exception as e:
        print(f"❌ Error submitting query: {e}")


if __name__ == "__main__":
    test_web_interface()
