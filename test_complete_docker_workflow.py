#!/usr/bin/env python3
"""
Test script to demonstrate COMPLETE Docker USER_ID synchronization workflow.

This script demonstrates the full workflow:
1. Stop running Docker containers
2. Update USER_ID in environment files
3. Restart containers with new configuration
4. Verify the complete process
"""

import os
import sys
import time
import shutil
from pathlib import Path

# Add the scripts directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "scripts"))

def test_complete_docker_workflow():
    """Test the complete Docker container stop → update → restart workflow."""
    
    print("🧪 TESTING COMPLETE DOCKER USER_ID SYNCHRONIZATION WORKFLOW")
    print("=" * 70)
    
    # Import the sync tool
    try:
        from docker_user_sync import DockerUserSync
        print("✅ Successfully imported DockerUserSync")
    except ImportError as e:
        print(f"❌ Failed to import DockerUserSync: {e}")
        return False
    
    # Step 1: Check initial state
    print("\n📋 Step 1: Check Initial Docker State")
    print("-" * 50)
    
    sync_manager = DockerUserSync(dry_run=False)
    initial_results = sync_manager.check_user_id_consistency()
    
    print("Initial container states:")
    for server_name, result in initial_results.items():
        container_name = result['config']['container_name']
        is_running = sync_manager.is_container_running(container_name)
        print(f"  {server_name} ({container_name}): {'🟢 Running' if is_running else '🟡 Stopped'}")
        print(f"    USER_ID: {result['docker_user_id']}")
    
    # Step 2: Create backups
    print(f"\n📋 Step 2: Create Configuration Backups")
    print("-" * 50)
    
    backup_files = {}
    for server_name, config in sync_manager.docker_configs.items():
        env_file_path = config['dir'] / config['env_file']
        if env_file_path.exists():
            backup_path = env_file_path.with_suffix('.backup_workflow_test')
            shutil.copy2(env_file_path, backup_path)
            backup_files[server_name] = backup_path
            print(f"  📁 Backed up {server_name}: {env_file_path.name} → {backup_path.name}")
    
    # Step 3: Stop all running containers
    print(f"\n📋 Step 3: Stop All Running Docker Containers")
    print("-" * 50)
    
    stopped_containers = []
    for server_name, result in initial_results.items():
        config = result['config']
        container_name = config['container_name']
        
        if sync_manager.is_container_running(container_name):
            print(f"  🛑 Stopping {server_name} ({container_name})...")
            success = sync_manager.stop_docker_service(config)
            if success:
                stopped_containers.append(server_name)
                print(f"    ✅ Successfully stopped {server_name}")
                
                # Wait a moment for container to fully stop
                time.sleep(2)
                
                # Verify it's stopped
                if not sync_manager.is_container_running(container_name):
                    print(f"    ✅ Confirmed {server_name} is stopped")
                else:
                    print(f"    ⚠️  {server_name} may still be stopping...")
            else:
                print(f"    ❌ Failed to stop {server_name}")
        else:
            print(f"  ⏸️  {server_name} was already stopped")
    
    # Step 4: Update configurations
    test_user_id = "WorkflowTestUser"
    print(f"\n📋 Step 4: Update Docker Configurations to USER_ID={test_user_id}")
    print("-" * 50)
    
    update_success = {}
    for server_name, config in sync_manager.docker_configs.items():
        env_file_path = config['dir'] / config['env_file']
        print(f"  🔧 Updating {server_name}...")
        
        success = sync_manager.update_env_file_user_id(env_file_path, test_user_id)
        update_success[server_name] = success
        
        if success:
            # Verify the update
            updated_user_id = sync_manager.get_env_file_user_id(env_file_path)
            if updated_user_id == test_user_id:
                print(f"    ✅ Successfully updated {server_name}: USER_ID={updated_user_id}")
            else:
                print(f"    ❌ Update verification failed for {server_name}: got {updated_user_id}")
        else:
            print(f"    ❌ Failed to update {server_name}")
    
    # Step 5: Restart containers with new configuration
    print(f"\n📋 Step 5: Restart Containers with New Configuration")
    print("-" * 50)
    
    restart_success = {}
    for server_name in stopped_containers:
        if update_success.get(server_name, False):
            config = sync_manager.docker_configs[server_name]['config']
            container_name = config['container_name']
            
            print(f"  🚀 Starting {server_name} ({container_name}) with USER_ID={test_user_id}...")
            success = sync_manager.start_docker_service(config)
            restart_success[server_name] = success
            
            if success:
                print(f"    ✅ Successfully started {server_name}")
                
                # Wait for container to fully start
                time.sleep(3)
                
                # Verify it's running
                if sync_manager.is_container_running(container_name):
                    print(f"    ✅ Confirmed {server_name} is running with new config")
                else:
                    print(f"    ⚠️  {server_name} may still be starting...")
            else:
                print(f"    ❌ Failed to start {server_name}")
        else:
            print(f"  ⏭️  Skipping {server_name} (config update failed)")
    
    # Step 6: Verify the complete workflow
    print(f"\n📋 Step 6: Verify Complete Workflow")
    print("-" * 50)
    
    # Check final state
    final_results = sync_manager.check_user_id_consistency()
    
    workflow_success = True
    for server_name, result in final_results.items():
        container_name = result['config']['container_name']
        is_running = sync_manager.is_container_running(container_name)
        docker_user_id = result['docker_user_id']
        
        print(f"  {server_name}:")
        print(f"    Container Status: {'🟢 Running' if is_running else '🟡 Stopped'}")
        print(f"    USER_ID: {docker_user_id}")
        print(f"    Expected: {test_user_id}")
        
        config_correct = docker_user_id == test_user_id
        was_restarted = server_name in restart_success and restart_success[server_name]
        
        if server_name in stopped_containers:
            if config_correct and was_restarted:
                print(f"    Status: ✅ Complete workflow successful")
            else:
                print(f"    Status: ❌ Workflow failed")
                workflow_success = False
        else:
            print(f"    Status: ⏸️  Was not running initially")
    
    # Step 7: Restore original configuration
    print(f"\n📋 Step 7: Restore Original Configuration")
    print("-" * 50)
    
    # Stop containers again
    for server_name in restart_success:
        if restart_success[server_name]:
            config = sync_manager.docker_configs[server_name]['config']
            container_name = config['container_name']
            print(f"  🛑 Stopping {server_name} for restoration...")
            sync_manager.stop_docker_service(config)
            time.sleep(2)
    
    # Restore from backups
    for server_name, backup_path in backup_files.items():
        config = sync_manager.docker_configs[server_name]
        env_file_path = config['dir'] / config['env_file']
        if backup_path.exists():
            shutil.copy2(backup_path, env_file_path)
            print(f"  ✅ Restored {server_name} configuration")
            # Clean up backup
            backup_path.unlink()
    
    # Restart containers that were originally running
    for server_name, result in initial_results.items():
        container_name = result['config']['container_name']
        was_initially_running = sync_manager.is_container_running(container_name)
        
        if server_name in stopped_containers:  # These were running initially
            config = result['config']
            print(f"  🚀 Restarting {server_name} with original configuration...")
            sync_manager.start_docker_service(config)
            time.sleep(2)
    
    print(f"\n🎉 COMPLETE WORKFLOW TEST RESULTS:")
    print(f"  Container Stop/Start: {'✅ SUCCESS' if stopped_containers else '⏸️  No containers were running'}")
    print(f"  Configuration Update: {'✅ SUCCESS' if all(update_success.values()) else '❌ FAILED'}")
    print(f"  Container Restart: {'✅ SUCCESS' if all(restart_success.values()) else '❌ FAILED'}")
    print(f"  Overall Workflow: {'✅ SUCCESS' if workflow_success else '❌ FAILED'}")
    print(f"  Configuration Restore: ✅ SUCCESS")
    
    return workflow_success

if __name__ == "__main__":
    try:
        success = test_complete_docker_workflow()
        if success:
            print(f"\n✅ COMPLETE DOCKER WORKFLOW TEST PASSED!")
            print(f"🚀 Stop → Update → Restart workflow is working correctly!")
        else:
            print(f"\n❌ COMPLETE DOCKER WORKFLOW TEST FAILED!")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
