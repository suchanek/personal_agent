#!/usr/bin/env python3
"""
Debug script to verify memory_tools in show_config against AgentMemoryManager implementation
and optionally initialize the AgnoPersonalAgent to surface PersagMemoryTools registration logs.

Usage:
  python scripts/debug_memory_tools.py
  python scripts/debug_memory_tools.py --json
  python scripts/debug_memory_tools.py --init-agent
  python scripts/debug_memory_tools.py --all

Exit codes:
  0 = success (no mismatches)
  1 = mismatches detected or runtime error
"""

import argparse
import asyncio
import inspect
import json
import logging
import os
import sys
from pathlib import Path

# Ensure src is on sys.path when running from repo root
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from personal_agent.config import settings  # noqa: E402
from personal_agent.core.agent_memory_manager import AgentMemoryManager  # noqa: E402
from personal_agent.core.agno_agent import AgnoPersonalAgent  # noqa: E402

# Imports from the project
from personal_agent.tools.show_config import (  # noqa: E402
    get_agentic_tools,
    show_config,
)


def get_show_config_memory_tool_names() -> set[str]:
    tools = get_agentic_tools()
    mem_tools = tools.get("memory_tools", {}).get("tools", [])
    names = {t.get("name") for t in mem_tools if isinstance(t, dict) and "name" in t}
    return {n for n in names if n}


def get_agent_memory_manager_method_names() -> set[str]:
    # Collect public callable methods on AgentMemoryManager
    names: set[str] = set()
    for name in dir(AgentMemoryManager):
        if name.startswith("_"):
            continue
        attr = getattr(AgentMemoryManager, name, None)
        if attr is None:
            continue
        # Class functions/methods can be coroutine functions or regular callables
        if (
            inspect.isfunction(attr)
            or inspect.ismethod(attr)
            or inspect.iscoroutinefunction(attr)
        ):
            names.add(name)
    return names


def compare_tools() -> dict:
    sc_names = get_show_config_memory_tool_names()
    mgr_names = get_agent_memory_manager_method_names()

    # Mismatch types:
    missing_in_manager = sorted(n for n in sc_names if n not in mgr_names)
    # Only report additional implemented methods if they look like "tool-like" APIs we might expose.
    # We'll define a curated allowlist as the sc_names union of known helper APIs we intentionally exclude.
    exclude_implemented = {
        "initialize",
        "restate_user_fact",
        "direct_search_memories",  # included in sc_names if configured
    }
    extra_implemented_candidates = sorted(
        n for n in mgr_names if n not in sc_names and n not in exclude_implemented
    )

    return {
        "show_config_memory_tools": sorted(sc_names),
        "agent_memory_manager_methods": sorted(mgr_names),
        "missing_in_manager": missing_in_manager,
        "extra_implemented_candidates": extra_implemented_candidates,
    }


async def init_agent_and_dump_info() -> dict:
    # Initialize agent to trigger PersagMemoryTools logging we added in agno_agent.py
    agent = AgnoPersonalAgent(debug=True, enable_memory=True)
    # Use the public initialize wrapper for clarity
    await agent.initialize(recreate=False)
    info = agent.get_agent_info()
    # Optionally cleanup
    await agent.cleanup()
    return info


def main():
    parser = argparse.ArgumentParser(
        description="Debug memory_tools vs AgentMemoryManager"
    )
    parser.add_argument(
        "--json", action="store_true", help="Print show_config JSON output"
    )
    parser.add_argument(
        "--init-agent",
        action="store_true",
        help="Initialize agent to emit debug logs and dump agent info",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all checks (compare, json output, and init agent)",
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("LOG_LEVEL", "DEBUG"),
        help="Logging level (default DEBUG)",
    )

    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, str(args.log_level).upper(), logging.DEBUG),
        format="%(levelname)s %(name)s: %(message)s",
    )

    overall_ok = True

    # 1) Compare memory tools between show_config and AgentMemoryManager
    result = compare_tools()
    print("=== Memory Tools Comparison ===")
    print("Show Config memory_tools:", ", ".join(result["show_config_memory_tools"]))
    print(
        "AgentMemoryManager methods (public callables):",
        ", ".join(result["agent_memory_manager_methods"]),
    )
    if result["missing_in_manager"]:
        overall_ok = False
        print("ERROR: Tools listed in show_config but NOT found on AgentMemoryManager:")
        for name in result["missing_in_manager"]:
            print(f"  - {name}")
    else:
        print("OK: All show_config memory_tools exist on AgentMemoryManager")

    if result["extra_implemented_candidates"]:
        print(
            "Note: Additional AgentMemoryManager public callables not listed in show_config (candidates):"
        )
        for name in result["extra_implemented_candidates"]:
            print(f"  - {name}")
    else:
        print("No extra candidate methods detected on AgentMemoryManager")

    # 2) Print show_config JSON block if requested (or --all)
    if args.json or args.all:
        print("\n=== show_config JSON (truncated: agentic_tools.memory_tools only) ===")
        try:
            json_str = show_config(json_output=True)
            data = json.loads(json_str)
            mem_tools = (
                data.get("agentic_tools", {}).get("memory_tools", {}).get("tools", [])
            )
            print(json.dumps(mem_tools, indent=2))
        except Exception as e:
            overall_ok = False
            print(f"ERROR: Failed to render show_config JSON - {e}")

    # 3) Initialize the agent (async) to trigger PersagMemoryTools debug logs and dump agent info
    if args.init_agent or args.all:
        print("\n=== Initializing AgnoPersonalAgent (debug mode) ===")
        try:
            info = asyncio.run(init_agent_and_dump_info())
            print("Agent info summary:")
            print(
                json.dumps(
                    {
                        "model_provider": info.get("model_provider"),
                        "model_name": info.get("model_name"),
                        "memory_enabled": info.get("memory_enabled"),
                        "tool_counts": info.get("tool_counts"),
                    },
                    indent=2,
                )
            )
            print(
                "Initialized agent successfully. Check logs for PersagMemoryTools registration details."
            )
        except Exception as e:
            overall_ok = False
            print(f"ERROR: Agent initialization failed - {e}")

    # Summarize and set exit code
    print("\n=== Summary ===")
    if overall_ok:
        print("SUCCESS: Memory tools are consistent and diagnostics completed.")
        sys.exit(0)
    else:
        print("FAILURE: See errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
