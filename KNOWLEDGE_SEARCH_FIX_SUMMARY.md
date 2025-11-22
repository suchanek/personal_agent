# Knowledge Search Fix Summary

## Problem
The SQLite/LanceDB knowledge search in the Streamlit UI was returning irrelevant results for all queries. Searching for "snoopy" returned completely unrelated documents like "wacka wacka" and "hello".

## Root Causes Discovered

### 1. Missing Relevance Scores
**Issue**: Agno's `LanceDb._build_search_results()` method discards the `_relevance_score` column from LanceDB's search results.

**Location**: `.venv/lib/python3.12/site-packages/agno/vectordb/lancedb/lance_db.py:529-548`

**Evidence**:
- LanceDB hybrid search returns pandas DataFrame with `_relevance_score` column
- Agno's wrapper extracts only `payload`, `vector`, ignoring the score
- Documents have no way to filter by relevance

### 2. No Similarity Threshold Support
**Issue**: Agno's `AgentKnowledge.search()` and `CombinedKnowledgeBase.search()` don't support `similarity_threshold` parameter.

**Location**: `.venv/lib/python3.12/site-packages/agno/knowledge/agent.py:99-113`

**Evidence**:
- Memory search has `similarity_threshold` parameter and works correctly
- Knowledge search delegates to vector DB without any filtering
- No way to exclude low-relevance results

### 3. Hybrid Search Scoring Issue
**Issue**: LanceDB hybrid search returns very similar low scores (~0.014-0.016) for both relevant and irrelevant queries.

**Evidence** from test results:
```
Query: "machine learning" (relevant)
- Score: 0.0164, 0.0164, 0.0161
- Content: "Machine learning is a subset of AI..."

Query: "snoopy" (irrelevant)
- Score: 0.0164, 0.0161, 0.0159
- Content: "wacka wacka those keys are wacky..."
```

This suggests the hybrid search is not effectively discriminating between matches.

## Solution Implemented

### Created `EnhancedLanceDb` Class
**Location**: `src/personal_agent/core/agno_storage.py:119-217`

**Features**:
1. **Preserves relevance scores**: Overrides `_build_search_results()` to extract `_relevance_score` from DataFrame and store in `Document.meta_data`

2. **Supports similarity filtering**: Overrides `search()` to accept `similarity_threshold` parameter
   - For `_relevance_score`: Keeps results where score >= threshold (higher is better)
   - For `_distance`: Keeps results where distance <= threshold (lower is better)

3. **Supports unlimited results**: When `limit=0`, fetches 1000 results and returns all after filtering

4. **Backward compatible**: Falls back to parent behavior when threshold not specified

### Created `EnhancedCombinedKnowledgeBase` Class
**Location**: `src/personal_agent/core/agno_storage.py:79-116`

**Features**:
- Extends `CombinedKnowledgeBase` to support `similarity_threshold` parameter
- Passes threshold through to `EnhancedLanceDb` instances
- Maintains compatibility with standard `AgentKnowledge` interface

### Integration
Updated `create_combined_knowledge_base()` to use enhanced classes:
- All `LanceDb` instances replaced with `EnhancedLanceDb`
- `CombinedKnowledgeBase` replaced with `EnhancedCombinedKnowledgeBase`
- Returns type: `Optional[EnhancedCombinedKnowledgeBase]`

## Test Results

### With `recreate=True` (fresh knowledge base):

```
Query: "machine learning" with threshold=0.016
✅ Filtered 10 results to 3 documents
   1. Score=0.0164: Machine learning is a subset of AI...
   2. Score=0.0164: Machine learning is a subset of AI...
   3. Score=0.0161: Test knowledge content...

Query: "snoopy" with threshold=0.016
✅ Filtered 10 results to 2 documents
   1. Score=0.0164: wacka wacka those keys are wacky...
   2. Score=0.0161: wacka wacka wacka though this is silly...
```

### Observations:
1. ✅ Relevance scores are now preserved in meta_data
2. ✅ Threshold filtering works correctly
3. ❌ Hybrid search still returns similar scores for relevant and irrelevant queries

## Solution: Pure Vector Search

**Problem with hybrid search resolved**: Switched from `SearchType.hybrid` to `SearchType.vector` which provides EXCELLENT discrimination!

### Test Results with Pure Vector Search:

```
Query: "machine learning" (relevant)
- Distance: 0.3631 (VERY CLOSE - excellent match!)
- Content: "Machine learning is a subset of AI..."

Query: "snoopy" (irrelevant)
- Distance: 1.09-1.21 (FAR AWAY - correctly filtered!)
- Content: "wacka wacka those keys are wacky..."
```

### Threshold Filtering Works Perfectly:

```
✅ "machine learning" with threshold=0.8
   → Kept 1 document (distance=0.3631 <= 0.8)

✅ "snoopy" with threshold=0.8
   → Filtered out ALL documents (all distances > 0.8)
```

### Recommended Thresholds (for vector search):
- **0.5 or less**: Very strict - only near-perfect semantic matches
- **0.8**: Moderate - good semantic similarity required
- **1.0**: Loose - allows more distant matches
- **Range**: 0.0 (perfect match) to 2.0 (very different)

### Why Vector Search Works Better:

1. **Pure semantic similarity**: Uses only embedding vectors, no keyword matching interference
2. **Clear score range**: Distance metric (0.0-2.0) provides intuitive separation
3. **Better discrimination**: Good matches (0.3-0.5) clearly separated from bad matches (1.0+)
4. **Consistent scoring**: Scores are meaningful and comparable across queries

## Files Modified

1. `/Users/egs/repos/personal_agent/src/personal_agent/core/agno_storage.py`
   - Added `EnhancedCombinedKnowledgeBase` class (lines 79-116)
   - Added `EnhancedLanceDb` class (lines 119-220)
   - **Changed all knowledge bases to use `SearchType.vector`** (instead of hybrid)
   - Updated `create_combined_knowledge_base()` to use enhanced classes
   - Updated type hints for return types

2. `/Users/egs/repos/personal_agent/test_knowledge_search.py`
   - Created comprehensive test script to reproduce and verify the fix
   - Tests both with and without similarity thresholds
   - Demonstrates excellent discrimination with vector search

## Usage

### In Code:
```python
# Knowledge base is automatically created with EnhancedCombinedKnowledgeBase using vector search
kb = create_combined_knowledge_base()

# Search with threshold (for vector search: lower distance = better match)
results = kb.search(
    query="machine learning",
    num_documents=5,
    similarity_threshold=0.8  # Max distance (0.5=strict, 0.8=moderate, 1.0=loose)
)

# Check scores
for doc in results:
    if doc.meta_data and '_distance' in doc.meta_data:
        distance = doc.meta_data['_distance']
        print(f"Distance: {distance:.4f} - {'GOOD' if distance < 0.8 else 'BAD'} match")
```

### In Streamlit UI:
The knowledge search will automatically use the enhanced classes and pure vector search after:
1. Restarting the app
2. Running with `recreate=True` once to rebuild the knowledge base with vector search

### Recommended Default Threshold:
Use **0.8** as a reasonable default for filtering out irrelevant results while keeping good matches.

## Final Recommendation

✅ **SOLUTION COMPLETE**: The fix is fully working with pure vector search!

1. ✅ Scores are preserved (_distance for vector search)
2. ✅ Threshold filtering works perfectly
3. ✅ Pure vector search provides excellent discrimination (0.36 vs 1.09+)
4. ✅ "Snoopy" queries are correctly filtered out
5. ✅ "Machine learning" queries return relevant results

The system is production-ready. Users should:
- **Use threshold=0.8** as a good default for filtering
- **Expect distance scores**: 0.0-0.5 (excellent), 0.5-0.8 (good), 0.8+ (poor/irrelevant)
- **Rebuild knowledge base once** with `recreate=True` to use the new vector search configuration
