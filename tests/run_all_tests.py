#!/usr/bin/env python3
"""
Test runner script to execute all test scripts in the tests/ directory.

This script provides a convenient way to run all tests and see which ones pass or fail.
"""

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def get_test_files() -> List[Path]:
    """Get all test files in the tests directory."""
    tests_dir = Path(__file__).parent
    test_files = []
    
    # Find all Python files that start with 'test_' or contain 'test' in the name
    for file_path in tests_dir.glob("*.py"):
        if (file_path.name.startswith("test_") or 
            "test" in file_path.name.lower() or
            file_path.name.startswith("debug_") or
            file_path.name.startswith("analyze_") or
            file_path.name.startswith("quick_") or
            file_path.name.startswith("run_") or
            file_path.name.startswith("fix_") or
            file_path.name.startswith("similarity_")):
            # Skip this runner script itself
            if file_path.name != "run_all_tests.py":
                test_files.append(file_path)
    
    return sorted(test_files)


def run_test_file(test_file: Path) -> Tuple[str, bool, str]:
    """Run a single test file and return results."""
    print(f"\n🧪 Running {test_file.name}...")
    print("-" * 60)
    
    try:
        # Run the test file
        result = subprocess.run(
            [sys.executable, str(test_file)],
            cwd=test_file.parent.parent,  # Run from project root
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        success = result.returncode == 0
        output = result.stdout + result.stderr
        
        # Print the output
        if output.strip():
            print(output)
        
        if success:
            print(f"✅ {test_file.name} PASSED")
        else:
            print(f"❌ {test_file.name} FAILED (exit code: {result.returncode})")
        
        return test_file.name, success, output
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {test_file.name} TIMED OUT (5 minutes)")
        return test_file.name, False, "Test timed out after 5 minutes"
    except Exception as e:
        print(f"💥 {test_file.name} ERROR: {e}")
        return test_file.name, False, str(e)


def main():
    """Main function to run all tests."""
    print("🚀 RUNNING ALL TESTS IN tests/ DIRECTORY")
    print("=" * 80)
    
    # Get all test files
    test_files = get_test_files()
    
    if not test_files:
        print("❌ No test files found in tests/ directory")
        return 1
    
    print(f"📋 Found {len(test_files)} test files:")
    for test_file in test_files:
        print(f"   - {test_file.name}")
    
    # Run all tests
    results: Dict[str, Tuple[bool, str]] = {}
    
    for test_file in test_files:
        name, success, output = run_test_file(test_file)
        results[name] = (success, output)
    
    # Print summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for success, _ in results.values() if success)
    failed = len(results) - passed
    
    print(f"Total tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success rate: {(passed/len(results)*100):.1f}%")
    
    if failed > 0:
        print(f"\n❌ FAILED TESTS:")
        for name, (success, output) in results.items():
            if not success:
                print(f"   - {name}")
    
    print(f"\n✅ PASSED TESTS:")
    for name, (success, output) in results.items():
        if success:
            print(f"   - {name}")
    
    print("\n" + "=" * 80)
    if failed == 0:
        print("🎉 ALL TESTS PASSED!")
    else:
        print(f"⚠️  {failed} test(s) failed. Check the output above for details.")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
