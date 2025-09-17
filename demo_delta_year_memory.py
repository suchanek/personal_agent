#!/usr/bin/env python3
"""
Demo script showing delta_year memory functionality.

This script demonstrates how the delta_year attribute allows creating memories
as if writing from the perspective of the user at a specific age.

Usage:
    python demo_delta_year_memory.py

Author: Demo script for delta_year functionality
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add the src directory to the path
current_dir = Path(__file__).resolve().parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

from personal_agent.core.user_model import User


def demo_delta_year_concept():
    """Demonstrate the delta_year concept with examples."""
    print("🎭 Delta Year Memory Concept Demo")
    print("=" * 50)
    print()

    print("The delta_year attribute allows you to create memories as if you were")
    print("writing from the perspective of your user at a specific age.")
    print()

    # Example user
    user = User(
        user_id="demo_user",
        user_name="Alex Johnson",
        birth_date="1990-08-15",  # Born August 15, 1990
    )

    print(f"User: {user.user_name}")
    print(f"Born: {user.birth_date}")
    print()

    # Show different delta_year scenarios
    scenarios = [
        (None, "Current time (normal memories)"),
        (0, "Current time (explicit normal)"),
        (5, "As a 5-year-old child"),
        (12, "As a 12-year-old pre-teen"),
        (18, "As an 18-year-old young adult"),
        (25, "As a 25-year-old adult"),
        (35, "As a 35-year-old professional"),
    ]

    current_time = datetime.now()
    print(f"Current date/time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    for delta_year, description in scenarios:
        user.delta_year = delta_year
        memory_timestamp = user.get_memory_timestamp()

        age_at_memory = current_time.year - 1990 if delta_year is None else delta_year

        print(f"📅 {description}")
        print(f"   Delta year: {delta_year}")
        print(f"   Memory timestamp: {memory_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   User age at memory time: ~{age_at_memory} years old")
        print()

    print("💡 Use Cases:")
    print("   • Child memories: Set delta_year=6 to remember as a 6-year-old")
    print("   • Teenage memories: Set delta_year=15 for high school experiences")
    print("   • Career memories: Set delta_year=28 for professional milestones")
    print("   • Normal memories: Leave delta_year=None or delta_year=0")
    print()

    print("🔧 How it works:")
    print("   Memory year = birth_year + delta_year")
    print("   Memory month/day/time = current month/day/time")
    print("   This creates chronological consistency while allowing age-specific context")
    print()


if __name__ == "__main__":
    demo_delta_year_concept()
