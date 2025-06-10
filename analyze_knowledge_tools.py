#!/usr/bin/env python3
"""
Detailed analysis of KnowledgeTools from agno.tools.knowledge.

This script provides comprehensive information about the KnowledgeTools class,
including the actual tool functions it provides and their detailed signatures.
"""

import asyncio
import inspect
import logging
from pathlib import Path
from typing import Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)


def analyze_knowledge_tools_detailed() -> None:
    """Provide detailed analysis of KnowledgeTools methods and capabilities."""

    try:
        from agno.embedder.ollama import OllamaEmbedder
        from agno.knowledge.text import TextKnowledgeBase
        from agno.tools.knowledge import KnowledgeTools
        from agno.vectordb.lancedb import LanceDb, SearchType

        print("🔍 DETAILED KNOWLEDGE TOOLS ANALYSIS")
        print("=" * 80)

        # Create a test knowledge base
        test_storage_path = Path("tmp/test_knowledge")
        test_storage_path.mkdir(parents=True, exist_ok=True)

        vector_db = LanceDb(
            uri=str(test_storage_path / "lancedb"),
            table_name="test_knowledge",
            search_type=SearchType.hybrid,
            embedder=OllamaEmbedder(id="nomic-embed-text", dimensions=768),
        )

        knowledge_base = TextKnowledgeBase(
            path=test_storage_path,
            vector_db=vector_db,
        )

        # Create KnowledgeTools instance
        knowledge_tools = KnowledgeTools(
            knowledge=knowledge_base,
            think=True,
            search=True,
            analyze=True,
            add_few_shot=True,
            add_instructions=True,
        )

        print("\n📋 INDIVIDUAL TOOL FUNCTIONS")
        print("-" * 60)

        # Analyze each tool function
        if hasattr(knowledge_tools, "tools") and knowledge_tools.tools:
            for i, tool in enumerate(knowledge_tools.tools, 1):
                print(f"\n🔧 Tool {i}: {getattr(tool, '__name__', 'Unknown')}")

                # Get function signature
                try:
                    sig = inspect.signature(tool)
                    print(f"   Signature: {tool.__name__}{sig}")
                except Exception as e:
                    print(f"   Signature: Could not determine - {e}")

                # Get docstring
                if tool.__doc__:
                    print(f"   Description: {tool.__doc__.strip()}")
                else:
                    print("   Description: No documentation available")

                # Try to get parameter details
                try:
                    sig = inspect.signature(tool)
                    if sig.parameters:
                        print("   Parameters:")
                        for param_name, param in sig.parameters.items():
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
                            print(f"     • {param_name}: {annotation} = {default}")
                except Exception:
                    pass

        # Show DEFAULT_INSTRUCTIONS if available
        if hasattr(KnowledgeTools, "DEFAULT_INSTRUCTIONS"):
            print("\n📝 DEFAULT INSTRUCTIONS")
            print("-" * 60)
            print(KnowledgeTools.DEFAULT_INSTRUCTIONS)

        # Show FEW_SHOT_EXAMPLES if available
        if hasattr(KnowledgeTools, "FEW_SHOT_EXAMPLES"):
            print("\n💡 FEW SHOT EXAMPLES")
            print("-" * 60)
            print(KnowledgeTools.FEW_SHOT_EXAMPLES)

        # Test method signatures
        print("\n🧪 METHOD ANALYSIS")
        print("-" * 60)

        methods_to_analyze = ["search", "think", "analyze"]
        for method_name in methods_to_analyze:
            if hasattr(knowledge_tools, method_name):
                method = getattr(knowledge_tools, method_name)
                print(f"\n🔍 {method_name.upper()} Method:")

                try:
                    sig = inspect.signature(method)
                    print(f"   Signature: {method_name}{sig}")

                    if method.__doc__:
                        doc_lines = method.__doc__.strip().split("\n")
                        print(
                            f"   Purpose: {doc_lines[0] if doc_lines else 'No description'}"
                        )

                        # Show Args and Returns if in docstring
                        in_args = False
                        in_returns = False
                        for line in doc_lines[1:]:
                            line = line.strip()
                            if line.startswith("Args:"):
                                in_args = True
                                in_returns = False
                                print("   Args:")
                            elif line.startswith("Returns:"):
                                in_args = False
                                in_returns = True
                                print("   Returns:")
                            elif in_args and line and not line.startswith("Returns:"):
                                print(f"     {line}")
                            elif in_returns and line:
                                print(f"     {line}")

                except Exception as e:
                    print(f"   Error analyzing {method_name}: {e}")

        # Configuration options analysis
        print("\n⚙️ CONFIGURATION OPTIONS")
        print("-" * 60)

        config_options = {
            "knowledge": "Required - The knowledge base instance to search",
            "think": "bool (default: True) - Enable thinking/reasoning tool",
            "search": "bool (default: True) - Enable knowledge base search tool",
            "analyze": "bool (default: True) - Enable analysis tool",
            "instructions": "Optional[str] - Custom instructions for the tools",
            "add_instructions": "bool (default: True) - Add default instructions",
            "add_few_shot": "bool (default: False) - Add few-shot examples",
            "few_shot_examples": "Optional[str] - Custom few-shot examples",
        }

        for option, description in config_options.items():
            print(f"  • {option}: {description}")

        print("\n✅ Analysis complete!")

    except ImportError as e:
        print(f"❌ Cannot import required modules: {e}")
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        import traceback

        traceback.print_exc()


def show_usage_examples() -> None:
    """Show practical usage examples of KnowledgeTools."""

    print("\n🚀 PRACTICAL USAGE EXAMPLES")
    print("=" * 80)

    examples = [
        {
            "title": "Basic Agent with Knowledge Search",
            "code": """from agno.agent import Agent
from agno.tools.knowledge import KnowledgeTools
from agno.knowledge.text import TextKnowledgeBase

# Create knowledge base (see agno docs for details)
knowledge_base = TextKnowledgeBase(...)

# Create KnowledgeTools
knowledge_tools = KnowledgeTools(knowledge=knowledge_base)

# Create agent with knowledge tools
agent = Agent(
    model=model,
    tools=[knowledge_tools],
    show_tool_calls=True  # See the tool calls
)

# Ask questions that will use the knowledge base
response = await agent.arun("What information do you have about X?")""",
        },
        {
            "title": "Advanced Configuration with All Features",
            "code": """# Full-featured KnowledgeTools setup
knowledge_tools = KnowledgeTools(
    knowledge=knowledge_base,
    think=True,           # Enable reasoning scratchpad
    search=True,          # Enable knowledge search  
    analyze=True,         # Enable analysis capabilities
    add_instructions=True, # Use built-in instructions
    add_few_shot=True,    # Add example interactions
    instructions="Custom instructions for your specific use case"
)""",
        },
        {
            "title": "Team Integration",
            "code": """from agno.team.team import Team

# Create multiple agents that share knowledge
research_agent = Agent(
    name="Research Agent",
    tools=[knowledge_tools, web_search_tools]
)

analysis_agent = Agent(
    name="Analysis Agent", 
    tools=[knowledge_tools, calculation_tools]
)

# Create team with shared knowledge access
team = Team(
    members=[research_agent, analysis_agent],
    tools=[knowledge_tools],  # Shared team-level tools
)""",
        },
        {
            "title": "Personal Agent Integration (Your Use Case)",
            "code": """# In your AgnoPersonalAgent class
if self.agno_knowledge:
    # Add KnowledgeTools for agent to search its knowledge base
    knowledge_tools = KnowledgeTools(knowledge=self.agno_knowledge)
    tools.append(knowledge_tools)
    
    # Enable search_knowledge for automatic search
    agent_kwargs["search_knowledge"] = True""",
        },
    ]

    for i, example in enumerate(examples, 1):
        print(f"\n📖 Example {i}: {example['title']}")
        print("-" * 40)
        print("```python")
        print(example["code"])
        print("```")


def main() -> None:
    """Main function."""
    print("🔍 COMPREHENSIVE KNOWLEDGE TOOLS ANALYSIS")
    print(
        "This script provides detailed information about agno.tools.knowledge.KnowledgeTools"
    )

    analyze_knowledge_tools_detailed()
    show_usage_examples()

    print("\n📚 SUMMARY")
    print("=" * 80)
    print("✅ KnowledgeTools provides three main functions:")
    print("   🧠 think() - Reasoning scratchpad for complex problems")
    print("   🔍 search() - Search knowledge base for relevant information")
    print("   📊 analyze() - Evaluate and analyze retrieved information")
    print()
    print("✅ Key Benefits:")
    print("   • Automatic knowledge base integration")
    print("   • Built-in reasoning capabilities")
    print("   • Configurable tool selection")
    print("   • Works with both single agents and teams")
    print("   • Supports streaming and non-streaming responses")
    print()
    print("✅ Perfect for your personal agent use case!")
    print("   The KnowledgeTools will automatically search your knowledge base")
    print("   when users ask personal questions like 'What is my name?'")


if __name__ == "__main__":
    main()
