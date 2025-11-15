"""
Team Instruction Manager for coordinating instruction levels across team agents.

Provides a centralized control point for managing instruction sophistication
levels across all team members with support for per-agent overrides.
"""

import logging
from typing import Dict

from personal_agent.core.agent_instruction_manager import InstructionLevel

logger = logging.getLogger(__name__)


class TeamInstructionManager:
    """Manages consistent instruction levels across all team agents.

    Provides:
    - Team-wide default instruction level
    - Per-agent level overrides
    - Query methods for agent-specific levels
    - Configuration validation
    """

    def __init__(
        self, team_instruction_level: InstructionLevel = InstructionLevel.CONCISE
    ):
        """Initialize team instruction manager.

        :param team_instruction_level: Default level for all team agents
        :raises TypeError: If team_instruction_level is not InstructionLevel enum
        """
        if not isinstance(team_instruction_level, InstructionLevel):
            raise TypeError(
                f"team_instruction_level must be InstructionLevel enum, "
                f"got {type(team_instruction_level).__name__}"
            )

        self.team_level = team_instruction_level
        self._agent_overrides: Dict[str, InstructionLevel] = {}

        logger.info(
            "Initialized TeamInstructionManager with level=%s",
            team_instruction_level.name,
        )

    def get_agent_level(self, agent_type: str) -> InstructionLevel:
        """Get instruction level for specific agent.

        Returns per-agent override if set, otherwise returns team default.

        :param agent_type: Type of agent (e.g., 'web', 'finance', 'memory')
        :return: InstructionLevel for the agent
        """
        agent_type = agent_type.lower().strip()

        # Check for agent-specific override
        if agent_type in self._agent_overrides:
            level = self._agent_overrides[agent_type]
            logger.debug("Using override for %s: %s", agent_type, level.name)
            return level

        # Return team default
        logger.debug("Using team default for %s: %s", agent_type, self.team_level.name)
        return self.team_level

    def set_agent_override(self, agent_type: str, level: InstructionLevel) -> None:
        """Override instruction level for specific agent.

        :param agent_type: Type of agent to override
        :param level: New instruction level for this agent
        :raises TypeError: If level is not InstructionLevel enum
        """
        if not isinstance(level, InstructionLevel):
            raise TypeError(
                f"level must be InstructionLevel enum, " f"got {type(level).__name__}"
            )

        agent_type = agent_type.lower().strip()
        self._agent_overrides[agent_type] = level

        logger.info("Set instruction override for %s: %s", agent_type, level.name)

    def clear_agent_override(self, agent_type: str) -> bool:
        """Clear override for specific agent.

        :param agent_type: Type of agent to clear
        :return: True if override was cleared, False if not found
        """
        agent_type = agent_type.lower().strip()

        if agent_type in self._agent_overrides:
            del self._agent_overrides[agent_type]
            logger.info("Cleared instruction override for %s", agent_type)
            return True

        logger.warning("No override found for %s", agent_type)
        return False

    def clear_all_overrides(self) -> None:
        """Clear all per-agent overrides, use team default for all."""
        self._agent_overrides.clear()
        logger.info("Cleared all per-agent instruction overrides")

    def set_team_level(self, level: InstructionLevel) -> None:
        """Set team-wide instruction level.

        This becomes the new default for all agents (unless overridden).

        :param level: New instruction level for the team
        :raises TypeError: If level is not InstructionLevel enum
        """
        if not isinstance(level, InstructionLevel):
            raise TypeError(
                f"level must be InstructionLevel enum, " f"got {type(level).__name__}"
            )

        old_level = self.team_level
        self.team_level = level

        logger.info(
            "Changed team instruction level: %s → %s", old_level.name, level.name
        )

    def get_config_summary(self) -> Dict[str, object]:
        """Get summary of current instruction configuration.

        :return: Dictionary with team level and all overrides
        """
        summary = {
            "team_level": self.team_level.name,
            "overrides": {
                agent: level.name for agent, level in self._agent_overrides.items()
            },
        }
        return summary

    def print_config(self) -> None:
        """Print human-readable instruction configuration."""
        summary = self.get_config_summary()

        print("\n" + "=" * 60)
        print("TEAM INSTRUCTION CONFIGURATION")
        print("=" * 60)
        print(f"Team Default Level: {summary['team_level']}")

        if summary["overrides"]:
            print("\nPer-Agent Overrides:")
            for agent_type, level in summary["overrides"].items():
                print(f"  - {agent_type}: {level}")
        else:
            print("\nNo per-agent overrides configured.")

        print("=" * 60 + "\n")

    def validate_configuration(self) -> bool:
        """Validate that configuration is consistent.

        :return: True if valid, False if issues found
        """
        # All values should be InstructionLevel enums
        if not isinstance(self.team_level, InstructionLevel):
            logger.error("Invalid team_level: %s", type(self.team_level))
            return False

        for agent_type, level in self._agent_overrides.items():
            if not isinstance(level, InstructionLevel):
                logger.error("Invalid level for %s: %s", agent_type, type(level))
                return False

        return True

    def __repr__(self) -> str:
        """String representation of team instruction manager."""
        return (
            f"TeamInstructionManager("
            f"team_level={self.team_level.name}, "
            f"overrides={len(self._agent_overrides)})"
        )
