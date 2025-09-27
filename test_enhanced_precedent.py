#!/usr/bin/env python3
"""
Test script for the enhanced PrecedentAgent with Browser Use integration.
This demonstrates the two-step workflow:
1. Perplexity identifies relevant cases
2. Browser Use gets detailed information from JUSTIA
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.precedentAgent import PrecedentAgent


def print_separator(title: str = None):
    """Print a formatted separator."""
    print("\n" + "="*80)
    if title:
        print(f"  {title}")
        print("="*80)
    print()


def test_enhanced_search():
    """Test the enhanced search with Browser Use."""
    print_separator("TEST 1: Enhanced Search with Browser Use")
    
    # Initialize agent with Browser Use enabled
    agent = PrecedentAgent(use_browser=True)
    
    # Test query for trade secret case
    query = "employee downloaded confidential files before leaving to competitor"
    
    print(f"Query: {query}")
    print("\nStarting enhanced search (Perplexity + Browser Use)...")
    print("-" * 60)
    
    # Use the enhanced search method
    result = agent.find_precedents_enhanced(
        query=query,
        jurisdiction="federal",
        num_cases=2,  # Limited for efficiency
        deep_search=True
    )
    
    print(f"\n\nFound {result.total_found} enhanced cases:")
    print("-" * 60)
    
    for i, case in enumerate(result.cases, 1):
        print(f"\n[Case {i}]")
        print(case.mini_doc)
        print()


def test_quick_search_comparison():
    """Compare results between Perplexity-only and Browser Use enhanced searches."""
    print_separator("TEST 2: Comparison - Perplexity vs Browser Use Enhanced")
    
    query = "Waymo v. Uber trade secret"
    
    # Test with Perplexity only
    print("A) Perplexity-Only Search:")
    print("-" * 40)
    agent_perplexity = PrecedentAgent(use_browser=False)
    result_perplexity = agent_perplexity.quick_search(query)
    print(result_perplexity)
    
    print("\n" + "-" * 40)
    print("B) Browser Use Enhanced Search:")
    print("-" * 40)
    agent_browser = PrecedentAgent(use_browser=True)
    result_browser = agent_browser.quick_search(query, use_browser=True)
    print(result_browser)


def test_topic_search():
    """Test searching by legal topic rather than specific case."""
    print_separator("TEST 3: Topic-Based Search with Browser Use")
    
    agent = PrecedentAgent(use_browser=True)
    
    # Search for a legal topic
    topic = "trade secret misappropriation involving source code theft"
    
    print(f"Legal Topic: {topic}")
    print("\nSearching for relevant precedents...")
    print("-" * 60)
    
    result = agent.find_precedents_enhanced(
        query=topic,
        jurisdiction="federal",
        num_cases=2,
        year_range=(2015, 2024),
        deep_search=True
    )
    
    if result.cases:
        for case in result.cases:
            print(f"\n• {case.case_name} ({case.year})")
            print(f"  Court: {case.court}")
            print(f"  Citation: {case.citation}")
            print(f"  Holding: {case.holding[:150]}...")
            if case.facts:
                print(f"  Facts: {case.facts[:150]}...")
            print(f"  Source: {case.source_url}")
            print(f"  Confidence: {case.confidence_score:.0%}")


def test_custom_browser_query():
    """Test using custom Browser Use queries."""
    print_separator("TEST 4: Custom Browser Use Query")
    
    from util.browseruse import BrowserUseAgent
    
    browser = BrowserUseAgent()
    
    # Create a custom query for a specific type of search
    custom_query = (
        "Go to JUSTIA US Law. "
        "Search for the most cited trade secret cases from the Federal Circuit. "
        "Focus on cases involving technology companies and former employees. "
        "For the top 2 cases, provide: "
        "1) Full case name and citation, "
        "2) Year and court, "
        "3) The specific trade secret issue involved, "
        "4) The test or standard applied by the court, "
        "5) The outcome and any injunction granted."
    )
    
    print("Custom Query:")
    print(custom_query)
    print("\nExecuting Browser Use search...")
    print("-" * 60)
    
    result = browser.search_case_on_justia(custom_query=custom_query)
    print("\nResults from JUSTIA:")
    print(result)


def test_fallback_handling():
    """Test fallback to Perplexity when Browser Use fails or is unavailable."""
    print_separator("TEST 5: Fallback Handling")
    
    # Create agent with Browser Use
    agent = PrecedentAgent(use_browser=True)
    
    # Test with a complex query that might challenge Browser Use
    query = "quantum computing patent trade secret hybrid protection strategy cases"
    
    print(f"Complex Query: {query}")
    print("\nAttempting enhanced search with automatic fallback...")
    print("-" * 60)
    
    result = agent.find_precedents_enhanced(
        query=query,
        num_cases=1,
        deep_search=True
    )
    
    if result.cases:
        case = result.cases[0]
        print(f"\nResult obtained:")
        print(f"Case: {case.case_name}")
        print(f"Source: {case.source_url}")
        print(f"Confidence: {case.confidence_score:.0%}")
        print(f"\nMini-doc:\n{case.mini_doc}")
    else:
        print("No cases found for this query.")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("  ENHANCED PRECEDENT AGENT TEST SUITE")
    print("  Testing Perplexity + Browser Use Integration")
    print("="*80)
    print(f"\nTest Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Enhanced Search", test_enhanced_search),
        ("Comparison Test", test_quick_search_comparison),
        ("Topic Search", test_topic_search),
        ("Custom Query", test_custom_browser_query),
        ("Fallback Handling", test_fallback_handling)
    ]
    
    print("\nTests to run:")
    for i, (name, _) in enumerate(tests, 1):
        print(f"  {i}. {name}")
    
    # Run tests
    for name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"\n⚠️  Error in {name}: {e}")
            import traceback
            traceback.print_exc()
    
    print_separator("ALL TESTS COMPLETED")
    print("The enhanced PrecedentAgent now uses a two-step process:")
    print("1. Perplexity for initial case discovery")
    print("2. Browser Use for detailed information from JUSTIA")
    print("\nThis provides more accurate and detailed case information!")


if __name__ == "__main__":
    main()
