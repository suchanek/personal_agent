# LightRAG Document Manager

## Overview

The LightRAG Document Manager provides a command-line interface for managing documents in LightRAG using the server API for stable and reliable operations.

## Usage

### Using the Wrapper Script (Recommended)

To avoid Click deprecation warnings, use the wrapper script:

```bash
./tools/docmgr_wrapper.sh [OPTIONS] [ACTIONS]
```

This wrapper script automatically uses the Python from your virtual environment and suppresses the Click deprecation warnings.

### Direct Usage

Alternatively, you can run the script directly:

```bash
python tools/docmgr.py [OPTIONS] [ACTIONS]
```

Note: This method may display Click deprecation warnings.

## Options

- `--server-url <URL>`: LightRAG server URL (default: from config)
- `--verify`: Verify deletion after completion by checking server
- `--no-confirm`: Skip confirmation prompts for deletion actions
- `--delete-source`: Delete the original source file from the inputs directory
- `--retry <ID1> [ID2...]`: Retry specific failed documents by their unique IDs
- `--retry-all`: Retry all documents currently in 'failed' status

## Actions

- `--status`: Show LightRAG server and document status
- `--list`: List all documents with detailed view (ID, file path, status, etc.)
- `--list-names`: List all document names (file paths only)
- `--delete-processing`: Delete all documents currently in 'processing' status
- `--delete-failed`: Delete all documents currently in 'failed' status
- `--delete-status <STATUS>`: Delete all documents with a specific custom status
- `--delete-ids <ID1> [ID2...]`: Delete specific documents by their unique IDs
- `--delete-name <PATTERN>`: Delete documents whose file paths match a glob-style pattern (e.g., '*.pdf', 'my_doc.txt')
- `--nuke`: Perform a comprehensive deletion. This implicitly sets: `--verify`, `--delete-source`, and `--no-confirm`. Must be used with a deletion action.

## Examples

```bash
# Check server status
./tools/docmgr_wrapper.sh --status

# List all documents
./tools/docmgr_wrapper.sh --list

# Delete all 'failed' documents and verify
./tools/docmgr_wrapper.sh --delete-failed --verify

# Delete a specific document by ID and also delete the source file
./tools/docmgr_wrapper.sh --delete-ids doc-12345 --delete-source

# Delete all '.md' files comprehensively
./tools/docmgr_wrapper.sh --nuke --delete-name '*.md'

# Retry a failed document
./tools/docmgr_wrapper.sh --retry doc-failed-123

# Retry all failed documents
./tools/docmgr_wrapper.sh --retry-all
```

## Technical Notes

The wrapper script (`docmgr_wrapper.sh`) uses Python's `-W` flag to suppress the Click deprecation warnings:

```bash
python -W ignore::DeprecationWarning:click.parser
```

This addresses the following warnings that would otherwise appear:

```
DeprecationWarning: Importing 'parser.split_arg_string' is deprecated, it will only be available in 'shell_completion' in Click 9.0.
```

These warnings come from the spacy and weasel packages that are dependencies of the project.