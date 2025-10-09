#!/usr/bin/env python3
"""
Test User Endpoints
===================

This script tests the new user management REST API endpoints.
"""

import json
import sys
from pathlib import Path

import requests

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
if src_path not in sys.path:
    sys.path.insert(0, str(src_path))


def test_list_users(base_url="http://100.100.248.61:8002"):
    """Test GET /api/v1/users endpoint."""
    print("🧑 Testing GET /api/v1/users")

    try:
        response = requests.get(f"{base_url}/api/v1/users", timeout=10)
        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success: {data.get('success')}")
            print(f"   Total users: {data.get('total_count', 0)}")

            users = data.get("users", [])
            if users:
                print("   Users found:")
                for user in users[:3]:  # Show first 3 users
                    print(
                        f"     - {user.get('user_id', 'unknown')}: {user.get('user_name', 'unknown')}"
                    )
                if len(users) > 3:
                    print(f"     ... and {len(users) - 3} more")
            else:
                print("   No users found")

            return True
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection failed: {str(e)}")
        return False


def test_switch_user(base_url="http://100.100.248.61:8002"):
    """Test POST /api/v1/users/switch endpoint."""
    print("\n🔄 Testing POST /api/v1/users/switch")

    # First get list of users to pick one
    try:
        response = requests.get(f"{base_url}/api/v1/users", timeout=10)
        if response.status_code != 200:
            print("   ❌ Cannot get user list to test switch")
            return False

        users = response.json().get("users", [])
        if not users:
            print("   ❌ No users available to test switch")
            return False

        # Pick the first user
        test_user = users[1]
        user_id = test_user.get("user_id")

        print(f"   Attempting to switch to user: {user_id}")

        # Test switch user
        switch_data = {
            "user_id": user_id,
            "restart_containers": False,  # Don't restart containers for testing
        }

        response = requests.post(
            f"{base_url}/api/v1/users/switch", json=switch_data, timeout=30
        )

        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success") == "True":
                print(f"   ✅ Successfully switched to user: {data.get('user_id')}")
                print(f"   Message: {data.get('message')}")
                return True
            else:
                print(f"   ❌ Switch failed: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"   ❌ Switch failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection failed: {str(e)}")
        return False


def main():
    """Main test function."""
    print("Personal Agent User Endpoints Test")
    print("=" * 40)

    base_url = "http://100.100.248.61:8002"

    # Test 1: List users
    list_ok = test_list_users(base_url)

    # Test 2: Switch user (only if list worked)
    if list_ok:
        switch_ok = test_switch_user(base_url)
    else:
        switch_ok = False
        print("\n🔄 Skipping switch test due to list failure")

    # Summary
    print("\n" + "=" * 40)
    print("TEST SUMMARY")
    print("=" * 40)

    if list_ok and switch_ok:
        print("✅ All user endpoint tests passed!")
    elif list_ok:
        print("⚠️  List users works, but switch user failed")
    else:
        print("❌ User endpoints are not working")
        print("\nTroubleshooting:")
        print("1. Make sure the dashboard is running")
        print("2. Check that REST API server started")
        print("3. Verify user management system is initialized")

    print("=" * 40)


if __name__ == "__main__":
    main()
