# 51. GitHub Issues for Task Management

- **Date**: 2025-08-06
- **Status**: Accepted

## Context

Project tasks and TODO items were previously being tracked in a `refs/TODO.md` file. While simple, this approach lacks the robust features needed for effective task management in a software project, such as assignment, labeling, discussion threads, and integration with commits and pull requests.

## Decision

We will use GitHub Issues as the primary system for tracking all project tasks, bugs, and enhancements. The `refs/TODO.md` file will be deprecated and removed.

All new tasks should be created as GitHub Issues. The `gh` command-line tool will be used for interacting with issues from the command line.

## Consequences

- **Improved Task Management**: We gain a more powerful and feature-rich system for managing project tasks.
- **Better Collaboration**: Issues provide a centralized place for discussion and collaboration on tasks.
- **Enhanced Visibility**: The project's backlog and work in progress are now clearly visible to all stakeholders.
- **Process Change**: All team members will need to adopt the new workflow of using GitHub Issues for task management.
