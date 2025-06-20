#!/bin/bash

# Simple script to run the tool call detection test

echo "🚀 Running Tool Call Detection Test"
echo "=================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python3."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "test_tool_call_detection.py" ]; then
    echo "❌ test_tool_call_detection.py not found. Please run from the project root."
    exit 1
fi

# Run the test
echo "🧪 Starting test execution..."
python3 test_tool_call_detection.py

echo ""
echo "✅ Test execution completed!"
echo ""
echo "📝 To run this test again, use:"
echo "   python3 test_tool_call_detection.py"
echo "   or"
echo "   bash run_tool_test.sh"
