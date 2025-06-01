"""
Web interface package for the Personal AI Agent.

This package provides Flask-based web interfaces for both LangChain and smolagents.
"""

from .interface import create_app, register_routes
from .smol_interface import create_app as create_smol_app
from .smol_interface import register_routes as register_smol_routes

__all__ = ["create_app", "register_routes", "create_smol_app", "register_smol_routes"]
