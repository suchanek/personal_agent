feat(memory): Standardize memory clearing and add cheatsheet

This commit introduces a critical fix to the memory management system and improves project documentation.

Key changes:

- **Standardized Memory Clearing**: Implemented a standardized approach to memory clearing to resolve inconsistencies between different system components. This ensures that when memories are cleared, the change is reliably reflected across the entire application. This is documented in ADR-016.

- **Consistent Memory Formatting**: User memories are now consistently stored in the third-person to improve the quality of the knowledge graph.

- **Scripts Cheatsheet**: A new `SCRIPTS_CHEATSHEET.md` file has been added to provide a centralized, easy-to-use reference for project scripts.

- **Legacy Code Removal**: The redundant `clear_lightrag_data.py` script has been removed.
