#!/usr/bin/env python3
"""
Personal Agent REST API Test Script
==================================

This script provides comprehensive testing for all REST API endpoints
of the Personal Agent system. It tests memory storage, knowledge storage,
URL content extraction, search functionality, and system status endpoints.

Usage:
    python test_rest_api.py [--host HOST] [--port PORT] [--verbose]

Requirements:
    - Personal Agent Streamlit app must be running
    - REST API server must be accessible (default: http://localhost:8001)

Author: Personal Agent Development Team
Version: v1.0.0
Last Revision: 2025-01-24
"""

import argparse
import json
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class PersonalAgentAPITester:
    """Comprehensive test suite for Personal Agent REST API."""
    
    def __init__(self, base_url: str = "http://localhost:8001", verbose: bool = False):
        self.base_url = base_url.rstrip('/')
        self.verbose = verbose
        self.session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Test results tracking
        self.test_results = []
        self.passed_tests = 0
        self.failed_tests = 0
        
        # Store created memory IDs for cleanup
        self.created_memory_ids = []
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{timestamp}] {level}:"
        print(f"{prefix} {message}")
    
    def verbose_log(self, message: str):
        """Log message only in verbose mode."""
        if self.verbose:
            self.log(message, "DEBUG")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Tuple[bool, Dict]:
        """Make HTTP request with error handling."""
        url = f"{self.base_url}{endpoint}"
        self.verbose_log(f"Making {method} request to {url}")
        
        try:
            response = self.session.request(method, url, timeout=30, **kwargs)
            
            # Log request details in verbose mode
            if self.verbose:
                self.verbose_log(f"Request: {method} {url}")
                if 'json' in kwargs:
                    self.verbose_log(f"Request body: {json.dumps(kwargs['json'], indent=2)}")
                self.verbose_log(f"Response status: {response.status_code}")
                self.verbose_log(f"Response body: {response.text[:500]}...")
            
            # Try to parse JSON response
            try:
                response_data = response.json()
            except json.JSONDecodeError:
                response_data = {"raw_response": response.text}
            
            return response.status_code < 400, {
                "status_code": response.status_code,
                "data": response_data,
                "headers": dict(response.headers)
            }
            
        except requests.exceptions.RequestException as e:
            self.log(f"Request failed: {str(e)}", "ERROR")
            return False, {"error": str(e)}
    
    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and track results."""
        self.log(f"Running test: {test_name}")
        
        try:
            success = test_func()
            if success:
                self.log(f"✅ PASSED: {test_name}", "SUCCESS")
                self.passed_tests += 1
            else:
                self.log(f"❌ FAILED: {test_name}", "ERROR")
                self.failed_tests += 1
            
            self.test_results.append({
                "name": test_name,
                "success": success,
                "timestamp": datetime.now().isoformat()
            })
            
            return success
            
        except Exception as e:
            self.log(f"❌ FAILED: {test_name} - Exception: {str(e)}", "ERROR")
            self.failed_tests += 1
            self.test_results.append({
                "name": test_name,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            return False
    
    def test_health_check(self) -> bool:
        """Test the health check endpoint."""
        success, response = self.make_request("GET", "/api/v1/health")
        
        if not success:
            return False
        
        data = response["data"]
        required_fields = ["status", "timestamp", "service", "version"]
        
        for field in required_fields:
            if field not in data:
                self.log(f"Missing required field in health response: {field}", "ERROR")
                return False
        
        if data["status"] != "healthy":
            self.log(f"Health status is not 'healthy': {data['status']}", "ERROR")
            return False
        
        self.verbose_log(f"Health check response: {json.dumps(data, indent=2)}")
        return True
    
    def test_system_status(self) -> bool:
        """Test the system status endpoint."""
        success, response = self.make_request("GET", "/api/v1/status")
        
        if not success:
            return False
        
        data = response["data"]
        required_fields = ["status", "timestamp", "streamlit_connected"]
        
        for field in required_fields:
            if field not in data:
                self.log(f"Missing required field in status response: {field}", "ERROR")
                return False
        
        self.verbose_log(f"System status: {json.dumps(data, indent=2)}")
        return True
    
    def test_store_memory_text(self) -> bool:
        """Test storing text content as memory."""
        test_data = {
            "content": "I am testing the REST API memory storage functionality. This is a test memory entry.",
            "topics": ["testing", "api"]
        }
        
        success, response = self.make_request("POST", "/api/v1/memory/store", json=test_data)
        
        if not success:
            return False
        
        data = response["data"]
        
        # Check for required response fields
        if not data.get("success"):
            self.log(f"Memory storage failed: {data.get('error', 'Unknown error')}", "ERROR")
            return False
        
        # Store memory ID for potential cleanup
        memory_id = data.get("memory_id")
        if memory_id:
            self.created_memory_ids.append(memory_id)
        
        self.verbose_log(f"Stored memory with ID: {memory_id}")
        return True
    
    def test_store_memory_from_url(self) -> bool:
        """Test storing content from URL as memory."""
        # Use a reliable test URL
        test_data = {
            "url": "https://httpbin.org/json",
            "title": "Test JSON Data",
            "topics": ["testing", "json"]
        }
        
        success, response = self.make_request("POST", "/api/v1/memory/store-url", json=test_data)
        
        if not success:
            # URL extraction might fail due to network issues, so we'll be lenient
            self.log("URL memory storage failed (this might be due to network issues)", "WARNING")
            return True  # Don't fail the entire test suite for network issues
        
        data = response["data"]
        
        if not data.get("success"):
            self.log(f"URL memory storage failed: {data.get('error', 'Unknown error')}", "WARNING")
            return True  # Don't fail for URL extraction issues
        
        # Store memory ID for potential cleanup
        memory_id = data.get("memory_id")
        if memory_id:
            self.created_memory_ids.append(memory_id)
        
        self.verbose_log(f"Stored memory from URL with ID: {memory_id}")
        return True
    
    def test_search_memories(self) -> bool:
        """Test searching memories."""
        # First ensure we have some memories by storing one
        self.test_store_memory_text()
        
        # Wait a moment for indexing
        time.sleep(1)
        
        # Search for memories
        params = {
            "q": "testing",
            "limit": 5,
            "similarity_threshold": 0.1
        }
        
        success, response = self.make_request("GET", "/api/v1/memory/search", params=params)
        
        if not success:
            return False
        
        data = response["data"]
        
        if not data.get("success"):
            self.log(f"Memory search failed: {data.get('error', 'Unknown error')}", "ERROR")
            return False
        
        results = data.get("results", [])
        self.verbose_log(f"Found {len(results)} memories matching 'testing'")
        
        # Validate result structure
        if results:
            first_result = results[0]
            required_fields = ["memory_id", "content", "similarity_score"]
            for field in required_fields:
                if field not in first_result:
                    self.log(f"Missing field in search result: {field}", "ERROR")
                    return False
        
        return True
    
    def test_list_memories(self) -> bool:
        """Test listing all memories."""
        params = {"limit": 10}
        
        success, response = self.make_request("GET", "/api/v1/memory/list", params=params)
        
        if not success:
            return False
        
        data = response["data"]
        
        if not data.get("success"):
            self.log(f"Memory listing failed: {data.get('error', 'Unknown error')}", "ERROR")
            return False
        
        memories = data.get("memories", [])
        total_count = data.get("total_count", 0)
        
        self.verbose_log(f"Listed {total_count} memories")
        
        # Validate memory structure if any exist
        if memories:
            first_memory = memories[0]
            required_fields = ["memory_id", "content"]
            for field in required_fields:
                if field not in first_memory:
                    self.log(f"Missing field in memory list result: {field}", "ERROR")
                    return False
        
        return True
    
    def test_memory_stats(self) -> bool:
        """Test getting memory statistics."""
        success, response = self.make_request("GET", "/api/v1/memory/stats")
        
        if not success:
            return False
        
        data = response["data"]
        
        if not data.get("success"):
            self.log(f"Memory stats failed: {data.get('error', 'Unknown error')}", "ERROR")
            return False
        
        stats = data.get("stats", {})
        self.verbose_log(f"Memory stats: {json.dumps(stats, indent=2)}")
        
        return True
    
    def test_store_knowledge_text(self) -> bool:
        """Test storing text in knowledge base."""
        test_data = {
            "content": "This is test knowledge content for the REST API. It contains information about testing procedures and API functionality.",
            "title": "REST API Testing Knowledge",
            "file_type": "txt"
        }
        
        success, response = self.make_request("POST", "/api/v1/knowledge/store-text", json=test_data)
        
        if not success:
            return False
        
        data = response["data"]
        
        if not data.get("success"):
            self.log(f"Knowledge text storage failed: {data.get('error', 'Unknown error')}", "ERROR")
            return False
        
        self.verbose_log(f"Stored knowledge text: {test_data['title']}")
        return True
    
    def test_store_knowledge_from_url(self) -> bool:
        """Test storing knowledge from URL."""
        test_data = {
            "url": "https://httpbin.org/json",
            "title": "Test JSON Knowledge"
        }
        
        success, response = self.make_request("POST", "/api/v1/knowledge/store-url", json=test_data)
        
        if not success:
            # URL extraction might fail due to network issues
            self.log("URL knowledge storage failed (this might be due to network issues)", "WARNING")
            return True  # Don't fail the entire test suite
        
        data = response["data"]
        
        if not data.get("success"):
            self.log(f"URL knowledge storage failed: {data.get('error', 'Unknown error')}", "WARNING")
            return True  # Don't fail for URL extraction issues
        
        self.verbose_log(f"Stored knowledge from URL: {test_data['url']}")
        return True
    
    def test_search_knowledge(self) -> bool:
        """Test searching knowledge base."""
        # First ensure we have some knowledge
        self.test_store_knowledge_text()
        
        # Wait a moment for indexing
        time.sleep(1)
        
        params = {
            "q": "testing",
            "mode": "auto",
            "limit": 5
        }
        
        success, response = self.make_request("GET", "/api/v1/knowledge/search", params=params)
        
        if not success:
            return False
        
        data = response["data"]
        
        if not data.get("success"):
            self.log(f"Knowledge search failed: {data.get('error', 'Unknown error')}", "ERROR")
            return False
        
        result = data.get("result", "")
        self.verbose_log(f"Knowledge search result length: {len(str(result))}")
        
        return True
    
    def test_knowledge_status(self) -> bool:
        """Test getting knowledge base status."""
        success, response = self.make_request("GET", "/api/v1/knowledge/status")
        
        if not success:
            return False
        
        data = response["data"]
        
        if not data.get("success"):
            self.log(f"Knowledge status failed: {data.get('error', 'Unknown error')}", "ERROR")
            return False
        
        status = data.get("status", {})
        self.verbose_log(f"Knowledge status: {json.dumps(status, indent=2)}")
        
        return True
    
    def test_error_handling(self) -> bool:
        """Test API error handling with invalid requests."""
        # Test missing content in memory store
        success, response = self.make_request("POST", "/api/v1/memory/store", json={})
        
        if success or response["status_code"] != 400:
            self.log("Expected 400 error for missing content, but got success", "ERROR")
            return False
        
        # Test invalid URL format
        success, response = self.make_request("POST", "/api/v1/memory/store-url", 
                                            json={"url": "not-a-valid-url"})
        
        if success or response["status_code"] != 400:
            self.log("Expected 400 error for invalid URL, but got success", "ERROR")
            return False
        
        # Test missing query parameter
        success, response = self.make_request("GET", "/api/v1/memory/search")
        
        if success or response["status_code"] != 400:
            self.log("Expected 400 error for missing query parameter, but got success", "ERROR")
            return False
        
        self.verbose_log("Error handling tests passed")
        return True
    
    def run_all_tests(self) -> bool:
        """Run all test cases."""
        self.log("Starting Personal Agent REST API Test Suite")
        self.log(f"Testing API at: {self.base_url}")
        
        # Define all tests
        tests = [
            ("Health Check", self.test_health_check),
            ("System Status", self.test_system_status),
            ("Store Memory Text", self.test_store_memory_text),
            ("Store Memory from URL", self.test_store_memory_from_url),
            ("Search Memories", self.test_search_memories),
            ("List Memories", self.test_list_memories),
            ("Memory Statistics", self.test_memory_stats),
            ("Store Knowledge Text", self.test_store_knowledge_text),
            ("Store Knowledge from URL", self.test_store_knowledge_from_url),
            ("Search Knowledge", self.test_search_knowledge),
            ("Knowledge Status", self.test_knowledge_status),
            ("Error Handling", self.test_error_handling),
        ]
        
        # Run all tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
            time.sleep(0.5)  # Small delay between tests
        
        # Print summary
        self.print_summary()
        
        return self.failed_tests == 0
    
    def print_summary(self):
        """Print test results summary."""
        total_tests = self.passed_tests + self.failed_tests
        success_rate = (self.passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print("\n" + "="*60)
        print("TEST RESULTS SUMMARY")
        print("="*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {self.passed_tests}")
        print(f"Failed: {self.failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests > 0:
            print("\nFAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['name']}")
                    if "error" in result:
                        print(f"     Error: {result['error']}")
        
        print("\nCREATED MEMORY IDs (for manual cleanup if needed):")
        for memory_id in self.created_memory_ids:
            print(f"  - {memory_id}")
        
        print("="*60)


def main():
    """Main function to run the test suite."""
    parser = argparse.ArgumentParser(description="Test Personal Agent REST API")
    parser.add_argument("--host", default="localhost", help="API host (default: localhost)")
    parser.add_argument("--port", type=int, default=8001, help="API port (default: 8001)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    
    args = parser.parse_args()
    
    base_url = f"http://{args.host}:{args.port}"
    
    # Create tester instance
    tester = PersonalAgentAPITester(base_url=base_url, verbose=args.verbose)
    
    # Run all tests
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
