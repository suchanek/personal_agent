"""
Unit tests for AgentInstructionManager.

This module tests the instruction creation and management functionality
extracted from the AgnoPersonalAgent class.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

import pytest
from unittest.mock import Mock, patch
from personal_agent.core.agent_instruction_manager import AgentInstructionManager, InstructionLevel


class TestInstructionLevel:
    """Test cases for InstructionLevel enum."""
    
    def test_instruction_level_values(self):
        """Test that all instruction levels are defined."""
        assert InstructionLevel.MINIMAL
        assert InstructionLevel.CONCISE
        assert InstructionLevel.STANDARD
        assert InstructionLevel.EXPLICIT
    
    def test_instruction_level_ordering(self):
        """Test that instruction levels can be compared."""
        # Test that they are different values
        levels = [InstructionLevel.MINIMAL, InstructionLevel.CONCISE, 
                 InstructionLevel.STANDARD, InstructionLevel.EXPLICIT]
        
        # All levels should be unique
        assert len(set(levels)) == 4


class TestAgentInstructionManager:
    """Test cases for AgentInstructionManager."""
    
    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.user_id = "test_user"
        self.instruction_level = InstructionLevel.STANDARD
        self.enable_memory = True
        self.enable_mcp = True
        self.mcp_servers = {
            "github": {"description": "GitHub integration"},
            "filesystem": {"description": "File system operations"}
        }
        
        self.manager = AgentInstructionManager(
            instruction_level=self.instruction_level,
            user_id=self.user_id,
            enable_memory=self.enable_memory,
            enable_mcp=self.enable_mcp,
            mcp_servers=self.mcp_servers
        )
    
    def test_init(self):
        """Test AgentInstructionManager initialization."""
        assert self.manager.instruction_level == self.instruction_level
        assert self.manager.user_id == self.user_id
        assert self.manager.enable_memory == self.enable_memory
        assert self.manager.enable_mcp == self.enable_mcp
        assert self.manager.mcp_servers == self.mcp_servers
    
    def test_init_with_disabled_features(self):
        """Test initialization with disabled features."""
        manager = AgentInstructionManager(
            instruction_level=InstructionLevel.MINIMAL,
            user_id="test_user",
            enable_memory=False,
            enable_mcp=False,
            mcp_servers={}
        )
        
        assert manager.enable_memory is False
        assert manager.enable_mcp is False
        assert manager.mcp_servers == {}
    
    def test_get_header_instructions(self):
        """Test header instructions generation."""
        header = self.manager.get_header_instructions()

        assert "personal AI friend" in header
        assert "Memory & Knowledge System" in header
        assert self.user_id in header
        assert "unified MemoryAndKnowledgeTools" in header
        assert "enabled" in header  # MCP status
    
    def test_get_header_instructions_disabled_features(self):
        """Test header instructions with disabled features."""
        manager = AgentInstructionManager(
            instruction_level=InstructionLevel.STANDARD,
            user_id="test_user",
            enable_memory=False,
            enable_mcp=False,
            mcp_servers={}
        )
        
        header = manager.get_header_instructions()
        
        assert "disabled" in header  # Memory status
        assert "disabled" in header  # MCP status
    
    def test_get_identity_rules(self):
        """Test identity rules generation."""
        identity = self.manager.get_identity_rules()
        
        assert "MEMORY EXPERT" in identity
        assert self.user_id in identity
        assert "NEVER PRETEND TO BE THE USER" in identity
        assert "AI assistant" in identity
    
    def test_get_personality_and_tone(self):
        """Test personality and tone guidelines."""
        personality = self.manager.get_personality_and_tone()

        assert "PERSONALITY & TONE" in personality
        assert "Be Direct & Efficient" in personality
        assert "Be Helpful" in personality
        assert "Be Accurate" in personality
    
    def test_get_concise_memory_rules(self):
        """Test concise memory rules generation."""
        rules = self.manager.get_concise_memory_rules()

        assert "Knowledge Tools (for factual information)" in rules
        assert "query_knowledge_base" in rules
        assert "ingest_knowledge_text" in rules or "ingest_knowledge_file" in rules
        assert "Always check memory first" in rules
    
    def test_get_detailed_memory_rules(self):
        """Test detailed memory rules generation."""
        rules = self.manager.get_detailed_memory_rules()

        assert "## MEMORY SYSTEM" in rules
        assert "Store user facts in first person" in rules
        assert "Present memories in second person" in rules
        assert "store_user_memory" in rules
        assert "query_memory" in rules
        assert "## KNOWLEDGE SYSTEM" in rules
    
    def test_get_concise_tool_rules(self):
        """Test concise tool rules generation."""
        rules = self.manager.get_concise_tool_rules()

        assert "## TOOL USAGE" in rules
        assert "YFinanceTools" in rules
        assert "DuckDuckGoTools" in rules
        assert "PersonalAgentFilesystemTools" in rules
    
    def test_get_detailed_tool_rules(self):
        """Test detailed tool rules generation."""
        rules = self.manager.get_detailed_tool_rules()

        assert "## TOOL USAGE RULES" in rules
        assert "Always use tools for factual information - never guess" in rules
        assert "## TOOL SELECTION:" in rules
        assert "YFinanceTools" in rules
        assert "DuckDuckGoTools" in rules
        assert "Use tools immediately, no hesitation" in rules
    
    def test_get_anti_hesitation_rules(self):
        """Test anti-hesitation rules generation."""
        rules = self.manager.get_anti_hesitation_rules()
        
        assert "NO OVERTHINKING RULE" in rules
        assert "ELIMINATE HESITATION" in rules
        assert "BANNED BEHAVIORS" in rules
        assert "REQUIRED IMMEDIATE RESPONSES" in rules
    
    def test_get_tool_list_with_mcp(self):
        """Test tool list generation with MCP enabled."""
        tool_list = self.manager.get_tool_list()

        assert "## CURRENT AVAILABLE TOOLS" in tool_list
        assert "YFinanceTools" in tool_list
        assert "DuckDuckGoTools" in tool_list
        assert "KnowledgeTools" in tool_list
        assert "query_knowledge_base" in tool_list
        assert "KnowledgeIngestionTools" in tool_list
        assert "PersagMemoryTools" in tool_list
        assert "MCP Server Tools" in tool_list
        assert "use_github_server" in tool_list
        assert "use_filesystem_server" in tool_list
    
    def test_get_tool_list_without_mcp(self):
        """Test tool list generation with MCP disabled."""
        manager = AgentInstructionManager(
            instruction_level=InstructionLevel.STANDARD,
            user_id="test_user",
            enable_memory=True,
            enable_mcp=False,
            mcp_servers={}
        )

        tool_list = manager.get_tool_list()

        assert "## CURRENT AVAILABLE TOOLS" in tool_list
        assert "YFinanceTools" in tool_list
        assert "MCP Server Tools**: Disabled" in tool_list
        assert "use_github_server" not in tool_list
    
    def test_get_core_principles(self):
        """Test core principles generation."""
        principles = self.manager.get_core_principles()

        assert "## CORE PRINCIPLES" in principles
        assert "Use tools immediately for factual information" in principles
        assert "Be accurate and helpful" in principles
        assert "Remember user information and present it clearly" in principles
        assert "Act as a capable AI assistant, not the user" in principles
    
    def test_create_instructions_minimal(self):
        """Test instruction creation for MINIMAL level."""
        manager = AgentInstructionManager(
            instruction_level=InstructionLevel.MINIMAL,
            user_id="test_user",
            enable_memory=True,
            enable_mcp=True,
            mcp_servers=self.mcp_servers
        )
        
        instructions = manager.create_instructions()
        
        # Should contain basic elements
        assert "helpful AI assistant" in instructions
        assert "CURRENT AVAILABLE TOOLS" in instructions
        
        # Should NOT contain detailed rules
        assert "SEMANTIC MEMORY SYSTEM" not in instructions
        assert "NO OVERTHINKING RULE" not in instructions
    
    def test_create_instructions_concise(self):
        """Test instruction creation for CONCISE level."""
        manager = AgentInstructionManager(
            instruction_level=InstructionLevel.CONCISE,
            user_id="test_user",
            enable_memory=True,
            enable_mcp=True,
            mcp_servers=self.mcp_servers
        )

        instructions = manager.create_instructions()

        # Should contain concise elements
        assert "## TOOL USAGE" in instructions
        assert "## CORE PRINCIPLES" in instructions
        assert "Knowledge Tools (for factual information)" in instructions

        # Should NOT contain detailed or anti-hesitation rules
        assert "## MEMORY SYSTEM" not in instructions
        assert "NO OVERTHINKING RULE" not in instructions
    
    def test_create_instructions_standard(self):
        """Test instruction creation for STANDARD level."""
        instructions = self.manager.create_instructions()

        # Should contain detailed elements
        assert "## MEMORY SYSTEM" in instructions
        assert "## TOOL USAGE RULES" in instructions
        assert "## CORE PRINCIPLES" in instructions

        # Should NOT contain anti-hesitation rules
        assert "NO OVERTHINKING RULE" not in instructions
    
    def test_create_instructions_explicit(self):
        """Test instruction creation for EXPLICIT level."""
        manager = AgentInstructionManager(
            instruction_level=InstructionLevel.EXPLICIT,
            user_id="test_user",
            enable_memory=True,
            enable_mcp=True,
            mcp_servers=self.mcp_servers
        )

        instructions = manager.create_instructions()

        # Should contain all elements including anti-hesitation
        assert "## MEMORY SYSTEM" in instructions
        assert "## TOOL USAGE RULES" in instructions
        assert "NO OVERTHINKING RULE" in instructions
        assert "## CORE PRINCIPLES" in instructions
    
    def test_create_instructions_structure(self):
        """Test that instructions are properly structured."""
        instructions = self.manager.create_instructions()

        # Should be a string
        assert isinstance(instructions, str)

        # Should contain multiple sections separated by double newlines
        sections = instructions.split('\n\n')
        assert len(sections) > 5  # Should have multiple sections

        # Should start with header content (after dedent removes leading whitespace)
        assert "You are" in instructions and "AI friend" in instructions
    
    def test_user_id_integration(self):
        """Test that user_id is properly integrated throughout instructions."""
        instructions = self.manager.create_instructions()
        
        # User ID should appear in multiple places
        user_id_count = instructions.count(self.user_id)
        assert user_id_count >= 2  # Should appear in header and identity rules at minimum
    
    def test_mcp_server_name_formatting(self):
        """Test that MCP server names are properly formatted for tool names."""
        # Test with server names that need formatting
        mcp_servers = {
            "github-server": {"description": "GitHub integration"},
            "file_system": {"description": "File system operations"},
            "web-scraper": {"description": "Web scraping"}
        }
        
        manager = AgentInstructionManager(
            instruction_level=InstructionLevel.STANDARD,
            user_id="test_user",
            enable_memory=True,
            enable_mcp=True,
            mcp_servers=mcp_servers
        )
        
        tool_list = manager.get_tool_list()
        
        # Hyphens should be replaced with underscores in tool names
        assert "use_github_server_server" in tool_list
        assert "use_file_system_server" in tool_list
        assert "use_web_scraper_server" in tool_list
    
    def test_empty_mcp_servers(self):
        """Test behavior with empty MCP servers dict."""
        manager = AgentInstructionManager(
            instruction_level=InstructionLevel.STANDARD,
            user_id="test_user",
            enable_memory=True,
            enable_mcp=True,
            mcp_servers={}
        )
        
        tool_list = manager.get_tool_list()
        
        # Should still show MCP section but with no servers
        assert "MCP Server Tools" in tool_list
        # Should not contain any use_*_server tools
        assert "use_" not in tool_list or "server" not in tool_list.split("use_")[1] if "use_" in tool_list else True


class TestAgentInstructionManagerIntegration:
    """Integration tests for AgentInstructionManager."""
    
    def test_instruction_consistency_across_levels(self):
        """Test that instructions are consistent across different levels."""
        user_id = "integration_test_user"
        mcp_servers = {"test": {"description": "Test server"}}
        
        managers = {}
        instructions = {}
        
        # Create managers for all levels
        for level in [InstructionLevel.MINIMAL, InstructionLevel.CONCISE, 
                     InstructionLevel.STANDARD, InstructionLevel.EXPLICIT]:
            managers[level] = AgentInstructionManager(
                instruction_level=level,
                user_id=user_id,
                enable_memory=True,
                enable_mcp=True,
                mcp_servers=mcp_servers
            )
            instructions[level] = managers[level].create_instructions()
        
        # All should contain user_id
        for level, instruction in instructions.items():
            assert user_id in instruction, f"User ID missing in {level} instructions"
        
        # All should contain tool list
        for level, instruction in instructions.items():
            assert "## CURRENT AVAILABLE TOOLS" in instruction, f"Tool list missing in {level} instructions"
        
        # All levels should have substantial content
        for level in [InstructionLevel.MINIMAL, InstructionLevel.CONCISE,
                      InstructionLevel.STANDARD, InstructionLevel.EXPLICIT]:
            assert len(instructions[level]) > 1000, f"{level.name} instructions too short"

        # EXPLICIT should include anti-hesitation rules
        assert "NO OVERTHINKING RULE" in instructions[InstructionLevel.EXPLICIT]
        # But other levels should not
        assert "NO OVERTHINKING RULE" not in instructions[InstructionLevel.STANDARD]
    
    def test_memory_disabled_instructions(self):
        """Test instructions when memory is disabled."""
        manager = AgentInstructionManager(
            instruction_level=InstructionLevel.STANDARD,
            user_id="test_user",
            enable_memory=False,
            enable_mcp=True,
            mcp_servers={"test": {"description": "Test"}}
        )
        
        instructions = manager.create_instructions()
        header = manager.get_header_instructions()
        
        # Memory should be marked as disabled
        assert "disabled" in header

        # Should still contain other sections
        assert "## PERSONALITY & TONE" in instructions
        assert "## CURRENT AVAILABLE TOOLS" in instructions
    
    def test_realistic_configuration(self):
        """Test with a realistic configuration."""
        manager = AgentInstructionManager(
            instruction_level=InstructionLevel.STANDARD,
            user_id="john_doe",
            enable_memory=True,
            enable_mcp=True,
            mcp_servers={
                "github": {"description": "GitHub repository management"},
                "filesystem": {"description": "Local file system operations"},
                "web-search": {"description": "Web search capabilities"}
            }
        )
        
        instructions = manager.create_instructions()
        
        # Should be a substantial instruction set
        assert len(instructions) > 1000
        
        # Should contain all expected sections
        expected_sections = [
            "personal AI friend",
            "john_doe",
            "## MEMORY SYSTEM",
            "## CURRENT AVAILABLE TOOLS",
            "## CORE PRINCIPLES"
        ]

        for section in expected_sections:
            assert section in instructions, f"Missing section: {section}"


if __name__ == "__main__":
    pytest.main([__file__])
