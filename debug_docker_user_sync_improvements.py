#!/usr/bin/env python3
"""
Comprehensive Debug Program for DockerUserSync Improvements

This program thoroughly tests all the improvements made to the DockerUserSync class
including error handling, validation, performance optimizations, and edge cases.
Uses dry-run mode to avoid making actual changes to the system.

Author: Personal Agent Development Team
"""

import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
import traceback

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from personal_agent.core.docker.user_sync import DockerUserSync, Colors
except ImportError as e:
    print(f"❌ Failed to import DockerUserSync: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

# Configure logging for detailed output
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_docker_user_sync.log')
    ]
)

logger = logging.getLogger(__name__)


class DockerUserSyncTester:
    """Comprehensive tester for DockerUserSync improvements."""
    
    def __init__(self):
        """Initialize the tester."""
        self.test_results: Dict[str, Dict] = {}
        self.temp_dir = None
        self.setup_test_environment()
    
    def setup_test_environment(self):
        """Set up a temporary test environment."""
        self.temp_dir = Path(tempfile.mkdtemp(prefix="docker_sync_test_"))
        logger.info(f"Created test environment: {self.temp_dir}")
        
        # Create mock directory structure
        (self.temp_dir / "lightrag_server").mkdir()
        (self.temp_dir / "lightrag_memory_server").mkdir()
        
        # Create mock environment files
        self.create_mock_env_file(
            self.temp_dir / "lightrag_server" / "env.server",
            "test_user_123"
        )
        self.create_mock_env_file(
            self.temp_dir / "lightrag_memory_server" / "env.memory_server",
            "different_user_456"
        )
        
        # Create mock docker-compose files
        self.create_mock_compose_file(self.temp_dir / "lightrag_server" / "docker-compose.yml")
        self.create_mock_compose_file(self.temp_dir / "lightrag_memory_server" / "docker-compose.yml")
    
    def create_mock_env_file(self, path: Path, user_id: str):
        """Create a mock environment file."""
        content = f"""# Mock environment file
DATABASE_URL=postgresql://localhost:5432/test
USER_ID={user_id}
DEBUG=true
# Comment line
ANOTHER_VAR=value
"""
        path.write_text(content)
        logger.debug(f"Created mock env file: {path}")
    
    def create_mock_compose_file(self, path: Path):
        """Create a mock docker-compose file."""
        content = """version: '3.8'
services:
  test_service:
    image: nginx:latest
    ports:
      - "8080:80"
"""
        path.write_text(content)
        logger.debug(f"Created mock compose file: {path}")
    
    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record results."""
        print(f"\n{Colors.BLUE}🧪 Running Test: {test_name}{Colors.NC}")
        print("=" * 60)
        
        try:
            result = test_func()
            self.test_results[test_name] = {
                "status": "PASSED" if result else "FAILED",
                "error": None
            }
            status_color = Colors.GREEN if result else Colors.RED
            status_icon = "✅" if result else "❌"
            print(f"{status_color}{status_icon} {test_name}: {'PASSED' if result else 'FAILED'}{Colors.NC}")
            return result
        except Exception as e:
            self.test_results[test_name] = {
                "status": "ERROR",
                "error": str(e)
            }
            print(f"{Colors.RED}💥 {test_name}: ERROR - {e}{Colors.NC}")
            logger.error(f"Test {test_name} failed with error: {e}")
            logger.debug(traceback.format_exc())
            return False
    
    def test_initialization_improvements(self) -> bool:
        """Test initialization improvements and validation."""
        print(f"{Colors.CYAN}Testing initialization improvements...{Colors.NC}")
        
        # Test 1: Normal initialization
        try:
            sync = DockerUserSync(base_dir=self.temp_dir, dry_run=True)
            print(f"✅ Normal initialization successful")
            print(f"   Base dir: {sync.base_dir}")
            print(f"   System USER_ID: {sync.system_user_id}")
            print(f"   Dry run: {sync.dry_run}")
        except Exception as e:
            print(f"❌ Normal initialization failed: {e}")
            return False
        
        # Test 2: Invalid base directory
        try:
            invalid_dir = self.temp_dir / "nonexistent"
            DockerUserSync(base_dir=invalid_dir, dry_run=True)
            print(f"❌ Should have failed with invalid directory")
            return False
        except ValueError as e:
            print(f"✅ Correctly rejected invalid directory: {e}")
        
        # Test 3: String base directory (should convert to Path)
        try:
            sync = DockerUserSync(base_dir=str(self.temp_dir), dry_run=True)
            print(f"✅ String base directory converted successfully")
            assert isinstance(sync.base_dir, Path)
        except Exception as e:
            print(f"❌ String base directory conversion failed: {e}")
            return False
        
        return True
    
    def test_user_id_validation(self) -> bool:
        """Test USER_ID validation improvements."""
        print(f"{Colors.CYAN}Testing USER_ID validation...{Colors.NC}")
        
        sync = DockerUserSync(base_dir=self.temp_dir, dry_run=True)
        
        # Test valid USER_IDs
        valid_ids = ["user123", "test_user", "user-name", "user.name", "123"]
        for user_id in valid_ids:
            if not sync._is_valid_user_id(user_id):
                print(f"❌ Valid USER_ID rejected: {user_id}")
                return False
            print(f"✅ Valid USER_ID accepted: {user_id}")
        
        # Test invalid USER_IDs
        invalid_ids = ["", "user;id", "user&id", "user|id", "user`id", "user$(id)", "user{id}", "a" * 101]
        for user_id in invalid_ids:
            if sync._is_valid_user_id(user_id):
                print(f"❌ Invalid USER_ID accepted: {user_id}")
                return False
            print(f"✅ Invalid USER_ID rejected: {user_id}")
        
        return True
    
    def test_env_file_operations(self) -> bool:
        """Test environment file operations improvements."""
        print(f"{Colors.CYAN}Testing environment file operations...{Colors.NC}")
        
        sync = DockerUserSync(base_dir=self.temp_dir, dry_run=True)
        
        # Test reading existing USER_ID
        env_file = self.temp_dir / "lightrag_server" / "env.server"
        user_id = sync.get_env_file_user_id(env_file)
        if user_id != "test_user_123":
            print(f"❌ Failed to read USER_ID: expected 'test_user_123', got '{user_id}'")
            return False
        print(f"✅ Successfully read USER_ID: {user_id}")
        
        # Test reading from non-existent file
        nonexistent_file = self.temp_dir / "nonexistent.env"
        user_id = sync.get_env_file_user_id(nonexistent_file)
        if user_id is not None:
            print(f"❌ Should return None for non-existent file")
            return False
        print(f"✅ Correctly handled non-existent file")
        
        # Test input validation
        try:
            sync.get_env_file_user_id("not_a_path")
            print(f"❌ Should have raised ValueError for invalid input")
            return False
        except ValueError:
            print(f"✅ Correctly validated input type")
        
        # Test updating USER_ID (dry run)
        result = sync.update_env_file_user_id(env_file, "new_user_id")
        if not result:
            print(f"❌ Failed to update USER_ID in dry run")
            return False
        print(f"✅ Successfully updated USER_ID in dry run")
        
        # Test invalid USER_ID update
        try:
            sync.update_env_file_user_id(env_file, "invalid;user")
            print(f"❌ Should have raised ValueError for invalid USER_ID")
            return False
        except ValueError:
            print(f"✅ Correctly rejected invalid USER_ID")
        
        return True
    
    def test_docker_operations(self) -> bool:
        """Test Docker operations improvements."""
        print(f"{Colors.CYAN}Testing Docker operations...{Colors.NC}")
        
        sync = DockerUserSync(base_dir=self.temp_dir, dry_run=True)
        
        # Test container status check with invalid input
        try:
            sync.is_container_running("")
            print(f"❌ Should have raised ValueError for empty container name")
            return False
        except ValueError:
            print(f"✅ Correctly validated container name")
        
        try:
            sync.is_container_running(123)
            print(f"❌ Should have raised ValueError for non-string container name")
            return False
        except ValueError:
            print(f"✅ Correctly validated container name type")
        
        # Test Docker service operations with invalid config
        try:
            sync.stop_docker_service("not_a_dict")
            print(f"❌ Should have raised ValueError for invalid config")
            return False
        except ValueError:
            print(f"✅ Correctly validated server config type")
        
        try:
            sync.stop_docker_service({"incomplete": "config"})
            print(f"❌ Should have raised ValueError for incomplete config")
            return False
        except ValueError:
            print(f"✅ Correctly validated server config completeness")
        
        # Test with valid config (dry run)
        valid_config = {
            "dir": self.temp_dir / "lightrag_server",
            "compose_file": "docker-compose.yml"
        }
        
        result = sync.stop_docker_service(valid_config)
        if not result:
            print(f"❌ Failed to stop service in dry run")
            return False
        print(f"✅ Successfully stopped service in dry run")
        
        result = sync.start_docker_service(valid_config)
        if not result:
            print(f"❌ Failed to start service in dry run")
            return False
        print(f"✅ Successfully started service in dry run")
        
        return True
    
    def test_consistency_checking(self) -> bool:
        """Test consistency checking improvements."""
        print(f"{Colors.CYAN}Testing consistency checking...{Colors.NC}")
        
        sync = DockerUserSync(base_dir=self.temp_dir, dry_run=True)
        
        # Test consistency check
        results = sync.check_user_id_consistency()
        
        if not isinstance(results, dict):
            print(f"❌ Consistency check should return a dictionary")
            return False
        
        expected_servers = ["lightrag_server", "lightrag_memory_server"]
        for server in expected_servers:
            if server not in results:
                print(f"❌ Missing server in results: {server}")
                return False
            
            result = results[server]
            required_keys = ["env_file_path", "docker_user_id", "system_user_id", "consistent", "container_running", "config"]
            for key in required_keys:
                if key not in result:
                    print(f"❌ Missing key in result for {server}: {key}")
                    return False
        
        print(f"✅ Consistency check returned complete results")
        
        # Check that inconsistencies are detected
        inconsistent_found = False
        for server, result in results.items():
            if not result["consistent"]:
                inconsistent_found = True
                print(f"✅ Detected inconsistency in {server}: {result['docker_user_id']} != {result['system_user_id']}")
        
        if not inconsistent_found:
            print(f"⚠️  No inconsistencies detected (this may be expected)")
        
        return True
    
    def test_synchronization(self) -> bool:
        """Test synchronization improvements."""
        print(f"{Colors.CYAN}Testing synchronization...{Colors.NC}")
        
        sync = DockerUserSync(base_dir=self.temp_dir, dry_run=True)
        
        # Test normal synchronization
        result = sync.sync_user_ids()
        if not isinstance(result, bool):
            print(f"❌ Sync should return boolean")
            return False
        print(f"✅ Synchronization completed: {result}")
        
        # Test force restart
        result = sync.sync_user_ids(force_restart=True)
        if not isinstance(result, bool):
            print(f"❌ Force restart sync should return boolean")
            return False
        print(f"✅ Force restart synchronization completed: {result}")
        
        return True
    
    def test_validation_system(self) -> bool:
        """Test comprehensive validation system."""
        print(f"{Colors.CYAN}Testing validation system...{Colors.NC}")
        
        sync = DockerUserSync(base_dir=self.temp_dir, dry_run=True)
        
        # Test comprehensive validation
        result = sync.validate_system_consistency()
        if not isinstance(result, bool):
            print(f"❌ Validation should return boolean")
            return False
        print(f"✅ System validation completed: {result}")
        
        return True
    
    def test_error_handling(self) -> bool:
        """Test error handling improvements."""
        print(f"{Colors.CYAN}Testing error handling...{Colors.NC}")
        
        # Test with corrupted environment file
        corrupted_env = self.temp_dir / "corrupted.env"
        corrupted_env.write_bytes(b'\xff\xfe\x00\x00')  # Invalid UTF-8
        
        sync = DockerUserSync(base_dir=self.temp_dir, dry_run=True)
        
        # Should handle corrupted file gracefully
        user_id = sync.get_env_file_user_id(corrupted_env)
        if user_id is not None:
            print(f"❌ Should return None for corrupted file")
            return False
        print(f"✅ Gracefully handled corrupted file")
        
        # Test with missing directory in config
        invalid_config = {
            "dir": self.temp_dir / "missing_directory",
            "compose_file": "docker-compose.yml"
        }
        
        result = sync.stop_docker_service(invalid_config)
        if result:
            print(f"❌ Should fail for missing directory")
            return False
        print(f"✅ Correctly handled missing directory")
        
        return True
    
    def test_colors_utility(self) -> bool:
        """Test Colors utility improvements."""
        print(f"{Colors.CYAN}Testing Colors utility...{Colors.NC}")
        
        # Test colorize method
        colored_text = Colors.colorize("Test", Colors.RED)
        expected = f"{Colors.RED}Test{Colors.NC}"
        if colored_text != expected:
            print(f"❌ Colorize method failed: expected '{expected}', got '{colored_text}'")
            return False
        print(f"✅ Colorize method works correctly")
        
        return True
    
    def run_all_tests(self):
        """Run all tests and provide summary."""
        print(f"\n{Colors.WHITE}🚀 STARTING COMPREHENSIVE DOCKER USER SYNC TESTING{Colors.NC}")
        print("=" * 80)
        
        tests = [
            ("Initialization Improvements", self.test_initialization_improvements),
            ("USER_ID Validation", self.test_user_id_validation),
            ("Environment File Operations", self.test_env_file_operations),
            ("Docker Operations", self.test_docker_operations),
            ("Consistency Checking", self.test_consistency_checking),
            ("Synchronization", self.test_synchronization),
            ("Validation System", self.test_validation_system),
            ("Error Handling", self.test_error_handling),
            ("Colors Utility", self.test_colors_utility),
        ]
        
        passed = 0
        failed = 0
        errors = 0
        
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
            else:
                if self.test_results[test_name]["status"] == "ERROR":
                    errors += 1
                else:
                    failed += 1
        
        # Print summary
        print(f"\n{Colors.WHITE}📊 TEST SUMMARY{Colors.NC}")
        print("=" * 50)
        print(f"{Colors.GREEN}✅ Passed: {passed}{Colors.NC}")
        print(f"{Colors.RED}❌ Failed: {failed}{Colors.NC}")
        print(f"{Colors.YELLOW}💥 Errors: {errors}{Colors.NC}")
        print(f"📝 Total: {len(tests)}")
        
        # Detailed results
        if failed > 0 or errors > 0:
            print(f"\n{Colors.YELLOW}📋 DETAILED RESULTS{Colors.NC}")
            print("-" * 40)
            for test_name, result in self.test_results.items():
                if result["status"] != "PASSED":
                    status_color = Colors.RED if result["status"] == "FAILED" else Colors.YELLOW
                    print(f"{status_color}{result['status']}: {test_name}{Colors.NC}")
                    if result["error"]:
                        print(f"   Error: {result['error']}")
        
        success_rate = (passed / len(tests)) * 100
        print(f"\n{Colors.CYAN}🎯 Success Rate: {success_rate:.1f}%{Colors.NC}")
        
        if success_rate == 100:
            print(f"{Colors.GREEN}🎉 ALL TESTS PASSED! The improvements are working perfectly.{Colors.NC}")
        elif success_rate >= 80:
            print(f"{Colors.YELLOW}⚠️  Most tests passed, but some issues need attention.{Colors.NC}")
        else:
            print(f"{Colors.RED}🚨 Multiple issues detected. Review the improvements.{Colors.NC}")
        
        return success_rate == 100
    
    def cleanup(self):
        """Clean up test environment."""
        if self.temp_dir and self.temp_dir.exists():
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info(f"Cleaned up test environment: {self.temp_dir}")


def main():
    """Main function to run all tests."""
    print(f"{Colors.BLUE}🔧 DockerUserSync Improvements Debug Program{Colors.NC}")
    print(f"{Colors.CYAN}Testing all improvements with dry-run mode{Colors.NC}")
    print()
    
    tester = DockerUserSyncTester()
    
    try:
        success = tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}⚠️  Testing interrupted by user{Colors.NC}")
        return 1
    except Exception as e:
        print(f"\n{Colors.RED}💥 Unexpected error during testing: {e}{Colors.NC}")
        logger.error(f"Unexpected error: {e}")
        logger.debug(traceback.format_exc())
        return 1
    finally:
        tester.cleanup()


if __name__ == "__main__":
    sys.exit(main())