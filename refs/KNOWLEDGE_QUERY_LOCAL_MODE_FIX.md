# Knowledge Query Local Mode Fix

## Issue Summary

The `query_knowledge_base` function was not properly handling `mode="local"` parameter, causing queries like "who is Schroeder" to return no results when they should have searched the local semantic knowledge base.

## Root Cause Analysis

The [`query_knowledge_base`](src/personal_agent/tools/knowledge_tools.py:489) function in `knowledge_tools.py` was **only querying the LightRAG server regardless of the mode parameter**. The function had logic to route queries based on mode but was missing the actual implementation to query the local semantic knowledge base when `mode="local"` was specified.

### Original Problem
```python
# The function only had this path - always querying LightRAG
url = f"{settings.LIGHTRAG_URL}/query"
params = {
    "query": query.strip(),
    "mode": mode,  # ← Mode was passed to LightRAG but no local handling
    "top_k": limit,
    "response_type": "Multiple Paragraphs",
}
response = requests.post(url, json=params, timeout=60)
```

### Why "who is Schroeder" Failed
1. Query "who is Schroeder" contains "who" → auto-routed to `mode="local"`
2. Function passed `mode="local"` to LightRAG server
3. LightRAG server doesn't understand `mode="local"` (it expects "global", "hybrid", etc.)
4. Query returned no results

## The Fix

### Changes Made

#### 1. Added Knowledge Coordinator Import
```python
from ..core.knowledge_coordinator import create_knowledge_coordinator
```

#### 2. Added Knowledge Coordinator Initialization
```python
def __init__(self, knowledge_manager: KnowledgeManager):
    self.knowledge_manager = knowledge_manager
    
    # Initialize knowledge coordinator for unified querying
    self.knowledge_coordinator = None
```

#### 3. Replaced Query Logic
```python
def query_knowledge_base(self, query: str, mode: str = "auto", limit: Optional[int] = 5) -> str:
    # ... validation logic remains the same ...
    
    # Initialize knowledge coordinator if not already done
    if self.knowledge_coordinator is None:
        # Try to get agno_knowledge from the knowledge manager if available
        agno_knowledge = getattr(self.knowledge_manager, 'agno_knowledge', None)
        self.knowledge_coordinator = create_knowledge_coordinator(
            agno_knowledge=agno_knowledge,
            lightrag_url=settings.LIGHTRAG_URL,
            debug=False
        )

    # Use the knowledge coordinator for unified querying
    import asyncio
    
    # Run the async query in a sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    result = loop.run_until_complete(
        self.knowledge_coordinator.query_knowledge_base(
            query=query.strip(),
            mode=mode,
            limit=limit,
            response_type="Multiple Paragraphs"
        )
    )
    
    return result
```

## How the Fix Works

### Before the Fix
```
User Query: "who is Schroeder" with mode="local"
    ↓
query_knowledge_base() function
    ↓
Always sends to LightRAG server with mode="local"
    ↓
LightRAG doesn't understand mode="local"
    ↓
Returns no results
```

### After the Fix
```
User Query: "who is Schroeder" with mode="local"
    ↓
query_knowledge_base() function
    ↓
Uses KnowledgeCoordinator.query_knowledge_base()
    ↓
KnowledgeCoordinator routes based on mode:
    - mode="local" → agno_knowledge.search() (local semantic)
    - mode="global"/"hybrid" → LightRAG server
    - mode="auto" → intelligent routing
    ↓
Returns appropriate results
```

## Benefits of This Fix

1. **Proper Mode Handling**: `mode="local"` now correctly queries the local semantic knowledge base
2. **Unified Interface**: All knowledge queries go through the same intelligent routing system
3. **Fallback Support**: If local search fails, it can fall back to LightRAG, and vice versa
4. **No Deprecated Dependencies**: Uses modern Agno-based semantic search, not deprecated Weaviate tools
5. **Consistent Behavior**: Leverages existing, well-tested `KnowledgeCoordinator` infrastructure

## Files Modified

- `src/personal_agent/tools/knowledge_tools.py`
  - Added import for `create_knowledge_coordinator`
  - Added `knowledge_coordinator` initialization in `__init__`
  - Replaced entire `query_knowledge_base` method to use `KnowledgeCoordinator`

## Testing

To verify the fix works:

1. Query with `mode="local"`: Should search local semantic knowledge base
2. Query with `mode="global"`: Should search LightRAG knowledge graph
3. Query with `mode="auto"`: Should intelligently route based on query characteristics
4. Query "who is Schroeder" should now work properly if Schroeder information exists in the knowledge base

## Technical Notes

- The fix uses `asyncio.run_until_complete()` to handle the async `KnowledgeCoordinator.query_knowledge_base()` method in the sync `query_knowledge_base()` function
- The knowledge coordinator is lazily initialized to avoid circular imports and performance issues
- The fix maintains backward compatibility with all existing mode parameters

## Additional Issues Discovered

After implementing the fix, testing revealed additional problems:

### Issue 1: Knowledge Base May Be Empty
- Both local semantic search and LightRAG are returning no results for "Schroeder"
- This suggests the knowledge base systems may be empty or not properly initialized
- The `agno_knowledge` parameter in `KnowledgeCoordinator` may be `None`

### Issue 2: Agent Hallucination Problem
- Despite clear instructions to use `GoogleSearchTools` as fallback when knowledge base returns no results
- The agent is fabricating fake results instead of following the proper fallback flow
- Agent instructions state: "If no results, THEN use GoogleSearchTools" but this isn't being followed

### Issue 3: Slow Response Times
- Query taking 39.3 seconds suggests timeout issues
- Both local semantic search and LightRAG may be timing out before returning proper "no results" responses

### Recommended Next Steps

1. **Verify Knowledge Base Content**: Check if the knowledge base systems have any content at all
2. **Test Knowledge Base Connectivity**: Ensure both local semantic search and LightRAG servers are accessible
3. **Fix Agent Instruction Following**: Investigate why the agent is hallucinating instead of using fallback tools
4. **Add Better Error Handling**: Improve timeout and error handling in the `KnowledgeCoordinator`

### Testing Commands

To verify the fix works properly:
```bash
# Test if LightRAG server is running
curl -X GET http://localhost:9621/health

# Test if knowledge base has any documents
curl -X GET http://localhost:9621/documents

# Test direct query to LightRAG
curl -X POST http://localhost:9621/query \
  -H "Content-Type: application/json" \
  -d '{"query": "who is Schroeder", "mode": "global", "top_k": 5}'
```