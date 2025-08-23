#!/usr/bin/env python3
"""
Comprehensive test script to verify that all tool path issues have been resolved.
Tests FileTools, ShellTools, and PythonTools across all team configurations.
"""

import sys
import os
from pathlib import Path
import asyncio

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_path_object(obj, attr_name, obj_description):
    """Test if an object's attribute is a proper Path object."""
    if hasattr(obj, attr_name):
        attr_value = getattr(obj, attr_name)
        print(f"  {obj_description} {attr_name}: {attr_value} (type: {type(attr_value).__name__})")
        if isinstance(attr_value, Path):
            print(f"    ✅ {attr_name} is a Path object")
            return True
        else:
            print(f"    ❌ {attr_name} is not a Path object")
            return False
    return True

def test_tools_in_agent(agent, agent_name):
    """Test all tools in an agent for proper Path usage."""
    print(f"\n🔍 Testing tools in {agent_name}:")
    all_good = True
    
    if hasattr(agent, 'tools') and agent.tools:
        for i, tool in enumerate(agent.tools):
            tool_name = getattr(tool, '__class__', type(tool)).__name__
            print(f"  Tool {i+1}: {tool_name}")
            
            # Test common path attributes
            for attr in ['base_dir', 'working_dir', 'directory']:
                if not test_path_object(tool, attr, f"    {tool_name}"):
                    all_good = False
                    
            # Test nested tools (like in toolkits)
            if hasattr(tool, 'tools') and tool.tools:
                for j, nested_tool in enumerate(tool.tools):
                    nested_name = getattr(nested_tool, '__class__', type(nested_tool)).__name__
                    print(f"    Nested Tool {j+1}: {nested_name}")
                    for attr in ['base_dir', 'working_dir', 'directory']:
                        if not test_path_object(nested_tool, attr, f"      {nested_name}"):
                            all_good = False
    else:
        print("  No tools found in this agent")
    
    return all_good

async def test_reasoning_team():
    """Test the reasoning team configuration."""
    print("\n🧪 Testing Reasoning Team...")
    try:
        from personal_agent.team.reasoning_team import create_team
        team = await create_team(use_remote=False)
        
        print(f"✅ Reasoning team created successfully!")
        print(f"Team name: {team.name}")
        print(f"Team members: {len(team.members)}")
        
        all_good = True
        
        # Test team-level tools
        if hasattr(team, 'tools') and team.tools:
            print("\n🔍 Testing team-level tools:")
            for i, tool in enumerate(team.tools):
                tool_name = getattr(tool, '__class__', type(tool)).__name__
                print(f"  Team Tool {i+1}: {tool_name}")
                for attr in ['base_dir', 'working_dir', 'directory']:
                    if not test_path_object(tool, attr, f"    {tool_name}"):
                        all_good = False
        
        # Test each member's tools
        if hasattr(team, 'members') and team.members:
            for member in team.members:
                member_name = getattr(member, 'name', 'Unknown Member')
                if not test_tools_in_agent(member, member_name):
                    all_good = False
        
        # Cleanup
        try:
            from personal_agent.team.reasoning_team import cleanup_team
            await cleanup_team(team)
            print("✅ Reasoning team cleanup completed")
        except Exception as e:
            print(f"⚠️ Warning during reasoning team cleanup: {e}")
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error testing reasoning team: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_personal_agent_team():
    """Test the personal agent team configuration."""
    print("\n🧪 Testing Personal Agent Team...")
    try:
        from personal_agent.team.personal_agent_team import create_personal_agent_team
        from personal_agent.config.settings import HOME_DIR
        
        print(f"HOME_DIR: {HOME_DIR} (type: {type(HOME_DIR)})")
        
        team = create_personal_agent_team(debug=False)
        
        print(f"✅ Personal agent team created successfully!")
        print(f"Team name: {team.name}")
        print(f"Team members: {len(team.members)}")
        
        all_good = True
        
        # Test team-level tools
        if hasattr(team, 'tools') and team.tools:
            print("\n🔍 Testing team-level tools:")
            for i, tool in enumerate(team.tools):
                tool_name = getattr(tool, '__class__', type(tool)).__name__
                print(f"  Team Tool {i+1}: {tool_name}")
                for attr in ['base_dir', 'working_dir', 'directory']:
                    if not test_path_object(tool, attr, f"    {tool_name}"):
                        all_good = False
        
        # Test each member's tools
        if hasattr(team, 'members') and team.members:
            for member in team.members:
                member_name = getattr(member, 'name', 'Unknown Member')
                if not test_tools_in_agent(member, member_name):
                    all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error testing personal agent team: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_specialized_agents():
    """Test individual specialized agents."""
    print("\n🧪 Testing Individual Specialized Agents...")
    
    try:
        from personal_agent.team.specialized_agents import (
            create_web_research_agent,
            create_finance_agent,
            create_calculator_agent,
            create_file_operations_agent,
            create_pubmed_agent,
            create_writer_agent,
        )
        
        agents_to_test = [
            ("Web Research Agent", create_web_research_agent),
            ("Finance Agent", create_finance_agent),
            ("Calculator Agent", create_calculator_agent),
            ("File Operations Agent", create_file_operations_agent),
            ("PubMed Agent", create_pubmed_agent),
            ("Writer Agent", create_writer_agent),
        ]
        
        all_good = True
        
        for agent_name, create_func in agents_to_test:
            try:
                print(f"\n🔍 Testing {agent_name}...")
                agent = create_func(debug=False)
                if not test_tools_in_agent(agent, agent_name):
                    all_good = False
                print(f"✅ {agent_name} passed path tests")
            except Exception as e:
                print(f"❌ Error testing {agent_name}: {e}")
                all_good = False
        
        return all_good
        
    except Exception as e:
        print(f"❌ Error testing specialized agents: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all comprehensive tests."""
    print("🚀 Starting Comprehensive Tool Path Tests")
    print("=" * 60)
    
    test_results = []
    
    # Test 1: Personal Agent Team
    result1 = test_personal_agent_team()
    test_results.append(("Personal Agent Team", result1))
    
    # Test 2: Individual Specialized Agents
    result2 = test_specialized_agents()
    test_results.append(("Specialized Agents", result2))
    
    # Test 3: Reasoning Team (async)
    result3 = await test_reasoning_team()
    test_results.append(("Reasoning Team", result3))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY:")
    print("=" * 60)
    
    all_passed = True
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 ALL TESTS PASSED! The tool path issues have been resolved.")
        print("✅ FileTools, ShellTools, and PythonTools are now using proper Path objects.")
    else:
        print("❌ SOME TESTS FAILED! There may still be path-related issues.")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)