#!/usr/bin/env python3
"""
Clear Memory When Ready Script

Waits for LightRAG pipeline to finish processing, then clears both memory systems.
"""

import asyncio
import sys
import time
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

import aiohttp
from personal_agent.config.settings import LIGHTRAG_MEMORY_URL


async def wait_for_pipeline_idle(max_wait_minutes=10):
    """Wait for LightRAG pipeline to become idle."""
    print(f"🔄 Waiting for LightRAG pipeline to finish processing...")
    
    max_wait_seconds = max_wait_minutes * 60
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        try:
            async with aiohttp.ClientSession() as session:
                # Check pipeline status
                async with session.get(f"{LIGHTRAG_MEMORY_URL}/documents/pipeline_status", timeout=10) as resp:
                    if resp.status == 200:
                        pipeline_data = await resp.json()
                        is_processing = pipeline_data.get("is_processing", False)
                        queue_size = pipeline_data.get("queue_size", 0)
                        
                        if not is_processing and queue_size == 0:
                            print("✅ Pipeline is idle - ready to clear memories!")
                            return True
                        else:
                            current_task = pipeline_data.get("current_task", "unknown")
                            print(f"⏳ Pipeline busy: processing={is_processing}, queue={queue_size}, task={current_task}")
                    else:
                        print(f"⚠️ Could not check pipeline status: {resp.status}")
                        
        except Exception as e:
            print(f"⚠️ Error checking pipeline: {e}")
        
        # Wait 5 seconds before checking again
        await asyncio.sleep(5)
    
    print(f"❌ Timeout: Pipeline still busy after {max_wait_minutes} minutes")
    return False


async def main():
    """Main function."""
    print("🧠 Memory Clearing - Wait for Pipeline Ready")
    print("=" * 50)
    
    # Wait for pipeline to be idle
    if await wait_for_pipeline_idle():
        print("\n🧹 Pipeline is ready - running memory cleaner...")
        
        # Import and run the memory cleaner
        from personal_agent.tools.memory_cleaner import main as cleaner_main
        
        # Override sys.argv to pass the right arguments
        original_argv = sys.argv
        sys.argv = ["memory_cleaner", "--no-confirm", "--verbose"]
        
        try:
            exit_code = await cleaner_main()
            if exit_code == 0:
                print("\n✅ Memory clearing completed successfully!")
            else:
                print(f"\n❌ Memory clearing failed with exit code: {exit_code}")
        finally:
            sys.argv = original_argv
    else:
        print("\n❌ Could not clear memories - pipeline is still busy")
        print("💡 Try again later or restart the LightRAG memory server")


if __name__ == "__main__":
    asyncio.run(main())
