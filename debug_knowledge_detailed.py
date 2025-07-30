#!/usr/bin/env python3
"""
Detailed debug script to compare direct API calls vs tool calls.
"""

import json
import sys
from pathlib import Path

import requests

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config.settings import LIGHTRAG_URL, USER_ID


def compare_api_vs_tool(query: str):
    """Compare direct API call vs tool call for the same query."""
    print(f"\n{'='*80}")
    print(f"🔍 DETAILED COMPARISON FOR QUERY: '{query}'")
    print(f"{'='*80}")

    # 1. Direct API call
    print(f"\n1️⃣ DIRECT API CALL")
    print("-" * 40)

    url = f"{LIGHTRAG_URL}/query"
    params = {
        "query": query.strip(),
        "mode": "hybrid",
        "top_k": 10,
        "response_type": "Multiple Paragraphs",
    }

    try:
        response = requests.post(url, json=params, timeout=60)
        print(f"Status: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")

        if response.status_code == 200:
            result = response.json()
            print(f"Response type: {type(result)}")
            print(
                f"Response keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}"
            )

            if isinstance(result, dict):
                content = result.get("response", result.get("content", str(result)))
            else:
                content = str(result)

            print(f"Content length: {len(content)}")
            print(f"Content preview: {content[:300]}...")

            # Check for no-context indicator
            if "[no-context]" in content:
                print("⚠️  NO-CONTEXT detected in direct API response")
            else:
                print("✅ Content found in direct API response")

            direct_content = content
        else:
            print(f"❌ API Error: {response.text}")
            direct_content = None

    except Exception as e:
        print(f"❌ API Exception: {e}")
        direct_content = None

    # 2. Tool call
    print(f"\n2️⃣ TOOL CALL")
    print("-" * 40)

    try:
        from personal_agent.tools.knowledge_ingestion_tools import (
            KnowledgeIngestionTools,
        )

        tools = KnowledgeIngestionTools()
        tool_result = tools.query_knowledge_base(query, mode="hybrid", limit=10)

        print(f"Tool result type: {type(tool_result)}")
        print(f"Tool result length: {len(tool_result)}")
        print(f"Tool result preview: {tool_result[:300]}...")

        # Check for no-context indicator
        if (
            "[no-context]" in tool_result
            or "No relevant knowledge found" in tool_result
        ):
            print("⚠️  NO-CONTEXT detected in tool response")
        else:
            print("✅ Content found in tool response")

        tool_content = tool_result

    except Exception as e:
        print(f"❌ Tool Exception: {e}")
        import traceback

        traceback.print_exc()
        tool_content = None

    # 3. Comparison
    print(f"\n3️⃣ COMPARISON")
    print("-" * 40)

    if direct_content and tool_content:
        if direct_content == tool_content:
            print("✅ Results are IDENTICAL")
        else:
            print("⚠️  Results are DIFFERENT")
            print(f"Direct API length: {len(direct_content)}")
            print(f"Tool length: {len(tool_content)}")

            # Check if one has no-context and other doesn't
            direct_no_context = "[no-context]" in direct_content
            tool_no_context = (
                "[no-context]" in tool_content
                or "No relevant knowledge found" in tool_content
            )

            if direct_no_context != tool_no_context:
                print("🚨 CRITICAL: One has content, the other doesn't!")
                if direct_no_context:
                    print("   - Direct API: NO CONTENT")
                    print("   - Tool: HAS CONTENT")
                else:
                    print("   - Direct API: HAS CONTENT")
                    print("   - Tool: NO CONTENT")
    else:
        print("❌ Cannot compare - one or both calls failed")


def inspect_tool_internals():
    """Inspect the tool's internal workings."""
    print(f"\n{'='*80}")
    print(f"🔧 TOOL INTERNALS INSPECTION")
    print(f"{'='*80}")

    try:
        from personal_agent.tools.knowledge_ingestion_tools import (
            KnowledgeIngestionTools,
        )

        tools = KnowledgeIngestionTools()

        # Check the settings being used
        from personal_agent.config import settings

        print(f"Settings LIGHTRAG_URL: {settings.LIGHTRAG_URL}")
        print(f"Settings USER_ID: {settings.USER_ID}")

        # Look at the actual query method
        import inspect

        source = inspect.getsource(tools.query_knowledge_base)
        print(f"\nMethod source (first 500 chars):")
        print(source[:500] + "...")

    except Exception as e:
        print(f"❌ Error inspecting tool: {e}")


def main():
    print("🚀 Starting DETAILED LightRAG Debug Session")

    # Test both queries
    test_queries = ["Who is Lucy", "Who is Schroeder"]

    for query in test_queries:
        compare_api_vs_tool(query)

    # Inspect tool internals
    inspect_tool_internals()

    print(f"\n{'='*80}")
    print("🏁 Detailed debug session complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
