"""
Test Problematic Charlie Brown Facts - Individual Injection Script

This script tests the 4 facts that previously failed to encode in LightRAG.
These facts contain heavy numerical/statistical content that may cause issues
with entity-relationship extraction.

Usage:
    python inject_problematic_facts.py

    The script will:
    1. Clear all existing memories via DELETE /api/v1/memory/clear
    2. Inject each problematic fact one at a time with detailed logging
    3. Wait 2 seconds between injections to allow LightRAG processing
    4. Report success/failure for each fact

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

# Problematic facts with heavy numerical/statistical content
# These failed to encode in LightRAG during bulk injection
problematic_facts = [
    "At its peak, our Peanuts strip ran in over 2,600 newspapers with a readership of 355 million people across 75 countries.",
    "The Peanuts comic strip was published for nearly 50 years with 17,897 strips in total.",
    "Charles M. Schulz drew every Peanuts strip himself, making it arguably the longest story ever told by one human being.",
    "The final Peanuts strip was published on February 13, 2000, the day after Mr. Schulz died.",
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


def inject_fact(fact_num, fact):
    """Inject a single fact with detailed logging."""
    print(f"\n{'='*80}")
    print(f"Testing Fact #{fact_num + 1}/{len(problematic_facts)}")
    print(f"Content: {fact}")
    print(f"{'='*80}")

    payload = {"content": fact, "topics": ["Peanuts", "Charlie Brown", "Friends"]}

    try:
        print(f"📤 Sending POST request...")
        response = requests.post(MEMORY_STORE_URL, json=payload, timeout=10)

        print(f"📥 Response Status: HTTP {response.status_code}")
        print(f"📥 Response Headers: {dict(response.headers)}")

        if response.ok:
            try:
                data = response.json()
                print(f"📥 Response JSON: {data}")

                if data.get("success") == "True":
                    print(f"✅ SUCCESS: Injected fact #{fact_num + 1}")
                    print(f"   Memory ID: {data.get('memory_id')}")
                    print(f"   Message: {data.get('message')}")
                    return True
                elif "error" in data:
                    print(f"❌ FAILED: {data['error']}")
                    return False
                else:
                    print(f"❌ FAILED: Unexpected response: {data}")
                    return False
            except Exception as e:
                print(f"❌ FAILED: Could not parse JSON: {e}")
                print(f"   Raw response: {response.text}")
                return False
        else:
            print(f"❌ FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ EXCEPTION: {e}")
        return False


def main():
    print("="*80)
    print("Testing Problematic Charlie Brown Facts")
    print("="*80)
    print(f"\nTotal facts to test: {len(problematic_facts)}")
    print("Each fact will be tested individually with a 2-second delay between injections.\n")

    # Clear all memories first (blocks until LightRAG pipeline completes)
    if not clear_memories():
        print("\n⚠️ Warning: Could not clear memories!")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborting.")
            return

    print("\n" + "="*80)
    print("Starting individual fact injection tests...")
    print("="*80)

    results = []
    for i, fact in enumerate(problematic_facts):
        success = inject_fact(i, fact)
        results.append((fact, success))

        if i < len(problematic_facts) - 1:
            print(f"\n⏳ Waiting 2 seconds before next injection...")
            time.sleep(2)

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    successful = sum(1 for _, success in results if success)
    failed = len(results) - successful

    print(f"\n✅ Successful: {successful}/{len(results)}")
    print(f"❌ Failed: {failed}/{len(results)}")

    if failed > 0:
        print(f"\n❌ Failed facts:")
        for i, (fact, success) in enumerate(results):
            if not success:
                print(f"   {i+1}. {fact[:80]}...")

    if successful == len(results):
        print("\n🎉 All problematic facts were successfully injected!")
    elif successful > 0:
        print("\n⚠️ Some facts succeeded and some failed. Further investigation needed.")
    else:
        print("\n❌ All facts failed. LightRAG may have issues with numerical/statistical content.")


if __name__ == "__main__":
    main()
