# Memory & User Management Dashboard

A comprehensive Streamlit dashboard for managing memories, users, and Docker services in the Personal Agent system.

## Features

- **System Status**: View system information, Docker container status, memory statistics, and user information
- **User Management**: Create new users, switch between users, and manage user settings
- **Memory Management**: View, search, and manage memories, with synchronization between SQLite and LightRAG graph systems
- **Docker Services**: Manage Docker containers, view logs, and configure Docker settings

## Installation

The dashboard is part of the Personal Agent system and requires the following dependencies:

```bash
pip install streamlit pandas docker psutil plotly
```

## Usage

To run the dashboard, execute the following command from the project root directory:

```bash
streamlit run src/personal_agent/streamlit/dashboard.py
```

Or use the provided script:

```bash
./scripts/run_dashboard.sh
```

## Components

The dashboard is organized into the following components:

- `dashboard.py`: Main entry point for the Streamlit application
- `components/`: UI components for each section of the dashboard
  - `system_status.py`: System status display
  - `user_management.py`: User management interface
  - `memory_management.py`: Memory management interface
  - `docker_services.py`: Docker service management interface
- `utils/`: Utility functions for the dashboard
  - `system_utils.py`: General system utilities
  - `docker_utils.py`: Docker-related utilities
  - `user_utils.py`: User management utilities
  - `memory_utils.py`: Memory management utilities

## Development

To extend the dashboard, you can add new components to the `components/` directory and update the main `dashboard.py` file to include them.

### Adding a New Component

1. Create a new file in the `components/` directory
2. Define a main function that renders the component
3. Import the component in `dashboard.py`
4. Add the component to the navigation

### Adding New Utilities

1. Create a new file in the `utils/` directory
2. Define utility functions
3. Import the utilities in the relevant components

## License

This dashboard is part of the Personal Agent system and is subject to the same license.