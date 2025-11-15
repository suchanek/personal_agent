"""
Comprehensive test runner for all refactored manager classes.

This module provides a unified way to run all tests for the refactored
AgnoPersonalAgent components using Python's built-in unittest framework.
"""

import unittest
import sys
import os
from pathlib import Path

def _add_src_to_syspath():
    # Ensure 'personal_agent' package is importable in src/ layout
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))

_add_src_to_syspath()

# Import all test modules
from tests.test_agent_model_manager import TestAgentModelManager, TestAgentModelManagerIntegration
from tests.test_agent_instruction_manager import (
    TestInstructionLevel, 
    TestAgentInstructionManager, 
    TestAgentInstructionManagerIntegration
)
from tests.test_agent_memory_manager import (
    TestAgentMemoryManager, 
    TestAgentMemoryManagerAsync, 
    TestAgentMemoryManagerIntegration
)
from tests.test_agent_knowledge_manager import (
    TestAgentKnowledgeManager, 
    TestAgentKnowledgeManagerAsync, 
    TestAgentKnowledgeManagerIntegration
)
from tests.test_agent_tool_manager import (
    TestAgentToolManager, 
    TestAgentToolManagerAsync, 
    TestAgentToolManagerIntegration
)


def create_test_suite():
    """Create a comprehensive test suite for all refactored managers."""
    suite = unittest.TestSuite()
    
    # Model Manager Tests
    suite.addTest(unittest.makeSuite(TestAgentModelManager))
    suite.addTest(unittest.makeSuite(TestAgentModelManagerIntegration))
    
    # Instruction Manager Tests
    suite.addTest(unittest.makeSuite(TestInstructionLevel))
    suite.addTest(unittest.makeSuite(TestAgentInstructionManager))
    suite.addTest(unittest.makeSuite(TestAgentInstructionManagerIntegration))
    
    # Memory Manager Tests
    suite.addTest(unittest.makeSuite(TestAgentMemoryManager))
    suite.addTest(unittest.makeSuite(TestAgentMemoryManagerAsync))
    suite.addTest(unittest.makeSuite(TestAgentMemoryManagerIntegration))
    
    # Knowledge Manager Tests
    suite.addTest(unittest.makeSuite(TestAgentKnowledgeManager))
    suite.addTest(unittest.makeSuite(TestAgentKnowledgeManagerAsync))
    suite.addTest(unittest.makeSuite(TestAgentKnowledgeManagerIntegration))
    
    # Tool Manager Tests
    suite.addTest(unittest.makeSuite(TestAgentToolManager))
    suite.addTest(unittest.makeSuite(TestAgentToolManagerAsync))
    suite.addTest(unittest.makeSuite(TestAgentToolManagerIntegration))
    
    return suite


def run_all_tests(verbosity=2):
    """Run all tests for the refactored manager classes.
    
    Args:
        verbosity: Test output verbosity level (0=quiet, 1=normal, 2=verbose)
        
    Returns:
        TestResult object with test results
    """
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)


def run_specific_manager_tests(manager_name, verbosity=2):
    """Run tests for a specific manager class.
    
    Args:
        manager_name: Name of the manager to test ('model', 'instruction', 'memory', 'knowledge', 'tool')
        verbosity: Test output verbosity level
        
    Returns:
        TestResult object with test results
    """
    suite = unittest.TestSuite()
    
    if manager_name.lower() == 'model':
        suite.addTest(unittest.makeSuite(TestAgentModelManager))
        suite.addTest(unittest.makeSuite(TestAgentModelManagerIntegration))
    elif manager_name.lower() == 'instruction':
        suite.addTest(unittest.makeSuite(TestInstructionLevel))
        suite.addTest(unittest.makeSuite(TestAgentInstructionManager))
        suite.addTest(unittest.makeSuite(TestAgentInstructionManagerIntegration))
    elif manager_name.lower() == 'memory':
        suite.addTest(unittest.makeSuite(TestAgentMemoryManager))
        suite.addTest(unittest.makeSuite(TestAgentMemoryManagerAsync))
        suite.addTest(unittest.makeSuite(TestAgentMemoryManagerIntegration))
    elif manager_name.lower() == 'knowledge':
        suite.addTest(unittest.makeSuite(TestAgentKnowledgeManager))
        suite.addTest(unittest.makeSuite(TestAgentKnowledgeManagerAsync))
        suite.addTest(unittest.makeSuite(TestAgentKnowledgeManagerIntegration))
    elif manager_name.lower() == 'tool':
        suite.addTest(unittest.makeSuite(TestAgentToolManager))
        suite.addTest(unittest.makeSuite(TestAgentToolManagerAsync))
        suite.addTest(unittest.makeSuite(TestAgentToolManagerIntegration))
    else:
        raise ValueError(f"Unknown manager name: {manager_name}. Valid options: model, instruction, memory, knowledge, tool")
    
    runner = unittest.TextTestRunner(verbosity=verbosity)
    return runner.run(suite)


def print_test_summary():
    """Print a summary of all available tests."""
    print("=" * 80)
    print("REFACTORED AGENT MANAGER TESTS")
    print("=" * 80)
    print()
    
    test_categories = {
        "Model Manager": [
            "TestAgentModelManager - Basic model creation and configuration",
            "TestAgentModelManagerIntegration - Integration tests with realistic parameters"
        ],
        "Instruction Manager": [
            "TestInstructionLevel - Instruction level enum tests",
            "TestAgentInstructionManager - Instruction generation and management",
            "TestAgentInstructionManagerIntegration - Cross-level instruction consistency"
        ],
        "Memory Manager": [
            "TestAgentMemoryManager - Basic memory operations",
            "TestAgentMemoryManagerAsync - Async memory operations",
            "TestAgentMemoryManagerIntegration - Full memory workflow tests"
        ],
        "Knowledge Manager": [
            "TestAgentKnowledgeManager - Knowledge base operations",
            "TestAgentKnowledgeManagerAsync - Async graph operations",
            "TestAgentKnowledgeManagerIntegration - Complete knowledge workflows"
        ],
        "Tool Manager": [
            "TestAgentToolManager - Tool registration and management",
            "TestAgentToolManagerAsync - Async tool execution",
            "TestAgentToolManagerIntegration - Full tool management workflows"
        ]
    }
    
    for category, tests in test_categories.items():
        print(f"{category}:")
        for test in tests:
            print(f"  • {test}")
        print()
    
    print("Usage Examples:")
    print("  python -m tests.test_refactored_managers                    # Run all tests")
    print("  python -m tests.test_refactored_managers --manager model    # Run model tests only")
    print("  python -m tests.test_refactored_managers --quiet            # Run with minimal output")
    print("  python -m tests.test_refactored_managers --summary          # Show this summary")
    print()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run tests for refactored agent manager classes")
    parser.add_argument("--manager", choices=['model', 'instruction', 'memory', 'knowledge', 'tool'],
                       help="Run tests for a specific manager only")
    parser.add_argument("--quiet", action="store_true", help="Run tests with minimal output")
    parser.add_argument("--summary", action="store_true", help="Show test summary and exit")
    
    args = parser.parse_args()
    
    if args.summary:
        print_test_summary()
        sys.exit(0)
    
    verbosity = 1 if args.quiet else 2
    
    try:
        if args.manager:
            print(f"Running tests for {args.manager.title()} Manager...")
            result = run_specific_manager_tests(args.manager, verbosity)
        else:
            print("Running all refactored manager tests...")
            result = run_all_tests(verbosity)
        
        # Print summary
        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
        
        if result.failures:
            print(f"\nFAILURES ({len(result.failures)}):")
            for test, traceback in result.failures:
                print(f"  • {test}")
        
        if result.errors:
            print(f"\nERRORS ({len(result.errors)}):")
            for test, traceback in result.errors:
                print(f"  • {test}")
        
        success = len(result.failures) == 0 and len(result.errors) == 0
        print(f"\nOverall result: {'PASSED' if success else 'FAILED'}")
        
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)
