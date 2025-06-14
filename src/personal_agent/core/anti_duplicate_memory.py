#!/usr/bin/env python3
"""
Anti-Duplicate Memory Manager for Ollama Models.

This module provides a superclass that extends Agno's Memory class with
intelligent duplicate detection and prevention capabilities.
"""

import difflib
import logging
import sys
from pathlib import Path
from typing import List, Optional, Union

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agno.memory.v2.db.base import MemoryDb
from agno.memory.v2.memory import Memory
from agno.memory.v2.schema import UserMemory
from agno.models.base import Model

from personal_agent.config import USER_ID
from personal_agent.utils import setup_logging

logger = setup_logging(__name__)


class AntiDuplicateMemory(Memory):
    """
    Enhanced Memory class that prevents duplicate memory creation.

    This class extends Agno's Memory class with intelligent duplicate detection
    and prevention mechanisms specifically designed to address the memory
    duplication issues found in Ollama models.
    """

    def __init__(
        self,
        db: MemoryDb,
        model: Optional[Model] = None,
        similarity_threshold: float = 0.8,
        enable_semantic_dedup: bool = True,
        enable_exact_dedup: bool = True,
        debug_mode: bool = False,
    ):
        """
        Initialize the anti-duplicate memory manager.

        :param db: Memory database instance
        :param model: Model for memory operations
        :param similarity_threshold: Threshold for semantic similarity (0.0-1.0)
        :param enable_semantic_dedup: Enable semantic duplicate detection
        :param enable_exact_dedup: Enable exact duplicate detection
        :param debug_mode: Enable debug logging
        """
        super().__init__(db=db, model=model)
        self.similarity_threshold = similarity_threshold
        self.enable_semantic_dedup = enable_semantic_dedup
        self.enable_exact_dedup = enable_exact_dedup
        self.debug_mode = debug_mode

        if self.debug_mode:
            logger.setLevel(logging.DEBUG)

        logger.info(
            "Initialized AntiDuplicateMemory with similarity_threshold=%.2f",
            similarity_threshold,
        )

    def _is_exact_duplicate(
        self, new_memory: str, existing_memories: List[UserMemory]
    ) -> Optional[UserMemory]:
        """
        Check for exact duplicate memories.

        :param new_memory: New memory text to check
        :param existing_memories: List of existing memories
        :return: Existing memory if duplicate found, None otherwise
        """
        new_memory_clean = new_memory.strip().lower()

        for existing in existing_memories:
            existing_clean = existing.memory.strip().lower()
            if new_memory_clean == existing_clean:
                logger.debug("Exact duplicate found: '%s'", new_memory)
                return existing

        return None

    def _is_semantic_duplicate(
        self, new_memory: str, existing_memories: List[UserMemory]
    ) -> Optional[UserMemory]:
        """
        Check for semantic duplicate memories using text similarity.

        :param new_memory: New memory text to check
        :param existing_memories: List of existing memories
        :return: Existing memory if duplicate found, None otherwise
        """
        new_memory_clean = new_memory.strip().lower()

        for existing in existing_memories:
            existing_clean = existing.memory.strip().lower()

            # Use difflib for similarity calculation
            similarity = difflib.SequenceMatcher(
                None, new_memory_clean, existing_clean
            ).ratio()

            if similarity >= self.similarity_threshold:
                logger.debug(
                    "Semantic duplicate found (similarity: %.2f): '%s' ~ '%s'",
                    similarity,
                    new_memory,
                    existing.memory,
                )
                return existing

        return None

    def _contains_multiple_facts(self, memory_text: str) -> bool:
        """
        Check if a memory contains multiple distinct facts.

        :param memory_text: Memory text to analyze
        :return: True if multiple facts detected
        """
        # Common indicators of combined memories
        combination_indicators = [
            " and ",
            " & ",
            ", and",
            " also ",
            " plus ",
            " as well as ",
            "; ",
        ]

        memory_lower = memory_text.lower()
        indicator_count = sum(
            1 for indicator in combination_indicators if indicator in memory_lower
        )

        # If memory is long and has multiple indicators, likely combined
        is_combined = len(memory_text) > 50 and indicator_count >= 1

        if is_combined:
            logger.debug("Combined memory detected: '%s'", memory_text)

        return is_combined

    def _deduplicate_batch(self, memories: List[UserMemory]) -> List[UserMemory]:
        """
        Remove duplicates from a batch of memories.

        This method handles rapid-fire memory creation where multiple identical
        memories might be created in quick succession.

        :param memories: List of memories to deduplicate
        :return: Deduplicated list of memories
        """
        if not memories:
            return memories

        unique_memories = []
        seen_exact = set()
        seen_semantic = []

        for memory in memories:
            memory_text = memory.memory.strip().lower()

            # Check for exact duplicates in this batch
            if self.enable_exact_dedup and memory_text in seen_exact:
                logger.debug("Batch exact duplicate rejected: '%s'", memory.memory)
                continue

            # Check for semantic duplicates in this batch
            is_semantic_duplicate = False
            if self.enable_semantic_dedup:
                for seen_memory in seen_semantic:
                    similarity = difflib.SequenceMatcher(
                        None, memory_text, seen_memory.lower()
                    ).ratio()

                    if similarity >= self.similarity_threshold:
                        logger.debug(
                            "Batch semantic duplicate rejected (similarity: %.2f): '%s'",
                            similarity,
                            memory.memory,
                        )
                        is_semantic_duplicate = True
                        break

            if not is_semantic_duplicate:
                unique_memories.append(memory)
                seen_exact.add(memory_text)
                seen_semantic.append(memory_text)

        logger.debug(
            "Batch deduplication: %d -> %d memories",
            len(memories),
            len(unique_memories),
        )

        return unique_memories

    def _should_reject_memory(
        self, new_memory: str, existing_memories: List[UserMemory]
    ) -> tuple[bool, str]:
        """
        Determine if a memory should be rejected.

        :param new_memory: New memory text to check
        :param existing_memories: List of existing memories
        :return: Tuple of (should_reject, reason)
        """
        # Check for exact duplicates
        if self.enable_exact_dedup:
            exact_duplicate = self._is_exact_duplicate(new_memory, existing_memories)
            if exact_duplicate:
                return True, f"Exact duplicate of: '{exact_duplicate.memory}'"

        # Check for semantic duplicates
        if self.enable_semantic_dedup:
            semantic_duplicate = self._is_semantic_duplicate(
                new_memory, existing_memories
            )
            if semantic_duplicate:
                return True, f"Semantic duplicate of: '{semantic_duplicate.memory}'"

        # Check for combined memories (reject if too complex)
        if self._contains_multiple_facts(new_memory):
            return True, "Memory contains multiple facts (should be separated)"

        return False, ""

    def add_user_memory(
        self,
        memory: UserMemory,
        user_id: str = USER_ID,
    ) -> Optional[str]:
        """
        Add a user memory with duplicate prevention.

        :param memory: UserMemory object to add
        :param user_id: User ID for the memory
        :return: Memory ID if added, None if rejected
        """
        # Get existing memories for this user
        existing_memories = self.get_user_memories(user_id=user_id)

        # Check if this memory should be rejected
        should_reject, reason = self._should_reject_memory(
            memory.memory, existing_memories
        )

        if should_reject:
            logger.info(
                "Rejecting memory for user %s: %s. Memory: '%s'",
                user_id,
                reason,
                memory.memory,
            )
            if self.debug_mode:
                print(f"🚫 REJECTED: {reason}")
                print(f"   Memory: '{memory.memory}'")
            return None

        # Memory is unique, proceed with addition
        logger.info("Adding unique memory for user %s: '%s'", user_id, memory.memory)
        if self.debug_mode:
            print(f"✅ ACCEPTED: '{memory.memory}'")

        return super().add_user_memory(memory=memory, user_id=user_id)

    def create_user_memories(
        self,
        message: Optional[str] = None,
        messages: Optional[List] = None,
        user_id: str = USER_ID,
    ) -> List[UserMemory]:
        """
        Create user memories with enhanced duplicate prevention.

        :param message: Single message to create memories from
        :param messages: List of messages to create memories from
        :param user_id: User ID for the memories
        :return: List of successfully created memories
        """
        logger.info("Creating memories for user %s", user_id)

        # Get existing memories before creation
        existing_memories_before = self.get_user_memories(user_id=user_id)
        existing_count_before = len(existing_memories_before)

        if self.debug_mode:
            print(f"\n🧠 Creating memories (existing: {existing_count_before})")
            if message:
                print(f"   Input: '{message}'")

        # Use parent class to create memories
        created_memories = super().create_user_memories(
            message=message, messages=messages, user_id=user_id
        )

        # Get all memories after creation
        all_memories_after = self.get_user_memories(user_id=user_id)

        # Find truly new memories (beyond what we had before)
        new_memories = all_memories_after[existing_count_before:]

        if self.debug_mode:
            print(f"   Raw memories created: {len(new_memories)}")

        # Post-process to remove any duplicates that slipped through
        deduplicated_memories = self._post_process_memories(
            new_memories, existing_memories_before
        )

        if self.debug_mode:
            print(f"   Final memories after dedup: {len(deduplicated_memories)}")
            for i, mem in enumerate(deduplicated_memories, 1):
                print(f"      {i}. {mem.memory}")

        return deduplicated_memories

    def _post_process_memories(
        self, new_memories: List[UserMemory], existing_memories: List[UserMemory]
    ) -> List[UserMemory]:
        """
        Post-process newly created memories to remove any duplicates.

        :param new_memories: Newly created memories
        :param existing_memories: Previously existing memories
        :return: Deduplicated list of new memories
        """
        if not new_memories:
            return []

        deduplicated = []
        all_existing = existing_memories.copy()

        for new_memory in new_memories:
            should_reject, reason = self._should_reject_memory(
                new_memory.memory, all_existing
            )

            if not should_reject:
                deduplicated.append(new_memory)
                all_existing.append(new_memory)  # Add to existing for next iteration
                logger.debug("Kept memory: '%s'", new_memory.memory)
            else:
                logger.info(
                    "Post-processing rejected memory: %s. Memory: '%s'",
                    reason,
                    new_memory.memory,
                )
                if self.debug_mode:
                    print(f"   🚫 Post-processing rejected: {reason}")

        return deduplicated

    def get_memory_stats(self, user_id: str = USER_ID) -> dict:
        """
        Get statistics about memory quality and duplicates.

        :param user_id: User ID to analyze
        :return: Dictionary with memory statistics
        """
        memories = self.get_user_memories(user_id=user_id)

        if not memories:
            return {"total_memories": 0}

        # Analyze for potential issues
        memory_texts = [m.memory for m in memories]
        unique_texts = set(memory_texts)

        # Find potential duplicates
        potential_duplicates = []
        for i, mem1 in enumerate(memories):
            for j, mem2 in enumerate(memories[i + 1 :], i + 1):
                similarity = difflib.SequenceMatcher(
                    None, mem1.memory.lower(), mem2.memory.lower()
                ).ratio()
                if similarity >= self.similarity_threshold:
                    potential_duplicates.append((i, j, similarity))

        # Find combined memories
        combined_memories = [
            i
            for i, mem in enumerate(memories)
            if self._contains_multiple_facts(mem.memory)
        ]

        # Calculate average memory length
        avg_length = sum(len(m.memory) for m in memories) / len(memories)

        return {
            "total_memories": len(memories),
            "unique_texts": len(unique_texts),
            "exact_duplicates": len(memory_texts) - len(unique_texts),
            "potential_semantic_duplicates": len(potential_duplicates),
            "combined_memories": len(combined_memories),
            "average_memory_length": avg_length,
            "duplicate_pairs": potential_duplicates,
            "combined_memory_indices": combined_memories,
        }

    def print_memory_analysis(self, user_id: str = USER_ID):
        """
        Print a detailed analysis of memory quality.

        :param user_id: User ID to analyze
        """
        stats = self.get_memory_stats(user_id)
        memories = self.get_user_memories(user_id=user_id)

        print(f"\n📊 MEMORY ANALYSIS FOR USER: {user_id}")
        print("=" * 50)
        print(f"Total memories: {stats['total_memories']}")
        print(f"Unique texts: {stats['unique_texts']}")
        print(f"Exact duplicates: {stats['exact_duplicates']}")
        print(
            f"Potential semantic duplicates: {stats['potential_semantic_duplicates']}"
        )
        print(f"Combined memories: {stats['combined_memories']}")
        print(f"Average memory length: {stats['average_memory_length']:.1f} chars")

        if stats["exact_duplicates"] > 0:
            print(f"\n⚠️  EXACT DUPLICATES DETECTED!")

        if stats["potential_semantic_duplicates"] > 0:
            print(f"\n🔍 POTENTIAL SEMANTIC DUPLICATES:")
            for i, j, similarity in stats["duplicate_pairs"]:
                print(f"  • {similarity:.2f} similarity:")
                print(f"    [{i}] {memories[i].memory}")
                print(f"    [{j}] {memories[j].memory}")

        if stats["combined_memories"] > 0:
            print(f"\n🔗 COMBINED MEMORIES:")
            for idx in stats["combined_memory_indices"]:
                print(f"  • [{idx}] {memories[idx].memory}")

        if (
            stats["exact_duplicates"] == 0
            and stats["potential_semantic_duplicates"] == 0
            and stats["combined_memories"] == 0
        ):
            print(f"\n✅ EXCELLENT: No duplicates or combined memories detected!")


# Convenience function for easy usage
def create_anti_duplicate_memory(
    db, model=None, similarity_threshold: float = 0.8, debug_mode: bool = False
) -> AntiDuplicateMemory:
    """
    Create an AntiDuplicateMemory instance with sensible defaults.

    :param db: Memory database instance
    :param model: Model for memory operations
    :param similarity_threshold: Threshold for semantic similarity
    :param debug_mode: Enable debug output
    :return: Configured AntiDuplicateMemory instance
    """
    return AntiDuplicateMemory(
        db=db,
        model=model,
        similarity_threshold=similarity_threshold,
        enable_semantic_dedup=True,
        enable_exact_dedup=True,
        debug_mode=debug_mode,
    )
