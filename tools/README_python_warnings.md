# Suppressing Python Warnings

## Overview

This document explains how to suppress specific Python warnings, particularly the Click deprecation warnings that appear when running Python scripts in this project.

## Click Deprecation Warnings

When running Python scripts that import packages like spacy or weasel, you may see deprecation warnings like:

```
DeprecationWarning: Importing 'parser.split_arg_string' is deprecated, it will only be available in 'shell_completion' in Click 9.0.
```

These warnings come from the Click library used by these packages and don't affect functionality, but they can clutter the output.

## Solutions

### 1. Virtual Environment Integration (Recommended - Now Active)

The warning suppression has been integrated into the virtual environment's activation script. When you activate the virtual environment with:

```bash
source .venv/bin/activate
```

The `PYTHONWARNINGS` environment variable is automatically set to suppress the deprecation warnings. You can now run Python scripts directly without any warnings:

```bash
python tools/docmgr.py --list
# or
.venv/bin/python tools/docmgr.py --list
```

This solution is automatic and persistent for the duration of your virtual environment session.

### 2. Using the run_without_warnings.sh Script (Alternative)

If you need to run scripts outside the virtual environment or want an alternative approach, you can use the provided wrapper script:

```bash
./tools/run_without_warnings.sh <script.py> [args...]
```

For example:
```bash
./tools/run_without_warnings.sh tools/docmgr.py --list
```

### 3. Using Python's -W Flag Directly

You can also use Python's `-W` flag directly:

```bash
python -W ignore::DeprecationWarning:click.parser your_script.py
```

### 4. Manual PYTHONWARNINGS Environment Variable

For temporary use outside the virtual environment:

```bash
export PYTHONWARNINGS="ignore::DeprecationWarning:click,ignore::DeprecationWarning:spacy,ignore::DeprecationWarning:weasel,ignore::ResourceWarning,ignore::UserWarning:spacy"
python your_script.py
```

## Technical Details

The warnings are coming from the spacy and weasel packages, which import the Click library. The Click library is using a deprecated feature (`parser.split_arg_string`) that will be moved to `shell_completion` in Click 9.0.

We've also added warning filters to the package's initialization code in:
- `src/personal_agent/utils/pag_logging.py` (in the `setup_logging_filters()` function)
- `src/personal_agent/__init__.py` (at the top of the file)

However, these filters only take effect after the packages are imported, which is too late to suppress the warnings that occur during import. That's why using the `-W` flag or the PYTHONWARNINGS environment variable is the most effective solution.
