#!/usr/bin/env python3
"""Debug script to check agent tools structure."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

try:
    from src.personal_agent.smol_main import initialize_smolagents_system

    print("Initializing smolagents system...")
    (multi_agent_system, smolagents_agent, query_kb, store_int, clear_kb) = (
        initialize_smolagents_system()
    )

    print(f"\n=== SMOLAGENTS AGENT ===")
    print(f"Agent type: {type(smolagents_agent)}")
    print(f"Has tools attribute: {hasattr(smolagents_agent, 'tools')}")

    if hasattr(smolagents_agent, "tools"):
        print(f"Tools type: {type(smolagents_agent.tools)}")
        print(f"Number of tools: {len(smolagents_agent.tools)}")

        if isinstance(smolagents_agent.tools, dict):
            print("Tools is a dictionary!")
            print(f"Keys (first 3): {list(smolagents_agent.tools.keys())[:3]}")
            print(f"Values (first 3): {list(smolagents_agent.tools.values())[:3]}")

            for i, (tool_name, tool_obj) in enumerate(
                list(smolagents_agent.tools.items())[:3]
            ):
                print(f"\nTool {i}:")
                print(f"  Key: {tool_name}")
                print(f"  Type: {type(tool_obj)}")
                print(f"  Has name attr: {hasattr(tool_obj, 'name')}")
                if hasattr(tool_obj, "name"):
                    print(f"  Name: {tool_obj.name}")
        else:
            for i, tool in enumerate(list(smolagents_agent.tools)[:3]):
                print(f"\nTool {i}:")
                print(f"  Type: {type(tool)}")
                print(f"  String representation: {str(tool)}")
                print(f"  Has name attr: {hasattr(tool, 'name')}")
                if hasattr(tool, "name"):
                    print(f"  Name: {tool.name}")
                else:
                    print(f"  Value: {tool}")

    print(f"\n=== MULTI-AGENT SYSTEM ===")
    print(f"Multi-agent type: {type(multi_agent_system)}")
    print(f"Has get_agent_info: {hasattr(multi_agent_system, 'get_agent_info')}")
    print(
        f"Has list_available_tools: {hasattr(multi_agent_system, 'list_available_tools')}"
    )

except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
