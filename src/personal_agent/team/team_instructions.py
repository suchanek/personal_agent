"""
Instruction templates for specialized team agents.

Provides simple instruction templates at different sophistication levels
for specialized agents (Web, Finance, Calculator, Python, File, System, Medical, Writer, Image).

This module integrates team agents with the instruction level system without
code explosion - keeping existing detailed instructions while adding minimal
level support.
"""

from personal_agent.core.agent_instruction_manager import InstructionLevel

# Existing detailed instructions from reasoning_team.py
DEFAULT_CODE_INSTRUCTIONS = """\
Your mission is to provide comprehensive code support. Follow these steps to ensure the best possible response:

1. **Code Creation and Execution**
    - Create complete, working code examples that users can run.
    - When building agents you must remember to use agent.run() and NOT agent.print_response()
    - This way you can capture the agent response and return it to the user
    - Make sure to return the `response` variable that tells you the result
    - Use the `save_to_file_and_run` tool to save code to a file and run.
    - Remember to:
        * Build the complete agent implementation and test 
        * Include all necessary imports and setup
        * Add comprehensive comments explaining the implementation
        * Test a requested agent with example queries via with `response = agent.run()`
        * Test requested code by executing it.
        * Ensure all dependencies are listed
        * Include error handling and best practices
        * Add type hints and documentation"""

DEFAULT_FILE_INSTRUCTIONS = """\
Your mission is to provide comprehensive file system management and operations support. Follow these guidelines:

1. **File Operations Safety**
    - Always validate file paths before performing operations
    - Check if files exist before attempting to read them
    - Confirm overwrite operations when modifying existing files
    - Use relative paths when possible to maintain portability

2. **File Reading Operations**
    - When reading files, provide clear summaries of content structure
    - For large files, offer to read specific sections or provide previews
    - Identify file types and suggest appropriate handling methods

3. **File Writing and Creation**
    - Always confirm the target location before writing files
    - Create necessary directory structures when needed
    - Use appropriate file extensions based on content type
    - Provide clear success/failure feedback"""


class TeamAgentInstructions:
    """Instruction templates for team agents at different levels."""

    @staticmethod
    def get_web_agent_instructions(level: InstructionLevel) -> list:
        """Get web search agent instructions for given level.

        :param level: Instruction level
        :return: Instruction list for the agent
        """
        if level == InstructionLevel.MINIMAL:
            return [
                "Search the web for information based on the input. Always include sources"
            ]

        # All other levels use the same instructions (already well-tuned)
        return [
            "Search the web for information based on the input. Always include sources"
        ]

    @staticmethod
    def get_finance_agent_instructions(level: InstructionLevel) -> list:
        """Get finance agent instructions for given level.

        :param level: Instruction level
        :return: Instruction list for the agent
        """
        if level == InstructionLevel.MINIMAL:
            return ["Use tables to display data."]

        return ["Use tables to display data."]

    @staticmethod
    def get_system_agent_instructions(level: InstructionLevel) -> list:
        """Get system agent instructions for given level.

        :param level: Instruction level
        :return: Instruction list for the agent
        """
        if level == InstructionLevel.MINIMAL:
            return ["Execute system commands safely."]

        return [
            "You are a system agent that can execute shell commands safely.",
            "Provide clear output and error messages from command execution.",
        ]

    @staticmethod
    def get_medical_agent_instructions(level: InstructionLevel) -> list:
        """Get medical agent instructions for given level.

        :param level: Instruction level
        :return: Instruction list for the agent
        """
        if level == InstructionLevel.MINIMAL:
            return ["Search PubMed for medical information."]

        return [
            "You are a medical agent that can answer questions about medical topics.",
            "Search PubMed for medical information and write about it.",
            "Use tables to display data.",
        ]

    @staticmethod
    def get_writer_agent_instructions(level: InstructionLevel) -> list:
        """Get writer agent instructions for given level.

        :param level: Instruction level
        :return: Instruction list for the agent
        """
        if level == InstructionLevel.MINIMAL:
            return ["Create content in the requested format and style."]

        return [
            "You are a versatile writer who can create content on any topic.",
            "When given a topic, write engaging and informative content in the requested format and style.",
            "If you receive mathematical expressions or calculations from the calculator agent, convert them into clear written text.",
            "Ensure your writing is clear, accurate and tailored to the specific request.",
            "Maintain a natural, engaging tone while being factually precise.",
            "Write something that would be good enough to be published in a newspaper like the New York Times.",
        ]

    @staticmethod
    def get_image_agent_instructions(level: InstructionLevel) -> list:
        """Get image agent instructions for given level.

        :param level: Instruction level
        :return: Instruction list for the agent
        """
        if level == InstructionLevel.MINIMAL:
            return ["Create images using DALL-E based on text descriptions."]

        return [
            "You are an AI image creation specialist.",
            "Your **only** task is to call the `create_image` tool using the user's description.",
            "Your entire response **MUST** be only the direct, raw, unmodified output from the `create_image` tool.",
            "**CRITICAL:** Do NOT add any text, thoughts, comments, or any other formatting. Your response must be ONLY the tool's output.",
        ]

    @staticmethod
    def get_calculator_agent_instructions(
        level: InstructionLevel,
    ) -> list:  # noqa: ARG004
        """Get calculator agent instructions for given level.

        :param level: Instruction level
        :return: Instruction list for the agent
        """
        if level == InstructionLevel.MINIMAL:
            return ["Perform mathematical calculations."]

        # All other levels use consistent instructions
        return ["Perform accurate mathematical calculations and provide results in a clear format."]

    @staticmethod
    def get_python_agent_instructions(level: InstructionLevel) -> str:
        """Get Python agent instructions for given level.

        :param level: Instruction level
        :return: Instruction string for the agent
        """
        if level == InstructionLevel.MINIMAL:
            return "Create and execute Python code."

        # Use the detailed instructions for all other levels
        return DEFAULT_CODE_INSTRUCTIONS

    @staticmethod
    def get_file_agent_instructions(level: InstructionLevel) -> str:
        """Get file agent instructions for given level.

        :param level: Instruction level
        :return: Instruction string for the agent
        """
        if level == InstructionLevel.MINIMAL:
            return "Read and write files in the system safely."

        # Use the detailed instructions for all other levels
        return DEFAULT_FILE_INSTRUCTIONS

    @staticmethod
    def get_all_agent_types() -> list:
        """Get list of all specialized agent types.

        :return: List of agent type names
        """
        return [
            "web",
            "finance",
            "calculator",
            "python",
            "file",
            "system",
            "medical",
            "writer",
            "image",
            "memory",
        ]

    @staticmethod
    def get_instructions_for_agent(agent_type: str, level: InstructionLevel):
        """Get instructions for a specific agent type.

        :param agent_type: Type of agent (e.g., 'web', 'finance')
        :param level: Instruction level
        :return: Complete instruction string or list

        :raises ValueError: If agent_type is unknown
        """
        agent_type = agent_type.lower().strip()

        # Map agent types to instruction methods
        instruction_methods = {
            "web": TeamAgentInstructions.get_web_agent_instructions,
            "finance": TeamAgentInstructions.get_finance_agent_instructions,
            "calculator": TeamAgentInstructions.get_calculator_agent_instructions,
            "python": TeamAgentInstructions.get_python_agent_instructions,
            "file": TeamAgentInstructions.get_file_agent_instructions,
            "system": TeamAgentInstructions.get_system_agent_instructions,
            "medical": TeamAgentInstructions.get_medical_agent_instructions,
            "writer": TeamAgentInstructions.get_writer_agent_instructions,
            "image": TeamAgentInstructions.get_image_agent_instructions,
        }

        if agent_type in instruction_methods:
            return instruction_methods[agent_type](level)
        else:
            raise ValueError(f"Unknown agent type: {agent_type}")
