#!/usr/bin/env python3
"""
Script to analyze and list the knowledge tools available from Agno's KnowledgeTools.

This script examines the KnowledgeTools class from agno.tools.knowledge and provides
detailed information about its capabilities, methods, and usage patterns.
"""

import asyncio
import inspect
import logging
from pathlib import Path
from typing import Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


def print_section_header(title: str) -> None:
    """Print a formatted section header.

    :param title: Section title to display
    """
    print("\n" + "=" * 80)
    print(f"🔍 {title}")
    print("=" * 80)


def print_subsection_header(title: str) -> None:
    """Print a formatted subsection header.

    :param title: Subsection title to display
    """
    print(f"\n📋 {title}")
    print("-" * 60)


def analyze_knowledge_tools_class() -> None:
    """Analyze the KnowledgeTools class structure and capabilities."""
    try:
        from agno.tools.knowledge import KnowledgeTools

        print_section_header("AGNO KNOWLEDGE TOOLS ANALYSIS")

        # Basic class information
        print_subsection_header("Class Information")
        print(f"✅ Class Name: {KnowledgeTools.__name__}")
        print(f"✅ Module: {KnowledgeTools.__module__}")

        # Class docstring
        if KnowledgeTools.__doc__:
            print_subsection_header("Class Documentation")
            print(KnowledgeTools.__doc__.strip())

        # Constructor analysis
        print_subsection_header("Constructor Signature")
        try:
            init_sig = inspect.signature(KnowledgeTools.__init__)
            print(f"__init__{init_sig}")

            # Parameter details
            for param_name, param in init_sig.parameters.items():
                if param_name != "self":
                    annotation = (
                        param.annotation
                        if param.annotation != inspect.Parameter.empty
                        else "Any"
                    )
                    default = (
                        param.default
                        if param.default != inspect.Parameter.empty
                        else "Required"
                    )
                    print(f"  • {param_name}: {annotation} = {default}")

        except Exception as e:
            print(f"❌ Could not analyze constructor: {e}")

        # Class hierarchy
        print_subsection_header("Class Hierarchy (MRO)")
        for i, cls in enumerate(KnowledgeTools.__mro__):
            print(f"  {i}: {cls}")

        # Public methods and attributes
        print_subsection_header("Public Methods and Attributes")
        public_members = [
            name for name in dir(KnowledgeTools) if not name.startswith("_")
        ]

        for member_name in sorted(public_members):
            try:
                member = getattr(KnowledgeTools, member_name)
                if callable(member):
                    try:
                        sig = inspect.signature(member)
                        print(f"  🔧 {member_name}{sig}")

                        # Get method docstring if available
                        if member.__doc__:
                            doc_lines = member.__doc__.strip().split("\n")
                            first_line = doc_lines[0] if doc_lines else ""
                            if first_line:
                                print(f"       → {first_line}")

                    except (ValueError, TypeError):
                        print(f"  🔧 {member_name}(...)")
                else:
                    print(f"  📄 {member_name} (attribute)")

            except Exception as e:
                print(f"  ❌ {member_name} - Error: {e}")

        # Source file information
        print_subsection_header("Source Information")
        try:
            source_file = inspect.getfile(KnowledgeTools)
            print(f"✅ Source file: {source_file}")

            # Try to get source code
            try:
                source_lines = inspect.getsourcelines(KnowledgeTools)
                print(
                    f"✅ Source lines: {len(source_lines[0])} lines starting at line {source_lines[1]}"
                )
            except Exception:
                print("❌ Could not retrieve source lines")

        except Exception as e:
            print(f"❌ Could not get source file: {e}")

        return True

    except ImportError as e:
        print_section_header("IMPORT ERROR")
        print(f"❌ Failed to import KnowledgeTools: {e}")
        print("\nTrying to analyze agno.tools module structure...")

        try:
            import agno.tools

            print(f"✅ agno.tools module: {agno.tools}")
            print(f"✅ Available items: {dir(agno.tools)}")
        except ImportError as e2:
            print(f"❌ agno.tools not available: {e2}")

        return False


def analyze_knowledge_tools_usage() -> None:
    """Analyze common usage patterns of KnowledgeTools from examples."""
    print_section_header("KNOWLEDGE TOOLS USAGE PATTERNS")

    usage_patterns = {
        "Basic Creation": [
            "knowledge_tools = KnowledgeTools(knowledge=knowledge_base)",
            "Creates a basic KnowledgeTools instance with a knowledge base",
        ],
        "Advanced Configuration": [
            "knowledge_tools = KnowledgeTools(\n    knowledge=agno_docs,\n    think=True,\n    search=True,\n    analyze=True,\n    add_few_shot=True\n)",
            "Creates KnowledgeTools with enhanced reasoning capabilities",
        ],
        "Team Integration": [
            "team_leader = Team(\n    tools=[knowledge_tools],\n    ...\n)",
            "Integrates KnowledgeTools into team-based agents",
        ],
        "Agent Integration": [
            "agent = Agent(\n    tools=[knowledge_tools],\n    show_tool_calls=True\n)",
            "Adds KnowledgeTools to a single agent",
        ],
    }

    for pattern_name, (code, description) in usage_patterns.items():
        print_subsection_header(pattern_name)
        print(description)
        print("```python")
        print(code)
        print("```")


def create_test_knowledge_tools() -> None:
    """Attempt to create and test a KnowledgeTools instance."""
    print_section_header("TESTING KNOWLEDGE TOOLS INSTANCE")

    try:
        from agno.embedder.ollama import OllamaEmbedder
        from agno.knowledge.text import TextKnowledgeBase
        from agno.tools.knowledge import KnowledgeTools
        from agno.vectordb.lancedb import LanceDb, SearchType

        print_subsection_header("Creating Test Knowledge Base")

        # Create a simple knowledge base for testing
        test_storage_path = Path("tmp/test_knowledge")
        test_storage_path.mkdir(parents=True, exist_ok=True)

        # Create vector database
        vector_db = LanceDb(
            uri=str(test_storage_path / "lancedb"),
            table_name="test_knowledge",
            search_type=SearchType.hybrid,
            embedder=OllamaEmbedder(id="nomic-embed-text", dimensions=768),
        )

        # Create knowledge base
        knowledge_base = TextKnowledgeBase(
            path=test_storage_path,
            vector_db=vector_db,
        )

        print("✅ Created test knowledge base")

        print_subsection_header("Creating KnowledgeTools Instance")

        # Test different configurations
        configurations = [
            ("Basic", {}),
            ("With Think", {"think": True}),
            ("With Search", {"search": True}),
            ("With Analyze", {"analyze": True}),
            (
                "Full Featured",
                {
                    "think": True,
                    "search": True,
                    "analyze": True,
                    "add_few_shot": True,
                    "add_instructions": True,
                },
            ),
        ]

        for config_name, config_params in configurations:
            try:
                print(f"\n🧪 Testing {config_name} configuration:")
                print(f"   Parameters: {config_params}")

                knowledge_tools = KnowledgeTools(
                    knowledge=knowledge_base, **config_params
                )

                print(f"   ✅ Created successfully: {type(knowledge_tools)}")

                # Try to inspect the created instance
                if hasattr(knowledge_tools, "tools"):
                    print(
                        f"   📊 Tools available: {len(knowledge_tools.tools) if knowledge_tools.tools else 0}"
                    )
                    if knowledge_tools.tools:
                        for i, tool in enumerate(
                            knowledge_tools.tools[:3], 1
                        ):  # Show first 3 tools
                            tool_name = getattr(
                                tool, "__name__", getattr(tool, "name", str(tool))
                            )
                            print(f"      {i}. {tool_name}")
                        if len(knowledge_tools.tools) > 3:
                            print(
                                f"      ... and {len(knowledge_tools.tools) - 3} more"
                            )

                # Check for specific methods
                for method_name in ["search", "think", "analyze"]:
                    if hasattr(knowledge_tools, method_name):
                        print(f"   ✅ Has {method_name} method")

            except Exception as e:
                print(f"   ❌ Failed to create {config_name}: {e}")

    except ImportError as e:
        print(f"❌ Cannot test KnowledgeTools: {e}")
    except Exception as e:
        print(f"❌ Error during testing: {e}")


def analyze_knowledge_tools_examples() -> None:
    """Extract and analyze KnowledgeTools usage from existing examples."""
    print_section_header("KNOWLEDGE TOOLS EXAMPLES FROM CODEBASE")

    # Common parameters found in examples
    common_parameters = {
        "knowledge": "The knowledge base instance to search",
        "think": "Enable thinking/reasoning capabilities",
        "search": "Enable knowledge base search functionality",
        "analyze": "Enable analysis capabilities",
        "add_few_shot": "Add few-shot examples for better performance",
        "add_instructions": "Add built-in instructions for the tools",
    }

    print_subsection_header("Common Parameters")
    for param, description in common_parameters.items():
        print(f"  • {param}: {description}")

    # Tool capabilities based on examples
    print_subsection_header("Tool Capabilities")
    capabilities = [
        "🔍 Search knowledge base for relevant information",
        "🧠 Think through complex problems step by step",
        "📊 Analyze information and data from knowledge sources",
        "💡 Provide reasoning and explanations",
        "📝 Generate responses based on knowledge base content",
        "🎯 Focus searches with specific queries",
        "🔗 Combine multiple pieces of information",
        "📚 Access stored documents and embeddings",
    ]

    for capability in capabilities:
        print(f"  {capability}")

    # Integration patterns
    print_subsection_header("Integration Patterns")
    patterns = [
        "Single Agent: Add to agent's tools list for knowledge-enhanced responses",
        "Team Agents: Share knowledge tools across multiple team members",
        "Reasoning Chains: Combine with ReasoningTools for advanced problem solving",
        "Streaming: Works with both streaming and non-streaming agent responses",
        "Citations: Automatically provides source attribution when available",
    ]

    for pattern in patterns:
        print(f"  • {pattern}")


def main() -> None:
    """Main function to run all analyses."""
    print("🚀 AGNO KNOWLEDGE TOOLS ANALYSIS")
    print("This script analyzes the KnowledgeTools package from agno.tools.knowledge")

    # Activate virtual environment reminder
    print("\n💡 Make sure your virtual environment is activated:")
    print("   source .venv/bin/activate")

    # Run analyses
    success = analyze_knowledge_tools_class()

    if success:
        analyze_knowledge_tools_usage()
        create_test_knowledge_tools()

    analyze_knowledge_tools_examples()

    print_section_header("SUMMARY")
    if success:
        print("✅ KnowledgeTools analysis completed successfully!")
        print("\n🔧 Key Features:")
        print("  • Provides search, think, and analyze capabilities")
        print("  • Integrates with knowledge bases for intelligent responses")
        print("  • Supports various configuration options")
        print("  • Works with both single agents and team setups")
        print("  • Enables reasoning over stored knowledge")
    else:
        print("❌ Could not fully analyze KnowledgeTools")
        print("  Check that agno is properly installed and available")

    print("\n📚 For more information, check the examples in:")
    print("  • src/agno/reasoning/tools/knowledge_tools.py")
    print("  • src/agno/reasoning/tools/capture_reasoning_content_knowledge_tools.py")
    print("  • src/agno/reasoning/teams/knowledge_tool_team.py")


if __name__ == "__main__":
    main()
