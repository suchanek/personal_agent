"""
Unit tests for PersagManager functionality
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open
import sys
import os

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath()

from personal_agent.core.persag_manager import PersagManager, get_userid, get_persag_manager


class TestPersagManager:
    
    def test_initialize_persag_directory(self):
        """Test ~/.persagent directory initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            persag_dir = temp_path / '.persagent'
            
            with patch.dict(os.environ, {'PERSAG_HOME': str(persag_dir)}):
                with patch('personal_agent.config.settings.PERSAG_HOME', persag_dir):
                    with patch('personal_agent.core.persag_manager.PERSAG_HOME', persag_dir):
                        manager = PersagManager()
                        success, message = manager.initialize_persag_directory()
                        
                        assert success
                        assert manager.persag_dir.exists()
                        assert manager.userid_file.exists()
                        assert "successfully" in message.lower()
    
    def test_get_userid(self):
        """Test user ID retrieval"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            persag_dir = temp_path / '.persagent'
            persag_dir.mkdir(exist_ok=True)
            userid_file = persag_dir / 'env.userid'
            
            # Write test user ID
            with open(userid_file, 'w') as f:
                f.write('USER_ID="test_user"\n')
            
            with patch.dict(os.environ, {'PERSAG_HOME': str(persag_dir)}):
                with patch('personal_agent.config.settings.PERSAG_HOME', persag_dir):
                    with patch('personal_agent.core.persag_manager.PERSAG_HOME', persag_dir):
                        manager = PersagManager()
                        assert manager.get_userid() == "test_user"
    
    def test_set_userid(self):
        """Test user ID setting"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            persag_dir = temp_path / '.persagent'
            
            with patch.dict(os.environ, {'PERSAG_HOME': str(persag_dir)}):
                with patch('personal_agent.config.settings.PERSAG_HOME', persag_dir):
                    with patch('personal_agent.core.persag_manager.PERSAG_HOME', persag_dir):
                        manager = PersagManager()
                        
                        success = manager.set_userid("new_user")
                        assert success
                        assert manager.get_userid() == "new_user"
    
    def test_migrate_docker_directories(self):
        """Test docker directory migration"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create mock project structure
            project_root = temp_path / "project"
            project_root.mkdir()
            
            lightrag_server = project_root / "lightrag_server"
            lightrag_server.mkdir()
            (lightrag_server / "env.server").write_text("USER_ID=charlie")
            (lightrag_server / "docker-compose.yml").write_text("version: '3'")
            
            with patch('pathlib.Path.home', return_value=temp_path):
                manager = PersagManager()
                success, message = manager.migrate_docker_directories(project_root)
                
                assert success
                assert (manager.persag_dir / "lightrag_server").exists()
                assert (manager.persag_dir / "lightrag_server" / "env.server").exists()
    
    def test_get_docker_config(self):
        """Test docker configuration retrieval"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                manager = PersagManager()
                config = manager.get_docker_config()
                
                assert "lightrag_server" in config
                assert "lightrag_memory_server" in config
                assert config["lightrag_server"]["env_file"] == "env.server"
                assert config["lightrag_memory_server"]["env_file"] == "env.memory_server"
    
    def test_validate_persag_structure_empty(self):
        """Test validation of empty ~/.persagent structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            persag_dir = temp_path / '.persagent'
            
            with patch.dict(os.environ, {'PERSAG_HOME': str(persag_dir)}):
                with patch('personal_agent.config.settings.PERSAG_HOME', persag_dir):
                    with patch('personal_agent.core.persag_manager.PERSAG_HOME', persag_dir):
                        manager = PersagManager()
                        is_valid, message = manager.validate_persag_structure()
                        
                        assert not is_valid
                        assert "does not exist" in message or "missing" in message
    
    def test_validate_persag_structure_complete(self):
        """Test validation of complete ~/.persagent structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            persag_dir = temp_path / '.persagent'
            persag_dir.mkdir(exist_ok=True)
            
            with patch.dict(os.environ, {'PERSAG_HOME': str(persag_dir)}):
                with patch('personal_agent.config.settings.PERSAG_HOME', persag_dir):
                    with patch('personal_agent.core.persag_manager.PERSAG_HOME', persag_dir):
                        manager = PersagManager()
                        
                        # Create complete structure
                        manager.userid_file.write_text('USER_ID="test_user"')
                        (persag_dir / '.env').write_text('USER_ID="test_user"')
                        
                        # Create docker directories
                        for name in ["lightrag_server", "lightrag_memory_server"]:
                            docker_dir = persag_dir / name
                            docker_dir.mkdir()
                            env_file = "env.server" if name == "lightrag_server" else "env.memory_server"
                            (docker_dir / env_file).write_text("USER_ID=test_user")
                            (docker_dir / "docker-compose.yml").write_text("version: '3'")
                        
                        is_valid, message = manager.validate_persag_structure()
                        
                        # Should be valid now with proper user_id
                        assert is_valid or "structure is valid" in message


class TestGlobalFunctions:
    
    def test_get_persag_manager_singleton(self):
        """Test that get_persag_manager returns singleton"""
        manager1 = get_persag_manager()
        manager2 = get_persag_manager()
        
        assert manager1 is manager2
    
    def test_get_userid_function(self):
        """Test global get_userid function"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            persag_dir = temp_path / '.persagent'
            persag_dir.mkdir(exist_ok=True)
            
            with patch.dict(os.environ, {'PERSAG_HOME': str(persag_dir)}):
                with patch('personal_agent.config.settings.PERSAG_HOME', persag_dir):
                    with patch('personal_agent.core.persag_manager.PERSAG_HOME', persag_dir):
                        # Reset the singleton to force re-initialization with our test path
                        import personal_agent.core.persag_manager as pm_module
                        pm_module._persag_manager = None
                        
                        # Initialize persag directory and set user
                        manager = get_persag_manager()
                        success = manager.set_userid("global_test_user")
                        assert success, "Failed to set user ID"
                        
                        # Verify the file was written
                        userid_file = persag_dir / 'env.userid'
                        assert userid_file.exists(), "env.userid file not created"
                        
                        # Test global function - it should read from the file we just created
                        user_id = get_userid()
                        assert user_id == "global_test_user"
                        
                        # Clean up singleton for other tests
                        pm_module._persag_manager = None


if __name__ == "__main__":
    pytest.main([__file__])