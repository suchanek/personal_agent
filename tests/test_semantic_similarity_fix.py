#!/usr/bin/env python3
"""
Test to validate the fix for semantic similarity false positives.

This test specifically checks that "I love halloween" and "I love vanilla ice cream"
are NOT flagged as duplicates after our fix to the short query boost logic.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.core.semantic_memory_manager import SemanticDuplicateDetector


def test_halloween_vs_ice_cream():
    """Test that halloween and ice cream preferences are not considered duplicates."""
    print("=" * 80)
    print("TEST 1: Halloween vs Ice Cream (Original Issue)")
    print("=" * 80)

    detector = SemanticDuplicateDetector(similarity_threshold=0.8)

    phrase1 = "I love halloween"
    phrase2 = "I love vanilla ice cream"

    is_dup, match, similarity = detector.is_duplicate(phrase1, [phrase2])

    print(f"\nPhrase 1: '{phrase1}'")
    print(f"Phrase 2: '{phrase2}'")
    print(f"\nSimilarity Score: {similarity:.4f} ({similarity*100:.2f}%)")
    print(f"Threshold: 0.8000 (80.00%)")
    print(f"Flagged as duplicate: {is_dup}")

    if is_dup:
        print(f"\n❌ FAILED: These should NOT be duplicates!")
        print(f"   Match: '{match}'")
        return False
    else:
        print(f"\n✅ PASSED: Correctly identified as different preferences")
        return True


def test_similar_preferences():
    """Test that truly similar preferences ARE still caught as duplicates."""
    print("\n" + "=" * 80)
    print("TEST 2: Similar Preferences (Should be duplicates)")
    print("=" * 80)

    detector = SemanticDuplicateDetector(similarity_threshold=0.8)

    test_cases = [
        {
            "phrase1": "I love coffee",
            "phrase2": "I love coffee",
            "should_match": True,
            "description": "Exact match"
        },
        {
            "phrase1": "I prefer tea",
            "phrase2": "I like tea",
            "should_match": True,
            "description": "Semantic duplicate (tea)"
        },
        {
            "phrase1": "I enjoy hiking",
            "phrase2": "I like hiking",
            "should_match": True,
            "description": "Semantic duplicate (hiking)"
        }
    ]

    all_passed = True

    for i, test in enumerate(test_cases, 1):
        phrase1 = test["phrase1"]
        phrase2 = test["phrase2"]
        should_match = test["should_match"]
        description = test["description"]

        is_dup, match, similarity = detector.is_duplicate(phrase1, [phrase2])

        print(f"\n  Test {i}: {description}")
        print(f"    Phrase 1: '{phrase1}'")
        print(f"    Phrase 2: '{phrase2}'")
        print(f"    Similarity: {similarity:.4f} ({similarity*100:.2f}%)")
        print(f"    Expected: {'Duplicate' if should_match else 'Different'}")
        print(f"    Result: {'Duplicate' if is_dup else 'Different'}")

        if is_dup == should_match:
            print(f"    ✅ PASSED")
        else:
            print(f"    ❌ FAILED")
            all_passed = False

    return all_passed


def test_different_subjects():
    """Test that different subjects with same structure are NOT duplicates."""
    print("\n" + "=" * 80)
    print("TEST 3: Different Subjects (Should NOT be duplicates)")
    print("=" * 80)

    detector = SemanticDuplicateDetector(similarity_threshold=0.8)

    test_cases = [
        {
            "phrase1": "I love halloween",
            "phrase2": "I love vanilla ice cream",
            "description": "Halloween vs Ice cream"
        },
        {
            "phrase1": "I love christmas",
            "phrase2": "I love chocolate cake",
            "description": "Christmas vs Chocolate"
        },
        {
            "phrase1": "I enjoy swimming",
            "phrase2": "I enjoy dancing",
            "description": "Swimming vs Dancing"
        },
        {
            "phrase1": "I prefer python",
            "phrase2": "I prefer java",
            "description": "Python vs Java"
        },
        {
            "phrase1": "I work at Google",
            "phrase2": "I work at Microsoft",
            "description": "Google vs Microsoft"
        }
    ]

    all_passed = True

    for i, test in enumerate(test_cases, 1):
        phrase1 = test["phrase1"]
        phrase2 = test["phrase2"]
        description = test["description"]

        is_dup, match, similarity = detector.is_duplicate(phrase1, [phrase2])

        print(f"\n  Test {i}: {description}")
        print(f"    Phrase 1: '{phrase1}'")
        print(f"    Phrase 2: '{phrase2}'")
        print(f"    Similarity: {similarity:.4f} ({similarity*100:.2f}%)")
        print(f"    Expected: Different")
        print(f"    Result: {'Duplicate' if is_dup else 'Different'}")

        if not is_dup:
            print(f"    ✅ PASSED")
        else:
            print(f"    ❌ FAILED: Should not be flagged as duplicate")
            all_passed = False

    return all_passed


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("\n" + "=" * 80)
    print("TEST 4: Edge Cases")
    print("=" * 80)

    detector = SemanticDuplicateDetector(similarity_threshold=0.8)

    test_cases = [
        {
            "phrase1": "I love dogs",
            "phrase2": "I love cats",
            "should_match": False,
            "description": "Dogs vs Cats"
        },
        {
            "phrase1": "I love pizza",
            "phrase2": "I love pasta",
            "should_match": False,
            "description": "Pizza vs Pasta"
        },
        {
            "phrase1": "I love my dog Max",
            "phrase2": "I love my dog",
            "should_match": True,
            "description": "Subset match with extra detail"
        }
    ]

    all_passed = True

    for i, test in enumerate(test_cases, 1):
        phrase1 = test["phrase1"]
        phrase2 = test["phrase2"]
        should_match = test["should_match"]
        description = test["description"]

        is_dup, match, similarity = detector.is_duplicate(phrase1, [phrase2])

        print(f"\n  Test {i}: {description}")
        print(f"    Phrase 1: '{phrase1}'")
        print(f"    Phrase 2: '{phrase2}'")
        print(f"    Similarity: {similarity:.4f} ({similarity*100:.2f}%)")
        print(f"    Expected: {'Duplicate' if should_match else 'Different'}")
        print(f"    Result: {'Duplicate' if is_dup else 'Different'}")

        if is_dup == should_match:
            print(f"    ✅ PASSED")
        else:
            print(f"    ❌ FAILED")
            all_passed = False

    return all_passed


def main():
    """Run all tests."""
    print("🧪 Semantic Similarity Fix Validation Tests")
    print()

    try:
        # Run all test suites
        test1_passed = test_halloween_vs_ice_cream()
        test2_passed = test_similar_preferences()
        test3_passed = test_different_subjects()
        test4_passed = test_edge_cases()

        # Summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        print(f"\nTest 1 (Halloween vs Ice Cream): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
        print(f"Test 2 (Similar Preferences):    {'✅ PASSED' if test2_passed else '❌ FAILED'}")
        print(f"Test 3 (Different Subjects):     {'✅ PASSED' if test3_passed else '❌ FAILED'}")
        print(f"Test 4 (Edge Cases):             {'✅ PASSED' if test4_passed else '❌ FAILED'}")

        all_passed = test1_passed and test2_passed and test3_passed and test4_passed

        if all_passed:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ The semantic similarity fix is working correctly")
            return True
        else:
            print("\n⚠️ SOME TESTS FAILED")
            print("❌ Review the failed tests above")
            return False

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
