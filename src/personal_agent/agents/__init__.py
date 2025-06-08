"""
Personal AI Agent modules for the agno framework.

This package contains specialized AI agents for different domains including coding,
finance, multimodal content generation, and knowledge management. All agents are
built using the agno framework with SQLite storage and LanceDB vector databases.

The main Agent class provides the core functionality, while specialized agent
instances offer pre-configured tools and capabilities for specific use cases.

Classes:
    Agent: Main agent class from agent_example.py with comprehensive functionality

Agent Instances:
    coding_agent: Specialized agent for software development tasks
    finance_agent: Agent configured for financial data analysis
    youtube_agent: Agent for YouTube content operations
    web_agent: General web search and browsing agent
    audio_agent: Multimodal agent for audio generation
    image_agent: Multimodal agent for image generation
    gif_agent: Multimodal agent for GIF creation
    video_agent: Multimodal agent for video generation
    fal_agent: Agent using FAL.ai services
    ml_gif_agent: Machine learning-powered GIF agent
    ml_music_agent: Machine learning-powered music agent
    ml_video_agent: Machine learning-powered video agent
    agno_support: Support agent for agno framework assistance
    agno_support_voice: Voice-enabled support agent

Knowledge Base Agents:
    arxiv_kb_async: Asynchronous ArXiv knowledge base agent
    pdf_kb_async: Asynchronous PDF knowledge base agent
    pdf_url_kb_async: Asynchronous PDF URL knowledge base agent

File Management:
    file_agent: Agent for file system operations using MCP

GitHub Integration:
    Various GitHub agents for repository management and operations
"""

# Main Agent class
from .agent_example import Agent
from .agno_assist import agno_support, agno_support_voice

# Specialized agent instances
from .coding_agent import coding_agent
from .multimodal_agents import (
    audio_agent,
    fal_agent,
    gif_agent,
    image_agent,
    ml_gif_agent,
    ml_music_agent,
    ml_video_agent,
)
from .ollama_agents import finance_agent, web_agent, youtube_agent

# Knowledge base agents (async)
try:
    from .arxiv_kb_async import arxiv_kb_agent
except ImportError:
    arxiv_kb_agent = None

try:
    from .pdf_kb_async import pdf_kb_agent
except ImportError:
    pdf_kb_agent = None

try:
    from .pdf_url_kb_async import pdf_url_kb_agent
except ImportError:
    pdf_url_kb_agent = None

# File management agent
try:
    from .file_agent import file_agent
except ImportError:
    file_agent = None

# GitHub agents
try:
    from .github_agents import github_agent, github_clone_agent, github_search_agent
except ImportError:
    github_agent = None
    github_search_agent = None
    github_clone_agent = None

# Define what gets exported when using "from agents import *"
__all__ = [
    # Main Agent class
    "Agent",
    # Core agent instances
    "coding_agent",
    "finance_agent",
    "youtube_agent",
    "web_agent",
    # Multimodal agents
    "audio_agent",
    "image_agent",
    "gif_agent",
    "fal_agent",
    "ml_gif_agent",
    "ml_music_agent",
    "ml_video_agent",
    # Support agents
    "agno_support",
    "agno_support_voice",
    # Knowledge base agents (optional)
    "arxiv_kb_agent",
    "pdf_kb_agent",
    "pdf_url_kb_agent",
    # File and GitHub agents (optional)
    "file_agent",
    "github_agent",
    "github_search_agent",
    "github_clone_agent",
]

# Remove None values from __all__ for agents that failed to import
__all__ = [item for item in __all__ if globals().get(item) is not None]
