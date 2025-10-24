#!/usr/bin/env python3
"""
Manually set the model in global state for testing REST API.
This simulates what Streamlit should be doing.
"""

import os
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from personal_agent.tools.global_state import get_global_state

# Get the model from environment or use default
model = os.getenv("LLM_MODEL", "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:q8_0")
user = os.getenv("USER_ID", "charlie")

# Update global state
global_state = get_global_state()
global_state.set("llm_model", model)
global_state.set("userid", user)

print(f"✅ Set global state:")
print(f"   - llm_model: {model}")
print(f"   - userid: {user}")

# Verify
status = global_state.get_status()
print(f"\n📊 Current global state status:")
print(f"   - model (via get_status): {status.get('model')}")
print(f"   - user (via get_status): {status.get('user')}")
print(f"   - agent_mode: {status.get('agent_mode')}")
