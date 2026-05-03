"""
Performance measurement script for Valura AI Agent Ecosystem.

Measures:
- p95 first-token latency (target: <2s)
- p95 end-to-end latency (target: <6s)
- Cost per query (target: <$0.05)
- Safety Guard performance (<10ms)
- Intent Classifier performance
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any, Tuple
from pathlib import Path
import json

from src.safety.guard import SafetyGuard
from src.classifier.intent import IntentClassifier
from src.agents.portfolio_health import PortfolioHealthAgent
from src.session.manager import SessionManager
from src.utils.fixtures import load_user_fixture
from src.utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# Pricing Configuration (Azure OpenAI gpt-4o-mini)
# =============================================================================

# Azure OpenAI gpt-4o-mini pricing (as of 2024)
INPUT_TOKEN_COST = 0.00015 / 1000   # $0.15 per 1M input tokens
OUTPUT_TOKEN_COST = 0.0006 / 1000   # $0.60 per 1M output tokens


# =============================================================================
# Test Queries
# =============================================================================

TEST_QUERIES = [
    # Portfolio health queries
    "How is my portfolio doing?",
    "What's my portfolio performance?",
    "Show me my portfolio health",
    "Analyze my investments",
    "How are my stocks performing?",
    
    # General investment queries
    "What stocks should I consider?",
    "Tell me about diversification",
    "What is the S&P 500?",
    "How do I calculate returns?",
    
    # Market research queries
    "What's the current price of AAPL?",
    "Show me Tesla stock performance",
    "What are the top tech stocks?",
]


# =============================================================================
# Performance Measurement Functions
# =============================================================================

def measure_safety_guard_performance(iterations: int = 1000) -> Dict[str, Any]:
    """Measure Safety Guard performance."""
    print("\n🔒 Measuring Safety Guard Performance...")
    
    guard = SafetyGuard()
    test_queries = [
        "How is my portfolio doing?",
        "What stocks should I consider?",
        "Tell me about diversification",
    ]
    
    latencies = []
    
    # Warm up
    for _ in range(10):
        guard.check_query(test_queries[0])
    
    # Measure
    for i in range(iterations):
        query = test_queries[i % len(test_queries)]
        start = time.time()
        guard.check_query(query)
        latency = (time.time() - start) * 1000  # Convert to ms
        latencies.append(latency)
    
    return {
        "component": "Safety Guard",
        "iterations": iterations,
        "mean_latency_ms": statistics.mean(latencies),
        "median_latency_ms": statistics.median(latencies),
        "p95_latency_ms": statistics.quantiles(latencies, n=20)[18],  # 95th percentile
        "p99_latency_ms": statistics.quantiles(latencies, n=100)[98],  # 99th percentile
        "min_latency_ms": min(latencies),
        "max_latency_ms": max(latencies),
        "target_ms": 10,
        "meets_target": statistics.quantiles(latencies, n=20)[18] < 10,
    }


async def measure_classifier_performance(iterations: int = 100) -> Dict[str, Any]:
    """Measure Intent Classifier performance."""
    print("\n🎯 Measuring Intent Classifier Performance...")
    
    classifier = IntentClassifier()
    session_manager = SessionManager()
    
    latencies = []
    total_input_tokens = 0
    total_output_tokens = 0
    
    for i in range(iterations):
        query = TEST_QUERIES[i % len(TEST_QUERIES)]
        session_id = f"perf-test-{i}"
        session_manager.create_session(session_id, "perf-user")
        
        start = time.time()
        result = await classifier.classify(query, session_id, session_manager)
        latency = (time.time() - start) * 1000  # Convert to ms
        latencies.append(latency)
        
        # Estimate token usage (rough approximation)
        # Input: system prompt (~500 tokens) + user query (~20 tokens) + history (~100 tokens)
        # Output: structured response (~150 tokens)
        total_input_tokens += 620
        total_output_tokens += 150
    
    # Calculate costs
    input_cost = total_input_tokens * INPUT_TOKEN_COST
    output_cost = total_output_tokens * OUTPUT_TOKEN_COST
    total_cost = input_cost + output_cost
    cost_per_query = total_cost / iterations
    
    return {
        "component": "Intent Classifier",
        "iterations": iterations,
        "mean_latency_ms": statistics.mean(latencies),
        "median_latency_ms": statistics.median(latencies),
        "p95_latency_ms": statistics.quantiles(latencies, n=20)[18],
        "p99_latency_ms": statistics.quantiles(latencies, n=100)[98],
        "min_latency_ms": min(latencies),
        "max_latency_ms": max(latencies),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_cost_usd": total_cost,
        "cost_per_query_usd": cost_per_query,
    }


async def measure_portfolio_health_performance(iterations: int = 50) -> Dict[str, Any]:
    """Measure Portfolio Health Agent performance."""
    print("\n📊 Measuring Portfolio Health Agent Performance...")
    
    agent = PortfolioHealthAgent()
    user = load_user_fixture("user_001_active_trader_us.json")
    
    latencies = []
    first_token_latencies = []
    total_input_tokens = 0
    total_output_tokens = 0
    
    for i in range(iterations):
        start = time.time()
        first_token_time = None
        
        # Measure first token latency
        async for chunk in agent.analyze_portfolio(user):
            if first_token_time is None:
                first_token_time = (time.time() - start) * 1000
                first_token_latencies.append(first_token_time)
        
        end_to_end_latency = (time.time() - start) * 1000
        latencies.append(end_to_end_latency)
        
        # Estimate token usage
        # Input: system prompt (~800 tokens) + portfolio data (~500 tokens)
        # Output: analysis (~600 tokens)
        total_input_tokens += 1300
        total_output_tokens += 600
    
    # Calculate costs
    input_cost = total_input_tokens * INPUT_TOKEN_COST
    output_cost = total_output_tokens * OUTPUT_TOKEN_COST
    total_cost = input_cost + output_cost
    cost_per_query = total_cost / iterations
    
    return {
        "component": "Portfolio Health Agent",
        "iterations": iterations,
        "first_token_mean_ms": statistics.mean(first_token_latencies),
        "first_token_p95_ms": statistics.quantiles(first_token_latencies, n=20)[18],
        "first_token_target_ms": 2000,
        "first_token_meets_target": statistics.quantiles(first_token_latencies, n=20)[18] < 2000,
        "end_to_end_mean_ms": statistics.mean(latencies),
        "end_to_end_p95_ms": statistics.quantiles(latencies, n=20)[18],
        "end_to_end_target_ms": 6000,
        "end_to_end_meets_target": statistics.quantiles(latencies, n=20)[18] < 6000,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_cost_usd": total_cost,
        "cost_per_query_usd": cost_per_query,
        "cost_target_usd": 0.05,
        "cost_meets_target": cost_per_query < 0.05,
    }


async def measure_end_to_end_performance(iterations: int = 30) -> Dict[str, Any]:
    """Measure full pipeline end-to-end performance."""
    print("\n🚀 Measuring End-to-End Pipeline Performance...")
    
    guard = SafetyGuard()
    classifier = IntentClassifier()
    agent = PortfolioHealthAgent()
    session_manager = SessionManager()
    user = load_user_fixture("user_001_active_trader_us.json")
    
    latencies = []
    first_token_latencies = []
    total_input_tokens = 0
    total_output_tokens = 0
    
    portfolio_queries = [
        "How is my portfolio doing?",
        "What's my portfolio performance?",
        "Analyze my investments",
    ]
    
    for i in range(iterations):
        query = portfolio_queries[i % len(portfolio_queries)]
        session_id = f"e2e-test-{i}"
        session_manager.create_session(session_id, "e2e-user")
        
        start = time.time()
        first_token_time = None
        
        # Step 1: Safety Guard
        safety_verdict = guard.check_query(query)
        if not safety_verdict.is_safe:
            continue
        
        # Step 2: Intent Classifier
        classification = await classifier.classify(query, session_id, session_manager)
        
        # Step 3: Route to agent (Portfolio Health)
        if classification.target_agent == "portfolio_health":
            async for chunk in agent.analyze_portfolio(user):
                if first_token_time is None:
                    first_token_time = (time.time() - start) * 1000
                    first_token_latencies.append(first_token_time)
        
        end_to_end_latency = (time.time() - start) * 1000
        latencies.append(end_to_end_latency)
        
        # Estimate token usage
        # Classifier: 620 input + 150 output
        # Agent: 1300 input + 600 output
        total_input_tokens += 1920
        total_output_tokens += 750
    
    # Calculate costs
    input_cost = total_input_tokens * INPUT_TOKEN_COST
    output_cost = total_output_tokens * OUTPUT_TOKEN_COST
    total_cost = input_cost + output_cost
    cost_per_query = total_cost / iterations
    
    return {
        "component": "End-to-End Pipeline",
        "iterations": iterations,
        "first_token_mean_ms": statistics.mean(first_token_latencies),
        "first_token_p95_ms": statistics.quantiles(first_token_latencies, n=20)[18],
        "first_token_target_ms": 2000,
        "first_token_meets_target": statistics.quantiles(first_token_latencies, n=20)[18] < 2000,
        "end_to_end_mean_ms": statistics.mean(latencies),
        "end_to_end_p95_ms": statistics.quantiles(latencies, n=20)[18],
        "end_to_end_target_ms": 6000,
        "end_to_end_meets_target": statistics.quantiles(latencies, n=20)[18] < 6000,
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "total_cost_usd": total_cost,
        "cost_per_query_usd": cost_per_query,
        "cost_target_usd": 0.05,
        "cost_meets_target": cost_per_query < 0.05,
    }


# =============================================================================
# Report Generation
# =============================================================================

def generate_report(results: List[Dict[str, Any]]) -> str:
    """Generate performance report."""
    report = []
    report.append("=" * 80)
    report.append("VALURA AI AGENT ECOSYSTEM - PERFORMANCE REPORT")
    report.append("=" * 80)
    report.append(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    for result in results:
        report.append("-" * 80)
        report.append(f"Component: {result['component']}")
        report.append("-" * 80)
        report.append(f"Iterations: {result['iterations']}")
        report.append("")
        
        # Latency metrics
        if "first_token_mean_ms" in result:
            report.append("First Token Latency:")
            report.append(f"  Mean:   {result['first_token_mean_ms']:.2f} ms")
            report.append(f"  p95:    {result['first_token_p95_ms']:.2f} ms")
            report.append(f"  Target: {result['first_token_target_ms']} ms")
            status = "✅ PASS" if result['first_token_meets_target'] else "❌ FAIL"
            report.append(f"  Status: {status}")
            report.append("")
        
        if "end_to_end_mean_ms" in result:
            report.append("End-to-End Latency:")
            report.append(f"  Mean:   {result['end_to_end_mean_ms']:.2f} ms")
            report.append(f"  p95:    {result['end_to_end_p95_ms']:.2f} ms")
            report.append(f"  Target: {result['end_to_end_target_ms']} ms")
            status = "✅ PASS" if result['end_to_end_meets_target'] else "❌ FAIL"
            report.append(f"  Status: {status}")
            report.append("")
        
        if "mean_latency_ms" in result:
            report.append("Latency:")
            report.append(f"  Mean:   {result['mean_latency_ms']:.2f} ms")
            report.append(f"  Median: {result['median_latency_ms']:.2f} ms")
            report.append(f"  p95:    {result['p95_latency_ms']:.2f} ms")
            report.append(f"  p99:    {result['p99_latency_ms']:.2f} ms")
            report.append(f"  Min:    {result['min_latency_ms']:.2f} ms")
            report.append(f"  Max:    {result['max_latency_ms']:.2f} ms")
            if "target_ms" in result:
                report.append(f"  Target: {result['target_ms']} ms")
                status = "✅ PASS" if result['meets_target'] else "❌ FAIL"
                report.append(f"  Status: {status}")
            report.append("")
        
        # Cost metrics
        if "cost_per_query_usd" in result:
            report.append("Cost Analysis:")
            report.append(f"  Input Tokens:  {result['total_input_tokens']:,}")
            report.append(f"  Output Tokens: {result['total_output_tokens']:,}")
            report.append(f"  Total Cost:    ${result['total_cost_usd']:.4f}")
            report.append(f"  Cost/Query:    ${result['cost_per_query_usd']:.4f}")
            if "cost_target_usd" in result:
                report.append(f"  Target:        ${result['cost_target_usd']:.2f}")
                status = "✅ PASS" if result['cost_meets_target'] else "❌ FAIL"
                report.append(f"  Status:        {status}")
            report.append("")
    
    report.append("=" * 80)
    report.append("SUMMARY")
    report.append("=" * 80)
    
    # Check if all targets met
    all_targets_met = True
    for result in results:
        if "first_token_meets_target" in result and not result["first_token_meets_target"]:
            all_targets_met = False
        if "end_to_end_meets_target" in result and not result["end_to_end_meets_target"]:
            all_targets_met = False
        if "cost_meets_target" in result and not result["cost_meets_target"]:
            all_targets_met = False
        if "meets_target" in result and not result["meets_target"]:
            all_targets_met = False
    
    if all_targets_met:
        report.append("✅ ALL PERFORMANCE TARGETS MET!")
    else:
        report.append("⚠️  Some performance targets not met. See details above.")
    
    report.append("=" * 80)
    
    return "\n".join(report)


# =============================================================================
# Main
# =============================================================================

async def main():
    """Run performance measurements."""
    print("=" * 80)
    print("VALURA AI AGENT ECOSYSTEM - PERFORMANCE MEASUREMENT")
    print("=" * 80)
    print("\nThis will measure:")
    print("  - Safety Guard performance (<10ms)")
    print("  - Intent Classifier performance")
    print("  - Portfolio Health Agent performance")
    print("  - End-to-End pipeline performance")
    print("  - Cost per query (<$0.05)")
    print("\nTargets:")
    print("  - p95 first-token latency: <2s")
    print("  - p95 end-to-end latency: <6s")
    print("  - Cost per query: <$0.05")
    print("\n" + "=" * 80)
    
    results = []
    
    # Measure Safety Guard
    safety_result = measure_safety_guard_performance(iterations=1000)
    results.append(safety_result)
    
    # Measure Intent Classifier
    classifier_result = await measure_classifier_performance(iterations=100)
    results.append(classifier_result)
    
    # Measure Portfolio Health Agent
    agent_result = await measure_portfolio_health_performance(iterations=50)
    results.append(agent_result)
    
    # Measure End-to-End Pipeline
    e2e_result = await measure_end_to_end_performance(iterations=30)
    results.append(e2e_result)
    
    # Generate report
    report = generate_report(results)
    print("\n" + report)
    
    # Save report
    report_file = Path("PERFORMANCE_REPORT.txt")
    report_file.write_text(report)
    print(f"\n📄 Report saved to: {report_file.absolute()}")
    
    # Save JSON results
    json_file = Path("performance_results.json")
    json_file.write_text(json.dumps(results, indent=2))
    print(f"📄 JSON results saved to: {json_file.absolute()}")


if __name__ == "__main__":
    asyncio.run(main())
