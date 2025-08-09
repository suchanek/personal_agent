# Personal Agent Docker/User Configuration Refactoring Plan

## Executive Summary

This document outlines a comprehensive refactoring to centralize all user-specific and docker-related configurations in a `~/.persag` directory, creating a single point of truth that is completely decoupled from the repository structure.

## Table of Contents

1. [Current Architecture Analysis](#current-architecture-analysis)
2. [New Architecture Design](#new-architecture-design)
3. [Implementation Plan](#implementation-plan)
4. [Detailed Component Specifications](#detailed-component-specifications)
5. [Migration Strategy](#migration-strategy)
6. [Testing Strategy](#testing-strategy)
7. [Risk Mitigation](#risk-mitigation)
8. [Implementation Timeline](#implementation-timeline)

## Current Architecture Analysis

### Current State

- **User ID Storage**: `env.userid` file in project root contains `USER_ID="charlie"`
- **Docker Directories**: `lightrag_server/` and `lightrag_memory_server/` in project root
- **USER_ID Usage**: Imported as constant from `src/personal_agent/config/settings.py:134`
- **Code References**: 181 references to USER_ID throughout codebase
- **Synchronization**: `DockerUserSync` class manages sync between system and docker env files
- **Initialization**: Handled by `src/personal_agent/core/agno_initialization.py`

### Key Dependencies

1. **settings.py**: Loads USER_ID from `env.userid` via `load_user_from_file()`
2. **DockerUserSync**: Hardcodes docker directory paths in `docker_configs`
3. **Storage Paths**: All depend on USER_ID pattern: `{DATA_DIR}/{STORAGE_BACKEND}/{USER_ID}`
4. **Docker Integration**: `ensure_docker_user_consistency()` called during initialization

### Current File Locations

```
project_root/
├── env.userid                   # USER_ID="charlie"
├── lightrag_server/
│   ├── env.server              # USER_ID=charlie
│   ├── docker-compose.yml
│   ├── config.ini
│   └── .env
├── lightrag_memory_server/
│   ├── env.memory_server       # USER_ID=charlie
│   ├── docker-compose.yml
│   ├── config.ini
│   └── env.save
└── backups/
    └── docker_env_backups/
```

## New Architecture Design

### ~/.persag Directory Structure

```
~/.persag/
├── env.userid                    # USER_ID="charlie" - Single source of truth
├── lightrag_server/             # Moved from project root
│   ├── env.server
│   ├── docker-compose.yml
│   ├── config.ini
│   └── .env
├── lightrag_memory_server/      # Moved from project root
│   ├── env.memory_server
│   ├── docker-compose.yml
│   ├── config.ini
│   └── env.save
└── backups/                     # For env file backups
    └── docker_env_backups/
```

### Core Architectural Changes

1. **Single Point of Truth**: All user/docker config in `~/.persag`
2. **Repository Independence**: Docker setup completely decoupled from code
3. **Dynamic User ID**: Replace static `USER_ID` constant with `get_userid()` function
4. **Centralized Management**: New `PersagManager` class for all operations

## Implementation Plan

### Phase 1: Foundation Components (Days 1-2)

#### 1.1 Create PersagManager Class

**File**: `src/personal_agent/core/persag_manager.py`

```python
"""
Personal Agent Configuration Manager

Manages ~/.persag directory structure and user configuration.
"""

import logging
import shutil
import os
from pathlib import Path
from typing import Optional, Tuple, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class PersagManager:
    """Manages ~/.persag directory structure and configuration"""
    
    def __init__(self):
        self.persag_dir = Path.home() / ".persag"
        self.userid_file = self.persag_dir / "env.userid"
        self.backup_dir = self.persag_dir / "backups"
        
    def initialize_persag_directory(self, project_root: Optional[Path] = None) -> Tuple[bool, str]:
        """
        Create ~/.persag structure and migrate existing files if needed.
        
        Args:
            project_root: Path to project root for migration (optional)
            
        Returns:
            Tuple of (success, message)
        """
        try:
            # Create base directory
            self.persag_dir.mkdir(exist_ok=True)
            self.backup_dir.mkdir(exist_ok=True)
            
            # Create default env.userid if it doesn't exist
            if not self.userid_file.exists():
                default_user_id = "default_user"
                
                # Try to migrate from project root if provided
                if project_root:
                    old_userid_file = project_root / "env.userid"
                    if old_userid_file.exists():
                        # Read existing user ID
                        with open(old_userid_file, 'r') as f:
                            content = f.read().strip()
                            if content.startswith("USER_ID="):
                                default_user_id = content.split("=", 1)[1].strip().strip("'\"")
                
                # Create new env.userid
                with open(self.userid_file, 'w') as f:
                    f.write(f'USER_ID="{default_user_id}"\n')
                
                logger.info(f"Created ~/.persag/env.userid with USER_ID={default_user_id}")
            
            # Migrate docker directories if project_root provided
            if project_root:
                success, message = self.migrate_docker_directories(project_root)
                if not success:
                    return False, f"Docker migration failed: {message}"
            
            return True, "~/.persag directory initialized successfully"
            
        except Exception as e:
            logger.error(f"Failed to initialize ~/.persag directory: {e}")
            return False, str(e)
    
    def get_userid(self) -> str:
        """
        Get current user ID from ~/.persag/env.userid
        
        Returns:
            Current user ID or 'default_user' if not found
        """
        try:
            if self.userid_file.exists():
                with open(self.userid_file, 'r') as f:
                    content = f.read().strip()
                    if content.startswith("USER_ID="):
                        return content.split("=", 1)[1].strip().strip("'\"")
        except Exception as e:
            logger.warning(f"Failed to read user ID from ~/.persag/env.userid: {e}")
        
        # Fallback to environment variable for backward compatibility
        return os.getenv("USER_ID", "default_user")
    
    def set_userid(self, user_id: str) -> bool:
        """
        Set user ID in ~/.persag/env.userid
        
        Args:
            user_id: New user ID to set
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            self.persag_dir.mkdir(exist_ok=True)
            
            # Write new user ID
            with open(self.userid_file, 'w') as f:
                f.write(f'USER_ID="{user_id}"\n')
            
            logger.info(f"Set USER_ID to '{user_id}' in ~/.persag/env.userid")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set user ID: {e}")
            return False
    
    def migrate_docker_directories(self, project_root: Path) -> Tuple[bool, str]:
        """
        Migrate docker directories from project root to ~/.persag
        
        Args:
            project_root: Path to project root directory
            
        Returns:
            Tuple of (success, message)
        """
        try:
            docker_dirs = ["lightrag_server", "lightrag_memory_server"]
            migrated = []
            
            for dir_name in docker_dirs:
                source_dir = project_root / dir_name
                target_dir = self.persag_dir / dir_name
                
                if source_dir.exists() and not target_dir.exists():
                    # Create backup first
                    backup_name = f"{dir_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    backup_path = self.backup_dir / backup_name
                    shutil.copytree(source_dir, backup_path)
                    
                    # Copy to ~/.persag
                    shutil.copytree(source_dir, target_dir)
                    migrated.append(dir_name)
                    
                    logger.info(f"Migrated {dir_name} to ~/.persag (backup: {backup_path})")
            
            if migrated:
                return True, f"Migrated directories: {', '.join(migrated)}"
            else:
                return True, "No directories needed migration"
                
        except Exception as e:
            logger.error(f"Failed to migrate docker directories: {e}")
            return False, str(e)
    
    def get_docker_config(self) -> Dict[str, Dict[str, Any]]:
        """
        Get docker configuration for ~/.persag directories
        
        Returns:
            Docker configuration dictionary
        """
        return {
            "lightrag_server": {
                "dir": self.persag_dir / "lightrag_server",
                "env_file": "env.server",
                "container_name": "lightrag_pagent",
                "compose_file": "docker-compose.yml",
            },
            "lightrag_memory_server": {
                "dir": self.persag_dir / "lightrag_memory_server",
                "env_file": "env.memory_server",
                "container_name": "lightrag_memory",
                "compose_file": "docker-compose.yml",
            },
        }
    
    def validate_persag_structure(self) -> Tuple[bool, str]:
        """
        Validate ~/.persag directory structure
        
        Returns:
            Tuple of (is_valid, message)
        """
        try:
            issues = []
            
            # Check base directory
            if not self.persag_dir.exists():
                issues.append("~/.persag directory does not exist")
            
            # Check env.userid
            if not self.userid_file.exists():
                issues.append("env.userid file missing")
            else:
                user_id = self.get_userid()
                if not user_id or user_id == "default_user":
                    issues.append("Invalid or default user ID")
            
            # Check docker directories
            docker_config = self.get_docker_config()
            for name, config in docker_config.items():
                docker_dir = config["dir"]
                if not docker_dir.exists():
                    issues.append(f"{name} directory missing")
                else:
                    env_file = docker_dir / config["env_file"]
                    compose_file = docker_dir / config["compose_file"]
                    
                    if not env_file.exists():
                        issues.append(f"{name} env file missing")
                    if not compose_file.exists():
                        issues.append(f"{name} docker-compose.yml missing")
            
            if issues:
                return False, "; ".join(issues)
            else:
                return True, "~/.persag structure is valid"
                
        except Exception as e:
            return False, f"Validation error: {e}"


# Global instance
_persag_manager = None

def get_persag_manager() -> PersagManager:
    """Get global PersagManager instance"""
    global _persag_manager
    if _persag_manager is None:
        _persag_manager = PersagManager()
    return _persag_manager

def get_userid() -> str:
    """Get current user ID - replaces USER_ID constant"""
    return get_persag_manager().get_userid()
```

#### 1.2 Update settings.py

**File**: `src/personal_agent/config/settings.py`

**Key Changes**:

```python
# Replace existing load_user_from_file() function
def load_user_from_file():
    """Load the USER_ID from ~/.persag/env.userid and set it in the environment."""
    from ..core.persag_manager import get_persag_manager
    
    persag_manager = get_persag_manager()
    user_id = persag_manager.get_userid()
    
    # Set in environment for backward compatibility
    os.environ["USER_ID"] = user_id
    return user_id

# Replace USER_ID constant with function
def get_userid() -> str:
    """Get the current USER_ID dynamically from ~/.persag/env.userid"""
    return load_user_from_file()

# Remove this line:
# USER_ID = get_env_var("USER_ID", "default_user")

# Update storage directory calculations to use get_userid()
def get_user_storage_paths():
    """Get user-specific storage paths"""
    current_user_id = get_userid()
    return {
        "AGNO_STORAGE_DIR": os.path.expandvars(f"{DATA_DIR}/{STORAGE_BACKEND}/{current_user_id}"),
        "AGNO_KNOWLEDGE_DIR": os.path.expandvars(f"{DATA_DIR}/{STORAGE_BACKEND}/{current_user_id}/knowledge"),
        "LIGHTRAG_STORAGE_DIR": os.path.expandvars(f"{DATA_DIR}/{STORAGE_BACKEND}/{current_user_id}/rag_storage"),
        "LIGHTRAG_INPUTS_DIR": os.path.expandvars(f"{DATA_DIR}/{STORAGE_BACKEND}/{current_user_id}/inputs"),
        "LIGHTRAG_MEMORY_STORAGE_DIR": os.path.expandvars(f"{DATA_DIR}/{STORAGE_BACKEND}/{current_user_id}/memory_rag_storage"),
        "LIGHTRAG_MEMORY_INPUTS_DIR": os.path.expandvars(f"{DATA_DIR}/{STORAGE_BACKEND}/{current_user_id}/memory_inputs"),
    }

# Initialize ~/.persag on module load
def _initialize_persag():
    """Initialize ~/.persag directory structure"""
    try:
        from ..core.persag_manager import get_persag_manager
        persag_manager = get_persag_manager()
        success, message = persag_manager.initialize_persag_directory(BASE_DIR)
        if not success:
            logger.warning(f"Failed to initialize ~/.persag: {message}")
    except Exception as e:
        logger.warning(f"Error initializing ~/.persag: {e}")

# Initialize on import
_initialize_persag()
```

### Phase 2: Core Component Updates (Days 3-4)

#### 2.1 Update DockerUserSync Class

**File**: `src/personal_agent/core/docker/user_sync.py`

**Key Changes**:

```python
class DockerUserSync:
    """Manages USER_ID synchronization between system and Docker containers."""

    def __init__(self, dry_run: bool = False):
        """Initialize the Docker User Sync manager."""
        from ..persag_manager import get_persag_manager
        
        self.dry_run = dry_run
        self.persag_manager = get_persag_manager()
        
        # Get system user ID from ~/.persag
        self.system_user_id = self.persag_manager.get_userid()
        if not self.system_user_id:
            raise ValueError("Could not determine system USER_ID from ~/.persag")

        # Docker server configurations - now using ~/.persag paths
        self.docker_configs = self.persag_manager.get_docker_config()

        # Backup directory in ~/.persag
        self.backup_dir = self.persag_manager.persag_dir / "backups" / "docker_env_backups"
        try:
            self.backup_dir.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.error("Failed to create backup directory %s: %s", self.backup_dir, e)
            raise ValueError(f"Cannot create backup directory: {e}")

        logger.info("Initialized DockerUserSync with ~/.persag")
        logger.info("System USER_ID: %s", self.system_user_id)
        logger.info("Dry run mode: %s", self.dry_run)

    def _get_system_user_id(self) -> Optional[str]:
        """Get system USER_ID from ~/.persag (override parent method)"""
        return self.persag_manager.get_userid()
```

#### 2.2 Update Docker Integration Manager

**File**: `src/personal_agent/core/docker_integration.py`

**Key Changes**:

```python
# Replace USER_ID import
from ..core.persag_manager import get_userid

class DockerIntegrationManager:
    """Manages Docker integration for the personal agent system."""
    
    def __init__(self, user_id: Optional[str] = None):
        """Initialize the Docker integration manager."""
        self.user_id = user_id or get_userid()  # Use get_userid() instead of USER_ID
        
        # Rest of initialization remains the same...
```

### Phase 3: Codebase Migration (Days 5-6)

#### 3.1 Mass Import Replacement

**Search and Replace Operations**:

1. **Import Statements**:
   ```python
   # Replace:
   from personal_agent.config.settings import USER_ID
   from ..config.settings import USER_ID
   
   # With:
   from personal_agent.config.settings import get_userid
   from ..config.settings import get_userid
   ```

2. **Variable Usage**:
   ```python
   # Replace:
   user_id = USER_ID
   current_user = USER_ID
   
   # With:
   user_id = get_userid()
   current_user = get_userid()
   ```

3. **Default Parameters**:
   ```python
   # Replace:
   def function(user_id: str = USER_ID):
   
   # With:
   def function(user_id: str = None):
       if user_id is None:
           user_id = get_userid()
   ```

#### 3.2 Critical Files to Update

**High Priority Files** (181 total references):

1. **Core Agent Files**:
   - `src/personal_agent/core/agno_agent.py` (3 references)
   - `src/personal_agent/core/agno_agent_new.py` (3 references)
   - `src/personal_agent/core/user_manager.py` (6 references)

2. **Initialization Files**:
   - `src/personal_agent/core/agno_initialization.py` (1 reference)
   - `src/personal_agent/agno_main.py` (1 reference)

3. **Tool Classes**:
   - `src/personal_agent/tools/memory_cleaner.py` (4 references)
   - `src/personal_agent/core/anti_duplicate_memory.py` (4 references)
   - `src/personal_agent/core/semantic_memory_manager.py` (4 references)

4. **Web Interface Files**:
   - `src/personal_agent/web/agno_interface.py` (4 references)
   - `src/personal_agent/streamlit/` (multiple files)

#### 3.3 Docker Compose File Updates

**Files to Update**:
- `~/.persag/lightrag_server/docker-compose.yml`
- `~/.persag/lightrag_memory_server/docker-compose.yml`

**Key Changes**:
```yaml
# Update volume mounts to use ~/.persag paths
volumes:
  - ~/.persag/lightrag_server/env.server:/app/.env
  - ${DATA_DIR}/${STORAGE_BACKEND}/${USER_ID}:/app/storage

# Update environment file references
env_file:
  - ~/.persag/lightrag_server/env.server
```

### Phase 4: Testing & Validation (Days 7-8)

#### 4.1 Unit Tests

**File**: `tests/test_persag_manager.py`

```python
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open

from personal_agent.core.persag_manager import PersagManager, get_userid

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
```

#### 4.2 Integration Tests

**File**: `tests/test_docker_integration.py`

```python
import pytest
from unittest.mock import patch, MagicMock

from personal_agent.core.docker_integration import DockerIntegrationManager
from personal_agent.core.docker.user_sync import DockerUserSync

class TestDockerIntegration:
    
    @patch('personal_agent.core.persag_manager.get_persag_manager')
    def test_docker_integration_with_persag(self, mock_persag):
        """Test docker integration uses ~/.persag"""
        mock_manager = MagicMock()
        mock_manager.get_userid.return_value = "test_user"
        mock_persag.return_value = mock_manager
        
        integration = DockerIntegrationManager()
        assert integration.user_id == "test_user"
    
    @patch('personal_agent.core.persag_manager.get_persag_manager')
    def test_docker_user_sync_with_persag(self, mock_persag):
        """Test DockerUserSync uses ~/.persag paths"""
        mock_manager = MagicMock()
        mock_manager.get_userid.return_value = "test_user"
        mock_manager.persag_dir = Path("/home/user/.persag")
        mock_manager.get_docker_config.return_value = {
            "lightrag_server": {
                "dir": Path("/home/user/.persag/lightrag_server"),
                "env_file": "env.server",
                "container_name": "lightrag_pagent",
                "compose_file": "docker-compose.yml",
            }
        }
        mock_persag.return_value = mock_manager
        
        sync = DockerUserSync(dry_run=True)
        assert sync.system_user_id == "test_user"
        assert "lightrag_server" in sync.docker_configs
```

#### 4.3 End-to-End Tests

**File**: `tests/test_e2e_persag.py`

```python
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from personal_agent.core.persag_manager import get_persag_manager
from personal_agent.config.settings import get_userid

class TestE2EPersag:
    
    def test_full_initialization_flow(self):
        """Test complete initialization from scratch"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('pathlib.Path.home', return_value=Path(temp_dir)):
                # Initialize ~/.persag
                manager = get_persag_manager()
                success, message = manager.initialize_persag_directory()
                
                assert success
                assert manager.persag_dir.exists()
                
                # Test user ID retrieval
                user_id = get_userid()
                assert user_id == "default_user"
                
                # Test user ID change
                manager.set_userid("charlie")
                assert get_userid() == "charlie"
    
    def test_migration_from_project_root(self):
        """Test migration from existing project structure"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create existing project structure
            project_root = temp_path / "project"
            project_root.mkdir()
            
            # Create env.userid
            (project_root / "env.userid").write_text('USER_ID="charlie"\n')
            
            # Create docker directories
            for dir_name in ["lightrag_server", "lightrag_memory_server"]:
                docker_dir = project_root / dir_name
                docker_dir.mkdir()
                (docker_dir / f"env.{dir_name.split('_')[1]}").write_text("USER_ID=charlie")
                (docker_dir / "docker-compose.yml").write_text("version: '3'")
            
            with patch('pathlib.Path.home', return_value=temp_path):
                manager = get_persag_manager()
                success, message = manager.initialize_persag_directory(project_root)
                
                assert success
                assert get_userid() == "charlie"
                assert (manager.persag_dir / "lightrag_server").exists()
                assert (manager.persag_dir / "lightrag_memory_server").exists()
```

## Migration Strategy

### Pre-Migration Checklist

1. **Backup Current Configuration**:
   ```bash
   # Create backup of current docker directories
   cp -r lightrag_server lightrag_server_backup
   cp -r lightrag_memory_server lightrag_memory_server_backup
   cp env.userid env.userid_backup
   ```

2. **Verify Current System State**:
   ```bash
   # Check current USER_ID
   cat env.userid
   
   # Check docker containers
   docker ps | grep lightrag
   
   # Check current storage directories
   ls -la /Users/Shared/personal_agent_data/agno/charlie/
   ```

### Migration Steps

#### Step 1: Deploy New Code
```bash
# Deploy updated codebase with PersagManager
git pull origin feature/persag-refactoring
pip install -e .
```

#### Step 2: Initialize ~/.persag
```python
# Run initialization script
from personal_agent.core.persag_manager import get_persag_manager

manager = get_persag_manager()
success, message = manager.initialize_persag_directory(Path.cwd())
print(f"Migration: {message}")
```

#### Step 3: Validate Migration
```python
# Verify ~/.persag structure
manager = get_persag_manager()
valid, message = manager.validate_persag_structure()
print(f"Validation: {message}")

# Test user ID retrieval
from personal_agent.config.settings import get_userid
print(f"Current USER_ID: {get_userid()}")
```

#### Step 4: Test Docker Integration
```bash
# Test docker synchronization
python -c "
from personal_agent.core.docker_integration import ensure_docker_user_consistency
success, message = ensure_docker_user_consistency()
print(f'Docker sync: {message}')
"
```

#### Step 5: Clean Up (Optional)
```bash
# After successful migration and testing
rm -rf lightrag_server_backup
rm -rf lightrag_memory_server_backup
rm env.userid_backup

# Remove original docker directories from project
rm -rf lightrag_server
rm -rf lightrag_memory_server
rm env.userid
```

### Rollback Procedure

If migration fails:

```bash
# Stop any running containers
docker-compose -f ~/.persag/lightrag_server/docker-compose.yml down
docker-compose -f ~/.persag/lightrag_memory_server/docker-compose.yml down

# Restore original structure
cp -r lightrag_server_backup lightrag_server
cp -r lightrag_memory_server_backup lightrag_memory_server
cp env.userid_backup env.userid

# Revert to previous code version
git checkout main
pip install -e .

# Restart containers
docker-compose -f lightrag_server/docker-compose.yml up -d
docker-compose -f lightrag_memory_server/docker-compose.yml up -d
```

## Risk Mitigation

### Identified Risks

1. **Data Loss**: Docker directories contain important configuration
2. **Service Disruption**: Docker containers may fail to start
3. **Path Dependencies**: Hard-coded paths in docker-compose files
4. **Environment Variables**: Cached USER_ID values in running processes

### Mitigation Strategies

1. **Automatic Backups**: All migration operations create timestamped backups
2. **Validation Checks**: Comprehensive validation before and after migration
3. **Gradual Rollout**: Phase-by-phase implementation with testing at each step
4. **Rollback Capability**: Complete rollback procedure documented and tested
5. **Backward Compatibility**: Fallback to environment variables during transition

### Monitoring and Validation

1. **Health Checks**: Automated validation of ~/.persag structure
2. **Docker Status**: Monitor container health after migration
3. **User ID Consistency**: Verify USER_ID synchronization across all components
4. **Storage Access**: Validate access to user-specific storage directories

## Implementation Timeline

### Week 1: Foundation
- **Day 1**: Create PersagManager class and basic functionality
- **Day 2**: Update settings.py and create get_userid() function
- **Day 3**: Update DockerUserSync to use ~/.persag paths
- **Day 4**: Create migration utilities and validation functions

### Week 2: Integration
- **Day 5**: Begin mass replacement of USER_ID references (high priority files)
- **Day 6**: Continue codebase migration (remaining files)
- **Day 7**: Update docker-compose files and test docker integration
- **Day 8**: Comprehensive testing and validation

### Week 3: Deployment
- **Day 9**: Deploy to staging environment and test migration
- **Day 10**: Performance testing and optimization
- **Day 11**: Documentation and training materials
- **Day 12**: Production deployment with monitoring

## Success Criteria

### Technical Criteria
- [ ] All 181 USER_ID references successfully migrated to get_userid()
- [ ] Docker containers start successfully from ~/.persag directories
- [ ] User switching functionality works with new architecture
- [ ] All existing functionality preserved (no regressions)
- [ ] Performance