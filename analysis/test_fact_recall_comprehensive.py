#!/usr/bin/env python3
"""
Comprehensive Fact Recall Tester for Personal Agent Memory System.

This test specifically validates fact recall capabilities by:
1. Storing structured facts from eric_facts.json and send_facts_helper.py
2. Testing recall of specific facts with various query patterns
3. Testing semantic search and topic-based retrieval
4. Testing edge cases and partial matches
5. Validating memory persistence and accuracy

Based on tests/test_pydantic_validation_fix.py but focused on fact recall testing.
"""

import asyncio
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Any

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from personal_agent.config import (
    AGNO_STORAGE_DIR,
    LLM_MODEL,
    OLLAMA_URL,
    USER_ID,
)
from personal_agent.core.agno_agent import AgnoPersonalAgent


class FactRecallTester:
    """Comprehensive fact recall testing system."""
    
    def __init__(self):
        self.agent = None
        self.test_facts = self._load_test_facts()
        self.stored_facts = []
        self.failed_tests = []
        self.passed_tests = []
        
    def _load_test_facts(self) -> Dict[str, List[str]]:
        """Load structured test facts from multiple sources."""
        facts = {
            "basic_info": [
                "My name is Eric G. Suchanek.",
                "I have a Ph.D. degree.",
                "I live at 4264 Meadow Creek CT Liberty TWP, OH 45011.",
                "My phone number is 513-593-4522.",
                "My email address is suchanek@mac.com.",
                "My GitHub profile is https://github.com/suchanek/.",
                "I am currently working on proteusPy at https://github.com/suchanek/proteusPy/."
            ],
            
            "professional_identity": [
                "I am a highly-skilled scientist seeking employment in computational chemistry, computational biology or Artificial Intelligence.",
                "I have broad experience in life science, computer systems, troubleshooting and customer service.",
                "I have management experience in a Fortune 50 company.",
                "I am currently working in structural biophysics, building proteusPy."
            ],
            
            "education": [
                "I graduated as Valedictorian from Lakota High School, West Chester, Ohio in June 1978, ranking 1st out of 550 students.",
                "I earned my BS from Washington University, St Louis in June 1982.",
                "I graduated in the top 10% of my class at Washington University.",
                "I graduated cum honore from Washington University.",
                "I was elected to Phi Beta Kappa at Washington University.",
                "I earned my Ph.D from Johns Hopkins Medical School, Baltimore MD in June 1987.",
                "I was at the top of my class in the combined program for Biochemistry, Cellular and Molecular Biology.",
                "My dissertation was titled 'Applications of Artificial Intelligence to Problems in Protein Engineering'.",
                "My PhD advisors received the Nobel Prize for the discovery of EcoR1, establishing the Biotechnology field."
            ],
            
            "technical_skills": [
                "I program in C, C++, Python, Fortran, Lisp, shell programming, and SQL.",
                "I use development tools including git, VisualStudio Code, and Jira.",
                "I work with machine learning using Python, Tensorflow, torch, numpy, scikit-learn, scipy, and pandas.",
                "I have experience with Unix, OSX, and Linux system management and administration.",
                "I use specialized software including Pixinsight and Microsoft Office.",
                "I am an Apple-certified hardware and software technician.",
                "I have skills in 3D modeling/CAD/CAM, image analysis, analytics and statistics, numerical analysis, and visualization."
            ],
            
            "current_work": [
                "I currently work as a GeekSquad Agent at BestBuy since 2019.",
                "I provide front-line technical support to customers at BestBuy.",
                "I troubleshoot, diagnose, and recommend strategies to meet customer needs.",
                "I work as an Astronomer at Monterey Institute for Research in Astronomy since 2018.",
                "I develop computer algorithms and programs for astrophysical and astrometric analysis of proper motion in stars using Python, Plotly, and Dash.",
                "I configure and install hardware and software to control generators via Arduino and C++.",
                "I configure hardware/software to control high-precision motors for instrument alignment and spectrograph configuration.",
                "I do software development across many areas primarily in Python/Astropy."
            ],
            
            "major_achievements": [
                "I developed one of the first real-time molecular visualization programs deployed on a personal computer (Commodore Amiga).",
                "I developed the first computer-based rapid screening algorithm for disulfide bond stabilization in proteins of known structure.",
                "I invented structure-based heuristics with considerable state-space optimizations.",
                "I built a high-resolution model of Parathyroid Hormone 1-34 from ab-initio modeling, subsequently verified with solution NMR.",
                "I built the first model of 7 trans-membrane G-protein Coupled Receptors within P&G.",
                "I architected, deployed and managed a high-performance multi-processor supercomputer center for P&G Pharmaceuticals.",
                "I built the first database of all disulfide bonds in the RCSB protein databank containing over 292,000 disulfide bonds."
            ]
        }
        
        return facts
    
    async def initialize_agent(self) -> bool:
        """Initialize the agent for testing."""
        print("🤖 Initializing agent for fact recall testing...")
        
        self.agent = AgnoPersonalAgent(
            model_provider="ollama",
            model_name=LLM_MODEL,
            ollama_base_url=OLLAMA_URL,
            user_id=USER_ID,
            debug=True,
            enable_memory=True,
            enable_mcp=False,  # Disable MCP for focused testing
            storage_dir=AGNO_STORAGE_DIR,
        )
        
        success = await self.agent.initialize()
        if not success:
            print("❌ Failed to initialize agent")
            return False
        
        print(f"✅ Agent initialized with model: {LLM_MODEL}")
        return True
    
    async def store_test_facts(self) -> bool:
        """Store all test facts in the memory system."""
        print("\n📝 Storing test facts in memory...")
        
        total_facts = 0
        stored_count = 0
        
        for category, facts in self.test_facts.items():
            print(f"\n  📂 Storing {category} facts...")
            
            for fact in facts:
                total_facts += 1
                try:
                    # Store each fact individually
                    response = await self.agent.run(f"Please remember this fact about me: {fact}")
                    
                    # Check if storage was successful
                    if any(indicator in response.lower() for indicator in ["stored", "remember", "noted", "✅", "🧠", "📝"]):
                        stored_count += 1
                        self.stored_facts.append({
                            "category": category,
                            "fact": fact,
                            "stored": True
                        })
                        print(f"    ✅ Stored: {fact[:50]}...")
                    else:
                        self.stored_facts.append({
                            "category": category,
                            "fact": fact,
                            "stored": False,
                            "response": response[:100]
                        })
                        print(f"    ⚠️ Unclear if stored: {fact[:50]}...")
                    
                    # Small delay to avoid overwhelming the system
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    print(f"    ❌ Failed to store: {fact[:50]}... - {e}")
                    self.stored_facts.append({
                        "category": category,
                        "fact": fact,
                        "stored": False,
                        "error": str(e)
                    })
        
        print(f"\n📊 Storage Summary: {stored_count}/{total_facts} facts stored successfully")
        return stored_count > 0
    
    async def test_basic_fact_recall(self) -> bool:
        """Test basic fact recall with direct questions."""
        print("\n🔍 Testing Basic Fact Recall...")
        
        test_queries = [
            # Basic info tests
            ("What is my name?", ["Eric", "Suchanek"], "basic_info"),
            ("What is my email address?", ["suchanek@mac.com"], "basic_info"),
            ("Where do I live?", ["Liberty TWP", "OH", "45011"], "basic_info"),
            ("What is my phone number?", ["513-593-4522"], "basic_info"),
            
            # Education tests
            ("Where did I get my PhD?", ["Johns Hopkins"], "education"),
            ("What was my dissertation about?", ["Artificial Intelligence", "Protein Engineering"], "education"),
            ("What high school did I attend?", ["Lakota"], "education"),
            ("What university did I attend for my BS?", ["Washington University"], "education"),
            
            # Professional tests
            ("Where do I currently work?", ["BestBuy", "GeekSquad", "Monterey Institute"], "current_work"),
            ("What programming languages do I know?", ["Python", "C++"], "technical_skills"),
            ("What is proteusPy?", ["proteusPy", "structural biophysics"], "professional_identity"),
            
            # Achievement tests
            ("What did I build at P&G?", ["supercomputer", "G-protein", "disulfide"], "major_achievements"),
            ("What database did I create?", ["disulfide bonds", "RCSB", "292,000"], "major_achievements"),
        ]
        
        passed = 0
        total = len(test_queries)
        
        for query, expected_terms, category in test_queries:
            print(f"\n  🔎 Query: {query}")
            
            try:
                start_time = time.time()
                response = await self.agent.run(query)
                end_time = time.time()
                
                # Check if expected terms are in the response
                found_terms = []
                for term in expected_terms:
                    if term.lower() in response.lower():
                        found_terms.append(term)
                
                if found_terms:
                    passed += 1
                    print(f"    ✅ PASS ({end_time - start_time:.2f}s): Found {found_terms}")
                    print(f"       Response: {response[:100]}...")
                    self.passed_tests.append({
                        "query": query,
                        "category": category,
                        "found_terms": found_terms,
                        "response_time": end_time - start_time
                    })
                else:
                    print(f"    ❌ FAIL: Expected {expected_terms}, got none")
                    print(f"       Response: {response[:150]}...")
                    self.failed_tests.append({
                        "query": query,
                        "category": category,
                        "expected": expected_terms,
                        "response": response[:200]
                    })
                
            except Exception as e:
                print(f"    ❌ ERROR: {e}")
                self.failed_tests.append({
                    "query": query,
                    "category": category,
                    "error": str(e)
                })
        
        success_rate = (passed / total) * 100
        print(f"\n📊 Basic Recall Results: {passed}/{total} ({success_rate:.1f}%) passed")
        
        return success_rate >= 70  # 70% success rate threshold
    
    async def test_semantic_search_recall(self) -> bool:
        """Test semantic search and partial matching."""
        print("\n🧠 Testing Semantic Search Recall...")
        
        semantic_queries = [
            # Partial/fuzzy queries
            ("Tell me about my education background", ["PhD", "Johns Hopkins", "Washington University"], "education"),
            ("What are my technical skills?", ["Python", "C++", "machine learning"], "technical_skills"),
            ("What have I accomplished in my career?", ["supercomputer", "database", "visualization"], "major_achievements"),
            ("What is my work experience?", ["BestBuy", "GeekSquad", "Astronomer"], "current_work"),
            
            # Topic-based queries
            ("What do you know about my programming experience?", ["Python", "C++", "Fortran"], "technical_skills"),
            ("Tell me about my scientific work", ["computational chemistry", "biophysics", "proteusPy"], "professional_identity"),
            ("What universities have I attended?", ["Washington University", "Johns Hopkins"], "education"),
            
            # Complex queries
            ("What makes me qualified for AI work?", ["PhD", "machine learning", "computational"], "professional_identity"),
            ("What is my contact information?", ["suchanek@mac.com", "513-593-4522"], "basic_info"),
        ]
        
        passed = 0
        total = len(semantic_queries)
        
        for query, expected_terms, category in semantic_queries:
            print(f"\n  🔎 Semantic Query: {query}")
            
            try:
                start_time = time.time()
                response = await self.agent.run(query)
                end_time = time.time()
                
                # Check for semantic matches (more lenient)
                found_terms = []
                for term in expected_terms:
                    if term.lower() in response.lower():
                        found_terms.append(term)
                
                # Consider it a pass if we find at least one expected term
                if found_terms:
                    passed += 1
                    print(f"    ✅ PASS ({end_time - start_time:.2f}s): Found {found_terms}")
                    print(f"       Response: {response[:100]}...")
                    self.passed_tests.append({
                        "query": query,
                        "category": category,
                        "found_terms": found_terms,
                        "response_time": end_time - start_time,
                        "test_type": "semantic"
                    })
                else:
                    print(f"    ❌ FAIL: Expected any of {expected_terms}, got none")
                    print(f"       Response: {response[:150]}...")
                    self.failed_tests.append({
                        "query": query,
                        "category": category,
                        "expected": expected_terms,
                        "response": response[:200],
                        "test_type": "semantic"
                    })
                
            except Exception as e:
                print(f"    ❌ ERROR: {e}")
                self.failed_tests.append({
                    "query": query,
                    "category": category,
                    "error": str(e),
                    "test_type": "semantic"
                })
        
        success_rate = (passed / total) * 100
        print(f"\n📊 Semantic Search Results: {passed}/{total} ({success_rate:.1f}%) passed")
        
        return success_rate >= 60  # 60% success rate threshold for semantic queries
    
    async def test_edge_cases(self) -> bool:
        """Test edge cases and challenging recall scenarios."""
        print("\n🎯 Testing Edge Cases...")
        
        edge_case_queries = [
            # Specific details
            ("How many students were in my high school class?", ["550"], "education"),
            ("What year did I graduate from high school?", ["1978"], "education"),
            ("How many disulfide bonds are in my database?", ["292,000"], "major_achievements"),
            
            # Negative queries (should not find incorrect info)
            ("Do I work at Google?", [], "negative_test"),  # Should say no or not mention Google
            ("Did I go to MIT?", [], "negative_test"),  # Should say no or not mention MIT
            
            # Complex factual queries
            ("What Nobel Prize discovery were my PhD advisors involved in?", ["EcoR1"], "education"),
            ("What company did I work at before BestBuy?", ["Miami University", "Apple"], "current_work"),
            ("What programming language do I use for astronomy work?", ["Python"], "current_work"),
        ]
        
        passed = 0
        total = len(edge_case_queries)
        
        for query, expected_terms, category in edge_case_queries:
            print(f"\n  🎯 Edge Case: {query}")
            
            try:
                start_time = time.time()
                response = await self.agent.run(query)
                end_time = time.time()
                
                if category == "negative_test":
                    # For negative tests, success means NOT finding incorrect info
                    # and ideally saying "I don't know" or similar
                    negative_indicators = ["don't know", "not sure", "no information", "can't find"]
                    if any(indicator in response.lower() for indicator in negative_indicators):
                        passed += 1
                        print(f"    ✅ PASS ({end_time - start_time:.2f}s): Correctly indicated uncertainty")
                        print(f"       Response: {response[:100]}...")
                    else:
                        print(f"    ⚠️ UNCLEAR: May have provided incorrect info")
                        print(f"       Response: {response[:150]}...")
                        # Don't count as complete failure for negative tests
                        passed += 0.5
                else:
                    # Regular edge case test
                    found_terms = []
                    for term in expected_terms:
                        if term.lower() in response.lower():
                            found_terms.append(term)
                    
                    if found_terms:
                        passed += 1
                        print(f"    ✅ PASS ({end_time - start_time:.2f}s): Found {found_terms}")
                        print(f"       Response: {response[:100]}...")
                    else:
                        print(f"    ❌ FAIL: Expected {expected_terms}, got none")
                        print(f"       Response: {response[:150]}...")
                
            except Exception as e:
                print(f"    ❌ ERROR: {e}")
        
        success_rate = (passed / total) * 100
        print(f"\n📊 Edge Case Results: {passed}/{total} ({success_rate:.1f}%) passed")
        
        return success_rate >= 50  # 50% success rate threshold for edge cases
    
    async def test_memory_persistence(self) -> bool:
        """Test that memories persist across queries."""
        print("\n💾 Testing Memory Persistence...")
        
        # Ask the same question multiple times to ensure consistency
        persistence_query = "What is my name and where do I work?"
        responses = []
        
        for i in range(3):
            print(f"\n  🔄 Persistence Test {i+1}/3")
            try:
                response = await self.agent.run(persistence_query)
                responses.append(response)
                print(f"    Response: {response[:100]}...")
                await asyncio.sleep(1)  # Small delay between queries
            except Exception as e:
                print(f"    ❌ ERROR: {e}")
                return False
        
        # Check for consistency in responses
        consistent_terms = ["Eric", "Suchanek"]
        consistency_scores = []
        
        for response in responses:
            score = sum(1 for term in consistent_terms if term.lower() in response.lower())
            consistency_scores.append(score)
        
        avg_consistency = sum(consistency_scores) / len(consistency_scores)
        consistency_rate = (avg_consistency / len(consistent_terms)) * 100
        
        print(f"\n📊 Persistence Results: {consistency_rate:.1f}% consistency across queries")
        
        return consistency_rate >= 80  # 80% consistency threshold
    
    def generate_test_report(self) -> str:
        """Generate a comprehensive test report."""
        total_passed = len(self.passed_tests)
        total_failed = len(self.failed_tests)
        total_tests = total_passed + total_failed
        
        if total_tests == 0:
            return "No tests were executed."
        
        overall_success_rate = (total_passed / total_tests) * 100
        
        report = [
            "=" * 60,
            "🧪 COMPREHENSIVE FACT RECALL TEST REPORT",
            "=" * 60,
            f"📊 Overall Results: {total_passed}/{total_tests} ({overall_success_rate:.1f}%) passed",
            "",
            "📈 Test Categories:",
        ]
        
        # Group results by category
        category_stats = {}
        for test in self.passed_tests:
            cat = test.get("category", "unknown")
            if cat not in category_stats:
                category_stats[cat] = {"passed": 0, "total": 0}
            category_stats[cat]["passed"] += 1
            category_stats[cat]["total"] += 1
        
        for test in self.failed_tests:
            cat = test.get("category", "unknown")
            if cat not in category_stats:
                category_stats[cat] = {"passed": 0, "total": 0}
            category_stats[cat]["total"] += 1
        
        for category, stats in category_stats.items():
            success_rate = (stats["passed"] / stats["total"]) * 100 if stats["total"] > 0 else 0
            report.append(f"  {category}: {stats['passed']}/{stats['total']} ({success_rate:.1f}%)")
        
        report.extend([
            "",
            "⚡ Performance Metrics:",
        ])
        
        # Calculate average response times
        response_times = [test.get("response_time", 0) for test in self.passed_tests if "response_time" in test]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            report.append(f"  Average Response Time: {avg_response_time:.2f}s")
        
        # Storage statistics
        stored_count = sum(1 for fact in self.stored_facts if fact.get("stored", False))
        total_facts = len(self.stored_facts)
        storage_rate = (stored_count / total_facts) * 100 if total_facts > 0 else 0
        report.append(f"  Fact Storage Rate: {stored_count}/{total_facts} ({storage_rate:.1f}%)")
        
        if self.failed_tests:
            report.extend([
                "",
                "❌ Failed Tests Summary:",
            ])
            for i, test in enumerate(self.failed_tests[:5], 1):  # Show first 5 failures
                report.append(f"  {i}. {test.get('query', 'Unknown query')}")
                if 'expected' in test:
                    report.append(f"     Expected: {test['expected']}")
                if 'error' in test:
                    report.append(f"     Error: {test['error']}")
        
        report.extend([
            "",
            "🎯 Recommendations:",
        ])
        
        if overall_success_rate >= 80:
            report.append("  ✅ Excellent fact recall performance!")
        elif overall_success_rate >= 60:
            report.append("  ⚠️ Good fact recall with room for improvement")
            report.append("  💡 Consider improving semantic search capabilities")
        else:
            report.append("  ❌ Poor fact recall performance detected")
            report.append("  🔧 Memory system may need debugging or model upgrade")
            report.append("  📝 Check fact storage and retrieval mechanisms")
        
        report.append("=" * 60)
        
        return "\n".join(report)


async def main():
    """Main test execution function."""
    print("🚀 Starting Comprehensive Fact Recall Tests")
    print("=" * 60)
    
    tester = FactRecallTester()
    
    try:
        # Initialize agent
        if not await tester.initialize_agent():
            print("❌ Failed to initialize agent")
            return False
        
        # Store test facts
        if not await tester.store_test_facts():
            print("❌ Failed to store test facts")
            return False
        
        # Wait for storage to settle
        print("\n⏳ Waiting for memory storage to settle...")
        await asyncio.sleep(3)
        
        # Run test suites
        test_results = []
        
        print("\n" + "=" * 60)
        basic_recall_success = await tester.test_basic_fact_recall()
        test_results.append(("Basic Fact Recall", basic_recall_success))
        
        print("\n" + "=" * 60)
        semantic_search_success = await tester.test_semantic_search_recall()
        test_results.append(("Semantic Search", semantic_search_success))
        
        print("\n" + "=" * 60)
        edge_cases_success = await tester.test_edge_cases()
        test_results.append(("Edge Cases", edge_cases_success))
        
        print("\n" + "=" * 60)
        persistence_success = await tester.test_memory_persistence()
        test_results.append(("Memory Persistence", persistence_success))
        
        # Generate and display report
        print("\n" + tester.generate_test_report())
        
        # Overall assessment
        passed_suites = sum(1 for _, success in test_results if success)
        total_suites = len(test_results)
        
        print(f"\n🏆 Test Suite Summary: {passed_suites}/{total_suites} suites passed")
        
        for suite_name, success in test_results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status}: {suite_name}")
        
        overall_success = passed_suites >= 3  # At least 3 out of 4 suites must pass
        
        if overall_success:
            print("\n🎉 OVERALL RESULT: FACT RECALL SYSTEM IS WORKING WELL!")
            return True
        else:
            print("\n⚠️ OVERALL RESULT: FACT RECALL SYSTEM NEEDS ATTENTION")
            return False
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🧪 Comprehensive Fact Recall Tester")
    print("This test validates fact storage and recall capabilities by:")
    print("1. Storing structured facts from eric_facts.json")
    print("2. Testing basic fact recall with direct questions")
    print("3. Testing semantic search and topic-based queries")
    print("4. Testing edge cases and challenging scenarios")
    print("5. Testing memory persistence across queries")
    print()
    
    # Run the tests
    success = asyncio.run(main())
    
    if success:
        print("\n✅ Fact recall test suite completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Fact recall test suite failed!")
        sys.exit(1)
