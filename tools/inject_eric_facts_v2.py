#!/usr/bin/env python3
"""
Modern Eric Facts Injection Script v2.0

This script uses the modern SemanticMemoryManager and AgnoPersonalAgent to inject
Eric's personal facts without manual categories, leveraging auto-classification
and dual storage (local SQLite + LightRAG graph).

Key improvements over v1:
- Uses SemanticMemoryManager with semantic duplicate detection
- Auto-classification instead of manual categories
- Dual storage in both local memory and graph memory
- Better progress tracking and validation
- Cleaner fact processing from structured text file
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Tuple

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.config import (
    AGNO_STORAGE_DIR,
    LLM_MODEL,
    OLLAMA_URL,
    REMOTE_OLLAMA_URL,
    USER_ID,
)
from personal_agent.core.agno_agent import AgnoPersonalAgent


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Modern Eric Facts Injection Script v2.0"
    )
    parser.add_argument(
        "--remote", action="store_true", help="Use remote Ollama URL instead of local"
    )
    parser.add_argument(
        "--clear-first", 
        action="store_true", 
        help="Clear all existing memories before injecting new facts"
    )
    parser.add_argument(
        "--delay", 
        type=float, 
        default=0.5, 
        help="Delay between fact injections in seconds (default: 0.5)"
    )
    parser.add_argument(
        "--limit", 
        type=int, 
        help="Limit number of facts to inject (for testing)"
    )
    parser.add_argument(
        "--dual-storage", 
        action="store_true", 
        default=True,
        help="Use dual storage (local + graph memory) - default: True"
    )
    parser.add_argument(
        "--local-only", 
        action="store_true", 
        help="Use local storage only (skip graph memory) - overrides --dual-storage"
    )
    parser.add_argument(
        "--validate", 
        action="store_true", 
        default=True,
        help="Run validation tests after injection - default: True"
    )
    return parser.parse_args()


def load_eric_facts() -> List[str]:
    """Load Eric's facts from the structured facts file.
    
    Returns:
        List of individual fact strings
    """
    facts_file = Path(__file__).parent.parent / "eric" / "eric_structured_facts.txt"
    
    if not facts_file.exists():
        raise FileNotFoundError(f"Facts file not found: {facts_file}")
    
    print(f"📖 Loading facts from: {facts_file}")
    
    with open(facts_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract individual facts (lines that don't start with # or are empty)
    facts = []
    for line in content.split('\n'):
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('##'):
            # Skip section headers and comments
            if not line.endswith('Facts') and not line.startswith('---'):
                facts.append(line)
    
    print(f"✅ Loaded {len(facts)} individual facts")
    return facts


async def initialize_agent(use_remote: bool = False) -> AgnoPersonalAgent:
    """Initialize the AgnoPersonalAgent with memory enabled.
    
    Args:
        use_remote: Whether to use remote Ollama URL
        
    Returns:
        Initialized AgnoPersonalAgent instance
    """
    ollama_url = REMOTE_OLLAMA_URL if use_remote else OLLAMA_URL
    
    print("🤖 Initializing AgnoPersonalAgent...")
    print(f"🌐 Using {'remote' if use_remote else 'local'} Ollama URL: {ollama_url}")
    print(f"👤 User ID: {USER_ID}")
    print(f"🧠 Model: {LLM_MODEL}")
    
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=ollama_url,
        user_id=USER_ID,
        debug=True,
        enable_memory=True,
        enable_mcp=False,  # Disable MCP for faster initialization
        storage_dir=AGNO_STORAGE_DIR,
    )
    
    success = await agent.initialize()
    if not success:
        raise RuntimeError("Failed to initialize AgnoPersonalAgent")
    
    print("✅ Agent initialized successfully")
    return agent


async def clear_existing_memories(agent: AgnoPersonalAgent) -> bool:
    """Clear all existing memories for the user.
    
    Args:
        agent: Initialized AgnoPersonalAgent
        
    Returns:
        True if successful, False otherwise
    """
    print("\n🧹 Clearing existing memories...")
    
    try:
        # Use the agent's memory tools to clear memories
        if hasattr(agent, 'agno_memory') and agent.agno_memory:
            success, message = agent.agno_memory.memory_manager.clear_memories(
                db=agent.agno_memory.db,
                user_id=agent.user_id
            )
            
            if success:
                print(f"✅ {message}")
                return True
            else:
                print(f"❌ Failed to clear memories: {message}")
                return False
        else:
            print("❌ Memory system not available")
            return False
            
    except Exception as e:
        print(f"❌ Error clearing memories: {e}")
        return False


async def inject_fact_dual_storage(
    agent: AgnoPersonalAgent, 
    fact: str, 
    fact_number: int, 
    total_facts: int,
    use_dual_storage: bool = True
) -> Tuple[bool, str, Dict[str, Any]]:
    """Inject a single fact using dual storage approach.
    
    Args:
        agent: Initialized AgnoPersonalAgent
        fact: The fact to inject
        fact_number: Current fact number (for progress)
        total_facts: Total number of facts
        use_dual_storage: Whether to use dual storage
        
    Returns:
        Tuple of (success, message, metadata)
    """
    print(f"\n📝 [{fact_number}/{total_facts}] Injecting: {fact[:80]}...")
    
    start_time = time.time()
    metadata = {
        "fact": fact,
        "fact_number": fact_number,
        "total_facts": total_facts,
        "local_storage": False,
        "graph_storage": False,
        "topics": None,
        "response_time": 0.0
    }
    
    try:
        if use_dual_storage:
            # Try dual storage but fall back to local-only if graph storage fails
            try:
                # Use the agent's store_user_memory method which handles dual storage
                result = await asyncio.wait_for(
                    agent.store_user_memory(content=fact), 
                    timeout=30.0  # 30 second timeout
                )
                
                # Parse the result to understand what happened
                if "✅" in result:
                    metadata["local_storage"] = "Local memory:" in result
                    metadata["graph_storage"] = "Graph memory:" in result
                    
                    end_time = time.time()
                    metadata["response_time"] = end_time - start_time
                    
                    print(f"✅ Success in {metadata['response_time']:.2f}s")
                    print(f"   Result: {result[:200]}...")  # Truncate long results
                    
                    return True, result, metadata
                else:
                    end_time = time.time()
                    metadata["response_time"] = end_time - start_time
                    
                    print(f"⚠️ Partial success or duplicate: {result[:100]}...")
                    return True, result, metadata  # Still count as success for duplicates
                    
            except (asyncio.TimeoutError, asyncio.CancelledError, Exception) as e:
                print(f"⚠️ Dual storage failed ({str(e)[:50]}...), falling back to local-only")
                # Fall back to local storage only
                use_dual_storage = False
        
        if not use_dual_storage:
            # Use direct memory manager for local storage only
            success, message, memory_id, topics = agent.agno_memory.memory_manager.add_memory(
                memory_text=fact,
                db=agent.agno_memory.db,
                user_id=agent.user_id,
                topics=None  # Let auto-classification handle it
            )
            
            end_time = time.time()
            metadata["response_time"] = end_time - start_time
            metadata["local_storage"] = success
            metadata["topics"] = topics
            
            if success:
                print(f"✅ Success (local-only) in {metadata['response_time']:.2f}s")
                print(f"   Memory ID: {memory_id}")
                print(f"   Topics: {topics}")
                return True, f"Local memory stored: {message}", metadata
            else:
                print(f"❌ Failed: {message}")
                return False, message, metadata
                
    except Exception as e:
        end_time = time.time()
        metadata["response_time"] = end_time - start_time
        error_msg = f"Error injecting fact: {str(e)}"
        print(f"❌ {error_msg}")
        return False, error_msg, metadata


async def inject_all_facts(
    agent: AgnoPersonalAgent, 
    facts: List[str], 
    delay: float = 0.5,
    limit: int = None,
    use_dual_storage: bool = True
) -> Dict[str, Any]:
    """Inject all facts with progress tracking.
    
    Args:
        agent: Initialized AgnoPersonalAgent
        facts: List of facts to inject
        delay: Delay between injections
        limit: Optional limit on number of facts
        use_dual_storage: Whether to use dual storage
        
    Returns:
        Dictionary with injection results and statistics
    """
    if limit:
        facts = facts[:limit]
        print(f"🎯 Limited to first {limit} facts")
    
    total_facts = len(facts)
    print(f"\n🚀 Starting injection of {total_facts} facts...")
    print(f"⏱️ Delay between facts: {delay}s")
    print(f"💾 Storage mode: {'Dual (Local + Graph)' if use_dual_storage else 'Local only'}")
    
    results = {
        "total_facts": total_facts,
        "successful": 0,
        "failed": 0,
        "duplicates": 0,
        "total_time": 0.0,
        "fact_results": [],
        "topics_found": set(),
        "errors": []
    }
    
    start_time = time.time()
    
    for i, fact in enumerate(facts, 1):
        success, message, metadata = await inject_fact_dual_storage(
            agent, fact, i, total_facts, use_dual_storage
        )
        
        results["fact_results"].append({
            "fact": fact,
            "success": success,
            "message": message,
            "metadata": metadata
        })
        
        if success:
            results["successful"] += 1
            if "duplicate" in message.lower() or "already exists" in message.lower():
                results["duplicates"] += 1
        else:
            results["failed"] += 1
            results["errors"].append(f"Fact {i}: {message}")
        
        # Collect topics
        if metadata.get("topics"):
            results["topics_found"].update(metadata["topics"])
        
        # Progress update every 10 facts
        if i % 10 == 0 or i == total_facts:
            success_rate = (results["successful"] / i) * 100
            avg_time = sum(r["metadata"]["response_time"] for r in results["fact_results"]) / i
            print(f"\n📊 Progress: {i}/{total_facts} ({success_rate:.1f}% success, avg {avg_time:.2f}s/fact)")
        
        # Delay between facts
        if i < total_facts and delay > 0:
            await asyncio.sleep(delay)
    
    end_time = time.time()
    results["total_time"] = end_time - start_time
    results["topics_found"] = list(results["topics_found"])
    
    return results


async def validate_injection(agent: AgnoPersonalAgent) -> Dict[str, Any]:
    """Validate the injection by checking memory state and testing recall.
    
    Args:
        agent: Initialized AgnoPersonalAgent
        
    Returns:
        Dictionary with validation results
    """
    print("\n🔍 Validating injection results...")
    
    validation = {
        "memory_count": 0,
        "memory_stats": {},
        "recall_tests": [],
        "validation_success": False
    }
    
    try:
        # Get memory statistics
        if hasattr(agent, 'agno_memory') and agent.agno_memory:
            stats = agent.agno_memory.memory_manager.get_memory_stats(
                db=agent.agno_memory.db,
                user_id=agent.user_id
            )
            
            validation["memory_stats"] = stats
            validation["memory_count"] = stats.get("total_memories", 0)
            
            print(f"📊 Memory Statistics:")
            print(f"   Total memories: {validation['memory_count']}")
            print(f"   Average length: {stats.get('average_memory_length', 0):.1f} chars")
            print(f"   Recent memories (24h): {stats.get('recent_memories_24h', 0)}")
            
            if stats.get("topic_distribution"):
                print(f"   Topic distribution:")
                for topic, count in stats["topic_distribution"].items():
                    print(f"     - {topic}: {count}")
        
        # Test recall with sample queries
        test_queries = [
            "What is Eric's name?",
            "Where did Eric get his PhD?", 
            "What programming languages does Eric know?",
            "What is Eric's current project?",
            "What companies has Eric worked for?"
        ]
        
        print(f"\n🧠 Testing recall with {len(test_queries)} queries...")
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n❓ Test {i}: {query}")
            try:
                # Use the agent's query_memory method directly
                if hasattr(agent.agno_memory, 'memory_manager'):
                    results = agent.agno_memory.memory_manager.search_memories(
                        query=query,
                        db=agent.agno_memory.db,
                        user_id=agent.user_id,
                        limit=3,
                        similarity_threshold=0.3
                    )
                    
                    if results:
                        print(f"✅ Found {len(results)} relevant memories")
                        for memory, score in results[:2]:  # Show top 2
                            print(f"   - {memory.memory[:100]}... (score: {score:.2f})")
                        
                        validation["recall_tests"].append({
                            "query": query,
                            "success": True,
                            "results_count": len(results),
                            "top_score": results[0][1] if results else 0.0
                        })
                    else:
                        print(f"❌ No relevant memories found")
                        validation["recall_tests"].append({
                            "query": query,
                            "success": False,
                            "results_count": 0,
                            "top_score": 0.0
                        })
                        
            except Exception as e:
                print(f"❌ Error testing recall: {e}")
                validation["recall_tests"].append({
                    "query": query,
                    "success": False,
                    "error": str(e)
                })
        
        # Determine overall validation success
        successful_recalls = sum(1 for test in validation["recall_tests"] if test.get("success", False))
        recall_rate = successful_recalls / len(test_queries) if test_queries else 0
        
        validation["validation_success"] = (
            validation["memory_count"] > 0 and 
            recall_rate >= 0.6  # At least 60% recall success
        )
        
        print(f"\n📊 Validation Summary:")
        print(f"   Memories stored: {validation['memory_count']}")
        print(f"   Recall tests passed: {successful_recalls}/{len(test_queries)} ({recall_rate:.1%})")
        print(f"   Overall validation: {'✅ PASSED' if validation['validation_success'] else '❌ FAILED'}")
        
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        validation["error"] = str(e)
    
    return validation


async def main():
    """Main function to run the Eric facts injection."""
    print("🚀 Eric Facts Injection Script v2.0")
    print("=" * 60)
    
    try:
        # Parse arguments
        args = parse_args()
        
        # Load facts
        facts = load_eric_facts()
        
        # Initialize agent
        agent = await initialize_agent(use_remote=args.remote)
        
        # Clear existing memories if requested
        if args.clear_first:
            clear_success = await clear_existing_memories(agent)
            if not clear_success:
                print("⚠️ Failed to clear memories, but continuing...")
        
        # Determine storage mode
        use_dual_storage = args.dual_storage and not args.local_only
        if args.local_only:
            print("🔧 Local-only mode enabled - skipping graph memory storage")
        
        # Inject facts
        results = await inject_all_facts(
            agent=agent,
            facts=facts,
            delay=args.delay,
            limit=args.limit,
            use_dual_storage=use_dual_storage
        )
        
        # Print injection results
        print(f"\n📊 INJECTION RESULTS:")
        print(f"=" * 60)
        print(f"✅ Successful: {results['successful']}/{results['total_facts']}")
        print(f"🔄 Duplicates: {results['duplicates']}")
        print(f"❌ Failed: {results['failed']}")
        print(f"⏱️ Total time: {results['total_time']:.1f}s")
        print(f"📈 Average time per fact: {results['total_time']/results['total_facts']:.2f}s")
        
        if results['topics_found']:
            print(f"🏷️ Topics discovered: {', '.join(results['topics_found'])}")
        
        if results['errors']:
            print(f"\n❌ Errors encountered:")
            for error in results['errors'][:5]:  # Show first 5 errors
                print(f"   - {error}")
            if len(results['errors']) > 5:
                print(f"   ... and {len(results['errors']) - 5} more errors")
        
        # Run validation if requested
        if args.validate:
            validation = await validate_injection(agent)
            
            # Final summary
            success_rate = (results['successful'] / results['total_facts']) * 100
            
            print(f"\n🎯 FINAL SUMMARY:")
            print(f"=" * 60)
            print(f"📝 Facts processed: {results['total_facts']}")
            print(f"✅ Success rate: {success_rate:.1f}%")
            print(f"💾 Memories stored: {validation.get('memory_count', 0)}")
            print(f"🧠 Validation: {'✅ PASSED' if validation.get('validation_success') else '❌ FAILED'}")
            
            if success_rate >= 90 and validation.get('validation_success'):
                print(f"\n🎉 EXCELLENT! Eric's facts have been successfully injected!")
                print(f"💡 The agent now has comprehensive knowledge about Eric.")
            elif success_rate >= 70:
                print(f"\n✅ GOOD! Most facts were successfully injected.")
                print(f"⚠️ Some issues detected - check the results above.")
            else:
                print(f"\n⚠️ ISSUES DETECTED! Many facts failed to inject properly.")
                print(f"🔧 Consider checking your agent configuration or memory system.")
        
        # Cleanup
        await agent.cleanup()
        
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Usage examples:")
    print("  python inject_eric_facts_v2.py                    # Basic injection")
    print("  python inject_eric_facts_v2.py --remote           # Use remote Ollama")
    print("  python inject_eric_facts_v2.py --clear-first      # Clear existing memories first")
    print("  python inject_eric_facts_v2.py --limit 20         # Inject only first 20 facts")
    print("  python inject_eric_facts_v2.py --delay 1.0        # 1 second delay between facts")
    print("  python inject_eric_facts_v2.py --local-only       # Use local storage only (skip graph)")
    print("  python inject_eric_facts_v2.py --clear-first --local-only --limit 50  # Safe test run")
    print()
    
    asyncio.run(main())
