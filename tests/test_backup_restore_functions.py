#!/usr/bin/env python3
"""
Test script for the new backup_user() and restore_user() functions in UserManager.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.user_manager import UserManager


def test_backup_restore_functions():
    """Test the backup_user() and restore_user() functions."""

    print("=== Testing UserManager backup_user() and restore_user() functions ===\n")

    # Initialize UserManager
    try:
        user_manager = UserManager()
        print("✓ UserManager initialized successfully")
    except Exception as e:
        print(f"✗ Failed to initialize UserManager: {e}")
        return

    # Test 1: List all users to see what's available
    print("\n1. Listing all users:")
    users = user_manager.get_all_users()
    if users:
        for user in users:
            print(
                f"   - {user['user_id']} ({'current' if user.get('is_current') else 'not current'})"
            )
        test_user_id = users[1]["user_id"]  # Use the first user for testing
    else:
        print("   No users found. Creating a test user...")
        test_user_id = "test_backup_user"
        create_result = user_manager.create_user(
            test_user_id, user_name="Test Backup User"
        )
        if create_result["success"]:
            print(f"   ✓ Created test user: {test_user_id}")
        else:
            print(f"   ✗ Failed to create test user: {create_result.get('error')}")
            return

    print(f"\nUsing user '{test_user_id}' for testing...")

    # Test 2: Try to backup the user
    print(f"\n2. Testing backup_user('{test_user_id}'):")
    backup_result = user_manager.backup_user(test_user_id)

    if backup_result["success"]:
        print("   ✓ Backup successful!")
        print(f"   - Backup path: {backup_result['backup_path']}")
        print(f"   - Files backed up: {backup_result['files_backed_up']}")
        print(f"   - Size: {backup_result['backup_size_mb']:.2f} MB")
        print(f"   - Timestamp: {backup_result['timestamp']}")
        backup_path = backup_result["backup_path"]
    else:
        print(f"   ✗ Backup failed: {backup_result.get('error')}")
        backup_path = None

    # Test 3: List available backups
    print(f"\n3. Testing list_user_backups():")
    backups_result = user_manager.list_user_backups()

    if backups_result["success"]:
        print(f"   ✓ Found {backups_result['total_backups']} backup(s)")
        for backup in backups_result["backups"]:
            print(
                f"   - {backup['backup_name']} ({backup['formatted_date']}, {backup['size_mb']:.2f} MB)"
            )
    else:
        print(f"   ✗ Failed to list backups: {backups_result.get('error')}")

    # Test 4: List backups for specific user
    print(f"\n4. Testing list_user_backups('{test_user_id}'):")
    user_backups_result = user_manager.list_user_backups(test_user_id)

    if user_backups_result["success"]:
        print(
            f"   ✓ Found {user_backups_result['total_backups']} backup(s) for user '{test_user_id}'"
        )
        for backup in user_backups_result["backups"]:
            print(
                f"   - {backup['backup_name']} ({backup['formatted_date']}, {backup['size_mb']:.2f} MB)"
            )
    else:
        print(f"   ✗ Failed to list user backups: {user_backups_result.get('error')}")

    # Test 5: Test restore_user function (dry run first)
    if backup_path:
        backup_name = Path(backup_path).name
        test_restore_user_id = f"{test_user_id}_restored"

        print(f"\n5. Testing restore_user('{test_restore_user_id}', '{backup_name}'):")
        restore_result = user_manager.restore_user(test_restore_user_id, backup_name)

        if restore_result["success"]:
            print("   ✓ Restore successful!")
            print(f"   - Restored from: {restore_result['backup_path']}")
            print(f"   - Restored to: {restore_result['restore_path']}")
            print(
                f"   - Files restored: {restore_result['data_restored']['files_restored']}"
            )
            print(
                f"   - Size: {restore_result['data_restored']['total_size_mb']:.2f} MB"
            )
            print("   - Actions performed:")
            for action in restore_result["actions_performed"]:
                print(f"     • {action}")
        else:
            print(f"   ✗ Restore failed: {restore_result.get('error')}")

    # Test 6: Test error cases
    print(f"\n6. Testing error cases:")

    # Test backup of non-existent user
    print("   a) Backup non-existent user:")
    error_result = user_manager.backup_user("non_existent_user")
    if not error_result["success"]:
        print(f"      ✓ Correctly failed: {error_result['error']}")
    else:
        print("      ✗ Should have failed but didn't")

    # Test restore from non-existent backup
    print("   b) Restore from non-existent backup:")
    error_result = user_manager.restore_user("test_user", "non_existent_backup")
    if not error_result["success"]:
        print(f"      ✓ Correctly failed: {error_result['error']}")
    else:
        print("      ✗ Should have failed but didn't")

    print("\n=== Test completed ===")


if __name__ == "__main__":
    test_backup_restore_functions()
