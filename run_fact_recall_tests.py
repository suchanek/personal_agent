#!/usr/bin/env python3
"""
Fact Recall Test Runner

This script provides an easy way to run the fact recall tests with different options.
"""

import subprocess
import sys
from pathlib import Path


def print_banner():
    """Print the test runner banner."""
    print("🧪 FACT RECALL TEST RUNNER")
    print("=" * 50)
    print("Available test options:")
    print("  1. Quick Test    - Fast validation of basic recall")
    print("  2. Comprehensive - Full fact recall test suite")
    print("  3. Both Tests    - Run quick test first, then comprehensive")
    print("=" * 50)


def run_test(test_script: str, test_name: str) -> bool:
    """Run a specific test script."""
    print(f"\n🚀 Running {test_name}...")
    print("=" * 60)
    
    try:
        # Run the test script
        result = subprocess.run([
            sys.executable, test_script
        ], cwd=Path(__file__).parent, capture_output=False, text=True)
        
        success = result.returncode == 0
        
        if success:
            print(f"\n✅ {test_name} completed successfully!")
        else:
            print(f"\n❌ {test_name} failed!")
        
        return success
        
    except Exception as e:
        print(f"\n❌ Error running {test_name}: {e}")
        return False


def main():
    """Main function."""
    print_banner()
    
    if len(sys.argv) > 1:
        # Command line argument provided
        choice = sys.argv[1].lower()
    else:
        # Interactive mode
        try:
            choice = input("Enter your choice (1-3): ").strip()
        except KeyboardInterrupt:
            print("\n\nTest runner cancelled.")
            sys.exit(0)
    
    # Map choices to test scripts
    test_scripts = {
        "1": ("tests/test_quick_fact_recall.py", "Quick Fact Recall Test"),
        "2": ("tests/test_fact_recall_comprehensive.py", "Comprehensive Fact Recall Test"),
        "quick": ("tests/test_quick_fact_recall.py", "Quick Fact Recall Test"),
        "comprehensive": ("tests/test_fact_recall_comprehensive.py", "Comprehensive Fact Recall Test"),
        "comp": ("tests/test_fact_recall_comprehensive.py", "Comprehensive Fact Recall Test"),
    }
    
    if choice == "3" or choice == "both":
        # Run both tests
        print("\n🔄 Running both tests in sequence...")
        
        # Run quick test first
        quick_success = run_test("tests/test_quick_fact_recall.py", "Quick Fact Recall Test")
        
        if quick_success:
            print("\n⏳ Quick test passed, proceeding to comprehensive test...")
            comp_success = run_test("tests/test_fact_recall_comprehensive.py", "Comprehensive Fact Recall Test")
            
            print("\n" + "=" * 60)
            print("📋 FINAL RESULTS")
            print("=" * 60)
            print(f"Quick Test: {'✅ PASS' if quick_success else '❌ FAIL'}")
            print(f"Comprehensive Test: {'✅ PASS' if comp_success else '❌ FAIL'}")
            
            if quick_success and comp_success:
                print("\n🎉 ALL TESTS PASSED! Fact recall system is working well.")
                sys.exit(0)
            else:
                print("\n⚠️ Some tests failed. Check the output above for details.")
                sys.exit(1)
        else:
            print("\n❌ Quick test failed. Skipping comprehensive test.")
            print("💡 Fix the basic issues first before running comprehensive tests.")
            sys.exit(1)
    
    elif choice in test_scripts:
        # Run single test
        script_path, test_name = test_scripts[choice]
        success = run_test(script_path, test_name)
        sys.exit(0 if success else 1)
    
    else:
        print(f"\n❌ Invalid choice: {choice}")
        print("Valid options: 1, 2, 3, quick, comprehensive, comp, both")
        sys.exit(1)


if __name__ == "__main__":
    print("Fact Recall Test Runner")
    print("Usage:")
    print("  python run_fact_recall_tests.py [option]")
    print("  Options: 1, 2, 3, quick, comprehensive, both")
    print("  If no option provided, interactive mode will start.")
    print()
    
    main()
