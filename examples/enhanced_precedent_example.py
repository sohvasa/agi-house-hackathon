#!/usr/bin/env python3
"""
Simple example demonstrating the enhanced PrecedentAgent workflow.

Workflow:
1. Perplexity identifies potential cases based on legal issue
2. Browser Use retrieves detailed information from JUSTIA US Law
3. Results are enhanced with accurate citations, holdings, and facts
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.precedentAgent import PrecedentAgent


def simple_enhanced_search():
    """
    Demonstrate a simple enhanced search for trade secret cases.
    """
    print("\n" + "="*70)
    print("  ENHANCED PRECEDENT SEARCH EXAMPLE")
    print("  Using Perplexity + Browser Use for Better Case Details")
    print("="*70)
    
    # Initialize the PrecedentAgent with Browser Use enabled
    agent = PrecedentAgent(
        name="EnhancedPrecedentAgent",
        use_browser=True,  # Enable Browser Use integration
        enable_caching=True  # Cache results for efficiency
    )
    
    # Define your legal query
    legal_issue = "employee stole trade secrets and joined competitor"
    
    print(f"\n📋 Legal Issue: {legal_issue}")
    print("\n" + "-"*50)
    
    # Perform enhanced search
    print("\n🔍 Step 1: Using Perplexity to identify relevant cases...")
    print("🌐 Step 2: Using Browser Use to get details from JUSTIA...\n")
    
    # The enhanced method automatically uses both tools
    result = agent.find_precedents_enhanced(
        query=legal_issue,
        jurisdiction="federal",
        num_cases=2,  # Get top 2 most relevant cases
        deep_search=True  # Enable Browser Use for detailed info
    )
    
    # Display results
    print("\n" + "="*70)
    print("  SEARCH RESULTS")
    print("="*70)
    
    if result.cases:
        print(f"\n✅ Found {result.total_found} relevant cases:\n")
        
        for i, case in enumerate(result.cases, 1):
            print(f"\n{'─'*60}")
            print(f"CASE {i}: {case.case_name}")
            print(f"{'─'*60}")
            
            print(f"📅 Year: {case.year}")
            print(f"⚖️  Court: {case.court}")
            print(f"📖 Citation: {case.citation}")
            print(f"🔗 Source: {case.source_url}")
            print(f"✨ Confidence: {case.confidence_score:.0%}")
            
            print(f"\n🎯 Holding:")
            print(f"   {case.holding}")
            
            print(f"\n📚 Rule of Law:")
            print(f"   {case.rule}")
            
            if case.facts:
                print(f"\n📋 Key Facts:")
                print(f"   {case.facts}")
            
            if case.outcome:
                print(f"\n⚡ Outcome: {case.outcome}")
            
            # Show relevance analysis
            if case.relevance_plaintiff or case.relevance_defendant:
                print(f"\n🎭 Relevance Analysis:")
                if case.relevance_plaintiff:
                    print(f"   • Plaintiff: {case.relevance_plaintiff}")
                if case.relevance_defendant:
                    print(f"   • Defendant: {case.relevance_defendant}")
    else:
        print("❌ No relevant cases found.")
    
    print("\n" + "="*70)
    print("  END OF RESULTS")
    print("="*70)


def quick_case_lookup():
    """
    Quick lookup of a specific case using Browser Use.
    """
    print("\n\n" + "="*70)
    print("  QUICK CASE LOOKUP")
    print("="*70)
    
    agent = PrecedentAgent(use_browser=True)
    
    # Look up a specific case
    case_name = "Waymo v. Uber"
    
    print(f"\n🔍 Looking up: {case_name}")
    
    # Use quick_search for a concise result
    result = agent.quick_search(
        f"{case_name} trade secret misappropriation",
        use_browser=True  # Force Browser Use for this search
    )
    
    print("\n📄 Result:")
    print("-"*50)
    print(result)


def compare_sources():
    """
    Compare results from Perplexity vs Browser Use.
    """
    print("\n\n" + "="*70)
    print("  SOURCE COMPARISON: Perplexity vs Browser Use")
    print("="*70)
    
    query = "trade secret case involving autonomous vehicle technology"
    
    # Create two agents
    perplexity_agent = PrecedentAgent(use_browser=False)
    browser_agent = PrecedentAgent(use_browser=True)
    
    print(f"\n📋 Query: {query}\n")
    
    # Perplexity-only search
    print("1️⃣  PERPLEXITY ONLY:")
    print("-"*40)
    perplexity_result = perplexity_agent.quick_search(query)
    print(perplexity_result)
    
    # Browser Use enhanced search
    print("\n2️⃣  BROWSER USE ENHANCED:")
    print("-"*40)
    browser_result = browser_agent.quick_search(query)
    print(browser_result)
    
    print("\n💡 Note the difference in detail and accuracy!")


if __name__ == "__main__":
    # Run the examples
    print("\n" + "🚀 "*20)
    print("  ENHANCED PRECEDENT AGENT EXAMPLES")
    print("  Combining Perplexity + Browser Use for Better Legal Research")
    print("🚀 "*20)
    
    # Example 1: Enhanced search with detailed results
    simple_enhanced_search()
    
    # Example 2: Quick case lookup
    quick_case_lookup()
    
    # Example 3: Compare sources
    compare_sources()
    
    print("\n\n" + "="*70)
    print("  💡 KEY BENEFITS OF THE ENHANCED WORKFLOW:")
    print("="*70)
    print("""
    1. 🎯 More Accurate Citations: Browser Use gets exact citations from JUSTIA
    2. 📊 Better Holdings: Direct extraction from court opinions
    3. 📋 Detailed Facts: Actual case facts from the source
    4. ⚖️  Higher Confidence: Data comes directly from JUSTIA US Law
    5. 🔄 Automatic Fallback: Uses Perplexity if Browser Use fails
    
    The two-step process ensures you get both broad coverage (Perplexity)
    and precise details (Browser Use) for comprehensive legal research.
    """)
    print("="*70)
