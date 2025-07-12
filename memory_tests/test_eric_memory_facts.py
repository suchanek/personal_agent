#!/usr/bin/env python3
"""
Test script to add multiple facts about user Eric to the memory system and analyze results.

This script:
1. Initializes the AntiDuplicateMemory system
2. Adds a series of facts about user Eric
3. Tests for duplicates and proper storage
4. Analyzes memory statistics and retrieval
5. Validates that the memory system is working correctly
"""

import os
import sys
import time
from pathlib import Path
from typing import List

# Add the src directory to the Python path - go up one level from memory_tests to project root
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.schema import UserMemory
from agno.models.ollama import Ollama

from personal_agent.config import AGNO_STORAGE_DIR
from personal_agent.core.anti_duplicate_memory import AntiDuplicateMemory


class EricMemoryTester:
    """Tester for adding facts about Eric to memory and analyzing results."""

    def __init__(self, use_temp_db: bool = True):
        """
        Initialize the tester.

        :param use_temp_db: If True, use temporary database for testing
        """
        self.use_temp_db = use_temp_db
        self.test_user_id = "eric_test"

        # Setup database
        if use_temp_db:
            self.db_path = f"{AGNO_STORAGE_DIR}/eric_memory_test.db"
            print(f"🗄️  Using test database: {self.db_path}")
        else:
            self.db_path = f"{AGNO_STORAGE_DIR}/agent_memory.db"
            print(f"🗄️  Using production database: {self.db_path}")

        # Initialize components
        self.db = SqliteMemoryDb(table_name="agent_memory", db_file=self.db_path)
        self.model = Ollama(id="llama3.1:8b")
        self.memory = AntiDuplicateMemory(
            db=self.db,
            model=self.model,
            similarity_threshold=0.8,
            enable_semantic_dedup=True,
            enable_exact_dedup=True,
            debug_mode=True,
            enable_optimizations=True,
        )

        print("✅ Memory system initialized")

    def cleanup(self):
        """Clean up test resources."""
        if self.use_temp_db and os.path.exists(self.db_path):
            try:
                os.unlink(self.db_path)
                print(f"🧹 Cleaned up test database: {self.db_path}")
            except Exception as e:
                print(f"⚠️  Could not delete database file: {e}")
        else:
            # Only clean up Eric's memories from production database if used
            try:
                memories = self.memory.get_user_memories(user_id=self.test_user_id)
                for memory in memories:
                    self.memory.delete_user_memory(
                        memory.memory_id, user_id=self.test_user_id
                    )
                print(
                    f"🧹 Cleaned up {len(memories)} memories for user {self.test_user_id}"
                )
            except Exception as e:
                print(f"⚠️  Warning: Could not clean up memories: {e}")

    def add_facts_about_eric(self):
        """Add a series of facts about Eric to the memory system."""
        facts = [
            # Personal information
            "Eric is a software engineer who specializes in AI and machine learning.",
            "Eric has been programming for over 15 years.",
            "Eric's favorite programming language is Python.",
            "Eric also knows JavaScript, TypeScript, and Go.",
            "Eric works remotely from his home office.",
            # Preferences
            "Eric prefers dark mode in all his applications and tools.",
            "Eric uses VS Code as his primary code editor.",
            "Eric enjoys using terminal-based tools and the command line.",
            "Eric prefers tea over coffee in the morning.",
            "Eric likes to listen to ambient music while coding.",
            # Habits
            "Eric usually starts work at 8:30 AM.",
            "Eric takes a lunch break at noon for about 45 minutes.",
            "Eric goes for a walk every afternoon to clear his mind.",
            "Eric attends team meetings on Mondays and Thursdays.",
            "Eric likes to review code in the mornings when his mind is fresh.",
            # Interests
            "Eric is interested in natural language processing and LLMs.",
            "Eric enjoys reading technical books about software architecture.",
            "Eric follows several technology blogs and newsletters.",
            "Eric is learning about distributed systems in his spare time.",
            "Eric contributes to open source projects on weekends.",
            # Slightly similar facts (to test deduplication)
            "Eric works as a software developer with focus on artificial intelligence.",
            "Eric has been writing code for more than 15 years.",
            "Python is Eric's preferred programming language.",
            "Eric works from home as a remote employee.",
            "Eric starts his workday around 8:30 in the morning.",
        ]

        print(f"\n📝 Adding {len(facts)} facts about Eric to memory system")
        print("=" * 50)

        created_memories = []

        for i, fact in enumerate(facts, 1):
            print(f"\n[{i}/{len(facts)}] Adding fact: '{fact}'")
            memories = self.memory.create_user_memories(
                message=fact, user_id=self.test_user_id
            )
            if memories:
                created_memories.extend(memories)
                print(f"✅ Added {len(memories)} memories")
            else:
                print("❌ Failed to add memory")

        print(
            f"\n📊 Summary: Added {len(created_memories)} memories out of {len(facts)} facts"
        )
        return created_memories

    def analyze_results(self, created_memories: List[UserMemory]):
        """Analyze the results of memory creation."""
        print("\n🔍 Analyzing memory results")
        print("=" * 50)

        # Get all current memories
        all_memories = self.memory.get_user_memories(user_id=self.test_user_id)
        print(f"📊 Total memories in database: {len(all_memories)}")

        # Check for duplicates
        memory_texts = [mem.memory for mem in all_memories]
        unique_texts = set(memory_texts)

        print(f"📊 Unique memory texts: {len(unique_texts)}")
        if len(memory_texts) > len(unique_texts):
            print(f"⚠️  Found {len(memory_texts) - len(unique_texts)} duplicate texts")
            duplicates = [text for text in memory_texts if memory_texts.count(text) > 1]
            print("Duplicates:")
            for dup in set(duplicates):
                print(f"  - '{dup}' (appears {memory_texts.count(dup)} times)")
        else:
            print("✅ No duplicate memory texts found")

        # Get memory stats
        stats = self.memory.get_memory_stats(user_id=self.test_user_id)

        print("\n📊 Memory Statistics:")
        for key, value in stats.items():
            if key not in ["duplicate_pairs", "combined_memory_indices"]:
                print(f"  {key}: {value}")

        # Test memory retrieval
        print("\n🔍 Testing memory retrieval")
        query_terms = [
            "python",
            "work schedule",
            "programming",
            "interests",
            "preferences",
        ]

        for term in query_terms:
            print(f"\nSearching for: '{term}'")
            relevant_memories = self.memory.search_user_memories(
                query=term, user_id=self.test_user_id, limit=3
            )

            if relevant_memories:
                print(f"Found {len(relevant_memories)} relevant memories:")
                for i, mem in enumerate(relevant_memories, 1):
                    print(f"  {i}. '{mem.memory}'")
            else:
                print("No relevant memories found")

        return all_memories

    def run_test(self):
        """Run the complete test."""
        print("\n🧪 Starting Eric Memory Test")
        print("=" * 70)

        try:
            # First, clean up any existing memories
            initial_memories = self.memory.get_user_memories(user_id=self.test_user_id)
            if initial_memories:
                print(
                    f"Found {len(initial_memories)} existing memories, cleaning up..."
                )
                for mem in initial_memories:
                    self.memory.delete_user_memory(
                        mem.memory_id, user_id=self.test_user_id
                    )

            # Add facts about Eric
            start_time = time.time()
            created_memories = self.add_facts_about_eric()
            add_time = time.time() - start_time

            # Analyze results
            self.analyze_results(created_memories)

            total_time = time.time() - start_time
            print(
                f"\n⏱️  Performance: Added {len(created_memories)} memories in {add_time:.2f}s"
            )
            print(f"⏱️  Total test time: {total_time:.2f}s")

            print("\n✅ Test completed successfully")

        except Exception as e:
            print(f"\n💥 Error during test: {e}")
            import traceback

            traceback.print_exc()

        finally:
            # Don't clean up automatically so we can inspect the results
            print(
                "\nℹ️  Database not cleaned up - run cleanup() manually to remove test data"
            )
            print(f"ℹ️  Database location: {self.db_path}")


if __name__ == "__main__":
    tester = EricMemoryTester(use_temp_db=True)
    try:
        tester.run_test()
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted by user")

    # Uncomment to clean up test database after running
    # tester.cleanup()

    print("\nTo clean up the database, run:")
    print("tester.cleanup()")
