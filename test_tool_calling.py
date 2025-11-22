#!/usr/bin/env python3
"""
Comprehensive test suite for diagnosing tool calling across different Ollama models.

This script tests tool calling capabilities, tracks metrics, and generates detailed reports
in JSON and Markdown formats.
"""
import asyncio
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Dict, List, Optional

from agno.agent import Agent
from agno.models.ollama import Ollama


# Test tools
def add_numbers(a: int, b: int) -> int:
    """Add two numbers together.

    :param a: First number
    :param b: Second number
    :return: Sum of a and b
    """
    return a + b


def get_weather(city: str) -> str:
    """Get the weather for a city.

    :param city: Name of the city
    :return: Weather description
    """
    return f"The weather in {city} is sunny and 72°F"


@dataclass
class TestResult:
    """Results from testing a single query on a model."""

    query: str
    model_name: str
    success: bool
    tool_calls_detected: bool
    tool_calls_executed: bool
    tool_call_count: int
    double_call_detected: bool
    unparsed_tool_calls: bool
    response_content: str
    response_time_seconds: float
    input_tokens: int
    output_tokens: int
    total_tokens: int
    error: Optional[str] = None
    raw_tool_calls: Optional[List[Dict]] = None


@dataclass
class ModelTestReport:
    """Complete test report for a single model."""

    model_name: str
    test_date: str
    total_queries: int
    successful_queries: int
    tool_calling_works: bool
    tool_calls_parseable: bool
    double_call_issue: bool
    average_response_time: float
    total_tokens_used: int
    test_results: List[TestResult]
    overall_status: str  # "WORKING", "BROKEN", "PARTIAL"
    notes: str


class ModelTester:
    """Test tool calling capabilities across different models."""

    # Text models to test (excluding vision and embedding models)
    TEXT_MODELS = [
        "llama32-tools:latest",
        "llama3.1:8b",
        "llama3.2:3b",
        "hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF:latest",
        "qwen3:latest",
        "qwen3:8b",
        "qwen3:4b",
        "qwen3:1.7B",
        "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q6_K",
        "hf.co/unsloth/Qwen3-4B-Instruct-2507-GGUF:Q4_K_M",
        "hf.co/unsloth/Qwen3-4B-Thinking-2507-GGUF:Q6_K",
        "hf.co/qwen/qwen2.5-coder-7b-instruct-gguf:latest",
        "qwen2.5-coder:3b",
        "myaniu/qwen2.5-1m:latest",
    ]

    # First query is warmup to load the model, remaining are actual tests
    TEST_QUERIES = [
        "Hello!",  # Warmup query (not counted in metrics)
        "What is 5 + 7?",
        "What's the weather in San Francisco?",
    ]

    def __init__(self, silent: bool = False):
        """Initialize the model tester.

        :param silent: If True, suppress console output during testing
        """
        self.silent = silent
        self.all_results: List[ModelTestReport] = []

    async def test_single_query(
        self, agent: Agent, model_name: str, query: str
    ) -> TestResult:
        """Test a single query on a model and collect metrics.

        :param agent: Agent instance to test with
        :param model_name: Name of the model being tested
        :param query: Query string to test
        :return: TestResult with all metrics
        """
        start_time = time.time()

        try:
            result = await agent.arun(query, stream=False)
            response_time = time.time() - start_time

            # Extract metrics
            input_tokens = 0
            output_tokens = 0
            tool_calls_list = []
            tool_call_count = 0
            unparsed_tool_calls = False

            if agent.run_response and agent.run_response.messages:
                for msg in agent.run_response.messages:
                    # Get token metrics
                    if hasattr(msg, "metrics") and msg.metrics:
                        metrics = msg.metrics
                        if hasattr(metrics, "input_tokens") and metrics.input_tokens:
                            input_tokens += metrics.input_tokens
                        if hasattr(metrics, "output_tokens") and metrics.output_tokens:
                            output_tokens += metrics.output_tokens

                    # Check for tool calls
                    if msg.role == "assistant":
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            tool_calls_list.extend(msg.tool_calls)
                            tool_call_count += len(msg.tool_calls)
                        elif msg.content and "<tool_call>" in msg.content:
                            unparsed_tool_calls = True

            # Detect double-calling (same tool called multiple times)
            tool_names = [
                tc.get("function", {}).get("name", "") for tc in tool_calls_list
            ]
            double_call_detected = len(tool_names) != len(set(tool_names))

            return TestResult(
                query=query,
                model_name=model_name,
                success=True,
                tool_calls_detected=tool_call_count > 0,
                tool_calls_executed=tool_call_count > 0,
                tool_call_count=tool_call_count,
                double_call_detected=double_call_detected,
                unparsed_tool_calls=unparsed_tool_calls,
                response_content=result.content[:200] if result.content else "",
                response_time_seconds=round(response_time, 3),
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                raw_tool_calls=tool_calls_list if tool_calls_list else None,
            )

        except Exception as e:
            return TestResult(
                query=query,
                model_name=model_name,
                success=False,
                tool_calls_detected=False,
                tool_calls_executed=False,
                tool_call_count=0,
                double_call_detected=False,
                unparsed_tool_calls=False,
                response_content="",
                response_time_seconds=time.time() - start_time,
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                error=str(e),
            )

    async def test_model(self, model_name: str) -> ModelTestReport:
        """Test all queries on a single model.

        :param model_name: Name of the Ollama model to test
        :return: ModelTestReport with complete results
        """
        if not self.silent:
            print(f"\n{'='*70}")
            print(f"Testing model: {model_name}")
            print(f"{'='*70}")

        try:
            model = Ollama(
                id=model_name,
                host="http://localhost:11434",
                options={
                    "temperature": 0.7,
                    "num_ctx": 8192,
                },
            )

            agent = Agent(
                name=f"Test Agent ({model_name})",
                model=model,
                tools=[add_numbers, get_weather],
                markdown=True,
                show_tool_calls=False,  # Suppress tool call output for cleaner logs
                debug_mode=False,  # Disable debug for cleaner output
            )

            test_results = []
            for idx, query in enumerate(self.TEST_QUERIES):
                is_warmup = idx == 0

                if not self.silent:
                    warmup_label = " (warmup)" if is_warmup else ""
                    print(f"\n  📝 Testing{warmup_label}: {query}")

                result = await self.test_single_query(agent, model_name, query)
                test_results.append(result)

                if not self.silent and not is_warmup:
                    status = "✅" if result.tool_calls_detected else "❌"
                    print(
                        f"     {status} Tool calls: {result.tool_call_count}, "
                        f"Time: {result.response_time_seconds}s, "
                        f"Tokens: {result.input_tokens}→{result.output_tokens} ({result.total_tokens})"
                    )
                    if result.double_call_detected:
                        print(f"     ⚠️  Double-call detected!")
                    if result.unparsed_tool_calls:
                        print(f"     ⚠️  Unparsed tool calls in content")

            # Calculate summary statistics (exclude warmup query at index 0)
            actual_test_results = test_results[1:]  # Skip warmup
            successful_queries = sum(1 for r in actual_test_results if r.success)
            tool_calling_works = all(
                r.tool_calls_detected for r in actual_test_results if r.success
            )
            tool_calls_parseable = not any(r.unparsed_tool_calls for r in actual_test_results)
            double_call_issue = any(r.double_call_detected for r in actual_test_results)
            avg_response_time = sum(
                r.response_time_seconds for r in actual_test_results
            ) / len(actual_test_results) if actual_test_results else 0
            total_tokens = sum(r.total_tokens for r in actual_test_results)

            # Determine overall status
            if not successful_queries:
                overall_status = "ERROR"
                notes = "Model failed to respond to queries"
            elif tool_calling_works and tool_calls_parseable:
                overall_status = "WORKING"
                notes = "Tool calling works correctly"
                if double_call_issue:
                    notes += " (but has double-call issue)"
            elif not tool_calls_parseable:
                overall_status = "BROKEN"
                notes = "Tool calls generated but not parsed correctly"
            else:
                overall_status = "PARTIAL"
                notes = "Some queries work, others don't"

            return ModelTestReport(
                model_name=model_name,
                test_date=datetime.now().isoformat(),
                total_queries=len(actual_test_results),  # Don't count warmup
                successful_queries=successful_queries,
                tool_calling_works=tool_calling_works,
                tool_calls_parseable=tool_calls_parseable,
                double_call_issue=double_call_issue,
                average_response_time=round(avg_response_time, 3),
                total_tokens_used=total_tokens,
                test_results=actual_test_results,  # Only include actual test results
                overall_status=overall_status,
                notes=notes,
            )

        except Exception as e:
            return ModelTestReport(
                model_name=model_name,
                test_date=datetime.now().isoformat(),
                total_queries=0,
                successful_queries=0,
                tool_calling_works=False,
                tool_calls_parseable=False,
                double_call_issue=False,
                average_response_time=0.0,
                total_tokens_used=0,
                test_results=[],
                overall_status="ERROR",
                notes=f"Failed to load/test model: {str(e)}",
            )

    async def test_all_models(self) -> List[ModelTestReport]:
        """Test all configured text models.

        :return: List of ModelTestReport for all tested models
        """
        print(f"\n{'='*70}")
        print(f"OLLAMA MODEL TOOL CALLING TEST SUITE")
        print(f"Testing {len(self.TEXT_MODELS)} models")
        print(f"{'='*70}")

        for model_name in self.TEXT_MODELS:
            try:
                report = await self.test_model(model_name)
                self.all_results.append(report)
            except KeyboardInterrupt:
                print("\n\n⏹️  Test interrupted by user")
                break
            except Exception as e:
                print(f"\n❌ Unexpected error testing {model_name}: {e}")

        return self.all_results

    def generate_json_report(
        self, output_path: str = "tool_calling_report.json"
    ) -> str:
        """Generate JSON report of all test results.

        :param output_path: Path to save the JSON report
        :return: Path to the saved report
        """
        report_data = {
            "test_date": datetime.now().isoformat(),
            "total_models_tested": len(self.all_results),
            "models": [asdict(report) for report in self.all_results],
        }

        with open(output_path, "w") as f:
            json.dump(report_data, f, indent=2)

        return output_path

    def generate_markdown_report(
        self, output_path: str = "tool_calling_report.md"
    ) -> str:
        """Generate Markdown report of all test results.

        :param output_path: Path to save the Markdown report
        :return: Path to the saved report
        """
        lines = []
        lines.append("# Ollama Model Tool Calling Test Report\n")
        lines.append(f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append(f"**Models Tested:** {len(self.all_results)}\n\n")

        # Summary table
        lines.append("## Summary\n")
        lines.append(
            "| Model | Status | Tool Calls Work | Parseable | Double-Call | Avg Time (s) | Input→Output (Total) |\n"
        )
        lines.append(
            "|-------|--------|----------------|-----------|-------------|--------------|----------------------|\n"
        )

        for report in self.all_results:
            status_emoji = {
                "WORKING": "✅",
                "BROKEN": "❌",
                "PARTIAL": "⚠️",
                "ERROR": "💥",
            }.get(report.overall_status, "❓")

            # Calculate average input/output tokens
            avg_input = sum(r.input_tokens for r in report.test_results) / len(report.test_results) if report.test_results else 0
            avg_output = sum(r.output_tokens for r in report.test_results) / len(report.test_results) if report.test_results else 0

            lines.append(
                f"| {report.model_name} | {status_emoji} {report.overall_status} | "
                f"{'✅' if report.tool_calling_works else '❌'} | "
                f"{'✅' if report.tool_calls_parseable else '❌'} | "
                f"{'⚠️' if report.double_call_issue else '✅'} | "
                f"{report.average_response_time} | "
                f"{int(avg_input)}→{int(avg_output)} ({report.total_tokens_used}) |\n"
            )

        # Detailed results per model
        lines.append("\n## Detailed Results\n")

        working_models = [r for r in self.all_results if r.overall_status == "WORKING"]
        broken_models = [r for r in self.all_results if r.overall_status == "BROKEN"]
        partial_models = [r for r in self.all_results if r.overall_status == "PARTIAL"]
        error_models = [r for r in self.all_results if r.overall_status == "ERROR"]

        if working_models:
            lines.append("\n### ✅ Working Models\n")
            for report in working_models:
                lines.append(f"\n#### {report.model_name}\n")
                lines.append(f"- **Status:** {report.overall_status}\n")
                lines.append(f"- **Notes:** {report.notes}\n")
                lines.append(
                    f"- **Successful Queries:** {report.successful_queries}/{report.total_queries}\n"
                )
                lines.append(
                    f"- **Average Response Time:** {report.average_response_time}s\n"
                )
                lines.append(f"- **Total Tokens:** {report.total_tokens_used}\n")

        if broken_models:
            lines.append("\n### ❌ Broken Models (Tool Calls Not Parsed)\n")
            for report in broken_models:
                lines.append(f"\n#### {report.model_name}\n")
                lines.append(f"- **Status:** {report.overall_status}\n")
                lines.append(f"- **Notes:** {report.notes}\n")
                lines.append(
                    f"- **Issue:** Tool calls are generated but not parsed into structured format\n"
                )

        if partial_models:
            lines.append("\n### ⚠️ Partially Working Models\n")
            for report in partial_models:
                lines.append(f"\n#### {report.model_name}\n")
                lines.append(f"- **Status:** {report.overall_status}\n")
                lines.append(f"- **Notes:** {report.notes}\n")

        if error_models:
            lines.append("\n### 💥 Error Models (Failed to Test)\n")
            for report in error_models:
                lines.append(f"\n#### {report.model_name}\n")
                lines.append(f"- **Error:** {report.notes}\n")

        # Recommendations
        lines.append("\n## Recommendations\n")
        lines.append("\nBased on the test results:\n\n")

        if working_models:
            lines.append("**✅ Recommended models for tool calling:**\n")
            for report in sorted(working_models, key=lambda r: r.average_response_time):
                double_call_warning = (
                    " (⚠️ has double-call issue)" if report.double_call_issue else ""
                )
                lines.append(
                    f"- `{report.model_name}` - {report.average_response_time}s avg{double_call_warning}\n"
                )

        if broken_models:
            lines.append("\n**❌ Avoid these models for tool calling:**\n")
            for report in broken_models:
                lines.append(f"- `{report.model_name}` - {report.notes}\n")

        # Technical notes
        lines.append("\n## Technical Notes\n")
        lines.append("\n### Double-Call Issue\n")
        lines.append("Some models call tools multiple times for the same query. ")
        lines.append(
            "This can be mitigated with specific instructions or post-processing.\n"
        )

        lines.append("\n### Unparsed Tool Calls\n")
        lines.append(
            "Models marked as 'BROKEN' generate tool calls in text format (e.g., `<tool_call>...`) "
        )
        lines.append(
            "but the Ollama client does not parse them into structured tool_calls. "
        )
        lines.append(
            "This is likely an issue with the model's template or Ollama client compatibility.\n"
        )

        with open(output_path, "w") as f:
            f.writelines(lines)

        return output_path


async def main():
    """Run the complete test suite."""
    tester = ModelTester(silent=False)

    # Run tests
    await tester.test_all_models()

    # Generate reports
    print(f"\n{'='*70}")
    print("Generating reports...")
    print(f"{'='*70}")

    json_path = tester.generate_json_report()
    print(f"✅ JSON report saved to: {json_path}")

    md_path = tester.generate_markdown_report()
    print(f"✅ Markdown report saved to: {md_path}")

    print(f"\n{'='*70}")
    print("Test suite complete!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    asyncio.run(main())
