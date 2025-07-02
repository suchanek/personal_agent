#!/usr/bin/env python3
"""
Quick runner for the tool call debug output test.

This script runs the test to verify that the Streamlit debug output fix is working.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the tool call debug output test."""
    print("🚀 Running Tool Call Debug Output Test")
    print("=" * 50)
    print("This test verifies that the Streamlit debug output fix is working correctly.")
    print("It will test tool call argument parsing and display.\n")
    
    # Path to the test script
    test_script = Path(__file__).parent / "test_tool_call_debug_output.py"
    
    if not test_script.exists():
        print(f"❌ Test script not found: {test_script}")
        return 1
    
    try:
        # Run the test script
        result = subprocess.run([sys.executable, str(test_script)], 
                              capture_output=False, 
                              text=True)
        
        if result.returncode == 0:
            print("\n🎉 Test completed successfully!")
            print("The tool call debug output fix appears to be working.")
        else:
            print(f"\n❌ Test failed with return code: {result.returncode}")
            print("Check the output above for error details.")
        
        return result.returncode
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
