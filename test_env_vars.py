#!/usr/bin/env python3
"""
Test if environment variables are properly passed to MCP server subprocess.
"""

import os
import subprocess
import sys
import time


def test_env_var_passing():
    """Test if environment variables are properly passed to subprocess."""
    print("🔍 Testing environment variable passing...")
    
    # Check if token is set
    github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if not github_token:
        print("❌ GITHUB_PERSONAL_ACCESS_TOKEN not set in current environment")
        return False
    
    print(f"✅ GITHUB_PERSONAL_ACCESS_TOKEN found (length: {len(github_token)})")
    print(f"🔑 Token starts with: {github_token[:10]}...")
    
    # Test token format - GitHub Personal Access Tokens should start with 'ghp_' for new format
    # or be 40 characters long for classic tokens
    if github_token.startswith('ghp_'):
        print("✅ Token appears to be new format (starts with ghp_)")
    elif len(github_token) == 40:
        print("✅ Token appears to be classic format (40 characters)")
    else:
        print(f"⚠️ Unusual token format - length: {len(github_token)}")
    
    # Test subprocess environment passing
    print("\n🧪 Testing subprocess environment variable passing...")
    
    # Prepare environment
    env = os.environ.copy()
    env.update({"GITHUB_PERSONAL_ACCESS_TOKEN": github_token})
    
    # Create a simple test script that prints the environment variable
    test_script = """
import os
token = os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN', '')
if token:
    print(f'SUCCESS: Token found in subprocess (length: {len(token)})')
    print(f'Token starts with: {token[:10]}...')
else:
    print('ERROR: Token not found in subprocess')
"""
    
    try:
        result = subprocess.run(
            [sys.executable, "-c", test_script],
            env=env,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        print(f"📤 Subprocess stdout: {result.stdout.strip()}")
        if result.stderr:
            print(f"📤 Subprocess stderr: {result.stderr.strip()}")
        
        return "SUCCESS" in result.stdout
        
    except Exception as e:
        print(f"❌ Error testing subprocess: {e}")
        return False

def test_github_api_directly():
    """Test GitHub API directly with the token."""
    print("\n🌐 Testing GitHub API directly...")
    
    github_token = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")
    if not github_token:
        print("❌ No token to test")
        return False
    
    try:
        import requests
        
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Test with a simple API call
        response = requests.get("https://api.github.com/user", headers=headers, timeout=10)
        
        print(f"📡 GitHub API response status: {response.status_code}")
        
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ GitHub API success - User: {user_data.get('login', 'unknown')}")
            return True
        elif response.status_code == 401:
            print("❌ GitHub API authentication failed - token is invalid")
            print(f"📄 Response: {response.text}")
            return False
        else:
            print(f"⚠️ GitHub API unexpected status: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing GitHub API: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Environment Variable and GitHub API Test")
    print("=" * 50)
    
    env_test = test_env_var_passing()
    api_test = test_github_api_directly()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  Environment Variable Passing: {'✅ PASS' if env_test else '❌ FAIL'}")
    print(f"  GitHub API Authentication: {'✅ PASS' if api_test else '❌ FAIL'}")
    
    if not api_test:
        print("\n💡 Token Issues to Check:")
        print("  1. Token might be expired")
        print("  2. Token might not have required permissions (repo, user)")
        print("  3. Token might be for a different GitHub account")
        print("  4. Generate a new token at: https://github.com/settings/tokens")
