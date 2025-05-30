"""
Web interface package for the Personal AI Agent.

This package provides the Flask-based web interface.
"""

from .interface import create_app, register_routes

__all__ = ["create_app", "register_routes"]
