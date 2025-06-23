#!/usr/bin/env python3
"""
Script to systematically feed individual facts to the Personal Agent one by one.
This script sends each fact separately and monitors success for each individual fact.
"""

import argparse
import asyncio
import sys
import time
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

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
        description="Individual Facts Feeder for Personal Agent"
    )
    parser.add_argument(
        "--remote", action="store_true", help="Use remote Ollama URL instead of local"
    )
    parser.add_argument(
        "categories",
        nargs="*",
        help="Categories to send (all, test, fast, slow, or specific category names)",
    )
    return parser.parse_args()


def get_all_individual_facts():
    """Return all individual facts as a flat list with category labels."""

    facts_by_category = {
        "basic_info": [
            "My name is Eric G. Suchanek.",
            "I have a Ph.D. degree.",
            "I live at 4264 Meadow Creek CT Liberty TWP, OH 45011.",
            "My phone number is 513-593-4522.",
            "My email address is suchanek@mac.com.",
            "My GitHub profile is https://github.com/suchanek/.",
            "I am currently working on proteusPy at https://github.com/suchanek/proteusPy/.",
        ],
        "professional_identity": [
            "I am a highly-skilled scientist seeking employment in computational chemistry, computational biology or Artificial Intelligence.",
            "I have broad experience in life science, computer systems, troubleshooting and customer service.",
            "I have management experience in a Fortune 50 company.",
            "I am currently working in structural biophysics, building proteusPy.",
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
            "My PhD advisors received the Nobel Prize for the discovery of EcoR1, establishing the Biotechnology field.",
        ],
        "technical_skills": [
            "I program in C, C++, Python, Fortran, Lisp, shell programming, and SQL.",
            "I use development tools including git, VisualStudio Code, and Jira.",
            "I work with machine learning using Python, Tensorflow, torch, numpy, scikit-learn, scipy, and pandas.",
            "I have experience with Unix, OSX, and Linux system management and administration.",
            "I use specialized software including Pixinsight and Microsoft Office.",
            "I am an Apple-certified hardware and software technician.",
            "I have skills in 3D modeling/CAD/CAM, image analysis, analytics and statistics, numerical analysis, and visualization.",
        ],
        "current_work": [
            "I currently work as a GeekSquad Agent at BestBuy since 2019.",
            "I provide front-line technical support to customers at BestBuy.",
            "I troubleshoot, diagnose, and recommend strategies to meet customer needs.",
            "I do software development across many areas primarily in Python",
        ],
        "major_achievements": [
            "I developed one of the first real-time molecular visualization programs deployed on a personal computer (Commodore Amiga).",
            "I developed the first computer-based rapid screening algorithm for disulfide bond stabilization in proteins of known structure.",
            "I invented structure-based heuristics with considerable state-space optimizations.",
            "I built a high-resolution model of Parathyroid Hormone 1-34 from ab-initio modeling, subsequently verified with solution NMR.",
            "I built the first model of 7 trans-membrane G-protein Coupled Receptors within P&G.",
            "I architected, deployed and managed a high-performance multi-processor supercomputer center for P&G Pharmaceuticals.",
            "I built the first database of all disulfide bonds in the RCSB protein databank containing over 292,000 disulfide bonds.",
        ],
        "previous_work": [
            "I worked as an Astronomer at Monterey Institute for Research in Astronomy since 2018.",
            "I developed computer algorithms and programs for astrophysical and astrometric analysis of proper motion in stars using Python, Plotly, and Dash.",
            "I configureed and install hardware and software to control generators via Arduino and C++.",
            "I configureed hardware/software to control high-precision motors for instrument alignment and spectrograph configuration.",
            "I worked as Support Desk Analyst II at Miami University, Oxford OH from 2013-2017.",
            "I provided front-line help desk support for IT-related technical issues at Miami University.",
            "I did knowledge management across multiple end-user and internal services at Miami University.",
            "I performed Mac computer repair for Macbook Pro, iMac and Macbook computers at Miami University.",
            "I worked as a Genius at Apple Computer, Kenwood OH from 2010-2013.",
            "I provided 'Genius Bar' one-on-one troubleshooting for over 11,000 customer sessions at Apple.",
            "I consistently achieved top customer feedback scores at Apple.",
            "I was recognized for excellent problem solving skills and management of difficult customer interactions at Apple.",
            "I worked as Director at Procter & Gamble from 2007-2010, leading the Global Modeling Community within P&G Corporate Functions R&D.",
            "I worked as Director, Research Computing and Informatics at Procter & Gamble Pharmaceuticals from 2000-2007.",
            "I designed, implemented and supported a Silicon Graphics supercomputing center at P&G Pharmaceuticals.",
            "I maintained greater than 99% uptime while running the scientific computing network at P&G Pharmaceuticals.",
            "I deployed over 90 SGI workstations for divisional chemists at P&G Pharmaceuticals.",
            "I was the lead molecular modeler within the Discovery division at P&G Pharmaceuticals.",
            "I managed the Research Computing and Informatics Section at P&G Pharmaceuticals.",
            "I worked as Senior Scientist at Procter & Gamble from 1992-2000, applying computational chemistry and bioinformatics to business problems.",
            "I worked as Scientist/Senior Scientist at Procter & Gamble from 1987-1992 in the Management Systems Division (MSD).",
            "I worked on The Builder Advisor project, coupling Fortran-based physical chemistry calculations to Windows interface.",
            "I worked on The Genotoxicity Advisor project, using a rule-based approach to predict genotoxicity.",
            "I worked on The Phase Advisor project, predicting phase behaviors of complex systems.",
        ],
        "publications": [
            "I co-authored 'Theoretical and Practical Considerations in Virtual Screening: A Beaten Field?' published in Current Med Chem 15:107-116 2008.",
            "I co-authored 'Design and Synthesis of 13,14-Dihydro Prostaglandin F1α Analogues as Potent and Selective Ligands for the Human FP Receptor' published in J. Med Chem 43 (5), pp 945–952, 2000.",
            "I co-authored 'An engineered intersubunit disulfide enhances the stability and DNA binding of the N-terminal domain of lambda repressor' published in Biochemistry 25 (20), pp 5992–599, 1986.",
            "I co-authored 'Computer-aided model-building strategies for protein design' published in Biochemistry 25 (20), pp 5987–599 1986.",
            "I co-authored 'Introduction of Intersubunit Disulfide Bonds In the Membrane-Distal Region of the Influenza Hemagglutinin Abolishes Membrane Fusion Activity' published in Cell 68:635-645 1992.",
        ],
        "management_experience": [
            "I was Section Leader of the Research Computing and Informatics group within P&G Pharmaceuticals.",
            "I was Director of the Global Modeling Community within P&G Corporate Functions R&D.",
            "I managed groups of scientists and coordinated project work.",
            "I managed careers, salaries, and ratings for my team members.",
            "I had budget approval and management responsibilities for hardware and software installations.",
            "I communicated with senior management regularly.",
            "I have experience building diverse teams.",
            "I have experience mentoring staff.",
            "I have experience planning and delegating work.",
        ],
        "customer_service": [
            "I provided over 11,000 customer sessions as an Apple Genius.",
            "I achieved top customer feedback scores at Apple.",
            "I have excellent problem solving and difficult customer interaction management skills.",
            "I currently provide front-line technical support at GeekSquad.",
        ],
        "personal_characteristics": [
            "I am a veteran P&G employee with understanding of high-performing corporate culture.",
            "I have the ability to rapidly integrate into new work situations.",
            "I have effective communication skills across a broad spectrum of users and customers.",
            "I have patient and effective teaching abilities.",
            "I have a technical background enabling work across multiple disciplines from astrophysics to computational chemistry to machine learning.",
        ],
    }

    # Flatten into individual facts with category labels
    individual_facts = []
    for category, facts in facts_by_category.items():
        for fact in facts:
            individual_facts.append(
                {"category": category, "fact": fact, "id": len(individual_facts) + 1}
            )

    return individual_facts


async def initialize_agent(use_remote=False):
    """Initialize the AgnoPersonalAgent."""
    ollama_url = REMOTE_OLLAMA_URL if use_remote else OLLAMA_URL

    print("🤖 Initializing Personal Agent...")
    print(f"🌐 Using {'remote' if use_remote else 'local'} Ollama URL: {ollama_url}")

    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=ollama_url,
        user_id=USER_ID,
        debug=True,
        enable_memory=True,
        enable_mcp=True,
        storage_dir=AGNO_STORAGE_DIR,
    )

    await agent.initialize()
    print(f"✅ Agent initialized with model: {LLM_MODEL}")
    return agent


async def send_warmup_greeting(agent):
    """Send initial greeting to identify yourself and warm up the model."""
    print("\n👋 Sending warm-up greeting...")

    greeting = "Hello, it's Eric again"

    try:
        start_time = time.time()
        response = await agent.run(greeting)
        end_time = time.time()

        response_time = end_time - start_time

        if response and len(response) > 0:
            print(f"✅ Warm-up successful in {response_time:.2f}s")
            print(f"🤖 Response: {response[:150]}...")
            return True
        else:
            print(f"⚠️ Empty response to greeting")
            return False

    except Exception as e:
        print(f"❌ Error sending greeting: {str(e)}")
        return False


async def condition_agent_for_fact_storage(agent):
    """Condition the agent with instructions for efficient fact storage."""
    print("\n🎯 Conditioning agent for fact storage...")

    conditioning_message = """I'm going to share a series of personal facts about myself that I want you to store in your memory. For each fact I share:

1. Store the fact exactly as I state it without interpretation or elaboration
2. Do not ask questions or provide commentary about the facts
3. Simply respond with "Stored" or "Got it" to confirm you've saved the fact
4. Keep your responses brief - just acknowledge that you've stored the information

This will help me efficiently build your knowledge about me. Are you ready to receive my personal facts?"""

    try:
        start_time = time.time()
        response = await agent.run(conditioning_message)
        end_time = time.time()

        response_time = end_time - start_time

        if response and len(response) > 0:
            print(f"✅ Agent conditioned successfully in {response_time:.2f}s")
            print(f"🤖 Response: {response[:200]}...")
            return True
        else:
            print(f"⚠️ Empty response to conditioning")
            return False

    except Exception as e:
        print(f"❌ Error conditioning agent: {str(e)}")
        return False


async def send_individual_fact(agent, fact_data, fact_number, total_facts):
    """Send a single fact to the agent and monitor success."""
    fact_id = fact_data["id"]
    category = fact_data["category"]
    fact = fact_data["fact"]

    # Create a message for this individual fact
    message = f"Please remember this fact about me: {fact}"

    print(f"\n📝 [{fact_number}/{total_facts}] Sending fact #{fact_id} ({category})")
    print(f"💬 Fact: {fact}")

    try:
        start_time = time.time()
        response = await agent.run(message)
        end_time = time.time()

        response_time = end_time - start_time

        if response and len(response) > 0:
            print(f"✅ Success in {response_time:.2f}s")
            print(f"🤖 Response: {response[:100]}...")

            # Check memory count after each fact
            if hasattr(agent, "agno_memory") and agent.agno_memory:
                try:
                    memories = agent.agno_memory.get_user_memories(user_id=USER_ID)
                    memory_count = len(memories) if memories else 0
                    print(f"💾 Total memories: {memory_count}")
                except Exception as memory_error:
                    print(f"⚠️ Could not check memory: {str(memory_error)}")

            return True, response_time, None
        else:
            print(f"❌ Empty response from agent")
            return False, response_time, "Empty response"

    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        print(f"❌ Error: {str(e)}")
        return False, response_time, str(e)


async def feed_facts_systematically(agent, facts_to_send=None, delay_between_facts=1.0):
    """Feed individual facts to the agent systematically."""
    all_facts = get_all_individual_facts()

    if facts_to_send:
        # Filter facts by category if specified
        filtered_facts = []
        for fact_data in all_facts:
            if fact_data["category"] in facts_to_send:
                filtered_facts.append(fact_data)
        facts_list = filtered_facts
    else:
        facts_list = all_facts

    total_facts = len(facts_list)
    print(f"📊 Preparing to send {total_facts} individual facts")

    if facts_to_send:
        print(f"🎯 Categories: {', '.join(facts_to_send)}")
    else:
        print("📦 Sending ALL facts")

    successful_facts = 0
    failed_facts = 0
    total_time = 0
    fact_results = []

    for i, fact_data in enumerate(facts_list, 1):
        success, response_time, error = await send_individual_fact(
            agent, fact_data, i, total_facts
        )

        total_time += response_time

        fact_results.append(
            {
                "fact_id": fact_data["id"],
                "category": fact_data["category"],
                "fact": fact_data["fact"],
                "success": success,
                "response_time": response_time,
                "error": error,
            }
        )

        if success:
            successful_facts += 1
        else:
            failed_facts += 1

        # Progress update every 10 facts
        if i % 10 == 0 or i == total_facts:
            success_rate = (successful_facts / i) * 100
            avg_time = total_time / i
            print(
                f"\n📊 Progress: {i}/{total_facts} ({success_rate:.1f}% success, avg {avg_time:.2f}s/fact)"
            )

        # Delay between facts to avoid overwhelming the agent
        if i < total_facts and delay_between_facts > 0:
            await asyncio.sleep(delay_between_facts)

    return successful_facts, failed_facts, fact_results


async def verify_final_memory_state(agent):
    """Verify the final state of the agent's memory."""
    print("\n🔍 Verifying final memory state...")

    try:
        if hasattr(agent, "agno_memory") and agent.agno_memory:
            memories = agent.agno_memory.get_user_memories(user_id=USER_ID)

            if memories:
                print(f"✅ Final memory count: {len(memories)} memories stored")

                # Group memories by category if possible
                category_counts = {}
                for memory in memories:
                    memory_content = getattr(memory, "memory", "")
                    # Try to identify category from content
                    for category in [
                        "basic_info",
                        "education",
                        "technical_skills",
                        "current_work",
                        "major_achievements",
                    ]:
                        if any(
                            keyword in memory_content.lower()
                            for keyword in [
                                "name" if category == "basic_info" else "",
                                "graduated" if category == "education" else "",
                                "program" if category == "technical_skills" else "",
                                "work" if category == "current_work" else "",
                                "developed" if category == "major_achievements" else "",
                            ]
                        ):
                            category_counts[category] = (
                                category_counts.get(category, 0) + 1
                            )
                            break

                if category_counts:
                    print("📋 Memory distribution by category:")
                    for category, count in category_counts.items():
                        print(
                            f"  • {category.replace('_', ' ').title()}: {count} memories"
                        )

                return True
            else:
                print("❌ No memories found in final state")
                return False
        else:
            print("❌ Memory system not available")
            return False

    except Exception as e:
        print(f"❌ Error verifying final memory state: {str(e)}")
        return False


async def test_random_fact_recall(agent, num_tests=5):
    """Test recall of random facts."""
    print(f"\n🧠 Testing recall of {num_tests} random facts...")

    test_queries = [
        "What is my name?",
        "Where did I get my PhD?",
        "What programming languages do I know?",
        "What is my current project?",
        "What companies have I worked for?",
        "What was my dissertation about?",
        "What achievements am I most proud of?",
        "What is my educational background?",
        "What technical skills do I have?",
        "What is my work experience?",
    ]

    import random

    selected_queries = random.sample(test_queries, min(num_tests, len(test_queries)))

    successful_recalls = 0

    for i, query in enumerate(selected_queries, 1):
        try:
            print(f"\n❓ Test {i}/{num_tests}: {query}")
            response = await agent.run(query)

            if response and len(response) > 30:  # Reasonable response length
                print(f"✅ Good recall: {response[:120]}...")
                successful_recalls += 1
            else:
                print(f"⚠️ Weak recall: {response}")

        except Exception as e:
            print(f"❌ Error testing recall: {str(e)}")

    recall_rate = (successful_recalls / len(selected_queries)) * 100
    print(
        f"\n📊 Recall test results: {successful_recalls}/{len(selected_queries)} successful ({recall_rate:.1f}%)"
    )
    return successful_recalls >= len(selected_queries) // 2


async def main():
    """Main function to systematically feed individual facts."""
    print("🚀 Starting Individual Facts Feeder")
    print("=" * 60)

    try:
        # Parse command line arguments
        args = parse_args()

        # Initialize agent with remote option
        agent = await initialize_agent(use_remote=args.remote)

        # Send warm-up greeting
        warmup_success = await send_warmup_greeting(agent)
        if not warmup_success:
            print("⚠️ Warm-up greeting failed, but continuing...")

        # Condition agent for efficient fact storage
        conditioning_success = await condition_agent_for_fact_storage(agent)
        if not conditioning_success:
            print("⚠️ Agent conditioning failed, but continuing...")

        # Parse categories and mode
        categories_to_send = None
        delay_between_facts = 1.0

        if args.categories:
            if "all" in args.categories:
                categories_to_send = None
                print("📦 Mode: Feeding ALL individual facts")
            elif "test" in args.categories:
                categories_to_send = ["basic_info", "professional_identity"]
                print("🧪 Mode: Test run with basic facts only")
            elif "fast" in args.categories:
                categories_to_send = None
                delay_between_facts = 0.5
                print("⚡ Mode: Fast feeding (0.5s delay)")
            elif "slow" in args.categories:
                categories_to_send = None
                delay_between_facts = 2.0
                print("🐌 Mode: Slow feeding (2s delay)")
            else:
                # Specific categories
                categories_to_send = args.categories
                print(f"🎯 Mode: Feeding specific categories: {categories_to_send}")
        else:
            # Default: essential categories
            categories_to_send = ["basic_info", "professional_identity", "education"]
            print("🎯 Mode: Default - feeding essential facts")

        # Feed facts systematically
        successful_facts, failed_facts, fact_results = await feed_facts_systematically(
            agent, categories_to_send, delay_between_facts
        )

        # Calculate statistics
        total_facts = successful_facts + failed_facts
        success_rate = (successful_facts / total_facts * 100) if total_facts > 0 else 0
        total_time = sum(result["response_time"] for result in fact_results)
        avg_time_per_fact = total_time / total_facts if total_facts > 0 else 0

        print(f"\n📊 FEEDING RESULTS:")
        print(
            f"✅ Successful facts: {successful_facts}/{total_facts} ({success_rate:.1f}%)"
        )
        print(f"❌ Failed facts: {failed_facts}")
        print(f"⏱️ Total time: {total_time:.1f}s")
        print(f"📈 Average time per fact: {avg_time_per_fact:.2f}s")

        # Show failed facts if any
        if failed_facts > 0:
            print(f"\n❌ Failed facts:")
            for result in fact_results:
                if not result["success"]:
                    print(
                        f"  • [{result['category']}] {result['fact'][:80]}... - {result['error']}"
                    )

        # Verify final memory state
        memory_success = await verify_final_memory_state(agent)

        # Test fact recall
        recall_success = await test_random_fact_recall(agent)

        # Final summary
        print("\n" + "=" * 60)
        print("📋 FINAL SUMMARY")
        print("=" * 60)
        print(f"📝 Individual facts sent: {successful_facts}/{total_facts}")
        print(f"💾 Memory system working: {memory_success}")
        print(f"🧠 Fact recall working: {recall_success}")
        print(f"📊 Overall success rate: {success_rate:.1f}%")

        if success_rate >= 90 and memory_success and recall_success:
            print(
                "\n🎉 EXCELLENT! Your Personal Agent has successfully learned about you!"
            )
            print(
                "💡 Individual facts have been systematically stored and are recallable."
            )
        elif success_rate >= 70:
            print("\n✅ GOOD! Most facts were successfully stored.")
            print("⚠️ Some issues detected - check failed facts above.")
        else:
            print("\n⚠️ ISSUES DETECTED! Many facts failed to store properly.")
            print("🔧 Consider checking your agent configuration or Ollama connection.")

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("Usage:")
    print(
        "  python feed_individual_facts.py                    # Feed essential facts individually"
    )
    print(
        "  python feed_individual_facts.py --remote           # Use remote Ollama server"
    )
    print(
        "  python feed_individual_facts.py all                # Feed ALL facts individually"
    )
    print(
        "  python feed_individual_facts.py --remote all       # Feed ALL facts using remote server"
    )
    print(
        "  python feed_individual_facts.py test               # Test with basic facts only"
    )
    print(
        "  python feed_individual_facts.py fast               # Fast mode (0.5s delay)"
    )
    print("  python feed_individual_facts.py slow               # Slow mode (2s delay)")
    print(
        "  python feed_individual_facts.py basic_info education  # Specific categories"
    )
    print(
        "  python feed_individual_facts.py --remote basic_info education  # Remote + specific categories"
    )
    print()

    asyncio.run(main())
