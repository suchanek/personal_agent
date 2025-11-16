"""
Charlie Brown Facts Injection Script for Personal Agent Memory System

This script injects a comprehensive set of Charlie Brown facts from the Peanuts
comic strip into the Personal Agent's memory system via REST API. The facts are
written in first-person perspective as if they are Charlie Brown's own memories.

The script demonstrates:
- REST API integration for memory management
- Bulk memory injection with automatic clearing
- First-person narrative memory storage
- Topic-based memory categorization

Facts Categories:
    - Identity & Basics: Charlie Brown's appearance, personality, and debut
    - Friends & Family: Relationships with Linus, Lucy, Snoopy, Sally, and others
    - Adventures & Activities: Baseball team, kite flying, Christmas tree selection
    - Peanuts History: Comic strip milestones, creator info, and cultural impact

Usage:
    python inject_charlie_brown_friends_facts.py

    The script will:
    1. Clear all existing memories via DELETE /api/v1/memory/clear
       (This endpoint blocks until the LightRAG pipeline completes deletion)
    2. Inject 38 Charlie Brown facts via POST /api/v1/memory/store
    3. Display progress for each injection

Requirements:
    - Personal Agent REST API server running on localhost:8001
    - requests library: pip install requests

API Endpoints Used:
    - DELETE http://localhost:8001/api/v1/memory/clear
    - POST http://localhost:8001/api/v1/memory/store

Author: Eric G. Suchanek, PhD
Date: 2025-11-16
Branch: v0.8.77ldev
Version: 1.0.0
"""

import time

import requests

API_BASE_URL = "http://localhost:8001/api/v1"
MEMORY_STORE_URL = f"{API_BASE_URL}/memory/store"
MEMORY_CLEAR_URL = f"{API_BASE_URL}/memory/clear"

facts = [
    # My Identity & Basics
    "I am the main character in the Peanuts comic strip created by Charles M. Schulz.",
    "I am eight years old and I'm known for my round head and zigzag patterned shirt.",
    "My catchphrase is 'Good Grief!' which I say when I'm frustrated or disappointed.",
    "People describe me as a lovable loser who frequently suffers and lacks self-confidence.",
    "I first appeared in the Peanuts comic strip on October 2, 1950.",
    # My Friends & Family
    "Linus van Pelt is my best friend and he's known for always carrying his security blanket.",
    "Lucy van Pelt is Linus's older sister and she gives advice at her psychiatric booth.",
    "Snoopy is my imaginative dog and my closest companion.",
    "Peppermint Patty is an athletic girl who calls me 'Chuck'.",
    "Marcie is Peppermint Patty's best friend and she calls Peppermint Patty 'Sir'.",
    "Schroeder is a piano prodigy who Lucy admires and follows around.",
    "Sally is my younger sister.",
    "Franklin is a kind and thoughtful friend in our group.",
    "Pigpen is known for being perpetually dirty but we all accept him as a friend.",
    "Woodstock is Snoopy's small, yellow bird friend who speaks in chirps.",
    "The Little Red-Haired Girl is my secret crush and I get nervous whenever she's around.",
    "Violet and Patty are my classmates who sometimes tease me.",
    "Shermy was one of my earliest friends when our strip began.",
    "Peggy Jean was my girlfriend for roughly nine years in the comic strip.",
    # My Adventures & Activities
    "I manage a baseball team that always loses games, often by ridiculous scores like 123 to 0.",
    "I play as the pitcher on my baseball team despite our constant losses.",
    "I struggle with flying kites because they keep getting eaten by the Kite-Eating Tree.",
    "The Kite-Eating Tree is my nemesis that swallows my kites with a resounding SWAMP sound.",
    "Every autumn Lucy promises to hold a football for me to kick, but she always pulls it away at the last moment and I land flat on my back.",
    "My baseball team learns about sportsmanship and teamwork despite our terrible losing streak.",
    "I once coached a younger baseball team while sleeping in a cardboard box at night.",
    "I competed in a spelling bee as one of my many adventures.",
    "I selected a small, scraggly Christmas tree that everyone else thought was pathetic, but it became special.",
    # The Peanuts Story
    "Our Peanuts comic strip debuted on October 2, 1950 in seven U.S. newspapers.",
    "Charles M. Schulz created our world in Peanuts, which originated from his earlier strip called Li'l Folks.",
    "My signature zigzag pattern first appeared on my shirt on December 21, 1950.",
    "At its peak, our Peanuts strip ran in over 2,600 newspapers with a readership of 355 million people across 75 countries.",
    "The Peanuts comic strip was published for nearly 50 years with 17,897 strips in total.",
    "Charles M. Schulz drew every Peanuts strip himself, making it arguably the longest story ever told by one human being.",
    "The final Peanuts strip was published on February 13, 2000, the day after Mr. Schulz died.",
    "Our first TV special, A Charlie Brown Christmas, premiered on December 9, 1965 and became an instant classic.",
    "Our Peanuts strip was translated into 21 languages during Mr. Schulz's lifetime.",
    "During my early years, I was more lighthearted and impish before becoming the dour defeatist everyone knows.",
]


def clear_memories():
    """Clear all memories before injecting new facts."""
    print("🧹 Clearing all existing memories...")
    try:
        response = requests.delete(MEMORY_CLEAR_URL, timeout=10)
        if response.ok:
            try:
                data = response.json()
                if data.get("success") == "True" or data.get("success") is True:
                    print(f"✅ Cleared all memories: {data.get('message')}")
                    return True
                else:
                    print(f"⚠️ Clear response: {data}")
                    return False
            except Exception as e:
                print(f"⚠️ Could not parse clear response: {e} | Raw: {response.text}")
                return False
        else:
            print(
                f"❌ Failed to clear memories | HTTP {response.status_code} | {response.text}"
            )
            return False
    except Exception as e:
        print(f"❌ Exception while clearing memories: {e}")
        return False


def main():
    # Clear all memories first (blocks until LightRAG pipeline completes)
    if not clear_memories():
        print("⚠️ Warning: Could not clear memories, continuing anyway...")

    print(f"\n📝 Injecting {len(facts)} Charlie Brown facts...\n")

    for fact in facts[:10]:
        payload = {"content": fact, "topics": ["Peanuts", "Charlie Brown", "Friends"]}
        try:
            response = requests.post(MEMORY_STORE_URL, json=payload, timeout=10)
            if response.ok:
                try:
                    data = response.json()
                    if data.get("success") == "True":
                        print(
                            f"Injected: {fact} | memory_id: {data.get('memory_id')} | message: {data.get('message')}"
                        )
                    elif "error" in data:
                        print(f"Failed: {fact} | Error: {data['error']}")
                    else:
                        print(f"Failed: {fact} | Unexpected response: {data}")
                except Exception as e:
                    print(
                        f"Failed: {fact} | Could not parse JSON: {e} | Raw: {response.text}"
                    )
            else:
                print(f"Failed: {fact} | HTTP {response.status_code} | {response.text}")
        except Exception as e:
            print(f"Exception for fact '{fact}': {e}")
        time.sleep(1)


if __name__ == "__main__":
    main()
