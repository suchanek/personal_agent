#!/usr/bin/env python3
"""
Automated script to send personal facts to the Personal Agent and monitor for success.
This script directly interacts with the AgnoPersonalAgent to load facts into memory.
"""

import asyncio
import sys
import time
from pathlib import Path
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from personal_agent.config import AGNO_STORAGE_DIR, LLM_MODEL, OLLAMA_URL, USER_ID
from personal_agent.core.agno_agent import AgnoPersonalAgent

def get_fact_categories():
    """Return organized categories of facts for easy sending to the agent."""
    
    categories = {
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
        ],
        
        "previous_work": [
            "I worked as Support Desk Analyst II at Miami University, Oxford OH from 2013-2017.",
            "I provided front-line help desk support for IT-related technical issues at Miami University.",
            "I did knowledge management across multiple end-user and internal services at Miami University.",
            "I performed Mac computer repair for Macbook Pro, iMac and Macbook computers at Miami University.",
            "I worked as a Genius at Apple Computer, Kenwood OH from 2010-2013.",
            "I provided 'Genius Bar' one-on-one troubleshooting for over 11,000 customer sessions at Apple.",
            "I consistently achieved top customer feedback scores at Apple.",
            "I was recognized for excellent problem solving skills and management of difficult customer interactions at Apple."
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
            "I have experience planning and delegating work."
        ]
    }
    
    return categories

def create_fact_message(categories_to_include=None):
    """Create a message with facts from specified categories or all categories."""
    categories = get_fact_categories()
    
    if categories_to_include is None:
        categories_to_include = list(categories.keys())
    
    message = "Please remember these facts about me:\n\n"
    
    for category_name in categories_to_include:
        if category_name in categories:
            message += f"**{category_name.replace('_', ' ').title()}:**\n"
            for fact in categories[category_name]:
                message += f"• {fact}\n"
            message += "\n"
    
    return message

async def initialize_agent():
    """Initialize the AgnoPersonalAgent."""
    print("🤖 Initializing Personal Agent...")
    
    agent = AgnoPersonalAgent(
        model_provider="ollama",
        model_name=LLM_MODEL,
        ollama_base_url=OLLAMA_URL,
        user_id=USER_ID,
        debug=True,
        enable_memory=True,
        enable_mcp=True,
        storage_dir=AGNO_STORAGE_DIR,
    )
    
    await agent.initialize()
    print(f"✅ Agent initialized with model: {LLM_MODEL}")
    return agent

async def send_facts_to_agent(agent, categories_to_send=None, batch_size=2):
    """Send facts to the agent in batches and monitor for success."""
    categories = get_fact_categories()
    
    if categories_to_send is None:
        categories_to_send = list(categories.keys())
    
    print(f"📝 Preparing to send {len(categories_to_send)} categories of facts...")
    print(f"Categories: {', '.join(categories_to_send)}")
    
    # Send facts in batches to avoid overwhelming the agent
    total_facts = sum(len(categories[cat]) for cat in categories_to_send if cat in categories)
    print(f"📊 Total facts to send: {total_facts}")
    
    success_count = 0
    error_count = 0
    
    # Process categories in batches
    for i in range(0, len(categories_to_send), batch_size):
        batch = categories_to_send[i:i + batch_size]
        batch_message = create_fact_message(batch)
        
        print(f"\n🚀 Sending batch {i//batch_size + 1}: {', '.join(batch)}")
        print(f"📏 Message length: {len(batch_message)} characters")
        
        try:
            start_time = time.time()
            response = await agent.run(batch_message)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            if response and len(response) > 0:
                print(f"✅ Batch sent successfully in {response_time:.2f}s")
                print(f"🤖 Agent response: {response[:200]}...")
                success_count += len(batch)
                
                # Check if memories were actually stored
                if hasattr(agent, 'agno_memory') and agent.agno_memory:
                    try:
                        memories = agent.agno_memory.get_user_memories(user_id=USER_ID)
                        print(f"💾 Total memories stored: {len(memories) if memories else 0}")
                    except Exception as memory_error:
                        print(f"⚠️ Could not check memory count: {str(memory_error)}")
                
            else:
                print(f"❌ Empty response from agent")
                error_count += len(batch)
                
        except Exception as e:
            print(f"❌ Error sending batch: {str(e)}")
            error_count += len(batch)
        
        # Small delay between batches to avoid overwhelming the agent
        if i + batch_size < len(categories_to_send):
            print("⏳ Waiting 2 seconds before next batch...")
            await asyncio.sleep(2)
    
    return success_count, error_count

async def verify_facts_stored(agent):
    """Verify that facts were successfully stored in memory."""
    print("\n🔍 Verifying facts were stored in memory...")
    
    try:
        if hasattr(agent, 'agno_memory') and agent.agno_memory:
            memories = agent.agno_memory.get_user_memories(user_id=USER_ID)
            
            if memories:
                print(f"✅ Found {len(memories)} memories stored")
                
                # Show a sample of stored memories
                print("\n📋 Sample of stored memories:")
                for i, memory in enumerate(memories[:5], 1):
                    memory_content = getattr(memory, "memory", "No content")
                    print(f"  {i}. {memory_content[:100]}...")
                
                if len(memories) > 5:
                    print(f"  ... and {len(memories) - 5} more memories")
                
                return True
            else:
                print("❌ No memories found in storage")
                return False
        else:
            print("❌ Memory system not available")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying memories: {str(e)}")
        return False

async def test_fact_recall(agent):
    """Test that the agent can recall stored facts."""
    print("\n🧠 Testing fact recall...")
    
    test_questions = [
        "What is my name?",
        "Where did I go to school?",
        "What is my current project?",
        "What companies have I worked for?",
        "What programming languages do I know?"
    ]
    
    successful_recalls = 0
    
    for question in test_questions:
        try:
            print(f"\n❓ Testing: {question}")
            response = await agent.run(question)
            
            if response and len(response) > 20:  # Reasonable response length
                print(f"✅ Good response: {response[:150]}...")
                successful_recalls += 1
            else:
                print(f"⚠️ Short response: {response}")
                
        except Exception as e:
            print(f"❌ Error testing recall: {str(e)}")
    
    print(f"\n📊 Recall test results: {successful_recalls}/{len(test_questions)} successful")
    return successful_recalls >= len(test_questions) // 2  # At least half should work

async def main():
    """Main function to run the automated fact sending process."""
    print("🚀 Starting Automated Personal Facts Sender")
    print("=" * 50)
    
    try:
        # Initialize agent
        agent = await initialize_agent()
        
        # Get user choice for what to send
        if len(sys.argv) > 1:
            if sys.argv[1] == "all":
                categories_to_send = None  # Send all categories
                print("📦 Mode: Sending ALL facts")
            elif sys.argv[1] == "test":
                categories_to_send = ["basic_info", "professional_identity"]
                print("🧪 Mode: Test run with basic facts only")
            else:
                # Specific categories provided
                categories_to_send = sys.argv[1:]
                print(f"🎯 Mode: Sending specific categories: {categories_to_send}")
        else:
            # Default: send essential facts first
            categories_to_send = ["basic_info", "professional_identity", "education"]
            print("🎯 Mode: Default - sending essential facts")
        
        # Send facts to agent
        success_count, error_count = await send_facts_to_agent(agent, categories_to_send)
        
        print(f"\n📊 Sending Results:")
        print(f"✅ Successful: {success_count} categories")
        print(f"❌ Errors: {error_count} categories")
        
        # Verify facts were stored
        storage_success = await verify_facts_stored(agent)
        
        # Test fact recall
        recall_success = await test_fact_recall(agent)
        
        # Final summary
        print("\n" + "=" * 50)
        print("📋 FINAL SUMMARY")
        print("=" * 50)
        print(f"✅ Facts sent successfully: {success_count > 0}")
        print(f"💾 Facts stored in memory: {storage_success}")
        print(f"🧠 Fact recall working: {recall_success}")
        
        if success_count > 0 and storage_success and recall_success:
            print("\n🎉 SUCCESS! Your Personal Agent now knows about you!")
            print("💡 You can now chat with the agent using the Streamlit interface.")
        else:
            print("\n⚠️ Some issues detected. Check the logs above for details.")
            
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("Usage:")
    print("  python auto_send_facts.py                    # Send essential facts")
    print("  python auto_send_facts.py all                # Send ALL facts")
    print("  python auto_send_facts.py test               # Test run with basic facts")
    print("  python auto_send_facts.py basic_info education  # Send specific categories")
    print()
    
    asyncio.run(main())
