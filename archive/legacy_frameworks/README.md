# Legacy Framework Archive

This directory contains archived implementations of the Personal AI Agent using legacy frameworks that have been replaced by the current Agno-based system.

## Archive Date

June 5, 2025

## Current System

The active system now uses:

- **Framework**: Agno (replacing LangChain and smolagents)
- **Main Entry Point**: `src/personal_agent/agno_main.py`
- **Tools**: Static MCP tool implementations in `src/personal_agent/agno_static_tools.py`
- **Architecture**: Direct MCP client calls instead of dynamic tool creation

## Archived Components

### LangChain Framework (`langchain/`)

- `main.py` - Main entry point for LangChain ReAct agent
- `core/agent.py` - LangChain agent implementation with ReAct pattern
- `core/memory.py` - Weaviate vector store integration
- `web/interface.py` - Flask web interface for LangChain agent
- `utils/store_fact.py` - Fact storage utility with LangChain embeddings

### smolagents Framework (`smolagents/`)

- `smol_main.py` - Main entry point for smolagents system
- `core/smol_agent.py` - smolagents agent implementation  
- `tools/smol_tools.py` - Tool implementations for smolagents
- `web/smol_interface.py` - Flask web interface for smolagents
- `utils/smol_blog.py` - Blog generation utility

## Migration Notes

### Key Improvements in Agno System

1. **Static Tools**: Replaced dynamic tool creation with static tool implementations
2. **Performance**: Eliminated temporary agent creation overhead (120+ lines removed)
3. **Reliability**: Direct MCP client calls with proper error handling
4. **Architecture**: Cleaner separation of concerns with closure-based tool factory pattern

### GitHub Search Fix

The migration resolved a critical Pydantic validation error:

- **Before**: `repo: str = ""` (invalid default for required parameter)
- **After**: `repo: Optional[str] = None` (proper optional parameter handling)
- **Result**: GitHub search now executes in ~0.34s with proper results

### Compatibility

Legacy interfaces remain importable but raise `NotImplementedError` with guidance to use `agno_main.py`.

## File Structure

```
legacy_frameworks/
├── README.md (this file)
├── langchain/
│   ├── main.py
│   ├── core/
│   │   ├── agent.py
│   │   └── memory.py
│   ├── web/
│   │   └── interface.py
│   └── utils/
│       └── store_fact.py
└── smolagents/
    ├── smol_main.py
    ├── core/
    │   └── smol_agent.py
    ├── tools/
    │   └── smol_tools.py
    ├── web/
    │   └── smol_interface.py
    └── utils/
        └── smol_blog.py
```

## Restoration Notes

If needed, these files can be restored by:

1. Moving files back to their original locations
2. Reverting the import changes in `__init__.py` files
3. Installing framework dependencies (`langchain`, `smolagents`)

However, the current Agno system is recommended for all new development.
