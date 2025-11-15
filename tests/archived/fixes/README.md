# Archived Fix Tests

This directory contains 28 temporary test files that were created during development to verify specific bug fixes. These tests are preserved for historical reference and can be safely archived or deleted once their related issues are confirmed as resolved.

## Purpose

These tests were created in development iterations to:
- Validate specific bug fixes
- Test edge cases that broke the system
- Verify multi-iteration fixes
- Document problem scenarios

They are not part of the regular test suite and are not run in CI/CD pipelines.

## Archived Tests

### Memory System Fixes (8 files)
Tests created to verify various memory management bug fixes:

- `test_memory_agent_complete_fix.py` - Complete memory agent fix verification
- `test_memory_agent_fix.py` - Initial memory agent fix
- `test_memory_clearing_fix.py` - Memory clearing operation fix
- `test_memory_deletion_fix.py` - Memory deletion logic fix
- `test_memory_stats_fix.py` - Memory statistics calculation fix
- `test_memory_sync_fix.py` - Dual-storage memory synchronization fix
- `test_streamlit_memory_fix.py` - Streamlit memory interface fix
- `test_team_memory_stats_fix.py` - Team memory statistics fix

**Status**: These can be deleted once memory system is verified stable

### Team & UI Fixes (3 files)
Tests for multi-agent team and UI component fixes:

- `test_fixed_streamlit_team.py` - Streamlit team interface fix
- `test_fixed_teamwrapper.py` - Team wrapper class fix
- `test_team_image_fix.py` - Team image handling fix

**Status**: Delete after UI stability verified

### Data & Configuration Fixes (11 files)
Tests for data handling, configuration, and format issues:

- `test_data_dir_fixes.py` - Data directory path handling
- `test_multiuser_fix.py` - Multi-user context switching fix
- `test_knowledge_query_fix.py` - Knowledge query routing fix
- `test_json_format_fix.py` - JSON serialization format fix
- `test_semantic_similarity_fix.py` - Semantic similarity calculation fix
- `test_pydantic_validation_fix.py` - Pydantic model validation fix
- `test_final_image_fix.py` - Final image handling iteration
- `test_fixed_image_agent.py` - Image agent capability fix
- `test_fixed_sync_async_pattern.py` - Async/sync pattern fix
- `test_topic_consistency_fix.py` - Topic consistency fix
- `test_final_streaming_fix.py` - Streaming response fix

**Status**: Verify data handling is stable before deletion

### Integration & Diagnostic Fixes (6 files)
High-level integration and debugging tests:

- `test_final_github_use_case.py` - GitHub integration use case fix
- `test_final_integration.py` - Final integration verification
- `test_lightrag_debug.py` - LightRAG debugging
- `test_response_attributes_debug.py` - Response attribute debug
- `test_agno_agent_diagnosis.py` - Agent diagnosis (duplicate kept for reference)
- `test_streamlit_helpers_fix.py` - Streamlit helper functions fix

**Status**: Archive once system integration is proven stable

## How to Use These Tests

### Run a specific archived test for verification:
```bash
pytest tests/archived/fixes/test_memory_sync_fix.py -v
```

### Run all archived tests to verify fixes:
```bash
pytest tests/archived/fixes/ -v
```

### Before Deleting

1. **Verify the original issue is resolved**:
   - Check the related GitHub issue or PR
   - Confirm the bug no longer occurs
   - Review the equivalent test in the main test suite

2. **Run the equivalent main test**:
   - Run the corresponding test in `tests/memory/`, `tests/team/`, etc.
   - Ensure it passes consistently

3. **Document the deletion**:
   - Note which issue was fixed
   - Reference the main test that replaces it
   - Update this README

## Cleanup Strategy

### Phase 1: Verification (Immediate)
- Run each archived test to confirm it passes
- Identify which main test replaces each archived test
- Document the mapping

### Phase 2: Consolidation (After 2-4 weeks stable)
- Delete archived tests that have been verified multiple times
- Keep any that revealed edge cases not covered by main tests
- Archive the deletion decision in commit history

### Phase 3: Archive (After 1-2 months stable)
- Move remaining tests to a `history/` directory
- Create an index of what each tested and when it was archived
- Link from main README for historical reference

## Test Coverage

These archived tests currently cover:
- 28 separate bug scenarios
- Multiple iterations of the same issues
- Edge cases and race conditions
- Integration between major components

Once the main test suite is enhanced with similar coverage, these can be safely removed.

## Future Recommendations

1. **Consolidate duplicate fixes**: Several bugs were fixed multiple times (memory_agent_fix → memory_agent_complete_fix). The main suite should have a single comprehensive test for each feature.

2. **Add regression markers**: Mark tests with `@pytest.mark.regression` to identify which bugs they target.

3. **Automate cleanup**: Create a script that checks if archived tests pass, and report which can be safely deleted.

4. **Link to issues**: Add comments in archived tests referencing the GitHub issue they address for traceability.

## Questions?

If unsure whether to delete an archived test:
1. Run it - if it passes, the fix is working
2. Find the equivalent main test - if it covers the same case, delete the archived version
3. If no equivalent exists, consider moving that test to the main suite

---

**Last Updated**: 2025-11-15
**Total Archived Tests**: 28
**Recommended Action**: Safe to delete once each fix is verified in main test suite
