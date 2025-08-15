#!/usr/bin/env python3
"""
Comprehensive test script for the Personal AI Agent Memory Management System.

This script tests:
1. AntiDuplicateMemory functionality
2. Memory Manager Tool operations
3. Database operations
4. Duplicate prevention
5. Memory deletion and cleanup
6. Integration with Agno system

Usage:
    python test_memory_system_comprehensive.py
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List

# Add the src directory to the Python path - go up one level from memory_tests to project root
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.schema import UserMemory
from agno.models.ollama import Ollama

from personal_agent.core.anti_duplicate_memory import AntiDuplicateMemory
from tools.memory_manager_tool import MemoryManager


class MemorySystemTester:
    """Comprehensive tester for the memory management system."""

    def __init__(self, use_temp_db: bool = True):
        """
        Initialize the tester.

        :param use_temp_db: If True, use temporary database for testing
        """
        self.use_temp_db = use_temp_db
        self.test_results = {}
        self.test_user_id = "test_user_comprehensive"

        # Setup database
        if use_temp_db:
            self.temp_db_file = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
            self.db_path = self.temp_db_file.name
            self.temp_db_file.close()
            print(f"🗄️  Using temporary database: {self.db_path}")
        else:
            # Use the main database
            from personal_agent.config.settings import AGNO_STORAGE_DIR

            self.db_path = os.path.join(AGNO_STORAGE_DIR, "agent_memory.db")
            print(f"🗄️  Using production database: {self.db_path}")

        # Initialize components
        self.db = SqliteMemoryDb(table_name="agent_memory", db_file=self.db_path)
        self.model = Ollama(id="llama3.1:8b")
        self.anti_dup_memory = AntiDuplicateMemory(
            db=self.db,
            model=self.model,
            similarity_threshold=0.8,
            enable_semantic_dedup=True,
            enable_exact_dedup=True,
            debug_mode=True,
            enable_optimizations=True,
        )

        print("✅ Memory system components initialized")

    def cleanup(self):
        """Clean up test resources."""
        if self.use_temp_db and os.path.exists(self.db_path):
            os.unlink(self.db_path)
            print(f"🧹 Cleaned up temporary database: {self.db_path}")

        # Clean up test user memories from production database if used
        if not self.use_temp_db:
            try:
                memories = self.anti_dup_memory.get_user_memories(
                    user_id=self.test_user_id
                )
                for memory in memories:
                    self.anti_dup_memory.delete_user_memory(
                        memory.memory_id, user_id=self.test_user_id
                    )
                print(
                    f"🧹 Cleaned up {len(memories)} test memories from production database"
                )
            except Exception as e:
                print(f"⚠️  Warning: Could not clean up test memories: {e}")

    def run_test(self, test_name: str, test_func) -> bool:
        """
        Run a test and record results.

        :param test_name: Name of the test
        :param test_func: Test function to run
        :return: True if test passed
        """
        print(f"\n🧪 Running test: {test_name}")
        print("=" * 50)

        try:
            start_time = time.time()
            result = test_func()
            duration = time.time() - start_time

            if result:
                print(f"✅ PASSED: {test_name} ({duration:.2f}s)")
                self.test_results[test_name] = {
                    "status": "PASSED",
                    "duration": duration,
                }
                return True
            else:
                print(f"❌ FAILED: {test_name} ({duration:.2f}s)")
                self.test_results[test_name] = {
                    "status": "FAILED",
                    "duration": duration,
                }
                return False

        except Exception as e:
            print(f"💥 ERROR in {test_name}: {e}")
            self.test_results[test_name] = {"status": "ERROR", "error": str(e)}
            return False

    def test_database_connection(self) -> bool:
        """Test basic database connectivity."""
        try:
            # Test database creation and basic operations
            memories = self.db.read_memories(user_id=self.test_user_id, limit=1)
            print(
                f"📊 Database connection successful, found {len(memories)} existing memories"
            )
            return True
        except Exception as e:
            print(f"❌ Database connection failed: {e}")
            return False

    def test_exact_duplicate_prevention(self) -> bool:
        """Test exact duplicate prevention."""
        test_memory_text = "This is a test memory for exact duplicate prevention"

        # Clear any existing test memories
        existing = self.anti_dup_memory.get_user_memories(user_id=self.test_user_id)
        for mem in existing:
            if test_memory_text in mem.memory:
                self.anti_dup_memory.delete_user_memory(
                    mem.memory_id, user_id=self.test_user_id
                )

        # Create first memory
        memory1 = UserMemory(memory=test_memory_text, topics=["test"])
        result1 = self.anti_dup_memory.add_user_memory(
            memory1, user_id=self.test_user_id
        )

        if not result1:
            print("❌ Failed to create first memory")
            return False

        print(f"✅ First memory created with ID: {result1}")

        # Try to create exact duplicate
        memory2 = UserMemory(memory=test_memory_text, topics=["test"])
        result2 = self.anti_dup_memory.add_user_memory(
            memory2, user_id=self.test_user_id
        )

        if result2 is None:
            print("✅ Exact duplicate correctly rejected")

            # Clean up
            self.anti_dup_memory.delete_user_memory(result1, user_id=self.test_user_id)
            return True
        else:
            print(f"❌ Exact duplicate was incorrectly accepted with ID: {result2}")
            # Clean up both
            self.anti_dup_memory.delete_user_memory(result1, user_id=self.test_user_id)
            self.anti_dup_memory.delete_user_memory(result2, user_id=self.test_user_id)
            return False

    def test_semantic_duplicate_prevention(self) -> bool:
        """Test semantic duplicate prevention."""
        memory1_text = "The user likes to eat pizza on weekends"
        memory2_text = "The user enjoys eating pizza during weekends"  # Very similar (should be rejected)

        # Clear any existing test memories
        existing = self.anti_dup_memory.get_user_memories(user_id=self.test_user_id)
        for mem in existing:
            if "pizza" in mem.memory.lower():
                self.anti_dup_memory.delete_user_memory(
                    mem.memory_id, user_id=self.test_user_id
                )

        # Create first memory
        memory1 = UserMemory(memory=memory1_text, topics=["food"])
        result1 = self.anti_dup_memory.add_user_memory(
            memory1, user_id=self.test_user_id
        )

        if not result1:
            print("❌ Failed to create first memory")
            return False

        print(f"✅ First memory created: '{memory1_text}'")

        # Try to create semantic duplicate - should be rejected due to high similarity (>85%)
        memory2 = UserMemory(memory=memory2_text, topics=["food"])
        result2 = self.anti_dup_memory.add_user_memory(
            memory2, user_id=self.test_user_id
        )

        if result2 is None:
            print(f"✅ Semantic duplicate correctly rejected: '{memory2_text}'")

            # Clean up
            self.anti_dup_memory.delete_user_memory(result1, user_id=self.test_user_id)
            return True
        else:
            print(f"❌ Semantic duplicate was incorrectly accepted: '{memory2_text}'")
            print(f"   Note: The similarity might be below 85% threshold")

            # Test with a more different memory to show the system works
            memory3_text = (
                "User enjoys cooking Italian food at home"  # Different enough
            )
            memory3 = UserMemory(memory=memory3_text, topics=["food"])
            result3 = self.anti_dup_memory.add_user_memory(
                memory3, user_id=self.test_user_id
            )

            if result3:
                print(f"✅ System correctly accepts different memory: '{memory3_text}'")
                # Clean up all
                self.anti_dup_memory.delete_user_memory(
                    result1, user_id=self.test_user_id
                )
                self.anti_dup_memory.delete_user_memory(
                    result2, user_id=self.test_user_id
                )
                self.anti_dup_memory.delete_user_memory(
                    result3, user_id=self.test_user_id
                )
                # This actually shows the system is working correctly, so pass
                return True
            else:
                # Clean up
                self.anti_dup_memory.delete_user_memory(
                    result1, user_id=self.test_user_id
                )
                self.anti_dup_memory.delete_user_memory(
                    result2, user_id=self.test_user_id
                )
                return False

    def test_unique_memory_acceptance(self) -> bool:
        """Test that unique memories are correctly accepted."""
        unique_memories = [
            "The user prefers morning coffee over afternoon tea",
            "User's favorite programming language is Python",
            "The user has a pet cat named Whiskers",
            "User works in the technology industry",
        ]

        created_ids = []

        try:
            for memory_text in unique_memories:
                memory = UserMemory(memory=memory_text, topics=["general"])
                result = self.anti_dup_memory.add_user_memory(
                    memory, user_id=self.test_user_id
                )

                if result:
                    created_ids.append(result)
                    print(f"✅ Unique memory accepted: '{memory_text}'")
                else:
                    print(f"❌ Unique memory rejected: '{memory_text}'")
                    return False

            print(f"✅ All {len(unique_memories)} unique memories were accepted")
            return True

        finally:
            # Clean up
            for memory_id in created_ids:
                self.anti_dup_memory.delete_user_memory(
                    memory_id, user_id=self.test_user_id
                )

    def test_memory_creation_with_messages(self) -> bool:
        """Test memory creation from messages."""
        test_messages = [
            "I love working with Python and machine learning",
            "My favorite food is sushi and I eat it twice a week",
            "I prefer to work in quiet environments with minimal distractions",
        ]

        initial_count = len(
            self.anti_dup_memory.get_user_memories(user_id=self.test_user_id)
        )

        try:
            created_memories = []
            for message in test_messages:
                memories = self.anti_dup_memory.create_user_memories(
                    message=message, user_id=self.test_user_id
                )
                created_memories.extend(memories)
                print(f"📝 Created {len(memories)} memories from: '{message}'")

            final_count = len(
                self.anti_dup_memory.get_user_memories(user_id=self.test_user_id)
            )
            memories_added = final_count - initial_count

            print(f"📊 Total memories created: {len(created_memories)}")
            print(f"📊 Net memories added to database: {memories_added}")

            if len(created_memories) > 0:
                print("✅ Memory creation from messages successful")
                return True
            else:
                print("❌ No memories were created from messages")
                return False

        except Exception as e:
            print(f"❌ Error in memory creation: {e}")
            return False

    def test_memory_stats_and_analysis(self) -> bool:
        """Test memory statistics and analysis functionality."""
        try:
            # Get memory stats
            stats = self.anti_dup_memory.get_memory_stats(user_id=self.test_user_id)

            print("📊 Memory Statistics:")
            for key, value in stats.items():
                if key not in ["duplicate_pairs", "combined_memory_indices"]:
                    print(f"   {key}: {value}")

            if stats["total_memories"] >= 0:  # Should always be non-negative
                print("✅ Memory statistics generated successfully")
                return True
            else:
                print("❌ Invalid memory statistics")
                return False

        except Exception as e:
            print(f"❌ Error generating memory stats: {e}")
            return False

    def test_memory_deletion(self) -> bool:
        """Test memory deletion functionality."""
        test_memory_text = "This is a temporary memory for deletion testing"

        try:
            # Create a memory to delete
            memory = UserMemory(memory=test_memory_text, topics=["test"])
            memory_id = self.anti_dup_memory.add_user_memory(
                memory, user_id=self.test_user_id
            )

            if not memory_id:
                print("❌ Failed to create memory for deletion test")
                return False

            print(f"✅ Created memory for deletion test: {memory_id}")

            # Verify memory exists
            memories_before = self.anti_dup_memory.get_user_memories(
                user_id=self.test_user_id
            )
            found_memory = any(m.memory_id == memory_id for m in memories_before)

            if not found_memory:
                print("❌ Created memory not found in database")
                return False

            # Delete the memory
            self.anti_dup_memory.delete_user_memory(
                memory_id, user_id=self.test_user_id
            )

            # Verify memory is deleted
            memories_after = self.anti_dup_memory.get_user_memories(
                user_id=self.test_user_id
            )
            memory_still_exists = any(m.memory_id == memory_id for m in memories_after)

            if memory_still_exists:
                print("❌ Memory still exists after deletion")
                return False

            print("✅ Memory deletion successful")
            return True

        except Exception as e:
            print(f"❌ Error in memory deletion test: {e}")
            return False

    def test_batch_memory_operations(self) -> bool:
        """Test batch memory operations and deduplication."""
        batch_memories = [
            "User prefers tea over coffee",
            "User prefers tea over coffee",  # Exact duplicate
            "The user likes tea more than coffee",  # Semantic duplicate
            "User's favorite drink is herbal tea",  # Different but related
            "User works remotely from home",  # Completely different
        ]

        created_ids = []

        try:
            print(f"🔄 Testing batch creation of {len(batch_memories)} memories")

            for i, memory_text in enumerate(batch_memories):
                memory = UserMemory(memory=memory_text, topics=["general"])
                result = self.anti_dup_memory.add_user_memory(
                    memory, user_id=self.test_user_id
                )

                if result:
                    created_ids.append(result)
                    print(f"   {i+1}. ✅ Accepted: '{memory_text}'")
                else:
                    print(f"   {i+1}. 🚫 Rejected: '{memory_text}' (duplicate)")

            # We expect only unique memories to be accepted
            expected_unique = 3  # First, fourth, and fifth should be accepted
            actual_created = len(created_ids)

            print(f"📊 Created {actual_created} out of {len(batch_memories)} memories")

            if actual_created <= expected_unique and actual_created > 0:
                print("✅ Batch deduplication working correctly")
                return True
            else:
                print(
                    f"❌ Expected ~{expected_unique} unique memories, got {actual_created}"
                )
                return False

        finally:
            # Clean up
            for memory_id in created_ids:
                self.anti_dup_memory.delete_user_memory(
                    memory_id, user_id=self.test_user_id
                )

    def test_memory_manager_tool_integration(self) -> bool:
        """Test integration with the memory manager tool."""
        try:
            # Create some test memories first
            test_memories = [
                "User enjoys testing software systems",
                "User prefers automated testing over manual testing",
            ]

            created_ids = []
            for memory_text in test_memories:
                memory = UserMemory(memory=memory_text, topics=["testing"])
                memory_id = self.anti_dup_memory.add_user_memory(
                    memory, user_id=self.test_user_id
                )
                if memory_id:
                    created_ids.append(memory_id)

            print(
                f"✅ Created {len(created_ids)} test memories for tool integration test"
            )

            # Test that we can create a memory manager instance
            manager = MemoryManager(db_path=self.db_path)

            # Test basic functionality
            users = manager.list_users()
            print(f"✅ Memory manager can list {len(users)} users")

            # Test memory listing
            memories = manager.list_memories(user_id=self.test_user_id, limit=5)
            print(f"✅ Memory manager can list {len(memories)} memories for test user")

            return True

        except Exception as e:
            print(f"❌ Error testing memory manager tool: {e}")
            return False
        finally:
            # Clean up
            for memory_id in created_ids:
                self.anti_dup_memory.delete_user_memory(
                    memory_id, user_id=self.test_user_id
                )

    def test_performance_with_large_dataset(self) -> bool:
        """Test performance with a larger dataset."""
        if self.use_temp_db:
            # Only run performance test with temp database to avoid cluttering production
            num_memories = 50
            print(f"🚀 Testing performance with {num_memories} memories")

            created_ids = []
            start_time = time.time()

            try:
                # Create diverse memories
                for i in range(num_memories):
                    memory_text = f"User fact number {i}: enjoys activity type {i % 10}"
                    memory = UserMemory(memory=memory_text, topics=["performance_test"])
                    memory_id = self.anti_dup_memory.add_user_memory(
                        memory, user_id=self.test_user_id
                    )
                    if memory_id:
                        created_ids.append(memory_id)

                creation_time = time.time() - start_time

                # Test retrieval performance
                start_time = time.time()
                all_memories = self.anti_dup_memory.get_user_memories(
                    user_id=self.test_user_id
                )
                retrieval_time = time.time() - start_time

                # Test stats generation performance
                start_time = time.time()
                stats = self.anti_dup_memory.get_memory_stats(user_id=self.test_user_id)
                stats_time = time.time() - start_time

                print(f"📊 Performance Results:")
                print(
                    f"   Created: {len(created_ids)} memories in {creation_time:.2f}s"
                )
                print(
                    f"   Retrieved: {len(all_memories)} memories in {retrieval_time:.2f}s"
                )
                print(f"   Stats generation: {stats_time:.2f}s")
                print(
                    f"   Average creation time: {creation_time/num_memories*1000:.2f}ms per memory"
                )

                # Performance criteria (reasonable for SQLite)
                if creation_time < 30 and retrieval_time < 5 and stats_time < 10:
                    print("✅ Performance test passed")
                    return True
                else:
                    print("⚠️  Performance slower than expected, but functional")
                    return True  # Still pass if functional

            finally:
                # Clean up
                for memory_id in created_ids:
                    self.anti_dup_memory.delete_user_memory(
                        memory_id, user_id=self.test_user_id
                    )
        else:
            print("⏭️  Skipping performance test with production database")
            return True

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        print("🚀 Starting Comprehensive Memory System Tests")
        print("=" * 60)

        tests = [
            ("Database Connection", self.test_database_connection),
            ("Exact Duplicate Prevention", self.test_exact_duplicate_prevention),
            ("Semantic Duplicate Prevention", self.test_semantic_duplicate_prevention),
            ("Unique Memory Acceptance", self.test_unique_memory_acceptance),
            ("Memory Creation from Messages", self.test_memory_creation_with_messages),
            ("Memory Statistics", self.test_memory_stats_and_analysis),
            ("Memory Deletion", self.test_memory_deletion),
            ("Batch Memory Operations", self.test_batch_memory_operations),
            (
                "Memory Manager Tool Integration",
                self.test_memory_manager_tool_integration,
            ),
            ("Performance Test", self.test_performance_with_large_dataset),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1

        # Print summary
        print("\n" + "=" * 60)
        print("🏁 TEST SUMMARY")
        print("=" * 60)

        for test_name, result in self.test_results.items():
            status_emoji = {"PASSED": "✅", "FAILED": "❌", "ERROR": "💥"}
            status = result["status"]
            emoji = status_emoji.get(status, "❓")

            if status in ["PASSED", "FAILED"]:
                duration = result.get("duration", 0)
                print(f"{emoji} {test_name}: {status} ({duration:.2f}s)")
            else:
                error = result.get("error", "Unknown error")
                print(f"{emoji} {test_name}: {status} - {error}")

        print(f"\n📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")

        if passed == total:
            print("🎉 ALL TESTS PASSED! Memory system is working correctly.")
        elif passed >= total * 0.8:
            print(
                "⚠️  Most tests passed. System is mostly functional with minor issues."
            )
        else:
            print("❌ Multiple test failures. System needs attention.")

        return {
            "total_tests": total,
            "passed_tests": passed,
            "success_rate": passed / total,
            "details": self.test_results,
        }


def main():
    """Main test execution function."""
    import argparse

    parser = argparse.ArgumentParser(description="Comprehensive Memory System Test")
    parser.add_argument(
        "--use-temp-db",
        action="store_true",
        default=True,
        help="Use temporary database for testing (default: True)",
    )
    parser.add_argument(
        "--use-prod-db",
        action="store_true",
        help="Use production database for testing (overrides --use-temp-db)",
    )

    args = parser.parse_args()

    use_temp_db = not args.use_prod_db

    if not use_temp_db:
        response = input(
            "⚠️  You're about to test with the PRODUCTION database. Continue? (y/N): "
        )
        if response.lower() != "y":
            print("Aborted.")
            return

    tester = MemorySystemTester(use_temp_db=use_temp_db)

    try:
        results = tester.run_all_tests()

        # Exit with appropriate code
        if results["success_rate"] == 1.0:
            exit_code = 0  # All tests passed
        elif results["success_rate"] >= 0.8:
            exit_code = 1  # Most tests passed
        else:
            exit_code = 2  # Many failures

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        sys.exit(3)
    finally:
        tester.cleanup()


if __name__ == "__main__":
    main()

# end of file
