#!/usr/bin/env python3
"""
Simple LM Studio test that matches the working example exactly.
"""

from agno.agent import Agent
from agno.models.lmstudio import LMStudio

# Create agent exactly like the working example
agent = Agent(model=LMStudio(id="qwen3-4b-mlx"), markdown=True)

# Test the simple query
print("🧪 Testing simple LM Studio integration...")
print("📤 Sending query: 'What is 2 + 2?'")

try:
    # Use the simple approach from the working example
    response = agent.run("What is 2 + 2?")
    print("✅ Query successful!")
    print(f"📥 Response: {response}")
except Exception as e:
    print(f"❌ Query failed: {e}")
    import traceback
    traceback.print_exc()
