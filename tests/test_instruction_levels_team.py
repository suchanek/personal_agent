"""
Integration tests for instruction levels across team agents.

Tests that:
1. Each instruction level is valid for all agents
2. Team agents apply instructions correctly
3. Overrides work as expected
4. Configuration is consistent
"""

import pytest

from personal_agent.core.agent_instruction_manager import InstructionLevel
from personal_agent.team.team_instruction_manager import TeamInstructionManager
from personal_agent.team.team_instructions import TeamAgentInstructions


class TestTeamInstructionTemplates:
    """Test instruction templates for team agents."""

    def test_web_agent_all_levels(self):
        """Test web agent has instructions for all levels."""
        for level in InstructionLevel:
            instructions = TeamAgentInstructions.get_web_agent_instructions(level)
            assert instructions is not None
            assert isinstance(instructions, (str, list))
            if isinstance(instructions, str):
                text = instructions.lower()
            else:
                text = " ".join(instructions).lower()
            assert "web" in text or "search" in text

    def test_finance_agent_all_levels(self):
        """Test finance agent has instructions for all levels."""
        for level in InstructionLevel:
            instructions = TeamAgentInstructions.get_finance_agent_instructions(level)
            assert instructions is not None
            assert isinstance(instructions, (str, list))
            if isinstance(instructions, str):
                assert len(instructions) > 0
            else:
                assert len(instructions) > 0

    def test_calculator_agent_all_levels(self):
        """Test calculator agent has instructions for all levels."""
        for level in InstructionLevel:
            instructions = TeamAgentInstructions.get_calculator_agent_instructions(
                level
            )
            assert instructions is not None
            assert isinstance(instructions, (str, list))
            if isinstance(instructions, str):
                assert len(instructions) > 0
            else:
                assert len(instructions) > 0

    def test_python_agent_all_levels(self):
        """Test Python agent has instructions for all levels."""
        for level in InstructionLevel:
            instructions = TeamAgentInstructions.get_python_agent_instructions(level)
            assert instructions is not None
            assert isinstance(instructions, str)
            assert len(instructions) > 0

    def test_instructions_grow_with_level(self):
        """Test that instructions generally get longer at higher levels."""
        levels = [
            InstructionLevel.MINIMAL,
            InstructionLevel.CONCISE,
            InstructionLevel.STANDARD,
            InstructionLevel.EXPLICIT,
        ]
        for agent_method in [
            TeamAgentInstructions.get_web_agent_instructions,
            TeamAgentInstructions.get_finance_agent_instructions,
            TeamAgentInstructions.get_calculator_agent_instructions,
            TeamAgentInstructions.get_python_agent_instructions,
        ]:
            lengths = [len(agent_method(level)) for level in levels]
            assert lengths == sorted(lengths)

    def test_get_all_agent_types(self):
        """Test that all agent types are listed."""
        agent_types = TeamAgentInstructions.get_all_agent_types()  # type: ignore
        assert isinstance(agent_types, list)
        assert "web" in agent_types
        assert "memory" in agent_types

    def test_get_instructions_for_agent(self):
        """Test generic instruction getter."""
        for level in InstructionLevel:
            instructions = TeamAgentInstructions.get_instructions_for_agent("web", level)  # type: ignore
            assert instructions is not None
            assert isinstance(instructions, (str, list))
            if isinstance(instructions, str):
                assert len(instructions) > 0
            else:
                assert len(instructions) > 0


class TestTeamInstructionManager:
    """Test team instruction manager."""

    def test_initialization_valid_level(self):
        """Test manager initializes with valid level."""
        manager = TeamInstructionManager(InstructionLevel.STANDARD)
        assert manager.team_level == InstructionLevel.STANDARD

    def test_initialization_invalid_level(self):
        """Test manager raises error with invalid level."""
        with pytest.raises(TypeError):
            TeamInstructionManager("CONCISE")  # type: ignore

    def test_get_agent_level_default(self):
        """Test getting agent level returns team default."""
        manager = TeamInstructionManager(InstructionLevel.CONCISE)
        assert manager.get_agent_level("web") == InstructionLevel.CONCISE

    def test_set_agent_override(self):
        """Test setting per-agent override."""
        manager = TeamInstructionManager(InstructionLevel.CONCISE)
        manager.set_agent_override("finance", InstructionLevel.EXPLICIT)
        assert manager.get_agent_level("finance") == InstructionLevel.EXPLICIT
        assert manager.get_agent_level("web") == InstructionLevel.CONCISE

    def test_clear_agent_override(self):
        """Test clearing per-agent override."""
        manager = TeamInstructionManager(InstructionLevel.CONCISE)
        manager.set_agent_override("finance", InstructionLevel.EXPLICIT)
        manager.clear_agent_override("finance")
        assert manager.get_agent_level("finance") == InstructionLevel.CONCISE

    def test_set_team_level(self):
        """Test changing team-wide level."""
        manager = TeamInstructionManager(InstructionLevel.CONCISE)
        manager.set_team_level(InstructionLevel.STANDARD)
        assert manager.get_agent_level("web") == InstructionLevel.STANDARD

    def test_get_config_summary(self):
        """Test getting configuration summary."""
        manager = TeamInstructionManager(InstructionLevel.CONCISE)
        manager.set_agent_override("finance", InstructionLevel.EXPLICIT)
        summary = manager.get_config_summary()
        overrides = summary["overrides"]  # type: ignore
        assert overrides["finance"] == "EXPLICIT"  # type: ignore

    def test_validate_configuration(self):
        """Test configuration validation."""
        manager = TeamInstructionManager(InstructionLevel.CONCISE)
        assert manager.validate_configuration() is True

    def test_case_insensitive_agent_names(self):
        """Test that agent names are case-insensitive."""
        manager = TeamInstructionManager(InstructionLevel.CONCISE)
        manager.set_agent_override("Finance", InstructionLevel.EXPLICIT)
        assert manager.get_agent_level("finance") == InstructionLevel.EXPLICIT
        assert manager.get_agent_level("Finance") == InstructionLevel.EXPLICIT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
