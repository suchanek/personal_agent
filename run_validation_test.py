#!/usr/bin/env python3
"""
Simple runner script for the Pydantic validation fix test.

This script runs the comprehensive test to verify that:
1. The Pydantic ValidationError is fixed
2. Tool calling works properly (no <|python_tag|> output)
3. Memory system functions correctly
4. Model upgrade is effective
"""

import asyncio
import subprocess
import sys
from pathlib import Path


def check_ollama_running():
    """Check if Ollama is running."""
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def check_model_available(model_name="llama3.1:8b"):
    """Check if the required model is available in Ollama."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            return model_name in result.stdout
        return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


async def main():
    """Main function to run the validation test."""
    print("🚀 Pydantic Validation Fix Test Runner")
    print("=" * 50)
    
    # Check prerequisites
    print("🔍 Checking prerequisites...")
    
    if not check_ollama_running():
        print("❌ Ollama is not running!")
        print("   Please start Ollama with: ollama serve")
        return False
    
    print("✅ Ollama is running")
    
    if not check_model_available("llama3.1:8b"):
        print("⚠️ llama3.1:8b model not found")
        print("   Downloading model... (this may take a while)")
        try:
            result = subprocess.run(
                ["ollama", "pull", "llama3.1:8b"],
                timeout=300  # 5 minutes timeout
            )
            if result.returncode != 0:
                print("❌ Failed to download model")
                return False
        except subprocess.TimeoutExpired:
            print("❌ Model download timed out")
            return False
    
    print("✅ Model is available")
    
    # Run the test
    print("\n🧪 Running validation tests...")
    
    try:
        # Import and run the test
        test_file = Path(__file__).parent / "tests" / "test_pydantic_validation_fix.py"
        
        if not test_file.exists():
            print(f"❌ Test file not found: {test_file}")
            return False
        
        # Run the test script
        result = subprocess.run([
            sys.executable, str(test_file)
        ], cwd=Path(__file__).parent)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


if __name__ == "__main__":
    print("This script runs comprehensive tests to validate the fixes for:")
    print("• Pydantic ValidationError in store_user_memory")
    print("• Tool calling issues (<|python_tag|> output)")
    print("• Memory system functionality")
    print("• Model configuration improvements")
    print()
    
    success = asyncio.run(main())
    
    if success:
        print("\n🎉 All validation tests passed!")
        print("✅ The fixes are working correctly")
    else:
        print("\n❌ Validation tests failed")
        print("🔧 Please check the error messages above")
    
    sys.exit(0 if success else 1)
