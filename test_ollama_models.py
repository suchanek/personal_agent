#!.venv/bin/python
"""
Ollama Model Testing Script

This script tests multiple Ollama models with the same set of queries at a configurable instruction level.
It logs the output to a file and monitors duration for each query.

Usage:
    python test_ollama_models.py [--instruction-level LEVEL] [--no-memory]

Available instruction levels:
- NONE: Minimal instructions
- MINIMAL: Basic guidance for capable models
- CONCISE: Focused on capabilities over rules
- STANDARD: Detailed instructions (default)
- EXPLICIT: Extra verbose for models needing guidance
- EXPERIMENTAL: Testing new rule prioritization

Options:
- --instruction-level: Set the instruction sophistication level
- --no-memory: Disable memory for consistent testing (memory enabled by default)

Models to test:
- qwen3:4b
- qwen2.5-coder:3b
- qwen2.5:latest
- qwen3:1.7B
- llama3.2:3b
- llama3:1.7b

Queries:
- "hello"
- "list your tools"
- "give me a financial analysis of NVDA"
"""

import argparse
import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.personal_agent.config.settings import OLLAMA_URL, USER_ID
from src.personal_agent.core.agent_instruction_manager import InstructionLevel
from src.personal_agent.core.agno_agent import create_agno_agent


class ModelTester:
    """Test multiple Ollama models with the same queries."""

    def __init__(
        self,
        models: List[str],
        queries: List[str],
        instruction_level: InstructionLevel = InstructionLevel.STANDARD,
        enable_memory: bool = True,
        output_file: str = "model_test_results.json",
    ):
        """
        Initialize the model tester.

        Args:
            models: List of model names to test
            queries: List of queries to test with each model
            instruction_level: The instruction level to use for testing
            enable_memory: Whether to enable memory for realistic testing
            output_file: Output file for results
        """
        self.models = models
        self.queries = queries
        self.instruction_level = instruction_level
        self.enable_memory = enable_memory
        self.output_file = output_file
        self.results = {}

    async def test_model(self, model_name: str) -> Dict[str, Any]:
        """
        Test a single model with all queries.

        Args:
            model_name: Name of the model to test

        Returns:
            Dictionary containing test results for the model
        """
        print(f"\n🤖 Testing model: {model_name}")
        print("=" * 50)

        model_results = {
            "model_name": model_name,
            "test_timestamp": datetime.now().isoformat(),
            "queries": {},
            "total_duration": 0,
            "initialization_time": 0,
            "errors": [],
        }

        try:
            # Initialize agent with specified instruction level
            init_start = time.time()
            agent = await create_agno_agent(
                model_provider="ollama",
                model_name=model_name,
                enable_memory=self.enable_memory,  # Use configurable memory setting
                enable_mcp=True,  # Disable MCP for consistent testing
                debug=False,
                ollama_base_url=OLLAMA_URL,
                user_id=USER_ID,
                recreate=False,
                instruction_level=self.instruction_level,
            )
            init_time = time.time() - init_start
            model_results["initialization_time"] = init_time

            print(f"✅ Agent initialized in {init_time:.2f}s")

            # Test each query
            total_query_time = 0
            for i, query in enumerate(self.queries, 1):
                print(f"\n📝 Query {i}/{len(self.queries)}: '{query}'")

                query_start = time.time()
                try:
                    response = await agent.run(query)
                    query_duration = time.time() - query_start
                    total_query_time += query_duration

                    query_result = {
                        "query": query,
                        "response": response,
                        "duration": query_duration,
                        "success": True,
                        "error": None,
                    }

                    print(f"⏱️  Duration: {query_duration:.2f}s")
                    print(
                        f"🤖 Response: {response[:200]}{'...' if len(response) > 200 else response}"
                    )

                except Exception as e:
                    query_duration = time.time() - query_start
                    total_query_time += query_duration
                    error_msg = str(e)

                    query_result = {
                        "query": query,
                        "response": None,
                        "duration": query_duration,
                        "success": False,
                        "error": error_msg,
                    }

                    print(f"❌ Error after {query_duration:.2f}s: {error_msg}")
                    model_results["errors"].append(f"Query '{query}': {error_msg}")

                model_results["queries"][f"query_{i}"] = query_result

            model_results["total_duration"] = init_time + total_query_time

            # Cleanup agent
            if hasattr(agent, "cleanup"):
                await agent.cleanup()

            print(
                f"\n✅ Model {model_name} completed in {model_results['total_duration']:.2f}s total"
            )

        except Exception as e:
            error_msg = f"Failed to initialize or test model {model_name}: {str(e)}"
            print(f"❌ {error_msg}")
            model_results["errors"].append(error_msg)
            model_results["initialization_error"] = error_msg

        return model_results

    async def run_tests(self) -> Dict[str, Any]:
        """
        Run tests on all models.

        Returns:
            Complete test results
        """
        print("🚀 Starting Ollama Model Testing")
        print(f"📋 Models to test: {', '.join(self.models)}")
        print(f"📝 Queries: {len(self.queries)} queries")
        print(f"📄 Output file: {self.output_file}")
        print(f"🔧 Instruction level: {self.instruction_level.name}")
        print(f"🧠 Memory: {'Enabled' if self.enable_memory else 'Disabled'}")
        print(f"🌐 Ollama URL: {OLLAMA_URL}")

        overall_start = time.time()

        # Test each model
        for model_name in self.models:
            model_results = await self.test_model(model_name)
            self.results[model_name] = model_results

            # Save results after each model (in case of crashes)
            self.save_results()

        overall_duration = time.time() - overall_start

        # Add summary information
        self.results["_summary"] = {
            "instruction_level": self.instruction_level.name,
            "memory_enabled": self.enable_memory,
            "total_models_tested": len(self.models),
            "total_queries_per_model": len(self.queries),
            "overall_duration": overall_duration,
            "test_completed": datetime.now().isoformat(),
            "successful_models": [
                model
                for model, results in self.results.items()
                if not model.startswith("_") and not results.get("initialization_error")
            ],
            "failed_models": [
                model
                for model, results in self.results.items()
                if not model.startswith("_") and results.get("initialization_error")
            ],
        }

        print(f"\n🎉 All tests completed in {overall_duration:.2f}s")
        print(
            f"✅ Successful models: {len(self.results['_summary']['successful_models'])}"
        )
        print(f"❌ Failed models: {len(self.results['_summary']['failed_models'])}")

        return self.results

    def save_results(self):
        """Save results to JSON file."""
        try:
            with open(self.output_file, "w", encoding="utf-8") as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False)
            print(f"💾 Results saved to {self.output_file}")
        except Exception as e:
            print(f"❌ Failed to save results: {e}")

    def print_summary(self):
        """Print a summary of test results."""
        if "_summary" not in self.results:
            print("❌ No summary available")
            return

        summary = self.results["_summary"]

        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        print(f"🤖 Models tested: {summary['total_models_tested']}")
        print(f"📝 Queries per model: {summary['total_queries_per_model']}")
        print(f"⏱️  Total duration: {summary['overall_duration']:.2f}s")
        print(f"✅ Successful: {len(summary['successful_models'])}")
        print(f"❌ Failed: {len(summary['failed_models'])}")

        if summary["successful_models"]:
            print(f"\n✅ Successful models:")
            for model in summary["successful_models"]:
                model_data = self.results[model]
                total_time = model_data.get("total_duration", 0)
                error_count = len(model_data.get("errors", []))
                print(f"   • {model}: {total_time:.2f}s total, {error_count} errors")

        if summary["failed_models"]:
            print(f"\n❌ Failed models:")
            for model in summary["failed_models"]:
                error = self.results[model].get("initialization_error", "Unknown error")
                print(f"   • {model}: {error}")

        print("\n📄 Detailed results saved to:", self.output_file)
        print("=" * 60)


async def main():
    """Main function to run the model tests."""

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Test multiple Ollama models with configurable instruction levels"
    )
    parser.add_argument(
        "--instruction-level",
        type=str,
        choices=[level.name for level in InstructionLevel],
        default="NONE",
        help="Instruction level to use for testing (default: STANDARD)",
    )
    parser.add_argument(
        "--no-memory",
        action="store_true",
        help="Disable memory for consistent testing (default: memory enabled)",
    )

    args = parser.parse_args()

    # Convert string to InstructionLevel enum
    instruction_level = InstructionLevel[args.instruction_level]
    enable_memory = not args.no_memory

    # Define models to test
    models = [
        "qwen3:1.7b",
        "qwen3:4b",
        "llama3.2:3b",
        "llama3.2:latest",
    ]

    # Define queries to test
    queries = [
        "hello!",
        "list your tools",
        "list your memories of me",
        "give me a financial analysis of NVDA",
        "calculate 5 + cos(34)",
        "summarize the top news headlines about AI",
        "write a funny poem about insane robots and show me",
    ]

    # Create output filename with timestamp, instruction level, and sanitized model names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Sanitize model names for filename (replace special characters with underscores)
    def sanitize_model_name(model_name: str) -> str:
        """Sanitize model name for use in filename."""
        import re

        # Replace any non-alphanumeric characters (except hyphens) with underscores
        sanitized = re.sub(r"[^a-zA-Z0-9\-]", "_", model_name)
        # Remove multiple consecutive underscores
        sanitized = re.sub(r"_+", "_", sanitized)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip("_")
        return sanitized

    # Create a string representing all models being tested
    sanitized_models = [sanitize_model_name(model) for model in models]
    models_string = "_".join(sanitized_models)

    # Limit the models string length to avoid overly long filenames
    if len(models_string) > 50:
        models_string = f"{models_string[:47]}..."

    output_file = f"model_test_results_{instruction_level.name.lower()}_{models_string}_{timestamp}.json"

    # Create and run tester
    tester = ModelTester(models, queries, instruction_level, enable_memory, output_file)

    try:
        results = await tester.run_tests()
        tester.print_summary()

        print(f"\n🎯 Testing complete! Check {output_file} for detailed results.")

    except KeyboardInterrupt:
        print("\n⚠️  Testing interrupted by user")
        tester.save_results()
        tester.print_summary()
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        tester.save_results()


if __name__ == "__main__":
    asyncio.run(main())
