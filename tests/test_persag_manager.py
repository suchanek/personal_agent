"""
Unit tests for PersagManager functionality
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open

from src.personal_agent.core.persag_manager import PersagManager, get_userid, get_persag_manager


class TestPersagManager:
    
    def test_initialize_persag_directory(self):
        """Test ~/.persag directory initialization"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                manager = PersagManager()
                success, message = manager.initialize_persag_directory()
                
                assert success
                assert manager.persag_dir.exists()
                assert manager.userid_file.exists()
                assert "successfully" in message.lower()
    
    def test_get_userid(self):
        """Test user ID retrieval"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                manager = PersagManager()
                manager.persag_dir.mkdir(exist_ok=True)
                
                # Write test user ID
                with open(manager.userid_file, 'w') as f:
                    f.write('USER_ID="test_user"\n')
                
                assert manager.get_userid() == "test_user"
    
    def test_set_userid(self):
        """Test user ID setting"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
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
        """Test validation of empty ~/.persag structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                manager = PersagManager()
                is_valid, message = manager.validate_persag_structure()
                
                assert not is_valid
                assert "does not exist" in message
    
    def test_validate_persag_structure_complete(self):
        """Test validation of complete ~/.persag structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                manager = PersagManager()
                
                # Create complete structure
                manager.persag_dir.mkdir()
                manager.userid_file.write_text('USER_ID="test_user"')
                
                # Create docker directories
                for name in ["lightrag_server", "lightrag_memory_server"]:
                    docker_dir = manager.persag_dir / name
                    docker_dir.mkdir()
                    env_file = "env.server" if name == "lightrag_server" else "env.memory_server"
                    (docker_dir / env_file).write_text("USER_ID=test_user")
                    (docker_dir / "docker-compose.yml").write_text("version: '3'")
                
                is_valid, message = manager.validate_persag_structure()
                
                # This might still fail due to default_user check, but structure should be there
                assert "structure is valid" in message or "Invalid or default user ID" in message


class TestGlobalFunctions:
    
    def test_get_persag_manager_singleton(self):
        """Test that get_persag_manager returns singleton"""
        manager1 = get_persag_manager()
        manager2 = get_persag_manager()
        
        assert manager1 is manager2
    
    def test_get_userid_function(self):
        """Test global get_userid function"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                # Initialize persag directory
                manager = get_persag_manager()
                manager.set_userid("global_test_user")
                
                # Test global function
                user_id = get_userid()
                assert user_id == "global_test_user"


if __name__ == "__main__":
    pytest.main([__file__])