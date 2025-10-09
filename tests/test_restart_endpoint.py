#!/usr/bin/env python3
"""
Test script for the REST API restart endpoint
"""

import requests
import json
import sys
from datetime import datetime

def test_restart_endpoint(base_url="http://localhost:8002"):
    """Test the system restart endpoint."""
    print(f"🔄 Testing system restart endpoint at {base_url}")

    try:
        # Make POST request to restart endpoint
        response = requests.post(f"{base_url}/api/v1/system/restart", timeout=60)
        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            if data.get("success") == "True":
                print("   ✅ System restart successful!")
                print(f"   Message: {data.get('message')}")
                print(f"   Agent Mode: {data.get('agent_mode')}")
                print(f"   Model: {data.get('model')}")
                print(f"   Timestamp: {data.get('timestamp')}")
                return True
            else:
                print(f"   ❌ Restart failed: {data.get('error')}")
                return False
        else:
            print(f"   ❌ Restart request failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data.get('error', 'Unknown error')}")
            except:
                print(f"   Response: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection failed: {str(e)}")
        return False

def check_system_status_after_restart(base_url="http://localhost:8002"):
    """Check system status after restart."""
    print(f"\n📊 Checking system status after restart at {base_url}")

    try:
        response = requests.get(f"{base_url}/api/v1/status", timeout=10)
        print(f"   Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"   System status: {data['status']}")
            print(f"   Agent available: {data.get('agent_available', 'Unknown')}")
            print(f"   Team available: {data.get('team_available', 'Unknown')}")
            print(f"   Memory available: {data.get('memory_available', 'Unknown')}")
            print(f"   Knowledge available: {data.get('knowledge_available', 'Unknown')}")
            return data
        else:
            print(f"   ❌ Status check failed with status {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Connection failed: {str(e)}")
        return None

if __name__ == "__main__":
    print("Personal Agent REST API Restart Endpoint Test")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    base_url = "http://localhost:8003"

    # Test the restart endpoint
    restart_success = test_restart_endpoint(base_url)

    if restart_success:
        # Check status after restart
        status_data = check_system_status_after_restart(base_url)

        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)

        if status_data:
            agent_available = status_data.get('agent_available') == 'Yes'
            team_available = status_data.get('team_available') == 'Yes'
            memory_available = status_data.get('memory_available') == 'Yes'
            knowledge_available = status_data.get('knowledge_available') == 'Yes'

            if agent_available or team_available:
                print("✅ Restart test PASSED - System reinitialized successfully")
                print(f"   Agent/Team available: {'Yes' if agent_available or team_available else 'No'}")
                print(f"   Memory available: {'Yes' if memory_available else 'No'}")
                print(f"   Knowledge available: {'Yes' if knowledge_available else 'No'}")
            else:
                print("⚠️  Restart test PARTIAL - Restart completed but no agent/team available")
                print("   This may be expected if initialization takes time")
        else:
            print("❌ Restart test FAILED - Could not verify system status after restart")
    else:
        print("\n❌ Restart test FAILED - Restart endpoint returned error")

    print("=" * 50)
