#!/usr/bin/env python3
"""
Enhanced User Management Demo

Demonstrates the new comprehensive user profile features including
extended fields for email, phone, address, and cognitive state tracking.
"""

import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.core.user_manager import UserManager
from personal_agent.core.user_model import User


def demo_enhanced_user_management():
    """Demonstrate the enhanced user management capabilities."""
    print("Enhanced User Management Demo")
    print("=" * 40)
    
    # Initialize UserManager (will use default config)
    manager = UserManager()
    
    print("\n1. Creating a user with comprehensive profile...")
    result = manager.create_user(
        user_id="demo_user",
        user_name="Demo User",
        user_type="Standard",
        email="demo@example.com",
        phone="555-123-4567",
        address="123 Demo Street, Example City, ST 12345",
        cognitive_state=75
    )
    print(f"Result: {result}")
    
    print("\n2. Getting user details with profile summary...")
    details = manager.get_user_details("demo_user")
    if details:
        print(f"User ID: {details['user_id']}")
        print(f"Name: {details['user_name']}")
        print(f"Email: {details.get('email', 'Not set')}")
        print(f"Phone: {details.get('phone', 'Not set')}")
        print(f"Address: {details.get('address', 'Not set')}")
        print(f"Cognitive State: {details.get('cognitive_state', 'Not set')}")
        
        if 'profile_summary' in details:
            summary = details['profile_summary']
            print(f"Profile Completion: {summary.get('completion_percentage', 0):.1f}%")
            if summary.get('missing_fields'):
                print(f"Missing Fields: {', '.join(summary['missing_fields'])}")
    
    print("\n3. Updating cognitive state...")
    cognitive_result = manager.update_cognitive_state("demo_user", 85)
    print(f"Cognitive state update: {cognitive_result}")
    
    print("\n4. Updating contact information...")
    contact_result = manager.update_contact_info(
        "demo_user",
        email="updated.demo@example.com",
        phone="555-987-6543"
    )
    print(f"Contact update: {contact_result}")
    
    print("\n5. Getting updated profile summary...")
    summary = manager.get_user_profile_summary("demo_user")
    print(f"Profile summary: {summary}")
    
    print("\n6. Demonstrating validation...")
    print("Trying to set invalid cognitive state (150)...")
    invalid_result = manager.update_cognitive_state("demo_user", 150)
    print(f"Validation result: {invalid_result}")
    
    print("Trying to set invalid email...")
    invalid_email_result = manager.update_contact_info("demo_user", email="not-an-email")
    print(f"Email validation result: {invalid_email_result}")
    
    print("\n7. Creating a minimal user (backward compatibility)...")
    minimal_result = manager.create_user("minimal_user", "Minimal User")
    print(f"Minimal user creation: {minimal_result}")
    
    minimal_details = manager.get_user_details("minimal_user")
    if minimal_details:
        print(f"Minimal user cognitive state (default): {minimal_details.get('cognitive_state')}")
        if 'profile_summary' in minimal_details:
            print(f"Minimal user profile completion: {minimal_details['profile_summary'].get('completion_percentage', 0):.1f}%")
    
    print("\n8. Getting all users with profile information...")
    all_users = manager.get_all_users_with_profiles()
    print(f"Total users: {len(all_users)}")
    for user in all_users:
        profile_pct = user.get('profile_summary', {}).get('completion_percentage', 0)
        print(f"  - {user['user_id']}: {profile_pct:.1f}% profile complete")
    
    print("\n✅ Demo completed successfully!")
    print("\nKey Features Demonstrated:")
    print("- Extended user profiles with email, phone, address, cognitive state")
    print("- Comprehensive validation for all fields")
    print("- Profile completion tracking")
    print("- Backward compatibility with existing users")
    print("- Seamless integration with existing UserManager API")


if __name__ == "__main__":
    try:
        demo_enhanced_user_management()
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
