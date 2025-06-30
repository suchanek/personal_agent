#!/usr/bin/env python3
"""
Helper script to organize personal facts for sending to the Personal Agent.
This script provides organized facts that can be copy-pasted into the Streamlit chat interface.
"""

def get_fact_categories():
    """Return organized categories of facts for easy sending to the agent."""
    
    categories = {
        "personal_info": [
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
    
    return categories

def print_category_for_chat(category_name):
    """Print facts from a specific category formatted for chat input."""
    categories = get_fact_categories()
    
    if category_name not in categories:
        print(f"Category '{category_name}' not found. Available categories:")
        for cat in categories.keys():
            print(f"  - {cat}")
        return
    
    print(f"\n=== {category_name.upper().replace('_', ' ')} FACTS ===")
    print("Copy and paste this into the chat:")
    print("-" * 50)
    
    facts_text = "Please remember these facts about me:\n\n"
    for fact in categories[category_name]:
        facts_text += f"• {fact}\n"
    
    print(facts_text)
    print("-" * 50)

def print_all_categories():
    """Print all available categories."""
    categories = get_fact_categories()
    print("Available fact categories:")
    for i, category in enumerate(categories.keys(), 1):
        print(f"{i}. {category.replace('_', ' ').title()}")

def generate_batch_message(category_names):
    """Generate a message with facts from multiple categories."""
    categories = get_fact_categories()
    
    message = "Please remember these facts about me:\n\n"
    
    for category_name in category_names:
        if category_name in categories:
            message += f"**{category_name.replace('_', ' ').title()}:**\n"
            for fact in categories[category_name]:
                message += f"• {fact}\n"
            message += "\n"
    
    return message

def generate_all_facts_message():
    """Generate a message with ALL facts from ALL categories."""
    categories = get_fact_categories()
    return generate_batch_message(list(categories.keys()))

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python send_facts_helper.py list                    # Show all categories")
        print("  python send_facts_helper.py all                     # Send ALL facts")
        print("  python send_facts_helper.py <category>              # Show specific category")
        print("  python send_facts_helper.py batch <cat1> <cat2>...  # Combine categories")
        print("\nExamples:")
        print("  python send_facts_helper.py all")
        print("  python send_facts_helper.py basic_info")
        print("  python send_facts_helper.py batch basic_info education")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "list":
        print_all_categories()
    elif command == "all":
        message = generate_all_facts_message()
        print("\n=== ALL FACTS MESSAGE ===")
        print("Copy and paste this into the chat:")
        print("-" * 50)
        print(message)
        print("-" * 50)
    elif command == "batch":
        if len(sys.argv) < 3:
            print("Please specify categories for batch mode")
            print_all_categories()
        else:
            categories_to_include = sys.argv[2:]
            message = generate_batch_message(categories_to_include)
            print("\n=== BATCH MESSAGE ===")
            print("Copy and paste this into the chat:")
            print("-" * 50)
            print(message)
            print("-" * 50)
    else:
        print_category_for_chat(command)
