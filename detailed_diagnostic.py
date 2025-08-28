i#!/usr/bin/env python3
"""
Detailed diagnostic to understand streaming response structure
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agno.agent import Agent, RunResponse
from agno.utils.common import dataclass_to_dict

from src.personal_agent.team.reasoning_team import create_image_agent


async def detailed_diagnostic():
