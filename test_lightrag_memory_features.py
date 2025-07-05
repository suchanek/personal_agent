#!/usr/bin/env python3
"""
Comprehensive test script for the new LightRAG Memory Knowledge Features.

This script tests the enhanced memory capabilities including:
1. Local Semantic Memory (SQLite-based with SemanticMemoryManager)
2. Graph Memory (LightRAG-based for relationship capture)
3. Knowledge Base Integration (LanceDB + LightRAG)
4. Memory tool integration within the AgnoPersonalAgent
5. Cross-system memory operations and consistency

Usage:
    python test_lightrag_memory_features.py [--use-temp-db] [--skip-lightrag] [--debug]
"""

import asyncio
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

import aiohttp
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

# Import the agent and related components
from src.personal_agent.core.agno_agent import AgnoPersonalAgent, InstructionLevel
from src.personal_agent.config.settings import (
    LIGHTRAG_URL,
    LIGHTRAG_MEMORY_URL,
    USER_ID,
    AGNO_STORAGE_DIR,
)


class LightRAGMemoryTester:
    """Comprehensive tester for the new LightRAG memory knowledge features."""

    def __init__(
        self,
        use_temp_db: bool = True,
        skip_lightrag: bool = False,
        debug: bool = False,
        user_id: str = "test_user_lightrag",
    ):
        """
        Initialize the tester.

        :param use_temp_db: If True, use temporary database for testing
        :param skip_lightrag: If True, skip LightRAG server tests
        :param debug: Enable debug logging
        :param user_id: Test user ID
        """
        self.use_temp_db = use_temp_db
        self.skip_lightrag = skip_lightrag
        self.debug = debug
        self.user_id = user_id
        self.console = Console()
        self.test_results = {}
        
        # Setup storage directories
        if use_temp_db:
            self.temp_dir = tempfile.mkdtemp(prefix="lightrag_test_")
            self.storage_dir = os.path.join(self.temp_dir, "agno")
            self.knowledge_dir = os.path.join(self.temp_dir, "knowledge")
            os.makedirs(self.storage_dir, exist_ok=True)
            os.makedirs(self.knowledge_dir, exist_ok=True)
            self.console.print(f"🗄️  Using temporary storage: {self.temp_dir}")
        else:
            self.storage_dir = AGNO_STORAGE_DIR
            self.knowledge_dir = os.path.join(AGNO_STORAGE_DIR, "knowledge")
            self.console.print(f"🗄️  Using production storage: {self.storage_dir}")

        # Agent instance
        self.agent: Optional[AgnoPersonalAgent] = None

    async def cleanup(self):
        """Clean up test resources."""
        if self.agent:
            await self.agent.cleanup()
            
        if self.use_temp_db and hasattr(self, 'temp_dir'):
            import shutil
            try:
                shutil.rmtree(self.temp_dir)
                self.console.print(f"🧹 Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                self.console.print(f"⚠️  Warning: Could not clean up temp dir: {e}")

    async def run_test(self, test_name: str, test_func) -> bool:
        """
        Run a test and record results.

        :param test_name: Name of the test
        :param test_func: Test function to run
        :return: True if test passed
        """
        self.console.print(f"\n🧪 Running test: [bold cyan]{test_name}[/bold cyan]")
        self.console.print("=" * 60)

        try:
            start_time = time.time()
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
                transient=True,
            ) as progress:
                task = progress.add_task(f"Running {test_name}...", total=None)
                result = await test_func()
                progress.remove_task(task)
            
            duration = time.time() - start_time

            if result:
                self.console.print(f"✅ [bold green]PASSED[/bold green]: {test_name} ({duration:.2f}s)")
                self.test_results[test_name] = {
                    "status": "PASSED",
                    "duration": duration,
                }
                return True
            else:
                self.console.print(f"❌ [bold red]FAILED[/bold red]: {test_name} ({duration:.2f}s)")
                self.test_results[test_name] = {
                    "status": "FAILED",
                    "duration": duration,
                }
                return False

        except Exception as e:
            self.console.print(f"💥 [bold red]ERROR[/bold red] in {test_name}: {e}")
            if self.debug:
                import traceback
                self.console.print(traceback.format_exc())
            self.test_results[test_name] = {"status": "ERROR", "error": str(e)}
            return False

    async def test_lightrag_servers_connectivity(self) -> bool:
        """Test connectivity to both LightRAG servers."""
        if self.skip_lightrag:
            self.console.print("⏭️  Skipping LightRAG server connectivity test")
            return True

        try:
            # Test general knowledge LightRAG server
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(f"{LIGHTRAG_URL}/health", timeout=10) as resp:
                        if resp.status == 200:
                            self.console.print(f"✅ General LightRAG server ({LIGHTRAG_URL}) is accessible")
                            general_ok = True
                        else:
                            self.console.print(f"⚠️  General LightRAG server returned status {resp.status}")
                            general_ok = False
                except Exception as e:
                    self.console.print(f"❌ Cannot connect to general LightRAG server: {e}")
                    general_ok = False

                # Test memory LightRAG server
                try:
                    async with session.get(f"{LIGHTRAG_MEMORY_URL}/health", timeout=10) as resp:
                        if resp.status == 200:
                            self.console.print(f"✅ Memory LightRAG server ({LIGHTRAG_MEMORY_URL}) is accessible")
                            memory_ok = True
                        else:
                            self.console.print(f"⚠️  Memory LightRAG server returned status {resp.status}")
                            memory_ok = False
                except Exception as e:
                    self.console.print(f"❌ Cannot connect to memory LightRAG server: {e}")
                    memory_ok = False

            # Both servers should be accessible for full functionality
            if general_ok and memory_ok:
                return True
            elif general_ok or memory_ok:
                self.console.print("⚠️  Partial connectivity - some tests may be limited")
                return True
            else:
                self.console.print("❌ No LightRAG servers accessible")
                return False

        except Exception as e:
            self.console.print(f"❌ Error testing server connectivity: {e}")
            return False

    async def test_agent_initialization(self) -> bool:
        """Test AgnoPersonalAgent initialization with memory features."""
        try:
            self.agent = AgnoPersonalAgent(
                model_provider="ollama",
                model_name="llama3.1:8b",
                enable_memory=True,
                enable_mcp=False,  # Disable MCP for focused memory testing
                storage_dir=self.storage_dir,
                knowledge_dir=self.knowledge_dir,
                debug=self.debug,
                user_id=self.user_id,
                recreate=False,
                instruction_level=InstructionLevel.STANDARD,
            )

            success = await self.agent.initialize(recreate=False)
            
            if success and self.agent.agent:
                self.console.print("✅ Agent initialized successfully")
                
                # Check memory components
                if self.agent.agno_memory:
                    self.console.print("✅ Local semantic memory (SQLite) initialized")
                else:
                    self.console.print("⚠️  Local semantic memory not initialized")
                
                if self.agent.agno_knowledge:
                    self.console.print("✅ Knowledge base (LanceDB) initialized")
                else:
                    self.console.print("⚠️  Knowledge base not initialized")
                
                # Check available tools
                if hasattr(self.agent.agent, 'tools'):
                    tool_count = len(self.agent.agent.tools)
                    self.console.print(f"✅ Agent has {tool_count} tools available")
                    
                    # Look for memory-related tools
                    memory_tools = []
                    for tool in self.agent.agent.tools:
                        tool_name = getattr(tool, '__name__', str(type(tool).__name__))
                        if any(keyword in tool_name.lower() for keyword in ['memory', 'store', 'query', 'knowledge']):
                            memory_tools.append(tool_name)
                    
                    if memory_tools:
                        self.console.print(f"✅ Found {len(memory_tools)} memory-related tools")
                        if self.debug:
                            for tool in memory_tools:
                                self.console.print(f"   - {tool}")
                    else:
                        self.console.print("⚠️  No memory-related tools found")
                
                return True
            else:
                self.console.print("❌ Agent initialization failed")
                return False

        except Exception as e:
            self.console.print(f"❌ Error initializing agent: {e}")
            if self.debug:
                import traceback
                self.console.print(traceback.format_exc())
            return False

    async def test_local_semantic_memory_operations(self) -> bool:
        """Test local semantic memory operations (SQLite-based)."""
        if not self.agent or not self.agent.agno_memory:
            self.console.print("❌ Agent or memory not initialized")
            return False

        try:
            test_memories = [
                ("I love programming in Python and building AI applications", ["programming", "personal"]),
                ("My favorite food is sushi, especially salmon rolls", ["food", "preferences"]),
                ("I work remotely from my home office in San Francisco", ["work", "location"]),
                ("I have a pet cat named Whiskers who loves to sleep on my keyboard", ["pets", "personal"]),
            ]

            stored_count = 0
            
            # Test storing memories
            self.console.print("📝 Testing local semantic memory storage...")
            for memory_text, topics in test_memories:
                try:
                    # Use the agent's memory manager directly
                    success, message, memory_id = self.agent.agno_memory.memory_manager.add_memory(
                        memory_text=memory_text,
                        db=self.agent.agno_memory.db,
                        user_id=self.user_id,
                        topics=topics,
                    )
                    
                    if success:
                        stored_count += 1
                        self.console.print(f"   ✅ Stored: {memory_text[:50]}... (ID: {memory_id})")
                    else:
                        self.console.print(f"   ⚠️  Rejected: {memory_text[:50]}... ({message})")
                        
                except Exception as e:
                    self.console.print(f"   ❌ Error storing memory: {e}")

            # Test querying memories
            self.console.print("\n🔍 Testing semantic memory search...")
            search_queries = [
                "programming",
                "food preferences", 
                "work location",
                "pets",
            ]

            found_count = 0
            for query in search_queries:
                try:
                    results = self.agent.agno_memory.memory_manager.search_memories(
                        query=query,
                        db=self.agent.agno_memory.db,
                        user_id=self.user_id,
                        limit=5,
                        similarity_threshold=0.3,
                        search_topics=True,
                        topic_boost=0.5,
                    )
                    
                    if results:
                        found_count += 1
                        self.console.print(f"   ✅ Query '{query}': Found {len(results)} results")
                        if self.debug:
                            for memory, score in results[:2]:  # Show top 2
                                self.console.print(f"      - {memory.memory[:60]}... (score: {score:.3f})")
                    else:
                        self.console.print(f"   ⚠️  Query '{query}': No results found")
                        
                except Exception as e:
                    self.console.print(f"   ❌ Error searching for '{query}': {e}")

            # Test memory statistics
            try:
                stats = self.agent.agno_memory.memory_manager.get_memory_stats(
                    db=self.agent.agno_memory.db,
                    user_id=self.user_id
                )
                
                if isinstance(stats, dict) and 'total_memories' in stats:
                    self.console.print(f"📊 Memory stats: {stats['total_memories']} total memories")
                    if self.debug:
                        for key, value in stats.items():
                            if key not in ['duplicate_pairs', 'combined_memory_indices']:
                                self.console.print(f"   {key}: {value}")
                else:
                    self.console.print("⚠️  Could not retrieve memory statistics")
                    
            except Exception as e:
                self.console.print(f"❌ Error getting memory stats: {e}")

            # Success criteria: stored some memories and found some results
            success = stored_count > 0 and found_count > 0
            
            if success:
                self.console.print(f"✅ Local semantic memory test passed: {stored_count} stored, {found_count} queries successful")
            else:
                self.console.print(f"❌ Local semantic memory test failed: {stored_count} stored, {found_count} queries successful")
                
            return success

        except Exception as e:
            self.console.print(f"❌ Error in local semantic memory test: {e}")
            return False

    async def test_graph_memory_operations(self) -> bool:
        """Test graph memory operations (LightRAG-based)."""
        if self.skip_lightrag:
            self.console.print("⏭️  Skipping graph memory operations test")
            return True

        try:
            # Test storing graph memories
            self.console.print("📝 Testing graph memory storage...")
            
            graph_memories = [
                "John Smith is my colleague who works in the marketing department and loves coffee",
                "Sarah Johnson is my neighbor who has two dogs named Max and Luna, and she works as a veterinarian",
                "The coffee shop on Main Street serves excellent espresso and is owned by Maria Rodriguez",
                "My project manager Alice coordinates our team meetings every Tuesday at 2 PM",
            ]

            stored_count = 0
            for memory_text in graph_memories:
                try:
                    url = f"{LIGHTRAG_MEMORY_URL}/documents/text"
                    payload = {
                        "text": memory_text,
                        "document_id": f"test_memory_{int(time.time() * 1000)}"
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, json=payload, timeout=30) as resp:
                            if resp.status == 200:
                                stored_count += 1
                                self.console.print(f"   ✅ Stored graph memory: {memory_text[:50]}...")
                            else:
                                error_text = await resp.text()
                                self.console.print(f"   ❌ Failed to store: {resp.status} - {error_text}")
                                
                except Exception as e:
                    self.console.print(f"   ❌ Error storing graph memory: {e}")

            # Test querying graph memories
            self.console.print("\n🔍 Testing graph memory queries...")
            
            graph_queries = [
                ("Who works in marketing?", "local"),
                ("Tell me about people with pets", "global"),
                ("What do you know about coffee?", "hybrid"),
                ("Who are my colleagues and neighbors?", "mix"),
            ]

            successful_queries = 0
            for query, mode in graph_queries:
                try:
                    url = f"{LIGHTRAG_MEMORY_URL}/query"
                    payload = {
                        "query": query,
                        "mode": mode,
                        "top_k": 5
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, json=payload, timeout=60) as resp:
                            if resp.status == 200:
                                result = await resp.json()
                                
                                # Check for error in response (consistent with new interface)
                                if "error" in result:
                                    self.console.print(f"   ❌ Query '{query}' ({mode}): {result['error']}")
                                else:
                                    response_text = result.get("response", "No response")
                                    
                                    if response_text and len(response_text.strip()) > 10:
                                        successful_queries += 1
                                        self.console.print(f"   ✅ Query '{query}' ({mode}): Got response ({len(response_text)} chars)")
                                        if self.debug:
                                            self.console.print(f"      Response: {response_text[:100]}...")
                                    else:
                                        self.console.print(f"   ⚠️  Query '{query}' ({mode}): Empty or minimal response")
                            else:
                                error_text = await resp.text()
                                self.console.print(f"   ❌ Query '{query}' failed: {resp.status} - {error_text}")
                                
                except Exception as e:
                    self.console.print(f"   ❌ Error querying '{query}': {e}")

            # Test graph labels
            try:
                self.console.print("\n📊 Testing graph labels retrieval...")
                url = f"{LIGHTRAG_MEMORY_URL}/graph/label/list"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=30) as resp:
                        if resp.status == 200:
                            labels = await resp.json()
                            self.console.print(f"   ✅ Retrieved graph labels: {len(labels) if isinstance(labels, list) else 'N/A'}")
                            if self.debug and isinstance(labels, list):
                                self.console.print(f"      Labels: {labels[:5]}...")  # Show first 5
                        else:
                            error_text = await resp.text()
                            self.console.print(f"   ⚠️  Could not retrieve labels: {resp.status} - {error_text}")
                            
            except Exception as e:
                self.console.print(f"   ❌ Error retrieving graph labels: {e}")

            # Success criteria: stored some memories and got some query responses
            success = stored_count > 0 and successful_queries > 0
            
            if success:
                self.console.print(f"✅ Graph memory test passed: {stored_count} stored, {successful_queries} queries successful")
            else:
                self.console.print(f"❌ Graph memory test failed: {stored_count} stored, {successful_queries} queries successful")
                
            return success

        except Exception as e:
            self.console.print(f"❌ Error in graph memory test: {e}")
            return False

    async def test_agent_memory_tools_integration(self) -> bool:
        """Test memory tools integration through the agent."""
        if not self.agent:
            self.console.print("❌ Agent not initialized")
            return False

        try:
            self.console.print("🤖 Testing agent memory tools integration...")
            
            # Test queries that should trigger memory tools
            test_queries = [
                "Remember that I love hiking in the mountains on weekends",
                "What do you remember about my hobbies?",
                "Store this information: I prefer tea over coffee in the morning",
                "Search my memories for information about beverages",
            ]

            successful_interactions = 0
            
            for query in test_queries:
                try:
                    self.console.print(f"\n   🔄 Testing query: '{query}'")
                    
                    # Run the query through the agent
                    response = await self.agent.run(query)
                    
                    if response and len(response.strip()) > 20:
                        successful_interactions += 1
                        self.console.print(f"   ✅ Got response ({len(response)} chars)")
                        
                        # Check if tools were called
                        tool_info = self.agent.get_last_tool_calls()
                        if tool_info.get("has_tool_calls", False):
                            tool_count = tool_info.get("tool_calls_count", 0)
                            self.console.print(f"   🔧 Used {tool_count} tool calls")
                            
                            if self.debug:
                                for tool_detail in tool_info.get("tool_call_details", []):
                                    tool_name = tool_detail.get("function_name", "unknown")
                                    self.console.print(f"      - Called: {tool_name}")
                        else:
                            self.console.print("   ⚠️  No tool calls detected")
                            
                        if self.debug:
                            self.console.print(f"      Response preview: {response[:100]}...")
                    else:
                        self.console.print(f"   ❌ Got minimal or no response")
                        
                except Exception as e:
                    self.console.print(f"   ❌ Error with query '{query}': {e}")

            # Success criteria: most queries should work
            success = successful_interactions >= len(test_queries) * 0.5  # At least 50% success
            
            if success:
                self.console.print(f"✅ Agent memory tools integration passed: {successful_interactions}/{len(test_queries)} successful")
            else:
                self.console.print(f"❌ Agent memory tools integration failed: {successful_interactions}/{len(test_queries)} successful")
                
            return success

        except Exception as e:
            self.console.print(f"❌ Error in agent memory tools integration test: {e}")
            return False

    async def test_knowledge_base_integration(self) -> bool:
        """Test knowledge base integration and search capabilities."""
        if not self.agent or not self.agent.agno_knowledge:
            self.console.print("⚠️  Knowledge base not available, skipping test")
            return True

        try:
            self.console.print("📚 Testing knowledge base integration...")
            
            # Test knowledge base search
            test_queries = [
                "artificial intelligence",
                "machine learning",
                "python programming",
                "data science",
            ]

            successful_searches = 0
            
            for query in test_queries:
                try:
                    results = self.agent.agno_knowledge.search(query=query, num_documents=3)
                    
                    if results and len(results) > 0:
                        successful_searches += 1
                        self.console.print(f"   ✅ Query '{query}': Found {len(results)} results")
                        
                        if self.debug:
                            for i, result in enumerate(results[:2]):  # Show first 2
                                content_preview = result.content[:80] if hasattr(result, 'content') else str(result)[:80]
                                self.console.print(f"      {i+1}. {content_preview}...")
                    else:
                        self.console.print(f"   ⚠️  Query '{query}': No results found")
                        
                except Exception as e:
                    self.console.print(f"   ❌ Error searching for '{query}': {e}")

            # Test through agent (should use knowledge tools automatically)
            try:
                self.console.print("\n   🤖 Testing knowledge search through agent...")
                knowledge_query = "What do you know about machine learning algorithms?"
                response = await self.agent.run(knowledge_query)
                
                if response and len(response.strip()) > 50:
                    self.console.print("   ✅ Agent knowledge query successful")
                    if self.debug:
                        self.console.print(f"      Response preview: {response[:100]}...")
                else:
                    self.console.print("   ⚠️  Agent knowledge query returned minimal response")
                    
            except Exception as e:
                self.console.print(f"   ❌ Error in agent knowledge query: {e}")

            # Success criteria: some searches should work
            success = successful_searches > 0
            
            if success:
                self.console.print(f"✅ Knowledge base integration passed: {successful_searches}/{len(test_queries)} searches successful")
            else:
                self.console.print(f"❌ Knowledge base integration failed: {successful_searches}/{len(test_queries)} searches successful")
                
            return success

        except Exception as e:
            self.console.print(f"❌ Error in knowledge base integration test: {e}")
            return False

    async def test_cross_system_memory_consistency(self) -> bool:
        """Test consistency and interaction between different memory systems."""
        if not self.agent:
            self.console.print("❌ Agent not initialized")
            return False

        try:
            self.console.print("🔄 Testing cross-system memory consistency...")
            
            # Store the same information in different systems and see how they interact
            test_info = "Alice is my project manager who schedules our team meetings every Tuesday at 2 PM in the conference room"
            
            # Store in local semantic memory
            local_stored = False
            if self.agent.agno_memory:
                try:
                    success, message, memory_id = self.agent.agno_memory.memory_manager.add_memory(
                        memory_text=test_info,
                        db=self.agent.agno_memory.db,
                        user_id=self.user_id,
                        topics=["work", "meetings", "colleagues"],
                    )
                    local_stored = success
                    if success:
                        self.console.print("   ✅ Stored in local semantic memory")
                    else:
                        self.console.print(f"   ⚠️  Local storage: {message}")
                except Exception as e:
                    self.console.print(f"   ❌ Error storing in local memory: {e}")

            # Store in graph memory
            graph_stored = False
            if not self.skip_lightrag:
                try:
                    url = f"{LIGHTRAG_MEMORY_URL}/documents/text"
                    payload = {
                        "text": test_info,
                        "document_id": f"consistency_test_{int(time.time() * 1000)}"
                    }
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.post(url, json=payload, timeout=30) as resp:
                            graph_stored = resp.status == 200
                            if graph_stored:
                                self.console.print("   ✅ Stored in graph memory")
                            else:
                                error_text = await resp.text()
                                self.console.print(f"   ❌ Graph storage failed: {resp.status} - {error_text}")
                                
                except Exception as e:
                    self.console.print(f"   ❌ Error storing in graph memory: {e}")

            # Test queries that should find the information in both systems
            self.console.print("\n   🔍 Testing cross-system retrieval...")
            
            test_queries = [
                "Who is Alice?",
                "When are our team meetings?",
                "Tell me about my project manager",
            ]

            successful_retrievals = 0
            
            for query in test_queries:
                try:
                    # Query through agent (should use multiple systems)
                    response = await self.agent.run(query)
                    
                    if response and "alice" in response.lower():
                        successful_retrievals += 1
                        self.console.print(f"   ✅ Query '{query}': Found relevant information")
                        
                        # Check which tools were used
                        tool_info = self.agent.get_last_tool_calls()
                        if tool_info.get("has_tool_calls", False):
                            memory_tools_used = []
                            for tool_detail in tool_info.get("tool_call_details", []):
                                tool_name = tool_detail.get("function_name", "unknown")
                                if "memory" in tool_name.lower() or "query" in tool_name.lower():
                                    memory_tools_used.append(tool_name)
                            
                            if memory_tools_used and self.debug:
                                self.console.print(f"      Memory tools used: {', '.join(memory_tools_used)}")
                    else:
                        self.console.print(f"   ⚠️  Query '{query}': No relevant information found")
                        
                except Exception as e:
                    self.console.print(f"   ❌ Error with query '{query}': {e}")

            # Success criteria: stored in at least one system and retrieved successfully
            storage_success = local_stored or graph_stored
            retrieval_success = successful_retrievals > 0
            
            success = storage_success and retrieval_success
            
            if success:
                self.console.print(f"✅ Cross-system consistency passed: Storage OK, {successful_retrievals} retrievals successful")
            else:
                self.console.print(f"❌ Cross-system consistency failed: Storage: {storage_success}, Retrievals: {successful_retrievals}")
                
            return success

        except Exception as e:
            self.console.print(f"❌ Error in cross-system consistency test: {e}")
            return False

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        self.console.print(Panel.fit(
            "[bold blue]🚀 LightRAG Memory Knowledge Features Test Suite[/bold blue]\n"
            "Testing enhanced memory capabilities including semantic memory,\n"
            "graph memory, knowledge base integration, and cross-system operations.",
            title="Test Suite",
            border_style="blue"
        ))

        tests = [
            ("LightRAG Servers Connectivity", self.test_lightrag_servers_connectivity),
            ("Agent Initialization", self.test_agent_initialization),
            ("Local Semantic Memory Operations", self.test_local_semantic_memory_operations),
            ("Graph Memory Operations", self.test_graph_memory_operations),
            ("Agent Memory Tools Integration", self.test_agent_memory_tools_integration),
            ("Knowledge Base Integration", self.test_knowledge_base_integration),
            ("Cross-System Memory Consistency", self.test_cross_system_memory_consistency),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            if await self.run_test(test_name, test_func):
                passed += 1

        # Print comprehensive summary
        self.print_test_summary(passed, total)

        return {
            "total_tests": total,
            "passed_tests": passed,
            "success_rate": passed / total if total > 0 else 0,
            "details": self.test_results,
        }

    def print_test_summary(self, passed: int, total: int):
        """Print a comprehensive test summary with Rich formatting."""
        self.console.print("\n" + "=" * 80)
        
        # Create summary table
        summary_table = Table(
            title="🏁 Test Results Summary",
            show_header=True,
            header_style="bold magenta",
            border_style="blue"
        )
        summary_table.add_column("Test Name", style="cyan", no_wrap=False)
        summary_table.add_column("Status", style="white", justify="center")
        summary_table.add_column("Duration", style="green", justify="right")
        summary_table.add_column("Details", style="yellow")

        for test_name, result in self.test_results.items():
            status = result["status"]
            
            # Status with emoji
            if status == "PASSED":
                status_display = "✅ PASSED"
                status_style = "bold green"
            elif status == "FAILED":
                status_display = "❌ FAILED"
                status_style = "bold red"
            else:
                status_display = "💥 ERROR"
                status_style = "bold red"

            # Duration
            duration = result.get("duration", 0)
            duration_display = f"{duration:.2f}s" if duration > 0 else "N/A"

            # Details
            if status == "ERROR":
                details = result.get("error", "Unknown error")[:50] + "..."
            else:
                details = "OK"

            summary_table.add_row(
                test_name,
                f"[{status_style}]{status_display}[/{status_style}]",
                duration_display,
                details
            )

        self.console.print(summary_table)

        # Overall results
        success_rate = (passed / total * 100) if total > 0 else 0
        
        if passed == total:
            result_panel = Panel.fit(
                f"[bold green]🎉 ALL TESTS PASSED![/bold green]\n"
                f"Successfully completed {passed}/{total} tests ({success_rate:.1f}%)\n"
                f"LightRAG Memory Knowledge Features are working correctly!",
                title="Success",
                border_style="green"
            )
        elif success_rate >= 80:
            result_panel = Panel.fit(
                f"[bold yellow]⚠️  MOSTLY SUCCESSFUL[/bold yellow]\n"
                f"Passed {passed}/{total} tests ({success_rate:.1f}%)\n"
                f"System is mostly functional with minor issues.",
                title="Partial Success",
                border_style="yellow"
            )
        else:
            result_panel = Panel.fit(
                f"[bold red]❌ MULTIPLE FAILURES[/bold red]\n"
                f"Passed {passed}/{total} tests ({success_rate:.1f}%)\n"
                f"System needs attention before production use.",
                title="Issues Detected",
                border_style="red"
            )

        self.console.print(result_panel)


async def main():
    """Main test execution function."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Comprehensive LightRAG Memory Knowledge Features Test"
    )
    parser.add_argument(
        "--use-temp-db",
        action="store_true",
        default=True,
        help="Use temporary database for testing (default: True)",
    )
    parser.add_argument(
        "--use-prod-db",
        action="store_true",
        help="Use production database for testing (overrides --use-temp-db)",
    )
    parser.add_argument(
        "--skip-lightrag",
        action="store_true",
        help="Skip LightRAG server tests (useful when servers are not running)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging and verbose output",
    )
    parser.add_argument(
        "--user-id",
        default="test_user_lightrag",
        help="Test user ID to use (default: test_user_lightrag)",
    )

    args = parser.parse_args()

    use_temp_db = not args.use_prod_db

    if not use_temp_db:
        console = Console()
        console.print(
            Panel.fit(
                "[bold red]⚠️  WARNING[/bold red]\n"
                "You're about to test with the PRODUCTION database.\n"
                "This may create test data in your production system.",
                title="Production Database Warning",
                border_style="red"
            )
        )
        response = input("Continue? (y/N): ")
        if response.lower() != "y":
            print("Aborted.")
            return

    # Create and run tester
    tester = LightRAGMemoryTester(
        use_temp_db=use_temp_db,
        skip_lightrag=args.skip_lightrag,
        debug=args.debug,
        user_id=args.user_id,
    )

    try:
        results = await tester.run_all_tests()

        # Exit with appropriate code
        success_rate = results["success_rate"]
        if success_rate == 1.0:
            exit_code = 0  # All tests passed
        elif success_rate >= 0.8:
            exit_code = 1  # Most tests passed
        else:
            exit_code = 2  # Many failures

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        sys.exit(130)
    except Exception as e:
        console = Console()
        console.print(f"\n💥 [bold red]Unexpected error during testing:[/bold red] {e}")
        if args.debug:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(3)
    finally:
        await tester.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
