#!/bin/bash

# Run the CLI memory commands test script
echo "Running CLI memory commands test script..."
python memory_tests/test_cli_memory_commands.py

# Check the exit code
if [ $? -eq 0 ]; then
    echo "✅ Tests completed successfully!"
else
    echo "❌ Tests failed!"
fi