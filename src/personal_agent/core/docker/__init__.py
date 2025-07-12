"""
Docker integration package for the Personal AI Agent.

This package provides Docker container management and USER_ID synchronization
functionality for the personal agent system.
"""

from .user_sync import DockerUserSync

__all__ = ['DockerUserSync']
