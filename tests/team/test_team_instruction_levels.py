"""
Test cases for TeamInstructionManager, team agent instruction templates, and team agent factories.

Validates:
- TeamInstructionManager initialization, team-level and per-agent overrides
- Instruction level propagation to all team agent factories
- Team agent instruction templates for all agent types and levels
- Enum-only enforcement (no string backdoors)
- Configuration summary and validation logic

Follows implementation guide as gold standard.
"""

import sys
from pathlib import Path

import pytest

from personal_agent.core.agent_instruction_manager import InstructionLevel
from personal_agent.team.reasoning_team import (
    create_agents,
    create_image_agent,
    create_writer_agent,
)
from personal_agent.team.team_instruction_manager import TeamInstructionManager
from personal_agent.team.team_instructions import TeamAgentInstructions

AGENT_TYPES = [
    "web",
    "finance",
    "system",
    "medical",
    "writer",
    "image",
    "calculator",
    "python",
    "file",
]
INSTRUCTION_LEVELS = [
    InstructionLevel.MINIMAL,
    InstructionLevel.CONCISE,
    InstructionLevel.STANDARD,
    InstructionLevel.EXPLICIT,
]


def test_team_agent_instruction_templates():
    """Test that all team agent instruction templates return valid output for all levels."""
    for agent in AGENT_TYPES:
        method = getattr(TeamAgentInstructions, f"get_{agent}_agent_instructions")
        for level in INSTRUCTION_LEVELS:
            result = method(level)
            assert result is not None
            assert isinstance(result, (str, list))


def test_team_instruction_manager_initialization():
    """Test TeamInstructionManager initialization and team-level config."""
    manager = TeamInstructionManager(InstructionLevel.CONCISE)
    assert manager.team_level == InstructionLevel.CONCISE
    summary = manager.get_config_summary()
    assert summary["team_level"] == "CONCISE"
    assert manager.validate_configuration()


def test_team_instruction_manager_overrides():
    """Test per-agent override logic in TeamInstructionManager."""
    manager = TeamInstructionManager(InstructionLevel.STANDARD)
    manager.set_agent_override("web", InstructionLevel.EXPLICIT)
    assert manager.get_agent_level("web") == InstructionLevel.EXPLICIT
    assert manager.get_agent_level("finance") == InstructionLevel.STANDARD
    summary = manager.get_config_summary()
    overrides = summary["overrides"]  # type: ignore
    assert "web" in overrides  # type: ignore
    assert overrides["web"] == "EXPLICIT"  # type: ignore


def test_team_instruction_manager_enum_enforcement():
    """Test that only InstructionLevel enum is accepted (no string backdoors)."""
    manager = TeamInstructionManager(InstructionLevel.MINIMAL)
    with pytest.raises(TypeError):
        manager.set_agent_override("writer", "STANDARD")  # type: ignore
    with pytest.raises(TypeError):
        TeamInstructionManager("CONCISE")  # type: ignore


def test_team_agent_factories_instruction_level():
    """Test that all team agent factories accept and propagate instruction_level."""
    writer = create_writer_agent(
        debug=False, instruction_level=InstructionLevel.MINIMAL
    )
    assert writer.name == "Writer Agent"
    # Validate instructions for writer agent
    expected_writer_instructions = TeamAgentInstructions.get_writer_agent_instructions(
        InstructionLevel.MINIMAL
    )
    assert writer.instructions == expected_writer_instructions

    image = create_image_agent(debug=False, instruction_level=InstructionLevel.EXPLICIT)
    assert image.name == "Image Agent"
    expected_image_instructions = TeamAgentInstructions.get_image_agent_instructions(
        InstructionLevel.EXPLICIT
    )
    assert image.instructions == expected_image_instructions

    agents = create_agents(debug=False, instruction_level=InstructionLevel.STANDARD)
    assert isinstance(agents, tuple)
    # Validate instructions for each agent
    agent_instruction_methods = [
        TeamAgentInstructions.get_web_agent_instructions,
        TeamAgentInstructions.get_system_agent_instructions,
        TeamAgentInstructions.get_finance_agent_instructions,
        TeamAgentInstructions.get_medical_agent_instructions,
        TeamAgentInstructions.get_image_agent_instructions,
        TeamAgentInstructions.get_python_agent_instructions,
        TeamAgentInstructions.get_file_agent_instructions,
    ]
    for agent, get_instructions in zip(agents, agent_instruction_methods):
        expected_instructions = get_instructions(InstructionLevel.STANDARD)
        assert agent.instructions == expected_instructions


def test_team_instruction_manager_validation():
    """Test configuration validation logic for TeamInstructionManager."""
    manager = TeamInstructionManager(InstructionLevel.CONCISE)
    manager.set_agent_override("image", InstructionLevel.MINIMAL)
    assert manager.validate_configuration()
