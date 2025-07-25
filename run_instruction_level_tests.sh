#!/bin/bash

# Ollama Model Testing Script - Instruction Level Comparison
# This script runs the test_ollama_models.py script with different instruction levels
# and collects results for comparison.

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${BLUE}================================================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================================================================================${NC}"
}

print_info() {
    echo -e "${CYAN}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Create timestamp for this test run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_DIR="instruction_level_comparison_${TIMESTAMP}"

print_header "🚀 OLLAMA MODEL INSTRUCTION LEVEL COMPARISON TEST"
print_info "Starting comprehensive instruction level testing at $(date)"
print_info "Results will be saved in: ${RESULTS_DIR}/"

# Create results directory
mkdir -p "${RESULTS_DIR}"

# Define instruction levels to test
INSTRUCTION_LEVELS=("CONCISE" "STANDARD" "EXPLICIT")

# Track overall start time
OVERALL_START=$(date +%s)

# Initialize summary arrays
declare -a SUCCESSFUL_TESTS=()
declare -a FAILED_TESTS=()

print_info "Testing instruction levels: ${INSTRUCTION_LEVELS[*]}"
echo ""

# Run tests for each instruction level
for level in "${INSTRUCTION_LEVELS[@]}"; do
    print_header "🔧 TESTING INSTRUCTION LEVEL: ${level}"
    
    # Track start time for this level
    LEVEL_START=$(date +%s)
    
    print_info "Running test_ollama_models.py with --instruction-level ${level}"
    
    # Run the Python script with the current instruction level
    if python test_ollama_models.py --instruction-level "${level}"; then
        LEVEL_END=$(date +%s)
        LEVEL_DURATION=$((LEVEL_END - LEVEL_START))
        
        print_success "Instruction level ${level} completed successfully in ${LEVEL_DURATION} seconds"
        SUCCESSFUL_TESTS+=("${level}")
        
        # Move the generated results file to our results directory
        RESULT_FILE=$(ls -t model_test_results_${level,,}_*.json 2>/dev/null | head -n1)
        if [[ -n "$RESULT_FILE" ]]; then
            mv "$RESULT_FILE" "${RESULTS_DIR}/"
            print_info "Results file moved to: ${RESULTS_DIR}/${RESULT_FILE}"
        else
            print_warning "Could not find results file for ${level}"
        fi
        
    else
        LEVEL_END=$(date +%s)
        LEVEL_DURATION=$((LEVEL_END - LEVEL_START))
        
        print_error "Instruction level ${level} failed after ${LEVEL_DURATION} seconds"
        FAILED_TESTS+=("${level}")
        
        # Still try to move any partial results
        RESULT_FILE=$(ls -t model_test_results_${level,,}_*.json 2>/dev/null | head -n1)
        if [[ -n "$RESULT_FILE" ]]; then
            mv "$RESULT_FILE" "${RESULTS_DIR}/"
            print_info "Partial results file moved to: ${RESULTS_DIR}/${RESULT_FILE}"
        fi
    fi
    
    echo ""
done

# Calculate overall duration
OVERALL_END=$(date +%s)
OVERALL_DURATION=$((OVERALL_END - OVERALL_START))

# Generate summary report
SUMMARY_FILE="${RESULTS_DIR}/instruction_level_comparison_summary.txt"

print_header "📊 GENERATING COMPARISON SUMMARY"

cat > "${SUMMARY_FILE}" << EOF
OLLAMA MODEL INSTRUCTION LEVEL COMPARISON TEST SUMMARY
======================================================

Test Run: ${TIMESTAMP}
Test Date: $(date)
Overall Duration: ${OVERALL_DURATION} seconds ($(($OVERALL_DURATION / 60)) minutes)

INSTRUCTION LEVELS TESTED:
- CONCISE: Focused on capabilities over rules
- STANDARD: Detailed instructions (baseline)
- EXPLICIT: Extra verbose for models needing guidance

RESULTS SUMMARY:
================

Successful Tests (${#SUCCESSFUL_TESTS[@]}/${#INSTRUCTION_LEVELS[@]}):
EOF

for level in "${SUCCESSFUL_TESTS[@]}"; do
    echo "✅ ${level}" >> "${SUMMARY_FILE}"
done

cat >> "${SUMMARY_FILE}" << EOF

Failed Tests (${#FAILED_TESTS[@]}/${#INSTRUCTION_LEVELS[@]}):
EOF

for level in "${FAILED_TESTS[@]}"; do
    echo "❌ ${level}" >> "${SUMMARY_FILE}"
done

cat >> "${SUMMARY_FILE}" << EOF

RESULT FILES:
=============
EOF

# List all result files in the directory
for file in "${RESULTS_DIR}"/model_test_results_*.json; do
    if [[ -f "$file" ]]; then
        filename=$(basename "$file")
        filesize=$(du -h "$file" | cut -f1)
        echo "📄 ${filename} (${filesize})" >> "${SUMMARY_FILE}"
    fi
done

cat >> "${SUMMARY_FILE}" << EOF

ANALYSIS RECOMMENDATIONS:
========================

1. Compare response quality across instruction levels for each model
2. Analyze performance differences (initialization time, query duration)
3. Look for patterns in error rates between instruction levels
4. Identify which models benefit most from different instruction levels
5. Use results to optimize instruction level selection for production

NEXT STEPS:
===========

1. Review individual JSON result files for detailed analysis
2. Use parse_test_results.py to generate comparative charts
3. Consider running additional tests with MINIMAL or EXPERIMENTAL levels
4. Document findings for model selection and configuration decisions

EOF

print_success "Summary report generated: ${SUMMARY_FILE}"

# Display summary to console
print_header "📊 TEST COMPLETION SUMMARY"

echo ""
print_info "Overall Duration: ${OVERALL_DURATION} seconds ($(($OVERALL_DURATION / 60)) minutes)"
print_info "Results Directory: ${RESULTS_DIR}/"

if [[ ${#SUCCESSFUL_TESTS[@]} -gt 0 ]]; then
    print_success "Successful Tests (${#SUCCESSFUL_TESTS[@]}/${#INSTRUCTION_LEVELS[@]}):"
    for level in "${SUCCESSFUL_TESTS[@]}"; do
        echo -e "  ${GREEN}✅ ${level}${NC}"
    done
fi

if [[ ${#FAILED_TESTS[@]} -gt 0 ]]; then
    print_error "Failed Tests (${#FAILED_TESTS[@]}/${#INSTRUCTION_LEVELS[@]}):"
    for level in "${FAILED_TESTS[@]}"; do
        echo -e "  ${RED}❌ ${level}${NC}"
    done
fi

echo ""
print_info "📄 Summary report: ${SUMMARY_FILE}"
print_info "📁 All results saved in: ${RESULTS_DIR}/"

if [[ ${#SUCCESSFUL_TESTS[@]} -eq ${#INSTRUCTION_LEVELS[@]} ]]; then
    print_success "🎉 All instruction level tests completed successfully!"
    exit 0
elif [[ ${#SUCCESSFUL_TESTS[@]} -gt 0 ]]; then
    print_warning "⚠️  Some tests completed successfully, but ${#FAILED_TESTS[@]} failed"
    exit 1
else
    print_error "💥 All instruction level tests failed"
    exit 2
fi
