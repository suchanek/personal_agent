#!/usr/bin/env python3
"""
Test script to verify REST API model key fix.

This script tests that the /api/v1/health and /api/v1/status endpoints
return the correct model information from global state.
"""

import json
import sys
import time
from pathlib import Path

import requests

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))


def test_api_endpoints(base_url="http://localhost:8001"):
    """Test REST API endpoints for correct model information."""

    print("=" * 80)
    print("REST API Model Key Fix Test")
    print("=" * 80)
    print()

    # Test 1: Health endpoint
    print("Test 1: GET /api/v1/health")
    print("-" * 80)
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))

            # Check if model is present and not "unknown"
            model = data.get("model", "NOT_FOUND")
            if model != "unknown" and model != "NOT_FOUND":
                print(f"\n✅ PASS: Model correctly retrieved: {model}")
            else:
                print(f"\n❌ FAIL: Model is '{model}' (expected actual model name)")
        else:
            print(f"❌ FAIL: Health check failed with status {response.status_code}")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Could not connect to API: {e}")
        print("\nIs the Streamlit app running? Start it with: poe serve-persag")
        return False

    print()

    # Test 2: Status endpoint
    print("Test 2: GET /api/v1/status")
    print("-" * 80)
    try:
        response = requests.get(f"{base_url}/api/v1/status", timeout=5)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))

            # Check if model is present and not "unknown"
            model = data.get("model", "NOT_FOUND")
            if model != "unknown" and model != "NOT_FOUND":
                print(f"\n✅ PASS: Model correctly retrieved: {model}")
            else:
                print(f"\n❌ FAIL: Model is '{model}' (expected actual model name)")
        else:
            print(f"❌ FAIL: Status check failed with status {response.status_code}")
            print(response.text)

    except requests.exceptions.RequestException as e:
        print(f"❌ ERROR: Could not connect to API: {e}")
        return False

    print()

    # Test 3: Discovery endpoint (bonus test)
    print("Test 3: GET /api/v1/discovery")
    print("-" * 80)
    try:
        response = requests.get(f"{base_url}/api/v1/discovery", timeout=5)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(json.dumps(data, indent=2))
            print(f"\n✅ PASS: Discovery endpoint working")
        else:
            print(
                f"⚠️  WARNING: Discovery endpoint failed with status {response.status_code}"
            )

    except requests.exceptions.RequestException as e:
        print(f"⚠️  WARNING: Could not access discovery endpoint: {e}")

    print()
    print("=" * 80)
    print("Test Complete")
    print("=" * 80)

    return True


def check_global_state():
    """Check global state directly to see what model is stored."""
    print("\nBonus Check: Direct Global State Inspection")
    print("-" * 80)

    try:
        from personal_agent.tools.global_state import get_global_state

        global_state = get_global_state()
        status = global_state.get_status()

        print("Global State Contents:")
        print(f"  - llm_model: {status.get('llm_model', 'NOT_SET')}")
        print(f"  - user: {status.get('user', 'NOT_SET')}")
        print(f"  - agent_mode: {status.get('agent_mode', 'NOT_SET')}")
        print(f"  - agent_available: {status.get('agent_available', False)}")
        print(f"  - team_available: {status.get('team_available', False)}")

        model = status.get("llm_model")
        if model:
            print(f"\n✅ Global state has model: {model}")
        else:
            print(f"\n⚠️  Global state does not have 'llm_model' key")
            print(f"   Available keys: {list(status.keys())}")

    except Exception as e:
        print(f"❌ ERROR checking global state: {e}")
        print("   (This is normal if Streamlit app is not running)")

    print()


if __name__ == "__main__":
    # Check if API port is specified
    api_port = 8001  # Default Streamlit API port

    if len(sys.argv) > 1:
        try:
            api_port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port: {sys.argv[1]}")
            sys.exit(1)

    base_url = f"http://localhost:{api_port}"

    print(f"Testing REST API at: {base_url}")
    print(f"(Use: python {Path(__file__).name} <port> to test different port)")
    print()

    # Run tests
    success = test_api_endpoints(base_url)

    # Check global state if possible
    check_global_state()

    sys.exit(0 if success else 1)
