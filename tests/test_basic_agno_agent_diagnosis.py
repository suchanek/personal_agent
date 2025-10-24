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

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.run.response import RunResponse
from agno.storage.sqlite import SqliteStorage
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory

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
    Basic test using core agno.Agent to isolate performance issues
    """
    print("=== BASIC AGNO AGENT DIAGNOSTIC TEST ===")
    
    diag = PerformanceDiagnostic()
    
    # Test 1: Agent initialization
    print("\n1. Testing basic agno agent initialization...")
    diag.start_timer("agent_init")
    
    try:
        # Create basic agno agent with ollama
        agent = Agent(
            model=Ollama(id="qwen3:1.7b"),  # Use a small, fast model
            storage=SqliteStorage(table_name="agent_sessions", db_file="./test_agent.db"),
            memory=Memory(
                db=SqliteMemoryDb(db_file="./test_memory.db"),
            ),
            debug_mode=True,
        )
        diag.end_timer("agent_init")
        print(f"✅ Basic agno agent initialized successfully in {diag.get_timing('agent_init'):.2f}s")
    except Exception as e:
        diag.end_timer("agent_init")
        print(f"❌ Agent initialization failed: {e}")
        logger.exception("Agent initialization exception:")
        return
    
    # Test 2: Simple query (should be fast)
    print("\n2. Testing simple query...")
    diag.start_timer("simple_query")
    
    try:
        logger.info("Starting simple query: 'Hello, who are you?'")
        response = await agent.arun("Hello, who are you?")
        diag.end_timer("simple_query")
        
        print(f"✅ Simple query completed in {diag.get_timing('simple_query'):.2f}s")
        print(f"Response type: {type(response)}")
        
        # Check if it's RunResponse
        if isinstance(response, RunResponse):
            print("✅ Response is RunResponse type")
            print(f"Response content preview: {str(response.content)[:200]}...")
        else:
            print(f"⚠️  Response is not RunResponse, it's: {type(response)}")
            print(f"Response preview: {str(response)[:200]}...")
        
    except Exception as e:
        diag.end_timer("simple_query")
        print(f"❌ Simple query failed: {e}")
        logger.exception("Simple query exception:")
        return
    
    # Test 3: Memory-related query
    print("\n3. Testing memory-related query...")
    diag.start_timer("memory_query")
    
    try:
        logger.info("Starting memory query: 'Remember that I like pizza'")
        response = await agent.arun("Remember that I like pizza")
        diag.end_timer("memory_query")
        
        print(f"✅ Memory query completed in {diag.get_timing('memory_query'):.2f}s")
        print(f"Response type: {type(response)}")
        
        if isinstance(response, RunResponse):
            print("✅ Response is RunResponse type")
            print(f"Response content preview: {str(response.content)[:200]}...")
        else:
            print(f"Response preview: {str(response)[:200]}...")
        
    except Exception as e:
        diag.end_timer("memory_query")
        print(f"❌ Memory query failed: {e}")
        logger.exception("Memory query exception:")
    
    # Test 4: Memory retrieval query (this might be slow)
    print("\n4. Testing memory retrieval query...")
    diag.start_timer("memory_retrieval")
    
    try:
        logger.info("Starting memory retrieval: 'What do you remember about me?'")
        response = await agent.arun("What do you remember about me?")
        diag.end_timer("memory_retrieval")
        
        print(f"✅ Memory retrieval completed in {diag.get_timing('memory_retrieval'):.2f}s")
        print(f"Response type: {type(response)}")
        
        if isinstance(response, RunResponse):
            print("✅ Response is RunResponse type")
            print(f"Response content preview: {str(response.content)[:200]}...")
        else:
            print(f"Response preview: {str(response)[:200]}...")
        
    except Exception as e:
        diag.end_timer("memory_retrieval")
        print(f"❌ Memory retrieval failed: {e}")
        logger.exception("Memory retrieval exception:")
    
    # Test 5: Direct memory access (bypass agent.arun)
    print("\n5. Testing direct memory access...")
    diag.start_timer("direct_memory")
    
    try:
        if hasattr(agent, 'memory') and agent.memory:
            logger.info("Accessing memory directly")
            # Get memories directly from the memory system
            memories = agent.memory.get_user_memories(user_id="default")
            diag.end_timer("direct_memory")
            
            print(f"✅ Direct memory access completed in {diag.get_timing('direct_memory'):.2f}s")
            print(f"Number of memories: {len(memories) if memories else 0}")
        else:
            diag.end_timer("direct_memory")
            print("⚠️  No memory system found on agent")
            
    except Exception as e:
        diag.end_timer("direct_memory")
        print(f"❌ Direct memory access failed: {e}")
        logger.exception("Direct memory access exception:")
    
    # Summary
    print("\n=== DIAGNOSTIC SUMMARY ===")
    print(f"Agent initialization: {diag.get_timing('agent_init'):.2f}s")
    print(f"Simple query: {diag.get_timing('simple_query'):.2f}s")
    print(f"Memory storage query: {diag.get_timing('memory_query'):.2f}s")
    print(f"Memory retrieval query: {diag.get_timing('memory_retrieval'):.2f}s")
    print(f"Direct memory access: {diag.get_timing('direct_memory'):.2f}s")
    
    # Analysis
    memory_retrieval = diag.get_timing('memory_retrieval')
    direct_memory = diag.get_timing('direct_memory')
    simple_query = diag.get_timing('simple_query')
    
    if memory_retrieval > 10 and direct_memory < 2:
        print("\n🔍 DIAGNOSIS: The bottleneck is likely in agent.arun() response parsing/processing")
        print("   - Direct memory access is fast")
        print("   - agent.arun() with memory retrieval is slow")
        print("   - This suggests response parsing or LLM processing overhead")
    elif direct_memory > 5:
        print("\n🔍 DIAGNOSIS: The bottleneck is in the memory system itself")
        print("   - Direct memory access is slow")
        print("   - Memory retrieval/processing needs optimization")
    elif memory_retrieval > simple_query * 5:
        print("\n🔍 DIAGNOSIS: Memory-related queries are significantly slower")
        print("   - Simple queries are fast")
        print("   - Memory queries are slow")
        print("   - This suggests memory processing or LLM reasoning overhead")
    else:
        print("\n✅ DIAGNOSIS: Performance appears normal for basic agno agent")
    
    print("=" * 50)

if __name__ == "__main__":
    try:
        asyncio.run(test_basic_agno_agent())
    except KeyboardInterrupt:
        print("\n⚠️  Test cancelled by user")
    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        logger.exception("Test execution exception:")