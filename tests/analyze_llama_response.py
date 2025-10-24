#!/usr/bin/env python3
"""
Agno Team ↔ Ollama (llama3.2:3b) diagnostics

What it does:
1) Builds your team with llama3.2:3b (local)
2) Prints member model ids + flags that often break tools (e.g., JSON mode)
3) Sends "hello" (no tools expected)
4) Sends a tool-required question (10 + 32) and inspects tool_calls
5) Gives concrete recommendations based on what it sees
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import get_current_user_id
from personal_agent.team.reasoning_team import cleanup_team, create_team

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("llama32-3b-diagnostics")


def looks_like_json_text(x: Any) -> bool:
    if not isinstance(x, str):
        return False
    s = x.strip()
    return s.startswith("{") or s.startswith("[")


def summarize_member(member, idx):
    name = getattr(member, "name", f"Member-{idx}")
    model = getattr(getattr(member, "model", None), "id", "Unknown")
    params = getattr(getattr(member, "model", None), "params", None)
    print(f"  {idx+1}. {name}  → model: {model}")

    # Try to detect common pitfalls exposed via model params/config
    if params:
        fmt = (
            params.get("format")
            or params.get("response_format")
            or params.get("json_mode")
        )
        if fmt:
            print(
                f"     • format/json flag: {fmt}   ← WARNING: JSON mode breaks tool-calls"
            )
        stops = params.get("stop")
        if stops:
            print(f"     • stop tokens: {stops}")


async def run_and_analyze(team, prompt: str, label: str, user_id: str):
    print(f"\n📋 {label}: '{prompt}'")
    resp = await team.arun(prompt, user_id=user_id)
    print(f"✅ Response object: {type(resp).__name__}")

    # Top-level content
    if hasattr(resp, "content"):
        content = getattr(resp, "content")
        print(f"   • content type={type(content).__name__}, len={len(str(content))}")
        if looks_like_json_text(content):
            try:
                parsed = json.loads(content)
                print(
                    f"   • content parses as JSON (top-level): keys={list(parsed)[:6]}"
                )
            except Exception:
                print("   • content looks like JSON but failed to parse")

    # Top-level messages
    if hasattr(resp, "messages") and resp.messages:
        print(f"   • messages: {len(resp.messages)}")
        for i, m in enumerate(resp.messages):
            role = getattr(m, "role", "unknown")
            mcontent = getattr(m, "content", "")
            print(f"     - msg[{i}] role={role}, content_len={len(str(mcontent))}")
            # Tool calls?
            tcalls = getattr(m, "tool_calls", None)
            if tcalls:
                print(f"       tool_calls[{len(tcalls)}]:")
                for j, tc in enumerate(tcalls):
                    if isinstance(tc, dict):
                        fn = tc.get("function", {})
                        print(
                            f"         #{j+1} name={fn.get('name')} args={fn.get('arguments')}"
                        )
                    else:
                        fname = getattr(getattr(tc, "function", None), "name", None)
                        fargs = getattr(
                            getattr(tc, "function", None), "arguments", None
                        )
                        print(f"         #{j+1} name={fname} args={fargs}")

    # Member responses (team fan-out)
    if hasattr(resp, "member_responses") and resp.member_responses:
        print(f"   • member_responses: {len(resp.member_responses)}")
        for k, mr in enumerate(resp.member_responses):
            print(f"     - member[{k}]")
            msgs = getattr(mr, "messages", []) or []
            print(f"       messages: {len(msgs)}")
            for j, msg in enumerate(msgs):
                role = getattr(msg, "role", "unknown")
                mcontent = getattr(msg, "content", "")
                preview = str(mcontent)[:120].replace("\n", " ")
                print(f"         [{j}] role={role}: '{preview}...'")
                if looks_like_json_text(mcontent):
                    try:
                        parsed = json.loads(mcontent)
                        name = parsed.get("name")
                        if name:
                            print(
                                f"           JSON contains 'name'={name} (tool-ish payload?)"
                            )
                    except Exception:
                        pass
                tcalls = getattr(msg, "tool_calls", None)
                if tcalls:
                    print(f"           tool_calls[{len(tcalls)}]:")
                    for h, tc in enumerate(tcalls):
                        if isinstance(tc, dict):
                            fn = tc.get("function", {})
                            print(
                                f"             #{h+1} name={fn.get('name')} args={fn.get('arguments')}"
                            )
                        else:
                            fname = getattr(getattr(tc, "function", None), "name", None)
                            fargs = getattr(
                                getattr(tc, "function", None), "arguments", None
                            )
                            print(f"             #{h+1} name={fname} args={fargs}")

    return resp


async def main():
    print("🔍 LLAMA3.2:3b — TEAM DIAGNOSTICS")
    print("=" * 60)

    # Ensure no global JSON forcing flags leak in
    for envflag in ("AGNO_JSON_MODE", "AGNO_RESPONSE_FORMAT", "OPENAI_RESPONSE_FORMAT"):
        if os.getenv(envflag):
            print(f"⚠️  ENV {envflag} is set → may force JSON. Consider unsetting it.")

    print("📋 Step 1: Create team with llama3.2:3b ...")
    try:
        team = await create_team(use_remote=False, model_name="llama3.2:3b")
        if not team:
            print("❌ Failed to create team")
            return
        print(f"✅ Team created with {len(team.members)} members")
        print("\n🤖 Team Members:")
        for i, member in enumerate(team.members):
            summarize_member(member, i)
    except Exception as e:
        print(f"❌ Error creating team: {e}")
        raise

    try:
        user_id = get_current_user_id()
        # 1) Baseline non-tool chat
        await run_and_analyze(team, "hello", "Run A (no tools expected)", user_id)

        # 2) Tool-required query to see whether tool_calls propagate
        # (Your team should have an arithmetic or generic tools registry; if not, this will still show attempted tool_calls)
        await run_and_analyze(
            team,
            "What is 10 + 32? Use the calculator tool if you have one.",
            "Run B (tool exercise)",
            user_id,
        )

        # 3) Structured output probe — should remain conversational if tools are on
        await run_and_analyze(
            team,
            "Return exactly the phrase: READY",
            "Run C (structured-output probe)",
            user_id,
        )

    finally:
        try:
            await cleanup_team(team)
        except Exception as e:
            print(f"⚠️ Cleanup error: {e}")

    print("\n✅ Diagnostics complete.")
    print("\n🔧 Recommendations:")
    print(
        "  • If you see tool_calls in member messages but no execution, your Agno router isn’t handling Ollama tool_calls."
    )
    print(
        "  • If content is raw JSON (schema) instead of tool markup, something is enabling JSON/structured output."
    )
    print(
        "  • Ensure your Ollama adapter keeps `tools=[...]` on every round-trip and *never* sets format='json' when tools are on."
    )
    print(
        "  • If needed, normalize Ollama tool_calls → OpenAI-style before your router processes them."
    )


if __name__ == "__main__":
    asyncio.run(main())
