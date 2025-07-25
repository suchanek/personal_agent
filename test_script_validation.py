#!/usr/bin/env python3
"""
Quick validation script to test if the model testing script can import correctly
and basic functionality works.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_imports():
    """Test if all required imports work."""
    try:
        from src.personal_agent.core.agno_agent import create_agno_agent
        from src.personal_agent.core.agent_instruction_manager import InstructionLevel
        from src.personal_agent.config.settings import OLLAMA_URL, USER_ID
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_model_tester_class():
    """Test if ModelTester class can be instantiated."""
    try:
        # Import the ModelTester class from our script
        import importlib.util
        spec = importlib.util.spec_from_file_location("test_ollama_models", "test_ollama_models.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Test instantiation
        models = ["qwen3:8b"]  # Just one model for testing
        queries = ["hello"]    # Just one query for testing
        tester = module.ModelTester(models, queries, "test_output.json")
        
        print("✅ ModelTester class instantiated successfully")
        print(f"   Models: {tester.models}")
        print(f"   Queries: {tester.queries}")
        print(f"   Output file: {tester.output_file}")
        return True
    except Exception as e:
        print(f"❌ ModelTester instantiation error: {e}")
        return False

def test_settings():
    """Test if settings are loaded correctly."""
    try:
        from src.personal_agent.config.settings import OLLAMA_URL, USER_ID, LLM_MODEL
        print("✅ Settings loaded successfully")
        print(f"   OLLAMA_URL: {OLLAMA_URL}")
        print(f"   USER_ID: {USER_ID}")
        print(f"   LLM_MODEL: {LLM_MODEL}")
        return True
    except Exception as e:
        print(f"❌ Settings error: {e}")
        return False

def main():
    """Run all validation tests."""
    print("🧪 Validating model testing script...")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Settings Test", test_settings),
        ("ModelTester Class Test", test_model_tester_class),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        if test_func():
            passed += 1
        else:
            print(f"   Test failed!")
    
    print("\n" + "=" * 50)
    print(f"📊 Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed! The script should work correctly.")
        return True
    else:
        print("⚠️  Some validation tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
