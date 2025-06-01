#!/usr/bin/env python3
"""Test smolagents web interface with actual agent interaction."""

import os
import sys

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "src"))

from personal_agent.smol_main import create_smolagents_web_app


def test_smolagents_agent_interaction():
    """Test actual agent interaction through the web interface."""
    try:
        print("🧪 Testing smolagents agent interaction...")

        # Create the web app
        app = create_smolagents_web_app()

        with app.test_client() as client:
            print("🌐 Testing POST request with agent query...")

            # Test a simple query
            response = client.post(
                "/",
                data={
                    "query": "Hello, can you list the current directory?",
                    "topic": "general",
                },
            )

            print(f"📊 Response status: {response.status_code}")

            if response.status_code == 200:
                # Check if response contains expected elements
                response_text = response.get_data(as_text=True)

                # Look for key indicators of successful agent interaction
                success_indicators = [
                    "Agent Response",  # Response header
                    "Thinking Process",  # Thinking process section
                    "directory",  # Should contain directory listing results
                ]

                found_indicators = []
                for indicator in success_indicators:
                    if indicator.lower() in response_text.lower():
                        found_indicators.append(indicator)

                print(
                    f"✅ Found {len(found_indicators)}/{len(success_indicators)} success indicators"
                )
                print(f"📝 Found: {found_indicators}")

                # Check for smolagents badge
                if "Smolagents" in response_text:
                    print("✅ Smolagents branding present")
                else:
                    print("⚠️ Smolagents branding not found")

                # Look for agent thoughts/processing
                if "Thinking about your request" in response_text:
                    print("✅ Agent thinking process visible")
                else:
                    print("⚠️ Agent thinking process not visible")

                if len(found_indicators) >= 2:  # At least 2 out of 3 success indicators
                    print("✅ Agent interaction test PASSED!")
                    return True
                else:
                    print(
                        "❌ Agent interaction test FAILED - insufficient success indicators"
                    )
                    print("📄 Response preview:")
                    print(
                        response_text[:500] + "..."
                        if len(response_text) > 500
                        else response_text
                    )
                    return False
            else:
                print(f"❌ POST request failed with status: {response.status_code}")
                return False

    except Exception as e:
        print(f"❌ Error testing agent interaction: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_smolagents_agent_interaction()
    sys.exit(0 if success else 1)
