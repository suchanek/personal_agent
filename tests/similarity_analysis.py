#!/usr/bin/env python3
"""
Detailed analysis of why 'Hopkins' gets such a low similarity score.
"""

import sys
from pathlib import Path
import difflib
import re

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.core.semantic_memory_manager import SemanticDuplicateDetector


def analyze_similarity_calculation():
    """Analyze step-by-step why 'Hopkins' gets low similarity."""
    
    detector = SemanticDuplicateDetector()
    
    query = "Hopkins"
    memory = "I graduated from Johns Hopkins in 1987"
    
    print("🔍 DETAILED SIMILARITY ANALYSIS")
    print("=" * 60)
    print(f"Query: '{query}'")
    print(f"Memory: '{memory}'")
    print()
    
    # Step 1: Text normalization
    norm_query = detector._normalize_text(query)
    norm_memory = detector._normalize_text(memory)
    
    print("📝 STEP 1: Text Normalization")
    print(f"  Original query: '{query}'")
    print(f"  Normalized query: '{norm_query}'")
    print(f"  Original memory: '{memory}'")
    print(f"  Normalized memory: '{norm_memory}'")
    print()
    
    # Step 2: String similarity using difflib
    string_similarity = difflib.SequenceMatcher(None, norm_query, norm_memory).ratio()
    
    print("📊 STEP 2: String Similarity (difflib)")
    print(f"  Comparing: '{norm_query}' vs '{norm_memory}'")
    print(f"  String similarity: {string_similarity:.4f}")
    print(f"  Weight in final score: 60%")
    print()
    
    # Step 3: Key terms extraction
    terms_query = detector._extract_key_terms(query)
    terms_memory = detector._extract_key_terms(memory)
    
    print("🔑 STEP 3: Key Terms Extraction")
    print(f"  Query terms: {terms_query}")
    print(f"  Memory terms: {terms_memory}")
    
    # Calculate terms similarity
    if not terms_query and not terms_memory:
        terms_similarity = 1.0
    elif not terms_query or not terms_memory:
        terms_similarity = 0.0
    else:
        intersection = len(terms_query.intersection(terms_memory))
        union = len(terms_query.union(terms_memory))
        terms_similarity = intersection / union if union > 0 else 0.0
    
    print(f"  Intersection: {terms_query.intersection(terms_memory)} (count: {len(terms_query.intersection(terms_memory))})")
    print(f"  Union: {terms_query.union(terms_memory)} (count: {len(terms_query.union(terms_memory))})")
    print(f"  Terms similarity: {intersection}/{union} = {terms_similarity:.4f}")
    print(f"  Weight in final score: 40%")
    print()
    
    # Step 4: Final weighted combination
    final_score = (string_similarity * 0.6) + (terms_similarity * 0.4)
    
    print("🎯 STEP 4: Final Weighted Score")
    print(f"  String similarity contribution: {string_similarity:.4f} × 0.6 = {string_similarity * 0.6:.4f}")
    print(f"  Terms similarity contribution: {terms_similarity:.4f} × 0.4 = {terms_similarity * 0.4:.4f}")
    print(f"  Final score: {final_score:.4f}")
    print()
    
    # Verify with actual method
    actual_score = detector._calculate_semantic_similarity(query, memory)
    print(f"✅ Verification: Actual method returns {actual_score:.4f}")
    print()
    
    print("🤔 WHY IS THE SCORE SO LOW?")
    print("-" * 40)
    print("1. String similarity is very low because:")
    print(f"   - Query: '{norm_query}' (7 chars)")
    print(f"   - Memory: '{norm_memory}' (39 chars)")
    print("   - Most characters don't match, so difflib ratio is low")
    print()
    print("2. Terms similarity is moderate because:")
    print("   - Only 1 out of 4 meaningful terms match")
    print("   - The algorithm treats 'hopkins' as just one term among many")
    print()
    print("3. The algorithm is designed for semantic similarity between")
    print("   full sentences, not exact word matching within text!")


def demonstrate_improved_similarity():
    """Show how we could improve the similarity calculation."""
    
    print("\n" + "=" * 60)
    print("💡 IMPROVED SIMILARITY CALCULATION")
    print("=" * 60)
    
    def improved_similarity(query: str, text: str) -> float:
        """Improved similarity that gives higher scores for exact word matches."""
        
        # Normalize both texts
        query_norm = query.lower().strip()
        text_norm = text.lower().strip()
        
        # Check for exact word match (highest priority)
        query_words = set(re.findall(r'\b\w+\b', query_norm))
        text_words = set(re.findall(r'\b\w+\b', text_norm))
        
        exact_matches = query_words.intersection(text_words)
        
        if exact_matches:
            # If we have exact word matches, give a high base score
            match_ratio = len(exact_matches) / len(query_words)
            exact_word_score = 0.7 + (match_ratio * 0.3)  # 0.7 to 1.0
            
            # Also calculate traditional semantic similarity
            detector = SemanticDuplicateDetector()
            semantic_score = detector._calculate_semantic_similarity(query, text)
            
            # Combine with emphasis on exact matches
            final_score = max(exact_word_score, semantic_score)
            
            return final_score
        else:
            # No exact matches, fall back to semantic similarity
            detector = SemanticDuplicateDetector()
            return detector._calculate_semantic_similarity(query, text)
    
    # Test cases
    test_cases = [
        ("Hopkins", "I graduated from Johns Hopkins in 1987"),
        ("Hopkins", "I have a PhD in Biochemistry and Biophysics from Johns Hopkins Medical School"),
        ("education", "I graduated from Johns Hopkins in 1987"),
        ("PhD", "I have a PhD in Biochemistry and Biophysics from Johns Hopkins Medical School"),
        ("random", "I graduated from Johns Hopkins in 1987"),
    ]
    
    print("🧪 TESTING IMPROVED SIMILARITY:")
    print()
    
    detector = SemanticDuplicateDetector()
    
    for query, memory in test_cases:
        original_score = detector._calculate_semantic_similarity(query, memory)
        improved_score = improved_similarity(query, memory)
        
        print(f"Query: '{query}' vs Memory: '{memory[:50]}...'")
        print(f"  Original score: {original_score:.4f}")
        print(f"  Improved score: {improved_score:.4f}")
        print(f"  Improvement: {'+' if improved_score > original_score else ''}{improved_score - original_score:.4f}")
        print()


if __name__ == "__main__":
    analyze_similarity_calculation()
    demonstrate_improved_similarity()
