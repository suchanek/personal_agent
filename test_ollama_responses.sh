#!/bin/bash

# Test Ollama Raw Responses - llama3.1:8b
# Purpose: Identify source of <thinking> tags in responses
# Usage: ./test_ollama_responses.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MODEL="llama3.1:8b"
OLLAMA_URL="http://tesla.local:11434"
RESULTS_DIR="/tmp/ollama_test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create results directory
mkdir -p "$RESULTS_DIR"

echo -e "${BLUE}=== Ollama Response Testing Suite ===${NC}"
echo -e "${BLUE}Model: $MODEL${NC}"
echo -e "${BLUE}Timestamp: $TIMESTAMP${NC}"
echo -e "${BLUE}Results will be saved to: $RESULTS_DIR/${NC}"
echo ""

# Function to run test and save results
run_test() {
    local test_name="$1"
    local test_data="$2"
    local output_file="$RESULTS_DIR/${TIMESTAMP}_${test_name}.json"
    local response_file="$RESULTS_DIR/${TIMESTAMP}_${test_name}_response.txt"
    
    echo -e "${YELLOW}Running Test: $test_name${NC}"
    echo "Request data: $test_data"
    echo ""
    
    # Run curl and save full response
    if curl -s -X POST "$OLLAMA_URL/api/generate" \
        -H "Content-Type: application/json" \
        -d "$test_data" > "$output_file"; then
        
        echo -e "${GREEN}✓ Test completed successfully${NC}"
        
        # Extract and display response text
        if command -v jq >/dev/null 2>&1; then
            echo -e "${BLUE}Response text:${NC}"
            jq -r '.response' "$output_file" | tee "$response_file"
            
            # Check for thinking tags
            if grep -q "<thinking>" "$response_file" 2>/dev/null; then
                echo -e "${RED}⚠️  THINKING TAGS DETECTED in raw response!${NC}"
            else
                echo -e "${GREEN}✓ No thinking tags found in raw response${NC}"
            fi
        else
            echo -e "${YELLOW}jq not found - saving raw response only${NC}"
            cat "$output_file" > "$response_file"
        fi
        
        echo -e "Full response saved to: $output_file"
        echo -e "Response text saved to: $response_file"
        
    else
        echo -e "${RED}✗ Test failed${NC}"
        return 1
    fi
    
    echo ""
    echo "----------------------------------------"
    echo ""
}

# Function to run chat test
run_chat_test() {
    local test_name="$1"
    local test_data="$2"
    local output_file="$RESULTS_DIR/${TIMESTAMP}_${test_name}.json"
    local response_file="$RESULTS_DIR/${TIMESTAMP}_${test_name}_response.txt"
    
    echo -e "${YELLOW}Running Chat Test: $test_name${NC}"
    echo "Request data: $test_data"
    echo ""
    
    # Run curl with chat endpoint
    if curl -s -X POST "$OLLAMA_URL/api/chat" \
        -H "Content-Type: application/json" \
        -d "$test_data" > "$output_file"; then
        
        echo -e "${GREEN}✓ Chat test completed successfully${NC}"
        
        # Extract and display response text
        if command -v jq >/dev/null 2>&1; then
            echo -e "${BLUE}Response text:${NC}"
            jq -r '.message.content' "$output_file" | tee "$response_file"
            
            # Check for thinking tags
            if grep -q "<thinking>" "$response_file" 2>/dev/null; then
                echo -e "${RED}⚠️  THINKING TAGS DETECTED in raw response!${NC}"
            else
                echo -e "${GREEN}✓ No thinking tags found in raw response${NC}"
            fi
        else
            echo -e "${YELLOW}jq not found - saving raw response only${NC}"
            cat "$output_file" > "$response_file"
        fi
        
        echo -e "Full response saved to: $output_file"
        echo -e "Response text saved to: $response_file"
        
    else
        echo -e "${RED}✗ Chat test failed${NC}"
        return 1
    fi
    
    echo ""
    echo "----------------------------------------"
    echo ""
}

# Test 1: Basic Question
echo -e "${BLUE}TEST 1: Basic Question${NC}"
run_test "basic_question" '{
    "model": "'$MODEL'",
    "prompt": "What is the capital of France?",
    "stream": false
}'

# Test 2: Complex Reasoning (Most likely to trigger thinking tags)
echo -e "${BLUE}TEST 2: Complex Reasoning${NC}"
run_test "complex_reasoning" '{
    "model": "'$MODEL'",
    "prompt": "I need to plan a trip to Japan. Help me create an itinerary for 7 days including Tokyo and Kyoto. Consider budget, transportation, and must-see attractions.",
    "stream": false,
    "options": {
        "stream": false
    }
}'

# Test 3: Agent Configuration (Your exact Agno settings)
echo -e "${BLUE}TEST 3: Agent Configuration${NC}"
run_test "agent_config" '{
    "model": "'$MODEL'",
    "prompt": "You are an advanced personal AI assistant with comprehensive capabilities and built-in memory. What is artificial intelligence and how does machine learning work?",
    "stream": false,
    "options": {
        "temperature": 0.7,
        "top_p": 0.9,
        "top_k": 40,
        "repeat_penalty": 1.1,
        "num_ctx": 4096,
        "num_predict": 2048,
        "num_thread": 8
    }
}'

# Test 4: System Prompt (Chat format with explicit instructions)
echo -e "${BLUE}TEST 4: System Prompt (Chat Format)${NC}"
run_chat_test "system_prompt" '{
    "model": "'$MODEL'",
    "messages": [
        {
            "role": "system",
            "content": "You are a helpful assistant. Provide direct answers without showing your thinking process."
        },
        {
            "role": "user",
            "content": "Explain the difference between renewable and non-renewable energy sources."
        }
    ],
    "stream": false
}'

# Test 5: Problem-solving prompt (High chance of thinking tags)
echo -e "${BLUE}TEST 5: Problem Solving${NC}"
run_test "problem_solving" '{
    "model": "'$MODEL'",
    "prompt": "Solve this step by step: If a train travels 120 miles in 2 hours, and then travels 180 miles in 3 hours, what is the average speed for the entire journey?",
    "stream": false
}'

# Test 6: Creative writing (Another potential trigger)
echo -e "${BLUE}TEST 6: Creative Writing${NC}"
run_test "creative_writing" '{
    "model": "'$MODEL'",
    "prompt": "Write a short story about a robot who discovers emotions. Make it engaging and thoughtful.",
    "stream": false
}'

# Summary
echo -e "${BLUE}=== TEST SUMMARY ===${NC}"
echo -e "All test results saved to: $RESULTS_DIR/"
echo -e "Timestamp: $TIMESTAMP"
echo ""
echo -e "${YELLOW}To analyze results:${NC}"
echo -e "1. Check *_response.txt files for thinking tags"
echo -e "2. Compare responses across different test types"
echo -e "3. Look for patterns in when thinking tags appear"
echo ""
echo -e "${YELLOW}Quick analysis command:${NC}"
echo -e "grep -l '<thinking>' $RESULTS_DIR/${TIMESTAMP}_*_response.txt"
echo ""
echo -e "${GREEN}Testing complete!${NC}"
