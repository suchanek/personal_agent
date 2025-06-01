#!/usr/bin/env python3
"""Test the smolagents web interface."""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from personal_agent.smol_main import create_smolagents_web_app


def test_smolagents_web():
    """Test that the smolagents web interface can be created without errors."""
    try:
        print("🧪 Testing smolagents web interface creation...")
        
        # Create the web app
        app = create_smolagents_web_app()
        
        print("✅ Smolagents web app created successfully!")
        print(f"📍 App name: {app.name}")
        print(f"🔧 Routes available: {[rule.rule for rule in app.url_map.iter_rules()]}")
        
        # Test basic app configuration
        with app.test_client() as client:
            print("🌐 Testing GET request to home page...")
            response = client.get('/')
            print(f"📊 Response status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Home page loads successfully!")
                return True
            else:
                print(f"❌ Home page failed with status: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Error creating smolagents web app: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_smolagents_web()
    sys.exit(0 if success else 1)
