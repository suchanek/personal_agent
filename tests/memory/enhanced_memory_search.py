#!/usr/bin/env python3
"""
Enhanced Memory Search Script

This script directly queries the memory database to search both memory content
and topics/categories, providing detailed debugging information about why
searches succeed or fail.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.schema import UserMemory

from personal_agent.config import AGNO_STORAGE_DIR, USER_ID
from personal_agent.core.semantic_memory_manager import (
    SemanticMemoryManager,
    SemanticMemoryManagerConfig,
)


class EnhancedMemorySearcher:
    """Enhanced memory searcher that searches both content and topics."""

    def __init__(self, db_path: str, user_id: str = USER_ID):
        self.db_path = db_path
        self.user_id = user_id

        # Initialize database
        self.memory_db = SqliteMemoryDb(
            table_name="personal_agent_memory", db_file=db_path
        )

        # Initialize semantic memory manager for similarity calculations
        self.semantic_manager = SemanticMemoryManager(
            config=SemanticMemoryManagerConfig(
                similarity_threshold=0.3, debug_mode=True
            )
        )

    def get_all_memories(self) -> List[UserMemory]:
        """Get all memories for the user."""
        try:
            memory_rows = self.memory_db.read_memories(user_id=self.user_id)
            user_memories = []

            for row in memory_rows:
                if row.user_id == self.user_id and row.memory:
                    try:
                        user_memory = UserMemory.from_dict(row.memory)
                        user_memories.append(user_memory)
                    except (ValueError, KeyError, TypeError) as e:
                        print(
                            f"Warning: Failed to convert memory row to UserMemory: {e}"
                        )

            return user_memories
        except Exception as e:
            print(f"Error retrieving memories: {e}")
            return []

    def search_content_only(
        self, query: str, memories: List[UserMemory], similarity_threshold: float = 0.3
    ) -> List[Tuple[UserMemory, float, str]]:
        """Search only in memory content (current Streamlit behavior)."""
        results = []

        for memory in memories:
            similarity = (
                self.semantic_manager.duplicate_detector._calculate_semantic_similarity(
                    query, memory.memory
                )
            )

            if similarity >= similarity_threshold:
                results.append((memory, similarity, "content"))

        return sorted(results, key=lambda x: x[1], reverse=True)

    def search_topics_only(
        self, query: str, memories: List[UserMemory]
    ) -> List[Tuple[UserMemory, float, str]]:
        """Search only in memory topics."""
        results = []
        query_lower = query.lower().strip()

        for memory in memories:
            if memory.topics:
                # Check for exact topic match
                topic_matches = [
                    topic for topic in memory.topics if query_lower in topic.lower()
                ]
                if topic_matches:
                    # Score based on how many topics match and how closely
                    score = 0.0
                    for topic in topic_matches:
                        if query_lower == topic.lower():
                            score += 1.0  # Exact match
                        elif query_lower in topic.lower():
                            score += 0.8  # Partial match

                    # Normalize score (max 1.0)
                    final_score = min(score, 1.0)
                    results.append(
                        (memory, final_score, f"topics: {', '.join(topic_matches)}")
                    )

        return sorted(results, key=lambda x: x[1], reverse=True)

    def search_combined(
        self, query: str, memories: List[UserMemory], similarity_threshold: float = 0.3
    ) -> List[Tuple[UserMemory, float, str]]:
        """Search both content and topics, combining scores."""
        content_results = {
            id(mem): (mem, score, "content")
            for mem, score, _ in self.search_content_only(
                query, memories, similarity_threshold
            )
        }

        topic_results = {
            id(mem): (mem, score, match_info)
            for mem, score, match_info in self.search_topics_only(query, memories)
        }

        # Combine results
        combined_results = []
        all_memory_ids = set(content_results.keys()) | set(topic_results.keys())

        for mem_id in all_memory_ids:
            content_score = content_results.get(mem_id, (None, 0.0, ""))[1]
            topic_score = topic_results.get(mem_id, (None, 0.0, ""))[1]

            # Get memory object
            memory = content_results.get(mem_id, topic_results.get(mem_id))[0]

            # Combined scoring: weighted average favoring content slightly
            combined_score = (content_score * 0.6) + (topic_score * 0.4)

            # Create match info
            match_parts = []
            if content_score > 0:
                match_parts.append(f"content({content_score:.3f})")
            if topic_score > 0:
                topic_info = topic_results.get(mem_id, (None, 0.0, ""))[2]
                match_parts.append(f"{topic_info}({topic_score:.3f})")

            match_info = " + ".join(match_parts)

            if combined_score > 0:
                combined_results.append((memory, combined_score, match_info))

        return sorted(combined_results, key=lambda x: x[1], reverse=True)

    def analyze_memory_database(self) -> Dict[str, Any]:
        """Analyze the memory database to understand its contents."""
        memories = self.get_all_memories()

        if not memories:
            return {"error": "No memories found in database"}

        # Collect statistics
        total_memories = len(memories)
        memories_with_topics = sum(1 for m in memories if m.topics)

        # Topic distribution
        topic_counts = {}
        all_topics = []
        for memory in memories:
            if memory.topics:
                for topic in memory.topics:
                    topic_counts[topic] = topic_counts.get(topic, 0) + 1
                    all_topics.append(topic)

        # Content analysis
        content_lengths = [len(m.memory) for m in memories]
        avg_content_length = (
            sum(content_lengths) / len(content_lengths) if content_lengths else 0
        )

        # Sample memories for each topic
        topic_samples = {}
        for memory in memories:
            if memory.topics:
                for topic in memory.topics:
                    if topic not in topic_samples:
                        topic_samples[topic] = []
                    if len(topic_samples[topic]) < 2:  # Keep max 2 samples per topic
                        topic_samples[topic].append(
                            memory.memory[:100] + "..."
                            if len(memory.memory) > 100
                            else memory.memory
                        )

        return {
            "total_memories": total_memories,
            "memories_with_topics": memories_with_topics,
            "memories_without_topics": total_memories - memories_with_topics,
            "unique_topics": list(topic_counts.keys()),
            "topic_distribution": topic_counts,
            "average_content_length": avg_content_length,
            "topic_samples": topic_samples,
        }

    def search_and_debug(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Perform comprehensive search with detailed debugging."""
        print(f"\n🔍 Enhanced Memory Search for: '{query}'")
        print("=" * 60)

        memories = self.get_all_memories()

        if not memories:
            return {"error": "No memories found in database"}

        print(f"📊 Database contains {len(memories)} memories")

        # Perform all search types
        content_results = self.search_content_only(query, memories)
        topic_results = self.search_topics_only(query, memories)
        combined_results = self.search_combined(query, memories)

        # Display results
        print(f"\n📝 CONTENT-ONLY SEARCH (Current Streamlit behavior):")
        print("-" * 50)
        if content_results:
            for i, (memory, score, match_info) in enumerate(content_results[:limit], 1):
                print(f"{i}. Score: {score:.3f}")
                print(
                    f"   Memory: {memory.memory[:100]}{'...' if len(memory.memory) > 100 else ''}"
                )
                print(f"   Topics: {memory.topics if memory.topics else 'None'}")
                print()
        else:
            print("❌ No results found in content search")

        print(f"\n🏷️  TOPIC-ONLY SEARCH:")
        print("-" * 50)
        if topic_results:
            for i, (memory, score, match_info) in enumerate(topic_results[:limit], 1):
                print(f"{i}. Score: {score:.3f} - {match_info}")
                print(
                    f"   Memory: {memory.memory[:100]}{'...' if len(memory.memory) > 100 else ''}"
                )
                print(f"   Topics: {memory.topics}")
                print()
        else:
            print("❌ No results found in topic search")

        print(f"\n🔄 COMBINED SEARCH (Enhanced):")
        print("-" * 50)
        if combined_results:
            for i, (memory, score, match_info) in enumerate(
                combined_results[:limit], 1
            ):
                print(f"{i}. Score: {score:.3f} - {match_info}")
                print(
                    f"   Memory: {memory.memory[:100]}{'...' if len(memory.memory) > 100 else ''}"
                )
                print(f"   Topics: {memory.topics if memory.topics else 'None'}")
                print()
        else:
            print("❌ No results found in combined search")

        return {
            "query": query,
            "total_memories": len(memories),
            "content_results": len(content_results),
            "topic_results": len(topic_results),
            "combined_results": len(combined_results),
            "content_matches": [(m.memory[:50], s) for m, s, _ in content_results[:3]],
            "topic_matches": [
                (m.memory[:50], s, info) for m, s, info in topic_results[:3]
            ],
            "combined_matches": [
                (m.memory[:50], s, info) for m, s, info in combined_results[:3]
            ],
        }


def main():
    parser = argparse.ArgumentParser(description="Enhanced Memory Search Tool")
    parser.add_argument("--query", "-q", type=str, help="Search query")
    parser.add_argument(
        "--analyze", "-a", action="store_true", help="Analyze database contents"
    )
    parser.add_argument("--db-path", type=str, help="Database path (optional)")
    parser.add_argument("--user-id", type=str, default=USER_ID, help="User ID")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Result limit")

    args = parser.parse_args()

    # Determine database path
    if args.db_path:
        db_path = args.db_path
    else:
        db_path = str(Path(AGNO_STORAGE_DIR) / "agent_memory.db")

    print(f"🗄️  Using database: {db_path}")
    print(f"👤 User ID: {args.user_id}")

    # Initialize searcher
    searcher = EnhancedMemorySearcher(db_path, args.user_id)

    if args.analyze:
        print("\n📊 ANALYZING MEMORY DATABASE")
        print("=" * 60)
        analysis = searcher.analyze_memory_database()

        if "error" in analysis:
            print(f"❌ Error: {analysis['error']}")
            return

        print(f"Total memories: {analysis['total_memories']}")
        print(f"Memories with topics: {analysis['memories_with_topics']}")
        print(f"Memories without topics: {analysis['memories_without_topics']}")
        print(
            f"Average content length: {analysis['average_content_length']:.1f} characters"
        )

        print(f"\n🏷️  TOPIC DISTRIBUTION:")
        for topic, count in sorted(
            analysis["topic_distribution"].items(), key=lambda x: x[1], reverse=True
        ):
            print(f"  {topic}: {count} memories")

        print(f"\n📝 SAMPLE MEMORIES BY TOPIC:")
        for topic, samples in analysis["topic_samples"].items():
            print(f"\n  {topic.upper()}:")
            for sample in samples:
                print(f"    - {sample}")

    if args.query:
        result = searcher.search_and_debug(args.query, args.limit)

        print(f"\n📈 SEARCH SUMMARY:")
        print(f"  Content matches: {result['content_results']}")
        print(f"  Topic matches: {result['topic_results']}")
        print(f"  Combined matches: {result['combined_results']}")

    if not args.query and not args.analyze:
        print("\n🔍 TESTING BOTH QUERIES:")
        print("\n" + "=" * 80)

        # Test 'education'
        searcher.search_and_debug("education", args.limit)

        print("\n" + "=" * 80)

        # Test 'Hopkins'
        searcher.search_and_debug("Hopkins", args.limit)


if __name__ == "__main__":
    main()
