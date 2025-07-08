#!/usr/bin/env python3
"""
Test script to verify that the multi-user implementation is working correctly.
"""

import os
from src.personal_agent.core.agno_agent import AgnoPersonalAgent
from src.personal_agent.config.settings import AGNO_STORAGE_DIR, AGNO_KNOWLEDGE_DIR, USER_ID

def test_multiuser_paths():
    """Test that the multi-user paths are correctly configured."""
    
    print("🧪 Testing Multi-User Path Configuration")
    print("=" * 50)
    
    # Test 1: Check settings values
    print(f"📁 AGNO_STORAGE_DIR from settings: {AGNO_STORAGE_DIR}")
    print(f"📁 AGNO_KNOWLEDGE_DIR from settings: {AGNO_KNOWLEDGE_DIR}")
    print(f"👤 USER_ID from settings: {USER_ID}")
    print()
    
    # Test 2: Create agent with default parameters (should use settings)
    print("🤖 Creating AgnoPersonalAgent with default parameters...")
    agent = AgnoPersonalAgent()
    
    print(f"✅ Agent storage_dir: {agent.storage_dir}")
    print(f"✅ Agent knowledge_dir: {agent.knowledge_dir}")
    print(f"✅ Agent user_id: {agent.user_id}")
    print()
    
    # Test 3: Verify paths include user ID
    expected_storage_pattern = f"agno/{USER_ID}"
    expected_knowledge_pattern = f"knowledge/{USER_ID}"
    
    storage_correct = expected_storage_pattern in agent.storage_dir
    knowledge_correct = expected_knowledge_pattern in agent.knowledge_dir
    
    print("🔍 Path Validation:")
    print(f"   Storage path contains '{expected_storage_pattern}': {'✅' if storage_correct else '❌'}")
    print(f"   Knowledge path contains '{expected_knowledge_pattern}': {'✅' if knowledge_correct else '❌'}")
    print()
    
    # Test 4: Test with different user ID
    print("🧪 Testing with custom user_id...")
    custom_agent = AgnoPersonalAgent(user_id="test_user")
    print(f"✅ Custom agent user_id: {custom_agent.user_id}")
    print(f"✅ Custom agent storage_dir: {custom_agent.storage_dir}")
    print(f"✅ Custom agent knowledge_dir: {custom_agent.knowledge_dir}")
    print()
    
    # Summary
    all_correct = storage_correct and knowledge_correct
    print("📊 Test Results:")
    print(f"   Multi-user paths: {'✅ WORKING' if all_correct else '❌ BROKEN'}")
    
    if all_correct:
        print("\n🎉 SUCCESS: Multi-user implementation is working correctly!")
        print("   - Default parameters now use user-specific paths from settings")
        print("   - Storage and knowledge directories include user ID")
        print("   - No more hardcoded old paths")
    else:
        print("\n❌ FAILURE: Multi-user implementation still has issues")
        
    return all_correct

if __name__ == "__main__":
    test_multiuser_paths()
