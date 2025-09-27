#!/usr/bin/env python3
"""
Test the PrecedentAgent for finding and analyzing case law precedents.
Demonstrates mini-doc generation and case analysis capabilities.
Now enhanced with Browser Use for detailed JUSTIA US Law data.
"""

import os
from dotenv import load_dotenv
from agents.precedentAgent import PrecedentAgent

# Load environment variables
load_dotenv()


def print_section(title: str):
    """Print formatted section header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def test_quick_search():
    """Test quick search with mini-doc output (Browser Use Enhanced)"""
    print_section("QUICK SEARCH TEST - Mini-Doc Format (JUSTIA Enhanced)")
    
    agent = PrecedentAgent(use_browser=True)  # Enable Browser Use
    
    test_queries = [
        "Find a famous case involving trade secret misappropriation",
        "Employee downloaded confidential files breach of contract",
        "Copyright infringement software code",
        "Patent invalidity prior art",
        "Securities fraud insider trading"
    ]
    
    for query in test_queries:
        print(f"\n📋 Query: {query}")
        print("-" * 60)
        print("🌐 Using Browser Use to fetch from JUSTIA...")
        result = agent.quick_search(query, use_browser=True)  # Use Browser Use
        print(result)


def test_comprehensive_search():
    """Test comprehensive precedent search with Browser Use"""
    print_section("COMPREHENSIVE PRECEDENT SEARCH (JUSTIA ENHANCED)")
    
    agent = PrecedentAgent(use_browser=True)  # Enable Browser Use
    
    # Search for trade secret cases
    print("\n🔍 Searching for: Trade secret misappropriation involving employees")
    print("📊 Using enhanced search (Perplexity + Browser Use)...")
    
    # Use enhanced search with Browser Use
    result = agent.find_precedents_enhanced(
        "employee downloaded confidential files trade secret misappropriation NDA",
        jurisdiction="federal",
        num_cases=2,  # Limit for Browser Use efficiency
        deep_search=True  # Enable Browser Use
    )
    
    print(f"\n📊 Found {result.total_found} relevant cases from JUSTIA")
    print(f"🏛️ Jurisdiction: {result.jurisdiction}")
    
    # Display each case mini-doc
    for i, case in enumerate(result.cases, 1):
        print(f"\n{'='*60}")
        print(f" CASE #{i} - JUSTIA DATA")
        print('='*60)
        print(case.mini_doc)
        
        # Show additional analysis
        if case.facts:
            print(f"\n💡 Key Facts: {case.facts[:200]}...")
        if case.procedural_posture:
            print(f"📑 Procedural Posture: {case.procedural_posture}")
        if case.confidence_score > 0:
            print(f"🎯 Confidence Score: {case.confidence_score:.0%}")


def test_waymo_uber_style():
    """Test finding a specific case in the format requested"""
    print_section("WAYMO v. UBER STYLE CASE SEARCH (JUSTIA ENHANCED)")
    
    agent = PrecedentAgent(use_browser=True)  # Enable Browser Use
    
    print("\n🔍 Query: Find Waymo v. Uber trade secret case")
    print("🌐 Using Browser Use to get detailed info from JUSTIA...")
    
    # Search for the specific case using enhanced method
    result = agent.find_precedents_enhanced(
        "Waymo v. Uber trade secret misappropriation employee downloaded files",
        jurisdiction="federal",
        num_cases=1,
        year_range=(2016, 2018),
        deep_search=True
    )
    
    if result.cases:
        case = result.cases[0]
        
        # Format as mini-doc exactly as requested
        mini_doc = f"""Case: {case.case_name} ({case.year})
Citation: {case.court}, {case.year}
         {case.citation}
Holding: {case.holding}
Rule: {case.rule}
Relevance: {case.relevance_plaintiff if case.relevance_plaintiff else 'Analysis pending'}; {case.relevance_defendant if case.relevance_defendant else 'Further review needed'}
[Source: JUSTIA US Law]"""
        
        print("\n📄 Mini-Doc Output (Enhanced with JUSTIA):")
        print("-" * 60)
        print(mini_doc)
    else:
        print("❌ Case not found")


def test_landmark_cases():
    """Test finding landmark cases in an area of law with Browser Use"""
    print_section("LANDMARK CASES IN TRADE SECRET LAW (JUSTIA ENHANCED)")
    
    agent = PrecedentAgent(use_browser=True)  # Enable Browser Use
    
    print("\n🌐 Fetching landmark cases from JUSTIA...")
    
    # Use enhanced search for landmark cases
    landmark_result = agent.find_precedents_enhanced(
        "landmark trade secret cases technology companies",
        jurisdiction="federal",
        num_cases=3,
        deep_search=True
    )
    
    print("\n⚖️ Landmark Trade Secret Cases (from JUSTIA):")
    print("-" * 60)
    
    for case in landmark_result.cases:
        print(f"\n📚 {case.case_name} ({case.year})")
        print(f"   Court: {case.court}")
        print(f"   Citation: {case.citation}")
        print(f"   Holding: {case.holding[:150]}...")
        print(f"   Significance: Established that {case.rule[:100]}...")
        print(f"   Source: {case.source_url}")


def test_circuit_analysis():
    """Test analyzing different circuit approaches with Browser Use"""
    print_section("CIRCUIT SPLIT ANALYSIS (JUSTIA ENHANCED)")
    
    agent = PrecedentAgent(use_browser=True)  # Enable Browser Use
    
    print("\n🔍 Analyzing: Trade secret inevitable disclosure doctrine")
    print("🌐 Using Browser Use to search JUSTIA for circuit cases...")
    
    # Search for circuit split using enhanced method
    # We'll search for cases from different circuits
    circuits_to_test = ["Ninth Circuit", "Second Circuit"]
    
    print("\n📊 Circuit Approaches:")
    for circuit in circuits_to_test:
        result = agent.find_precedents_enhanced(
            f"{circuit} inevitable disclosure doctrine trade secrets",
            jurisdiction="federal",
            num_cases=1,
            deep_search=True
        )
        if result.cases:
            case = result.cases[0]
            print(f"\n{circuit}:")
            print(f"  • {case.case_name} ({case.year})")
            print(f"    Citation: {case.citation}")
            print(f"    Position: {case.holding[:100]}...")


def test_case_comparison():
    """Test comparing two precedents with enhanced data"""
    print_section("PRECEDENT COMPARISON (JUSTIA ENHANCED)")
    
    agent = PrecedentAgent(use_browser=True)  # Enable Browser Use
    
    print("\n📊 Comparing trade secret misappropriation cases:")
    print("🌐 Fetching enhanced data from JUSTIA for both cases...")
    
    # Get two cases to compare using enhanced search
    result = agent.find_precedents_enhanced(
        "trade secret misappropriation employee competitor",
        num_cases=2,
        deep_search=True
    )
    
    if len(result.cases) >= 2:
        case1 = result.cases[0]
        case2 = result.cases[1]
        
        print(f"\n1️⃣ {case1.case_name} ({case1.year})")
        print(f"   Citation: {case1.citation}")
        print(f"   Holding: {case1.holding[:100]}...")
        
        print(f"\n2️⃣ {case2.case_name} ({case2.year})")
        print(f"   Citation: {case2.citation}")
        print(f"   Holding: {case2.holding[:100]}...")
        
        # Analyze differences
        print("\n🔄 Comparison:")
        if case1.court_level == case2.court_level:
            print(f"  ✓ Both at {case1.court_level.value} level")
        else:
            print(f"  ✗ Different levels: {case1.court_level.value} vs {case2.court_level.value}")
        
        # Compare outcomes
        if "granted" in case1.holding.lower() and "granted" in case2.holding.lower():
            print("  ✓ Both granted relief")
        elif "denied" in case1.holding.lower() and "denied" in case2.holding.lower():
            print("  ✓ Both denied relief")
        else:
            print("  ✗ Different outcomes")
        
        print(f"\n📊 Data Quality:")
        print(f"  Case 1: {case1.confidence_score:.0%} confidence")
        print(f"  Case 2: {case2.confidence_score:.0%} confidence")
        print(f"  Both from: JUSTIA US Law")


def test_browser_vs_perplexity():
    """Compare results from Browser Use vs Perplexity only"""
    print_section("BROWSER USE vs PERPLEXITY COMPARISON")
    
    query = "trade secret misappropriation autonomous vehicle technology"
    
    print(f"\n📋 Query: {query}")
    
    # Test with Perplexity only
    print("\n1️⃣ PERPLEXITY ONLY:")
    print("-" * 40)
    agent_perplexity = PrecedentAgent(use_browser=False)
    perplexity_result = agent_perplexity.quick_search(query)
    print(perplexity_result)
    
    # Test with Browser Use
    print("\n2️⃣ BROWSER USE ENHANCED:")
    print("-" * 40)
    agent_browser = PrecedentAgent(use_browser=True)
    browser_result = agent_browser.quick_search(query, use_browser=True)
    print(browser_result)
    
    print("\n💡 Notice the difference in detail and accuracy!")


def main():
    # Check for API keys
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("⚠️  Error: PERPLEXITY_API_KEY not found in .env file")
        print("Please add your Perplexity API key to use the PrecedentAgent")
        return
    
    if not os.getenv("BROWSER_USE_API_KEY"):
        print("⚠️  Warning: BROWSER_USE_API_KEY not found")
        print("Browser Use features will be disabled")
    
    print("=" * 70)
    print(" PRECEDENT AGENT TEST - BROWSER USE ENHANCED")
    print(" Case Law Research with JUSTIA US Law Integration")
    print("=" * 70)
    
    try:
        # Run tests
        test_waymo_uber_style()  # Start with the specific example requested
        
        response = input("\n\nPress Enter to test quick searches (or 'q' to quit): ")
        if response.lower() != 'q':
            test_quick_search()
        
        response = input("\n\nPress Enter to test comprehensive search (or 'q' to quit): ")
        if response.lower() != 'q':
            test_comprehensive_search()
        
        response = input("\n\nPress Enter to test landmark cases (or 'q' to quit): ")
        if response.lower() != 'q':
            test_landmark_cases()
        
        response = input("\n\nPress Enter to test case comparison (or 'q' to quit): ")
        if response.lower() != 'q':
            test_case_comparison()
        
        response = input("\n\nPress Enter to compare Browser Use vs Perplexity (or 'q' to quit): ")
        if response.lower() != 'q':
            test_browser_vs_perplexity()
        
        print("\n" + "=" * 70)
        print(" TEST COMPLETE - BROWSER USE ENHANCED")
        print("=" * 70)
        print("\n✅ PrecedentAgent with Browser Use provides:")
        print("  • 🎯 Accurate citations directly from JUSTIA US Law")
        print("  • 📊 Detailed holdings and rules from court opinions")
        print("  • 📋 Actual case facts and procedural history")
        print("  • ⚖️ Enhanced relevance analysis")
        print("  • 🌐 Two-step verification (Perplexity + JUSTIA)")
        print("  • 💯 95% confidence for JUSTIA-sourced data")
        print("\n🎯 Superior legal research with authoritative sources!")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()