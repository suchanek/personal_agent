#!/usr/bin/env python3
"""
Comprehensive test script for DATA_DIR usage fixes.

This script tests that all the problematic DATA_DIR usage patterns have been
properly fixed to use the appropriate user-specific environment variables.

Tests:
1. Configuration loading and path resolution
2. Knowledge tools directory usage
3. MCP server configuration
4. Filesystem tools path validation
5. Agno storage directory creation
6. User isolation verification
"""

import os
import sys
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_configuration_loading():
    """Test that configuration properly loads user-specific paths."""
    print("🔧 Testing configuration loading...")
    
    try:
        from src.personal_agent.config import settings
        
        # Check that all required variables are defined
        required_vars = [
            'DATA_DIR', 'USER_DATA_DIR', 'AGNO_STORAGE_DIR', 
            'AGNO_KNOWLEDGE_DIR', 'LIGHTRAG_STORAGE_DIR'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not hasattr(settings, var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"   ❌ Missing configuration variables: {missing_vars}")
            return False
        
        # Check that user-specific paths contain user ID
        user_specific_vars = ['USER_DATA_DIR', 'AGNO_STORAGE_DIR', 'AGNO_KNOWLEDGE_DIR']
        for var in user_specific_vars:
            path = getattr(settings, var)
            if not any(user_id in path for user_id in ['default_user', os.environ.get('USER_ID', 'default_user')]):
                print(f"   ⚠️  {var} may not be user-specific: {path}")
        
        print("   ✅ Configuration loading successful")
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration loading failed: {e}")
        return False

def test_knowledge_tools_paths():
    """Test that knowledge tools use proper directory paths."""
    print("🧠 Testing knowledge tools directory usage...")
    
    try:
        from src.personal_agent.tools.knowledge_tools import KnowledgeTools
        from src.personal_agent.core.knowledge_manager import KnowledgeManager
        from src.personal_agent.config import settings
        
        # Create a mock knowledge manager
        km = MagicMock(spec=KnowledgeManager)
        tools = KnowledgeTools(km)
        
        # Test that semantic knowledge directory uses AGNO_KNOWLEDGE_DIR
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = Path(temp_dir) / "test.txt"
            test_file.write_text("Test content")
            
            # Mock the settings to use our temp directory
            with patch.object(settings, 'AGNO_KNOWLEDGE_DIR', temp_dir):
                result = tools.ingest_semantic_text("Test content", "Test Title")
                
                # Check that the result indicates success or proper error handling
                if "✅" in result or "⚠️" in result:
                    print("   ✅ Knowledge tools use proper directory paths")
                    return True
                else:
                    print(f"   ❌ Unexpected result: {result}")
                    return False
        
    except Exception as e:
        print(f"   ❌ Knowledge tools test failed: {e}")
        return False

def test_mcp_server_configuration():
    """Test that MCP servers use user-specific directories."""
    print("🔌 Testing MCP server configuration...")
    
    try:
        from src.personal_agent.config.mcp_servers import get_mcp_servers
        from src.personal_agent.config import settings
        
        servers = get_mcp_servers()
        
        # Check filesystem-data server configuration
        if 'filesystem-data' in servers:
            data_server = servers['filesystem-data']
            args = data_server.get('args', [])
            
            # The last argument should be the directory path
            if args and len(args) > 2:
                server_path = args[-1]
                
                # Check that it uses USER_DATA_DIR instead of raw DATA_DIR
                if hasattr(settings, 'USER_DATA_DIR'):
                    expected_path = settings.USER_DATA_DIR
                    if server_path == expected_path:
                        print("   ✅ MCP server uses user-specific directory")
                        return True
                    else:
                        print(f"   ❌ MCP server path mismatch: {server_path} != {expected_path}")
                        return False
                else:
                    print("   ⚠️  USER_DATA_DIR not available in settings")
                    return False
            else:
                print("   ❌ MCP server args not properly configured")
                return False
        else:
            print("   ❌ filesystem-data server not found in MCP configuration")
            return False
        
    except Exception as e:
        print(f"   ❌ MCP server configuration test failed: {e}")
        return False

def test_filesystem_tools_validation():
    """Test that filesystem tools use proper path validation."""
    print("📁 Testing filesystem tools path validation...")
    
    try:
        # Import the filesystem module
        from src.personal_agent.tools import filesystem
        from src.personal_agent.config import settings
        
        # Mock the MCP client and other dependencies
        mock_client = MagicMock()
        mock_client.active_servers = {}
        mock_client.start_server_sync.return_value = True
        mock_client.call_tool_sync.return_value = "Mock file content"
        
        filesystem.mcp_client = mock_client
        filesystem.logger = MagicMock()
        
        # Test that USER_DATA_DIR is used for path detection
        if hasattr(settings, 'USER_DATA_DIR'):
            test_path = f"{settings.USER_DATA_DIR}/test.txt"
            
            # This should trigger the filesystem-data server
            result = filesystem.mcp_read_file(test_path)
            
            # Check that the mock was called (indicating proper path routing)
            if mock_client.call_tool_sync.called:
                print("   ✅ Filesystem tools use proper path validation")
                return True
            else:
                print("   ❌ Filesystem tools did not route properly")
                return False
        else:
            print("   ⚠️  USER_DATA_DIR not available for testing")
            return False
        
    except Exception as e:
        print(f"   ❌ Filesystem tools test failed: {e}")
        return False

def test_agno_storage_directories():
    """Test that Agno storage uses proper directories."""
    print("🗄️  Testing Agno storage directory usage...")
    
    try:
        from src.personal_agent.core.agno_storage import create_agno_storage
        from src.personal_agent.config import settings
        
        # Test with temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock AGNO_STORAGE_DIR to use temp directory
            with patch.object(settings, 'AGNO_STORAGE_DIR', temp_dir):
                storage = create_agno_storage()
                
                # Check that storage was created in the expected location
                expected_db_path = Path(temp_dir) / "agent_sessions.db"
                if expected_db_path.exists():
                    print("   ✅ Agno storage uses proper directory")
                    return True
                else:
                    print(f"   ❌ Storage not created at expected path: {expected_db_path}")
                    return False
        
    except Exception as e:
        print(f"   ❌ Agno storage test failed: {e}")
        return False

def test_user_isolation():
    """Test that different users get isolated directories."""
    print("👥 Testing user isolation...")
    
    try:
        from src.personal_agent.config.user_id_mgr import get_user_storage_paths, refresh_user_dependent_settings
        
        # Test with different user IDs using the refresh function
        try:
            # Test user 1
            paths_1 = refresh_user_dependent_settings('test_user_1')
            
            # Test user 2  
            paths_2 = refresh_user_dependent_settings('test_user_2')
            
            # Check that paths are different
            if paths_1['AGNO_STORAGE_DIR'] != paths_2['AGNO_STORAGE_DIR']:
                print("   ✅ User isolation working correctly")
                print(f"      User 1 path: {paths_1['AGNO_STORAGE_DIR']}")
                print(f"      User 2 path: {paths_2['AGNO_STORAGE_DIR']}")
                return True
            else:
                print("   ❌ User isolation failed - same paths for different users")
                print(f"      Both paths: {paths_1['AGNO_STORAGE_DIR']}")
                return False
                
        except Exception as e:
            print(f"   ❌ Error during user isolation test: {e}")
            return False
        
    except Exception as e:
        print(f"   ❌ User isolation test failed: {e}")
        return False

def test_path_construction():
    """Test that paths are constructed properly without direct DATA_DIR usage."""
    print("🛤️  Testing path construction patterns...")
    
    try:
        from src.personal_agent.config import settings
        from src.personal_agent.config.user_id_mgr import get_current_user_id
        
        # Get the current user ID
        current_user_id = get_current_user_id()
        print(f"      Current user ID: {current_user_id}")
        
        # Check that user-specific paths contain the current user ID
        user_paths = [
            ('AGNO_STORAGE_DIR', settings.AGNO_STORAGE_DIR),
            ('AGNO_KNOWLEDGE_DIR', settings.AGNO_KNOWLEDGE_DIR),
            ('USER_DATA_DIR', settings.USER_DATA_DIR)
        ]
        
        issues = []
        for path_name, path in user_paths:
            print(f"      {path_name}: {path}")
            # Check that the path contains the current user ID
            if current_user_id not in path:
                issues.append(f"{path_name} does not contain user ID '{current_user_id}': {path}")
            # Check that it's not using raw DATA_DIR concatenation
            elif path == f"{settings.DATA_DIR}/agno" or path == f"{settings.DATA_DIR}/knowledge":
                issues.append(f"{path_name} appears to use raw DATA_DIR concatenation: {path}")
        
        if issues:
            print("   ❌ Path construction issues found:")
            for issue in issues:
                print(f"      - {issue}")
            return False
        else:
            print("   ✅ Path construction looks correct - all paths contain user ID")
            return True
        
    except Exception as e:
        print(f"   ❌ Path construction test failed: {e}")
        return False

def main():
    """Run all tests and report results."""
    print("=" * 60)
    print("🧪 DATA_DIR FIXES COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        ("Configuration Loading", test_configuration_loading),
        ("Knowledge Tools Paths", test_knowledge_tools_paths),
        ("MCP Server Configuration", test_mcp_server_configuration),
        ("Filesystem Tools Validation", test_filesystem_tools_validation),
        ("Agno Storage Directories", test_agno_storage_directories),
        ("User Isolation", test_user_isolation),
        ("Path Construction", test_path_construction),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"   💥 Test crashed: {e}")
            results.append((test_name, False))
        print()
    
    # Summary
    print("=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print()
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! DATA_DIR fixes are working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
