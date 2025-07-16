# User Switching Script for Personal Agent

## Overview

The `switch-user.py` script provides a comprehensive solution for switching between users in the Personal Agent system. It handles user creation, directory setup, configuration updates, and Docker service management.

## Features

- **User Creation**: Automatically creates new users if they don't exist
- **Directory Setup**: Creates all necessary user-specific directories
- **Configuration Management**: Updates USER_ID and refreshes all user-dependent settings
- **Docker Integration**: Restarts LightRAG services with the new user context
- **User Isolation**: Ensures complete separation between different users' data

## Usage

### Basic User Switching
```bash
python switch-user.py alice
```

### Create User Without Switching
```bash
python switch-user.py bob --create-only --user-name "Bob Johnson"
```

### Switch Without Restarting Services
```bash
python switch-user.py charlie --no-restart
```

### Check User Status
```bash
python switch-user.py --status alice
```

### Create Admin User
```bash
python switch-user.py admin --user-name "System Admin" --user-type Admin
```

## Command Line Options

- `user_id`: The user ID to switch to (required)
- `--user-name`: Display name for new users (defaults to formatted user_id)
- `--user-type`: User type for new users (Standard, Admin, Guest)
- `--no-restart`: Don't restart LightRAG services after switching
- `--status`: Display user status instead of switching
- `--create-only`: Only create the user, don't switch to them

## What the Script Does

### 1. User Validation
- Validates user ID format (alphanumeric, hyphens, underscores)
- Minimum 2 characters required

### 2. User Creation (if needed)
- Checks if user exists in the user registry
- Creates new user with specified name and type
- Registers user in the system

### 3. Directory Setup
- Creates user-specific storage directories:
  - Agno storage directory
  - Knowledge directory
  - LightRAG storage directory
  - LightRAG inputs directory
  - Memory storage directory
  - Memory inputs directory

### 4. User Context Switching
- Updates global USER_ID environment variable
- Refreshes all user-dependent configuration settings
- Updates user's last_seen timestamp

### 5. Docker Service Management
- Restarts LightRAG services with new user context
- Ensures proper user isolation in Docker containers
- Handles port conflicts and clean shutdowns

### 6. Status Display
- Shows comprehensive user information
- Displays current environment settings
- Shows LightRAG service status

## Directory Structure

After running the script, the following directory structure is created for each user:

```
/Users/Shared/personal_agent_data/agno/{user_id}/
├── knowledge/          # User's knowledge files
├── rag_storage/        # LightRAG storage
├── inputs/             # LightRAG input files
├── memory_rag_storage/ # Memory graph storage
└── memory_inputs/      # Memory input files
```

## Multi-User Benefits

### Complete User Isolation
- Each user has their own data directories
- Separate memory systems (SQLite + LightRAG)
- Independent Docker service contexts
- Isolated configuration settings

### Dynamic Configuration
- USER_ID changes are immediately reflected
- All user-dependent paths are recalculated
- No cached values interfere with switching

### Docker Integration
- Clean container restarts without port conflicts
- User-specific environment variables
- Proper service isolation

## Examples

### Switching Between Users
```bash
# Switch to Alice
python switch-user.py alice
# Output: Creates alice directories, switches context, restarts services

# Switch to Bob (create if needed)
python switch-user.py bob --user-name "Bob Smith"
# Output: Creates Bob user and directories, switches context

# Check current status
python switch-user.py --status alice
# Output: Shows Alice's user information and status
```

### Creating Users for Different Purposes
```bash
# Create a guest user
python switch-user.py guest --user-type Guest --create-only

# Create an admin user
python switch-user.py admin --user-type Admin --user-name "System Administrator"

# Create a project-specific user
python switch-user.py project_x --user-name "Project X User"
```

## Integration with Personal Agent

The script integrates seamlessly with the Personal Agent's multi-user infrastructure:

- **UserManager**: Handles user registry operations
- **AgnoPersonalAgent**: Manages user-specific agent instances
- **SemanticMemoryManager**: Provides user-isolated memory
- **Docker Integration**: Ensures container consistency
- **Configuration System**: Dynamic USER_ID propagation

## Error Handling

The script includes comprehensive error handling:

- User validation errors
- Directory creation failures
- Docker service restart issues
- Configuration update problems
- Network connectivity issues

## Security Considerations

- User IDs are validated for safety
- Directory permissions are properly set
- Environment variables are securely managed
- Docker containers run with appropriate user context

## Troubleshooting

### Common Issues

1. **Port Already Allocated**: The script handles Docker port conflicts automatically
2. **Permission Denied**: Ensure proper permissions on data directories
3. **User Already Exists**: Script will use existing user and update settings
4. **Docker Not Running**: Services restart will be skipped with warning

### Debug Mode

For troubleshooting, you can examine the detailed output and logs:
- User creation logs
- Directory creation details
- Configuration refresh information
- Docker service status
- Error messages with stack traces

## Related Documentation

- [Multi-User Dynamic USER_ID Implementation](MULTI_USER_DYNAMIC_USERID_IMPLEMENTATION_SUMMARY.md)
- [Docker Smart Restart Implementation](DOCKER_SMART_RESTART_IMPLEMENTATION_SUMMARY.md)
- [Personal Agent Configuration Guide](src/personal_agent/config/README.md)
