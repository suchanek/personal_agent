#!/usr/bin/env python3
"""
Migration script for Personal Agent ~/.persag refactoring

This script migrates the existing docker directories and env.userid file
from the project root to the new ~/.persag directory structure.
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.core.persag_manager import get_persag_manager

def main():
    """Main migration function"""
    print("🔄 Personal Agent ~/.persag Migration Script")
    print("=" * 50)
    
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Get project root (where this script is located)
        project_root = Path(__file__).parent.resolve()
        print(f"📁 Project root: {project_root}")
        
        # Get PersagManager
        persag_manager = get_persag_manager()
        print(f"🏠 ~/.persag directory: {persag_manager.persag_dir}")
        
        # Check current state
        print("\n🔍 Checking current state...")
        
        # Check if ~/.persag already exists and is valid
        is_valid, validation_message = persag_manager.validate_persag_structure()
        if is_valid:
            print("✅ ~/.persag structure is already valid!")
            print("   No migration needed.")
            return
        
        print(f"⚠️  Current state: {validation_message}")
        
        # Check what needs to be migrated
        old_userid_file = project_root / "env.userid"
        old_lightrag_server = project_root / "lightrag_server"
        old_lightrag_memory_server = project_root / "lightrag_memory_server"
        
        migration_needed = []
        if old_userid_file.exists():
            migration_needed.append("env.userid")
        if old_lightrag_server.exists():
            migration_needed.append("lightrag_server/")
        if old_lightrag_memory_server.exists():
            migration_needed.append("lightrag_memory_server/")
        
        if not migration_needed:
            print("ℹ️  No old files found to migrate.")
            print("   Initializing fresh ~/.persag structure...")
        else:
            print(f"📦 Files to migrate: {', '.join(migration_needed)}")
        
        # Perform migration
        print("\n🚀 Starting migration...")
        success, message = persag_manager.initialize_persag_directory(project_root)
        
        if success:
            print(f"✅ Migration successful: {message}")
            
            # Validate final state
            print("\n🔍 Validating migrated structure...")
            is_valid, validation_message = persag_manager.validate_persag_structure()
            
            if is_valid:
                print("✅ Migration validation passed!")
                print(f"   Current user ID: {persag_manager.get_userid()}")
                
                # Show what was created
                print(f"\n📁 ~/.persag structure created:")
                print(f"   {persag_manager.persag_dir}")
                print(f"   ├── env.userid")
                
                docker_config = persag_manager.get_docker_config()
                for name, config in docker_config.items():
                    if config["dir"].exists():
                        print(f"   ├── {name}/")
                        print(f"   │   ├── {config['env_file']}")
                        print(f"   │   └── {config['compose_file']}")
                
                print(f"   └── backups/")
                
                # Show next steps
                print(f"\n📋 Next steps:")
                print(f"   1. Test the system: python -m personal_agent.config.settings")
                print(f"   2. Verify docker integration works")
                print(f"   3. If everything works, you can remove old files:")
                if old_userid_file.exists():
                    print(f"      rm {old_userid_file}")
                if old_lightrag_server.exists():
                    print(f"      rm -rf {old_lightrag_server}")
                if old_lightrag_memory_server.exists():
                    print(f"      rm -rf {old_lightrag_memory_server}")
                
            else:
                print(f"⚠️  Migration validation issues: {validation_message}")
                print("   Please check the ~/.persag directory manually.")
        else:
            print(f"❌ Migration failed: {message}")
            return 1
            
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return 1
    
    print("\n🎉 Migration completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())