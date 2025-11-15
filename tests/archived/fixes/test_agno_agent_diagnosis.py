import asyncio
import time
import logging
from pathlib import Path
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.personal_agent.core.agno_agent import AgnoPersonalAgent
from src.personal_agent.core.agent_instruction_manager import InstructionLevel

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PerformanceDiagnostic:
    def __init__(self):
        self.timings = {}
        
    def start_timer(self, name):
        self.timings[name] = {'start': time.perf_counter()}
        logger.info(f"⏱️  Starting timer: {name}")
        
    def end_timer(self, name):
        if name in self.timings:
            self.timings[name]['end'] = time.perf_counter()
            duration = self.timings[name]['end'] - self.timings[name]['start']
            self.timings[name]['duration'] = duration
            logger.info(f"⏱️  Timer {name}: {duration:.2f} seconds")
            return duration
        return 0
        
    def get_timing(self, name):
        return self.timings.get(name, {}).get('duration', 0)

async def test_basic_agno_agent():
    """
    Basic test to isolate the performance issue with agno agent
    """
    print("=== AGNO AGENT DIAGNOSTIC TEST ===")
    
    diag = PerformanceDiagnostic()
    
    # Test 1: Agent initialization
    print("\n1. Testing agent initialization...")
    diag.start_timer("agent_init")
    
    try:
        agent = await AgnoPersonalAgent.create_with_init(
            enable_memory=True,
            debug=True,
            instruction_level=InstructionLevel.EXPLICIT,
            alltools=True,
        )
        diag.end_timer("agent_init")
        print(f"✅ Agent initialized successfully in {diag.get_timing('agent_init'):.2f}s")
    except Exception as e:
        diag.end_timer("agent_init")
        print(f"❌ Agent initialization failed: {e}")
        return
    
    # Test 2: Simple query (should be fast)
    print("\n2. Testing simple query...")
    diag.start_timer("simple_query")
    
    try:
        logger.info("Starting simple query: 'Hello, who are you?'")
        response = await agent.run("Hello, who are you?")
        diag.end_timer("simple_query")
        
        print(f"✅ Simple query completed in {diag.get_timing('simple_query'):.2f}s")
        print(f"Response type: {type(response)}")
        print(f"Response preview: {str(response)[:200]}...")
        
    except Exception as e:
        diag.end_timer("simple_query")
        print(f"❌ Simple query failed: {e}")
        return
    
    # Test 3: Memory query with detailed timing
    print("\n3. Testing memory query with detailed logging...")
    diag.start_timer("memory_query_total")
    
    try:
        logger.info("Starting memory query: 'list all memories'")
        
        # Add sub-timers to track different phases
        diag.start_timer("memory_query_start")
        
        # This is where we expect the bottleneck
        response = await agent.run("list all memories. do not interpret, just list them")
        
        diag.end_timer("memory_query_start")
        diag.end_timer("memory_query_total")
        
        print(f"✅ Memory query completed in {diag.get_timing('memory_query_total'):.2f}s")
        print(f"Response type: {type(response)}")
        print(f"Response length: {len(str(response)) if response else 0} characters")
        print(f"Response preview: {str(response)[:300]}...")
        
        # Check if response is RunResponse type
        if hasattr(response, '__class__'):
            print(f"Response class: {response.__class__.__name__}")
            if hasattr(response, 'data'):
                print(f"Response has data attribute: {hasattr(response, 'data')}")
            if hasattr(response, 'content'):
                print(f"Response has content attribute: {hasattr(response, 'content')}")
        
    except Exception as e:
        diag.end_timer("memory_query_start")
        diag.end_timer("memory_query_total")
        print(f"❌ Memory query failed: {e}")
        logger.exception("Memory query exception details:")
        return
    
    # Test 4: Direct memory system access (bypass agent.run)
    print("\n4. Testing direct memory system access...")
    diag.start_timer("direct_memory")
    
    try:
        if hasattr(agent, 'memory_manager') and agent.memory_manager:
            logger.info("Accessing memory manager directly")
            # Try to access memory directly to see if the bottleneck is in agent.run or memory system
            memories = await agent.memory_manager.get_all_memories()
            diag.end_timer("direct_memory")
            
            print(f"✅ Direct memory access completed in {diag.get_timing('direct_memory'):.2f}s")
            print(f"Number of memories: {len(memories) if memories else 0}")
        else:
            diag.end_timer("direct_memory")
            print("⚠️  No memory manager found on agent")
            
    except Exception as e:
        diag.end_timer("direct_memory")
        print(f"❌ Direct memory access failed: {e}")
        logger.exception("Direct memory access exception:")
    
    # Summary
    print("\n=== DIAGNOSTIC SUMMARY ===")
    print(f"Agent initialization: {diag.get_timing('agent_init'):.2f}s")
    print(f"Simple query: {diag.get_timing('simple_query'):.2f}s")
    print(f"Memory query (via agent.run): {diag.get_timing('memory_query_total'):.2f}s")
    print(f"Direct memory access: {diag.get_timing('direct_memory'):.2f}s")
    
    # Analysis
    memory_via_agent = diag.get_timing('memory_query_total')
    direct_memory = diag.get_timing('direct_memory')
    
    if memory_via_agent > 10 and direct_memory < 2:
        print("\n🔍 DIAGNOSIS: The bottleneck is likely in agent.run() response parsing/processing")
        print("   - Direct memory access is fast")
        print("   - agent.run() with memory query is slow")
        print("   - This suggests response parsing or tool execution overhead")
    elif direct_memory > 10:
        print("\n🔍 DIAGNOSIS: The bottleneck is in the memory system itself")
        print("   - Direct memory access is slow")
        print("   - Memory retrieval/processing needs optimization")
    elif memory_via_agent > 30:
        print("\n🔍 DIAGNOSIS: Severe performance issue detected")
        print("   - Memory query taking >30 seconds suggests major bottleneck")
        print("   - Check for infinite loops, blocking operations, or parsing issues")
    else:
        print("\n✅ DIAGNOSIS: Performance appears normal")
    
    print("=" * 50)

if __name__ == "__main__":
    try:
        asyncio.run(test_basic_agno_agent())
    except KeyboardInterrupt:
        print("\n⚠️  Test cancelled by user")
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        logger.exception("Test execution exception:")