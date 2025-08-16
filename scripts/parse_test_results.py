#!/usr/bin/env python3
"""
Test Results Parser and Summarizer

This script parses and summarizes the JSON output from the Ollama model testing script,
providing detailed analysis, comparisons, and visualizations of model performance.
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


class TestResultsAnalyzer:
    """Analyze and summarize model test results."""
    
    def __init__(self, json_file: str):
        """
        Initialize the analyzer with a JSON results file.
        
        Args:
            json_file: Path to the JSON results file
        """
        self.json_file = json_file
        self.data = self._load_data()
        self.console = Console()
        
    def _load_data(self) -> Dict[str, Any]:
        """Load and validate the JSON data."""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not data:
                raise ValueError("JSON file is empty")
                
            # If _summary is missing, generate it from available data
            if "_summary" not in data:
                print("⚠️  Warning: _summary section missing, generating from available data...")
                data["_summary"] = self._generate_summary_from_data(data)
                
            return data
        except FileNotFoundError:
            print(f"❌ Error: File '{self.json_file}' not found")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"❌ Error: Invalid JSON format - {e}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Error loading data: {e}")
            sys.exit(1)
    
    def _generate_summary_from_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary section from available model data."""
        models = [key for key in data.keys() if not key.startswith("_")]
        
        successful_models = []
        failed_models = []
        total_duration = 0
        total_queries = 0
        
        # Find the most recent timestamp for test completion
        latest_timestamp = None
        
        for model in models:
            model_data = data[model]
            
            # Check if model was successful
            if model_data.get("initialization_error"):
                failed_models.append(model)
            else:
                successful_models.append(model)
                total_duration += model_data.get("total_duration", 0)
            
            # Count queries
            if "queries" in model_data:
                total_queries += len(model_data["queries"])
            
            # Track latest timestamp
            timestamp = model_data.get("test_timestamp")
            if timestamp:
                if not latest_timestamp or timestamp > latest_timestamp:
                    latest_timestamp = timestamp
        
        # Calculate queries per model (assuming all models have same number of queries)
        queries_per_model = total_queries // len(models) if models else 0
        
        return {
            "total_models_tested": len(models),
            "total_queries_per_model": queries_per_model,
            "overall_duration": total_duration,
            "test_completed": latest_timestamp or "Unknown",
            "successful_models": successful_models,
            "failed_models": failed_models
        }
    
    def get_models(self) -> List[str]:
        """Get list of tested models."""
        return [key for key in self.data.keys() if not key.startswith("_")]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get the summary section."""
        return self.data.get("_summary", {})
    
    def get_model_data(self, model_name: str) -> Dict[str, Any]:
        """Get data for a specific model."""
        return self.data.get(model_name, {})
    
    def calculate_model_stats(self, model_name: str) -> Dict[str, Any]:
        """Calculate statistics for a specific model."""
        model_data = self.get_model_data(model_name)
        
        if not model_data or "queries" not in model_data:
            return {
                "model_name": model_name,
                "status": "failed",
                "error": model_data.get("initialization_error", "No data available")
            }
        
        queries = model_data["queries"]
        successful_queries = [q for q in queries.values() if q.get("success", False)]
        failed_queries = [q for q in queries.values() if not q.get("success", True)]
        
        if successful_queries:
            durations = [q["duration"] for q in successful_queries]
            avg_duration = sum(durations) / len(durations)
            min_duration = min(durations)
            max_duration = max(durations)
        else:
            avg_duration = min_duration = max_duration = 0
        
        return {
            "model_name": model_name,
            "status": "success" if not model_data.get("initialization_error") else "failed",
            "initialization_time": model_data.get("initialization_time", 0),
            "total_duration": model_data.get("total_duration", 0),
            "total_queries": len(queries),
            "successful_queries": len(successful_queries),
            "failed_queries": len(failed_queries),
            "success_rate": len(successful_queries) / len(queries) * 100 if queries else 0,
            "avg_query_duration": avg_duration,
            "min_query_duration": min_duration,
            "max_query_duration": max_duration,
            "errors": model_data.get("errors", []),
            "error_count": len(model_data.get("errors", []))
        }
    
    def generate_comparison_table(self) -> Table:
        """Generate a comparison table of all models."""
        table = Table(title="🤖 Model Performance Comparison", show_header=True, header_style="bold magenta")
        
        # Add columns
        table.add_column("Model", style="cyan", no_wrap=True)
        table.add_column("Status", style="green")
        table.add_column("Init Time", style="yellow", justify="right")
        table.add_column("Total Time", style="yellow", justify="right")
        table.add_column("Success Rate", style="blue", justify="right")
        table.add_column("Avg Query", style="blue", justify="right")
        table.add_column("Min Query", style="dim", justify="right")
        table.add_column("Max Query", style="dim", justify="right")
        table.add_column("Errors", style="red", justify="right")
        
        models = self.get_models()
        for model in sorted(models):
            stats = self.calculate_model_stats(model)
            
            # Format status with color
            if stats["status"] == "success":
                status = "[green]✅ Success[/green]"
            else:
                status = "[red]❌ Failed[/red]"
            
            # Format success rate with color
            success_rate = stats["success_rate"]
            if success_rate == 100:
                success_color = "green"
            elif success_rate >= 80:
                success_color = "yellow"
            else:
                success_color = "red"
            
            table.add_row(
                stats["model_name"],
                status,
                f"{stats['initialization_time']:.2f}s",
                f"{stats['total_duration']:.2f}s",
                f"[{success_color}]{success_rate:.1f}%[/{success_color}]",
                f"{stats['avg_query_duration']:.2f}s",
                f"{stats['min_query_duration']:.2f}s",
                f"{stats['max_query_duration']:.2f}s",
                str(stats['error_count'])
            )
        
        return table
    
    def generate_query_analysis_table(self) -> Table:
        """Generate a detailed query analysis table."""
        table = Table(title="📝 Query Performance Analysis", show_header=True, header_style="bold magenta")
        
        table.add_column("Model", style="cyan")
        table.add_column("Query", style="yellow")
        table.add_column("Duration", style="blue", justify="right")
        table.add_column("Status", style="green")
        table.add_column("Response Preview", style="dim")
        
        models = self.get_models()
        for model in sorted(models):
            model_data = self.get_model_data(model)
            if "queries" not in model_data:
                continue
                
            queries = model_data["queries"]
            for query_key in sorted(queries.keys()):
                query_data = queries[query_key]
                
                # Format status
                if query_data.get("success", False):
                    status = "[green]✅[/green]"
                else:
                    status = "[red]❌[/red]"
                
                # Format response preview
                response = query_data.get("response", "")
                if response:
                    preview = response[:50] + "..." if len(response) > 50 else response
                    preview = preview.replace("\n", " ")
                else:
                    preview = query_data.get("error", "No response")[:50]
                
                table.add_row(
                    model,
                    query_data.get("query", "Unknown"),
                    f"{query_data.get('duration', 0):.2f}s",
                    status,
                    preview
                )
        
        return table
    
    def generate_summary_panel(self) -> Panel:
        """Generate a summary panel with key metrics."""
        summary = self.get_summary()
        models = self.get_models()
        
        # Calculate aggregate statistics
        total_models = len(models)
        successful_models = len([m for m in models if not self.get_model_data(m).get("initialization_error")])
        failed_models = total_models - successful_models
        
        # Calculate total queries and success rates
        total_queries = 0
        successful_queries = 0
        total_duration = summary.get("overall_duration", 0)
        
        for model in models:
            model_data = self.get_model_data(model)
            if "queries" in model_data:
                queries = model_data["queries"]
                total_queries += len(queries)
                successful_queries += len([q for q in queries.values() if q.get("success", False)])
        
        overall_success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0
        
        # Create summary text
        summary_text = Text()
        summary_text.append("📊 Test Results Summary\n\n", style="bold blue")
        summary_text.append(f"🗓️  Test Date: {summary.get('test_completed', 'Unknown')}\n")
        summary_text.append(f"⏱️  Total Duration: {total_duration:.2f}s\n")
        summary_text.append(f"🤖 Models Tested: {total_models}\n")
        summary_text.append(f"✅ Successful Models: {successful_models}\n")
        summary_text.append(f"❌ Failed Models: {failed_models}\n")
        summary_text.append(f"📝 Total Queries: {total_queries}\n")
        summary_text.append(f"🎯 Overall Success Rate: {overall_success_rate:.1f}%\n")
        
        if successful_models > 0:
            avg_time_per_model = total_duration / successful_models
            summary_text.append(f"⚡ Avg Time per Model: {avg_time_per_model:.2f}s")
        
        return Panel(summary_text, title="📈 Executive Summary", border_style="green")
    
    def create_performance_charts(self, output_dir: str = "charts") -> List[str]:
        """Create performance visualization charts."""
        Path(output_dir).mkdir(exist_ok=True)
        chart_files = []
        
        models = self.get_models()
        if not models:
            print("⚠️  No model data available for charts")
            return chart_files
        
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # 1. Model Performance Comparison
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Model Performance Analysis', fontsize=16, fontweight='bold')
        
        # Collect data for charts
        model_names = []
        init_times = []
        total_times = []
        success_rates = []
        avg_query_times = []
        
        for model in models:
            stats = self.calculate_model_stats(model)
            if stats["status"] == "success":
                model_names.append(model.replace(":", "\n"))  # Break long names
                init_times.append(stats["initialization_time"])
                total_times.append(stats["total_duration"])
                success_rates.append(stats["success_rate"])
                avg_query_times.append(stats["avg_query_duration"])
        
        if model_names:
            # Initialization Times
            bars1 = ax1.bar(model_names, init_times, color='skyblue', alpha=0.7)
            ax1.set_title('Initialization Time by Model')
            ax1.set_ylabel('Time (seconds)')
            ax1.tick_params(axis='x', rotation=45)
            for bar, time in zip(bars1, init_times):
                ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                        f'{time:.1f}s', ha='center', va='bottom')
            
            # Total Duration
            bars2 = ax2.bar(model_names, total_times, color='lightcoral', alpha=0.7)
            ax2.set_title('Total Test Duration by Model')
            ax2.set_ylabel('Time (seconds)')
            ax2.tick_params(axis='x', rotation=45)
            for bar, time in zip(bars2, total_times):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                        f'{time:.1f}s', ha='center', va='bottom')
            
            # Success Rates
            colors = ['green' if rate == 100 else 'orange' if rate >= 80 else 'red' for rate in success_rates]
            bars3 = ax3.bar(model_names, success_rates, color=colors, alpha=0.7)
            ax3.set_title('Success Rate by Model')
            ax3.set_ylabel('Success Rate (%)')
            ax3.set_ylim(0, 105)
            ax3.tick_params(axis='x', rotation=45)
            for bar, rate in zip(bars3, success_rates):
                ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                        f'{rate:.1f}%', ha='center', va='bottom')
            
            # Average Query Time
            bars4 = ax4.bar(model_names, avg_query_times, color='mediumpurple', alpha=0.7)
            ax4.set_title('Average Query Response Time')
            ax4.set_ylabel('Time (seconds)')
            ax4.tick_params(axis='x', rotation=45)
            for bar, time in zip(bars4, avg_query_times):
                ax4.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1, 
                        f'{time:.1f}s', ha='center', va='bottom')
        
        plt.tight_layout()
        chart_file = f"{output_dir}/model_performance_comparison.png"
        plt.savefig(chart_file, dpi=300, bbox_inches='tight')
        plt.close()
        chart_files.append(chart_file)
        
        # 2. Query Performance Heatmap
        if len(models) > 1:
            fig, ax = plt.subplots(figsize=(12, 8))
            
            # Create matrix for heatmap
            query_names = []
            heatmap_data = []
            
            # Get query names from first successful model
            for model in models:
                model_data = self.get_model_data(model)
                if "queries" in model_data:
                    queries = model_data["queries"]
                    query_names = [queries[key]["query"] for key in sorted(queries.keys())]
                    break
            
            # Collect duration data for each model
            for model in models:
                model_data = self.get_model_data(model)
                if "queries" in model_data:
                    queries = model_data["queries"]
                    durations = []
                    for key in sorted(queries.keys()):
                        duration = queries[key].get("duration", 0)
                        durations.append(duration)
                    heatmap_data.append(durations)
                else:
                    heatmap_data.append([0] * len(query_names))
            
            if heatmap_data and query_names:
                df = pd.DataFrame(heatmap_data, index=models, columns=query_names)
                sns.heatmap(df, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax, 
                           cbar_kws={'label': 'Response Time (seconds)'})
                ax.set_title('Query Response Time Heatmap', fontsize=14, fontweight='bold')
                ax.set_xlabel('Queries')
                ax.set_ylabel('Models')
                
                plt.tight_layout()
                chart_file = f"{output_dir}/query_performance_heatmap.png"
                plt.savefig(chart_file, dpi=300, bbox_inches='tight')
                plt.close()
                chart_files.append(chart_file)
        
        return chart_files
    
    def export_to_csv(self, output_file: str = "model_test_summary.csv") -> str:
        """Export summary data to CSV."""
        models = self.get_models()
        data_rows = []
        
        for model in models:
            stats = self.calculate_model_stats(model)
            data_rows.append(stats)
        
        df = pd.DataFrame(data_rows)
        df.to_csv(output_file, index=False)
        return output_file
    
    def generate_detailed_report(self, output_file: str = "detailed_report.txt") -> str:
        """Generate a detailed text report."""
        models = self.get_models()
        summary = self.get_summary()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("OLLAMA MODEL TESTING - DETAILED REPORT\n")
            f.write("=" * 80 + "\n\n")
            
            # Summary section
            f.write("EXECUTIVE SUMMARY\n")
            f.write("-" * 40 + "\n")
            f.write(f"Test Date: {summary.get('test_completed', 'Unknown')}\n")
            f.write(f"Total Duration: {summary.get('overall_duration', 0):.2f} seconds\n")
            f.write(f"Models Tested: {len(models)}\n")
            f.write(f"Successful Models: {len(summary.get('successful_models', []))}\n")
            f.write(f"Failed Models: {len(summary.get('failed_models', []))}\n\n")
            
            # Individual model analysis
            f.write("INDIVIDUAL MODEL ANALYSIS\n")
            f.write("-" * 40 + "\n\n")
            
            for model in sorted(models):
                stats = self.calculate_model_stats(model)
                model_data = self.get_model_data(model)
                
                f.write(f"Model: {model}\n")
                f.write(f"Status: {stats['status'].upper()}\n")
                
                if stats['status'] == 'success':
                    f.write(f"Initialization Time: {stats['initialization_time']:.2f}s\n")
                    f.write(f"Total Duration: {stats['total_duration']:.2f}s\n")
                    f.write(f"Success Rate: {stats['success_rate']:.1f}%\n")
                    f.write(f"Average Query Time: {stats['avg_query_duration']:.2f}s\n")
                    f.write(f"Query Time Range: {stats['min_query_duration']:.2f}s - {stats['max_query_duration']:.2f}s\n")
                    
                    # Query details
                    if "queries" in model_data:
                        f.write("\nQuery Details:\n")
                        queries = model_data["queries"]
                        for key in sorted(queries.keys()):
                            query_data = queries[key]
                            status_symbol = "✅" if query_data.get("success", False) else "❌"
                            f.write(f"  {status_symbol} '{query_data.get('query', 'Unknown')}': {query_data.get('duration', 0):.2f}s\n")
                            if not query_data.get("success", False) and query_data.get("error"):
                                f.write(f"     Error: {query_data['error']}\n")
                else:
                    f.write(f"Error: {stats.get('error', 'Unknown error')}\n")
                
                if stats['errors']:
                    f.write(f"\nErrors ({len(stats['errors'])}):\n")
                    for error in stats['errors']:
                        f.write(f"  - {error}\n")
                
                f.write("\n" + "-" * 60 + "\n\n")
        
        return output_file
    
    def print_analysis(self):
        """Print comprehensive analysis to console."""
        self.console.print(self.generate_summary_panel())
        self.console.print()
        self.console.print(self.generate_comparison_table())
        self.console.print()
        self.console.print(self.generate_query_analysis_table())


def main():
    """Main function with command line interface."""
    parser = argparse.ArgumentParser(
        description="Parse and analyze Ollama model test results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python parse_test_results.py results.json
  python parse_test_results.py results.json --charts --csv --report
  python parse_test_results.py results.json --output-dir analysis/
        """
    )
    
    parser.add_argument("json_file", help="Path to the JSON results file")
    parser.add_argument("--charts", action="store_true", help="Generate performance charts")
    parser.add_argument("--csv", action="store_true", help="Export summary to CSV")
    parser.add_argument("--report", action="store_true", help="Generate detailed text report")
    parser.add_argument("--output-dir", default=".", help="Output directory for generated files")
    parser.add_argument("--all", action="store_true", help="Generate all outputs (charts, CSV, report)")
    
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    # Initialize analyzer
    try:
        analyzer = TestResultsAnalyzer(args.json_file)
    except Exception as e:
        print(f"❌ Failed to initialize analyzer: {e}")
        sys.exit(1)
    
    # Print console analysis
    print(f"📊 Analyzing results from: {args.json_file}")
    print()
    analyzer.print_analysis()
    
    generated_files = []
    
    # Generate additional outputs
    if args.charts or args.all:
        try:
            chart_dir = output_dir / "charts"
            chart_files = analyzer.create_performance_charts(str(chart_dir))
            generated_files.extend(chart_files)
            print(f"\n📈 Generated {len(chart_files)} chart(s) in {chart_dir}/")
        except ImportError:
            print("\n⚠️  Charts require matplotlib and seaborn. Install with: pip install matplotlib seaborn")
        except Exception as e:
            print(f"\n❌ Error generating charts: {e}")
    
    if args.csv or args.all:
        try:
            csv_file = output_dir / "model_test_summary.csv"
            analyzer.export_to_csv(str(csv_file))
            generated_files.append(str(csv_file))
            print(f"\n📄 Exported CSV summary to: {csv_file}")
        except Exception as e:
            print(f"\n❌ Error generating CSV: {e}")
    
    if args.report or args.all:
        try:
            report_file = output_dir / "detailed_report.txt"
            analyzer.generate_detailed_report(str(report_file))
            generated_files.append(str(report_file))
            print(f"\n📝 Generated detailed report: {report_file}")
        except Exception as e:
            print(f"\n❌ Error generating report: {e}")
    
    if generated_files:
        print(f"\n✅ Generated {len(generated_files)} additional file(s)")
        for file in generated_files:
            print(f"   📁 {file}")
    
    print(f"\n🎯 Analysis complete!")


if __name__ == "__main__":
    main()
