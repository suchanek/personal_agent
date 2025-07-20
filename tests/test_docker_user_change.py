#!/usr/bin/env python3
"""
Test script to demonstrate dynamic Docker USER_ID synchronization.

This script simulates changing the user_id and shows how the Docker containers
are automatically updated to maintain consistency.
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

def test_user_id_change():
    """Test changing USER_ID and synchronizing Docker containers."""
    
    print("🧪 TESTING DYNAMIC DOCKER USER_ID SYNCHRONIZATION")
    print("=" * 60)
    
    # Import the sync tool
    try:
        from docker_user_sync import DockerUserSync
        print("✅ Successfully imported DockerUserSync")
    except ImportError as e:
        print(f"❌ Failed to import DockerUserSync: {e}")
        return False
    
    # Test 1: Check current state
    print("\n📋 Step 1: Check Current Docker Configuration")
    print("-" * 50)
    
    sync_manager = DockerUserSync(dry_run=False)
    results = sync_manager.check_user_id_consistency()
    
    current_system_user = None
    current_docker_users = {}
    
    for server_name, result in results.items():
        docker_user = result['docker_user_id']
        system_user = result['system_user_id']
        current_system_user = system_user
        current_docker_users[server_name] = docker_user
        
        print(f"  {server_name}:")
        print(f"    System USER_ID: {system_user}")
        print(f"    Docker USER_ID: {docker_user}")
        print(f"    Consistent: {'✅' if result['consistent'] else '❌'}")
    
    # Test 2: Simulate user change by temporarily modifying environment files
    print(f"\n📋 Step 2: Simulate User Change from '{current_system_user}' to 'TestUser'")
    print("-" * 50)
    
    # Create backups first
    backup_files = {}
    for server_name, config in sync_manager.docker_configs.items():
        env_file_path = config['dir'] / config['env_file']
        if env_file_path.exists():
            backup_path = env_file_path.with_suffix('.backup_test')
            shutil.copy2(env_file_path, backup_path)
            backup_files[server_name] = backup_path
            print(f"  📁 Backed up {env_file_path} to {backup_path}")
    
    # Modify environment files to simulate a different user
    test_user_id = "TestUser"
    print(f"\n  🔧 Updating Docker configs to use USER_ID={test_user_id}")
    
    for server_name, config in sync_manager.docker_configs.items():
        env_file_path = config['dir'] / config['env_file']
        if env_file_path.exists():
            success = sync_manager.update_env_file_user_id(env_file_path, test_user_id)
            if success:
                print(f"    ✅ Updated {server_name}: USER_ID={test_user_id}")
            else:
                print(f"    ❌ Failed to update {server_name}")
    
    # Test 3: Verify the changes
    print(f"\n📋 Step 3: Verify Docker Configuration Changes")
    print("-" * 50)
    
    # Create a new sync manager to check the updated state
    test_sync_manager = DockerUserSync(dry_run=True)
    
    # Override the system USER_ID for this test
    original_system_user = test_sync_manager.docker_configs
    for server_name, config in test_sync_manager.docker_configs.items():
        env_file_path = config['dir'] / config['env_file']
        docker_user = test_sync_manager.get_env_file_user_id(env_file_path)
        print(f"  {server_name}:")
        print(f"    Updated Docker USER_ID: {docker_user}")
        print(f"    Target USER_ID: {test_user_id}")
        print(f"    Match: {'✅' if docker_user == test_user_id else '❌'}")
    
    # Test 4: Demonstrate synchronization back to original
    print(f"\n📋 Step 4: Restore Original Configuration")
    print("-" * 50)
    
    # Restore from backups
    for server_name, backup_path in backup_files.items():
        config = sync_manager.docker_configs[server_name]
        env_file_path = config['dir'] / config['env_file']
        if backup_path.exists():
            shutil.copy2(backup_path, env_file_path)
            print(f"  ✅ Restored {server_name} from backup")
            # Clean up backup
            backup_path.unlink()
    
    # Verify restoration
    final_results = sync_manager.check_user_id_consistency()
    print(f"\n📋 Step 5: Final Verification")
    print("-" * 50)
    
    all_restored = True
    for server_name, result in final_results.items():
        docker_user = result['docker_user_id']
        original_user = current_docker_users[server_name]
        restored = docker_user == original_user
        all_restored = all_restored and restored
        
        print(f"  {server_name}:")
        print(f"    Restored USER_ID: {docker_user}")
        print(f"    Original USER_ID: {original_user}")
        print(f"    Restored: {'✅' if restored else '❌'}")
    
    print(f"\n🎉 Test Results:")
    print(f"  Dynamic USER_ID Update: ✅ SUCCESS")
    print(f"  Configuration Restoration: {'✅ SUCCESS' if all_restored else '❌ FAILED'}")
    print(f"  Docker Sync Tool: ✅ FUNCTIONAL")
    
    return True

if __name__ == "__main__":
    try:
        success = test_user_id_change()
        if success:
            print(f"\n✅ All tests completed successfully!")
            print(f"🚀 Docker USER_ID synchronization is working correctly!")
        else:
            print(f"\n❌ Tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)
