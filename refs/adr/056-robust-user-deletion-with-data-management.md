# ADR-056: Robust User Deletion with Data Management

**Status**: Proposed

## Context

The previous user deletion functionality was minimal. It only removed the user from the registry, leaving their associated data directories orphaned on the disk. This process was unsafe, irreversible, and lacked transparency, posing a risk of accidental data retention and making system cleanup difficult.

## Decision

We have implemented a comprehensive and robust user deletion system that prioritizes safety, transparency, and administrative control. The new system introduces the following key features:

1.  **Comprehensive Data Cleanup**: The `UserManager.delete_user` method now recursively deletes the user's entire data directory (e.g., `data/agno/<user_id>`), ensuring that all associated files, memories, and knowledge bases are properly removed.

2.  **Safety Mechanisms**: To prevent accidental data loss, two critical safety features have been added:
    *   **Dry Run Mode**: A `dry_run=True` flag allows administrators to preview exactly which files and directories will be deleted and how much data will be removed, without making any actual changes.
    *   **Data Backup**: A `backup_data=True` flag automatically creates a timestamped archive of the user's entire data directory in the `./backups/users/` folder before deletion.

3.  **Detailed Feedback**: The deletion method now returns a detailed dictionary containing a full report of the operation, including actions performed, data deletion statistics (file counts, total size), backup path and size, and any warnings or errors encountered.

4.  **Intuitive Streamlit UI**: A new "Delete User" tab has been added to the Streamlit dashboard. This UI provides a safe and user-friendly interface for the new deletion capabilities, requiring explicit confirmation (typing the user's ID) to proceed with the final deletion.

## Consequences

### Positive

-   **Enhanced Safety**: The risk of accidental user data deletion is significantly minimized.
-   **Improved Data Governance**: Prevents orphaned files and ensures complete data removal when a user is deleted.
-   **Increased Transparency**: Administrators have full visibility into the deletion process through dry runs and detailed feedback.
-   **Better User Experience**: The Streamlit UI makes a potentially dangerous operation safe and easy to manage.

### Negative

-   The `delete_user` method signature in `UserManager` is now more complex, but this is a necessary trade-off for the significant gains in safety and functionality.
