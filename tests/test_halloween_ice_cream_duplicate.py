#!/usr/bin/env python3
"""
Test to reproduce and analyze the false positive duplicate detection between
"I love halloween" and "I love vanilla ice cream".

This test helps diagnose why the semantic similarity algorithm is incorrectly
flagging these two very different statements as duplicates.
"""

import difflib
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.core.topic_classifier import TopicClassifier
from personal_agent.core.anti_duplicate_memory import AntiDuplicateMemory


def test_similarity_calculation():
    """Test the raw similarity calculation between the two phrases."""
    print("=" * 80)
    print("TEST 1: Raw Similarity Calculation")
    print("=" * 80)

    phrase1 = "I love halloween"
    phrase2 = "I love vanilla ice cream"

    # Test exact matching (lowercased)
    phrase1_lower = phrase1.strip().lower()
    phrase2_lower = phrase2.strip().lower()

    print(f"\nPhrase 1: '{phrase1}'")
    print(f"Phrase 2: '{phrase2}'")
    print(f"\nPhrase 1 (cleaned): '{phrase1_lower}'")
    print(f"Phrase 2 (cleaned): '{phrase2_lower}'")

    # Calculate similarity using difflib (same as anti_duplicate_memory.py)
    similarity = difflib.SequenceMatcher(None, phrase1_lower, phrase2_lower).ratio()

    print(f"\n📊 Similarity Score: {similarity:.4f} ({similarity*100:.2f}%)")

    # Show what parts match
    matcher = difflib.SequenceMatcher(None, phrase1_lower, phrase2_lower)
    matching_blocks = matcher.get_matching_blocks()

    print(f"\n🔍 Matching Blocks:")
    for match in matching_blocks:
        if match.size > 0:
            matched_text = phrase1_lower[match.a:match.a + match.size]
            print(f"  - '{matched_text}' (size: {match.size})")

    return similarity


def test_topic_classification():
    """Test how topics are classified for both phrases."""
    print("\n" + "=" * 80)
    print("TEST 2: Topic Classification")
    print("=" * 80)

    phrase1 = "I love halloween"
    phrase2 = "I love vanilla ice cream"

    classifier = TopicClassifier()

    print(f"\nPhrase 1: '{phrase1}'")
    topics1 = classifier.classify(phrase1, return_list=False)
    print(f"Topics: {topics1}")

    print(f"\nPhrase 2: '{phrase2}'")
    topics2 = classifier.classify(phrase2, return_list=False)
    print(f"Topics: {topics2}")

    # Check if topics overlap
    if topics1 and topics2:
        topics1_set = set(topics1.keys())
        topics2_set = set(topics2.keys())
        overlap = topics1_set.intersection(topics2_set)

        print(f"\n📊 Topic Overlap: {overlap if overlap else 'None'}")

    return topics1, topics2


def test_semantic_threshold_calculation():
    """Test the semantic threshold calculation used by AntiDuplicateMemory."""
    print("\n" + "=" * 80)
    print("TEST 3: Semantic Threshold Calculation")
    print("=" * 80)

    phrase1 = "I love halloween"
    phrase2 = "I love vanilla ice cream"

    phrase1_lower = phrase1.strip().lower()
    phrase2_lower = phrase2.strip().lower()

    # Simulate the threshold calculation from anti_duplicate_memory.py
    print("\nAnalyzing content for threshold calculation...")

    # Check for preference indicators
    preference_indicators = [
        "prefer", "like", "enjoy", "love", "hate", "dislike",
        "favorite", "favourite", "best", "worst"
    ]

    has_preferences = any(
        indicator in phrase1_lower or indicator in phrase2_lower
        for indicator in preference_indicators
    )

    print(f"Has preference indicators: {has_preferences}")

    if has_preferences:
        threshold = 0.65
        print(f"✅ Using preference threshold: {threshold}")
    else:
        threshold = 0.8
        print(f"Using default threshold: {threshold}")

    # Calculate similarity
    similarity = difflib.SequenceMatcher(None, phrase1_lower, phrase2_lower).ratio()

    print(f"\n📊 Results:")
    print(f"  Similarity: {similarity:.4f} ({similarity*100:.2f}%)")
    print(f"  Threshold:  {threshold:.4f} ({threshold*100:.2f}%)")
    print(f"  Would be flagged as duplicate: {similarity >= threshold}")

    return similarity, threshold


def test_word_by_word_comparison():
    """Break down the phrases word by word to understand the similarity."""
    print("\n" + "=" * 80)
    print("TEST 4: Word-by-Word Comparison")
    print("=" * 80)

    phrase1 = "I love halloween"
    phrase2 = "I love vanilla ice cream"

    words1 = phrase1.lower().split()
    words2 = phrase2.lower().split()

    print(f"\nPhrase 1 words: {words1}")
    print(f"Phrase 2 words: {words2}")

    # Find common words
    common_words = set(words1).intersection(set(words2))
    print(f"\nCommon words: {common_words}")

    # Calculate word overlap ratio
    total_unique_words = len(set(words1).union(set(words2)))
    common_word_count = len(common_words)
    word_overlap_ratio = common_word_count / total_unique_words if total_unique_words > 0 else 0

    print(f"Word overlap ratio: {word_overlap_ratio:.4f} ({word_overlap_ratio*100:.2f}%)")

    # Show unique words
    unique_to_1 = set(words1) - set(words2)
    unique_to_2 = set(words2) - set(words1)

    print(f"\nUnique to phrase 1: {unique_to_1}")
    print(f"Unique to phrase 2: {unique_to_2}")

    return word_overlap_ratio


def test_character_by_character():
    """Analyze character-level similarity."""
    print("\n" + "=" * 80)
    print("TEST 5: Character-by-Character Analysis")
    print("=" * 80)

    phrase1 = "i love halloween"
    phrase2 = "i love vanilla ice cream"

    print(f"\nPhrase 1: '{phrase1}' (length: {len(phrase1)})")
    print(f"Phrase 2: '{phrase2}' (length: {len(phrase2)})")

    # Calculate the common prefix
    common_prefix = ""
    for c1, c2 in zip(phrase1, phrase2):
        if c1 == c2:
            common_prefix += c1
        else:
            break

    print(f"\nCommon prefix: '{common_prefix}' (length: {len(common_prefix)})")
    print(f"Prefix ratio: {len(common_prefix)/max(len(phrase1), len(phrase2)):.4f}")

    # This is key: "i love " is the common prefix
    # That's 7 characters out of 16 (phrase1) and 24 (phrase2)

    return common_prefix


def propose_solutions():
    """Propose solutions to fix the false positive."""
    print("\n" + "=" * 80)
    print("PROPOSED SOLUTIONS")
    print("=" * 80)

    print("""
The issue is that both phrases contain "I love", which creates a high similarity
score when using basic string similarity (difflib.SequenceMatcher).

Current behavior:
- Similarity: ~42% (too high for a 65% threshold with preferences)
- Both are preference statements, so threshold is lowered to 65%
- This causes false positives for any "I love X" statements

Proposed solutions:

1. **Increase the preference threshold** (Quick fix)
   - Change from 0.65 to 0.75 or 0.80
   - Pros: Simple, immediate fix
   - Cons: Might miss some real duplicates

2. **Add content-aware similarity** (Better fix)
   - Extract the actual subject of the preference (halloween vs ice cream)
   - Compare subjects separately from sentence structure
   - Only flag as duplicate if subjects are similar
   - Pros: More accurate, context-aware
   - Cons: More complex implementation

3. **Use semantic embeddings** (Best fix)
   - Use sentence embeddings to compare semantic meaning
   - "halloween" and "vanilla ice cream" would be very different vectors
   - Pros: Most accurate, captures true semantic similarity
   - Cons: Requires embedding model (more dependencies)

4. **Topic-based filtering** (Complementary fix)
   - Only compare memories with overlapping topics
   - "halloween" (preferences/hobbies?) vs "ice cream" (preferences/food?)
   - If topics don't overlap, don't compare
   - Pros: Reduces false positives across categories
   - Cons: Requires accurate topic classification

Recommended approach:
- **Short term:** Increase preference threshold to 0.75
- **Medium term:** Add content extraction and subject comparison
- **Long term:** Consider semantic embeddings for similarity
""")


def main():
    """Run all tests and analysis."""
    print("🧪 Testing Halloween vs Ice Cream Duplicate Detection Issue")
    print()

    try:
        # Run all tests
        similarity = test_similarity_calculation()
        topics1, topics2 = test_topic_classification()
        sim, threshold = test_semantic_threshold_calculation()
        word_overlap = test_word_by_word_comparison()
        common_prefix = test_character_by_character()

        # Summary
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)

        print(f"""
Phrase 1: "I love halloween"
Phrase 2: "I love vanilla ice cream"

Similarity Score:    {similarity:.4f} ({similarity*100:.2f}%)
Threshold (prefs):   {threshold:.4f} ({threshold*100:.2f}%)
Word Overlap:        {word_overlap:.4f} ({word_overlap*100:.2f}%)
Common Prefix:       "{common_prefix}" ({len(common_prefix)} chars)

Would be flagged:    {similarity >= threshold}

❌ Problem: The 42% similarity is too high because of the "I love " prefix.
   With a 65% threshold for preferences, this shouldn't be flagged, but
   we need to verify the actual behavior in the code.

🔍 Root Cause: The preference threshold (0.65) is correctly set, but there
   might be an issue with how the threshold is being applied or calculated
   in the actual code flow.
""")

        # Show solutions
        propose_solutions()

        print("\n✅ Analysis complete! Review the findings above.")
        return True

    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
