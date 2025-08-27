# ADR-078: Rename memory_tools.py to weaviate_memory_tools.py for Clarity

## Status
Accepted

## Date
2025-08-26

## Context

The file `src/personal_agent/tools/memory_tools.py` contains legacy Weaviate-based memory management tools that are no longer actively used in the current system. The codebase has evolved to use the agno framework without Weaviate, making this file's purpose unclear from its generic name.

### Current State Analysis

- The file contains a comment stating it's "legacy code, since we use the agno framework without Weaviate now"
- No Python files directly import from `memory_tools.py`
- The file is not exported in the tools package `__init__.py`
- The system now uses other memory tools like `persag_memory_tools.py` and `agno_memory_tools.py`
- References to the file exist primarily in documentation and historical records

### Problem

The generic name `memory_tools.py` creates confusion because:
1. It doesn't clearly indicate it's Weaviate-specific
2. It might be mistaken for current memory functionality
3. The name doesn't reflect its legacy status
4. Other memory-related files have more descriptive names

## Decision

Rename `src/personal_agent/tools/memory_tools.py` to `src/personal_agent/tools/weaviate_memory_tools.py` to:

1. **Clarify Purpose**: The new name explicitly indicates this is Weaviate-specific functionality
2. **Indicate Legacy Status**: Makes it clear this is not the primary memory system
3. **Improve Maintainability**: Reduces confusion for developers working with the codebase
4. **Align with Naming Conventions**: Follows the pattern of other specific tool files

## Implementation

### Changes Made

1. **File Rename**: Moved `memory_tools.py` to `weaviate_memory_tools.py`
2. **Header Update**: Updated file docstring to reflect new name and clarify legacy status
3. **Documentation Updates**: Updated non-historical documentation references:
   - `refs/CODEGPT_REFACTOR_ANALYSIS.md`
   - `refs/REFACTORING_ANALYSIS.md` 
   - `refs/PROJECT_SUMMARY.md`
4. **Historical Preservation**: Left historical ADRs unchanged as requested

### Safety Analysis

This rename is safe because:
- No direct Python imports of the file exist
- The file is not exported in package `__init__.py`
- All references are in documentation, not active code
- The file is marked as legacy and not actively used

## Consequences

### Positive
- **Improved Clarity**: Developers can immediately understand this is Weaviate-specific legacy code
- **Reduced Confusion**: No longer mistaken for current memory functionality
- **Better Organization**: Aligns with the project's naming conventions
- **Maintainability**: Easier to understand the codebase structure

### Neutral
- **Documentation Updates**: Some non-historical documentation needed updates
- **No Functional Impact**: System functionality remains unchanged

### Risks Mitigated
- **Low Risk Operation**: Comprehensive analysis showed no active dependencies
- **Historical Preservation**: ADRs remain unchanged to maintain historical accuracy
- **Verification**: Final verification ensures no references were missed

## Notes

- This change is part of ongoing code clarity improvements
- The file remains available for reference but is clearly marked as legacy
- Future developers will immediately understand the file's purpose and status
- The rename aligns with the project's evolution away from Weaviate to the agno framework
