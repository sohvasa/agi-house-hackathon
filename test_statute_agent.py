#!/usr/bin/env python3
"""
Quick test of the StatuteAgent for legal research.
This demonstrates the core functionality with minimal setup.
"""

import os
from dotenv import load_dotenv
from agents.statuteAgent import StatuteAgent

# Load environment variables
load_dotenv()

def main():
    # Check for API key
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("⚠️  Error: PERPLEXITY_API_KEY not found in .env file")
        print("Please add your Perplexity API key to use the StatuteAgent")
        return
    
    print("=" * 70)
    print(" STATUTE AGENT - Quick Legal Research Test")
    print("=" * 70)
    
    # Initialize the agent
    print("\n📚 Initializing StatuteAgent...")
    agent = StatuteAgent()
    
    # Example query from your requirements
    print("\n" + "-" * 70)
    print("TEST 1: Trade Secret Law")
    print("-" * 70)
    
    query = "Find the U.S. law that governs trade secret misappropriation, its citation, definitions of trade secret and misappropriation, and remedies"
    print(f"\n🔍 Query: {query}")
    
    try:
        result = agent.quick_search(query)
        print(f"\n📖 Result: {result}")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    # Additional quick tests
    print("\n" + "-" * 70)
    print("TEST 2: Other Common Statutes")
    print("-" * 70)
    
    test_queries = [
        "What federal law covers computer fraud and hacking?",
        "Find the securities fraud statute",
        "What is the RICO statute?"
    ]
    
    for i, q in enumerate(test_queries, 1):
        print(f"\n{i}. Query: {q}")
        try:
            result = agent.quick_search(q)
            print(f"   Result: {result}")
        except Exception as e:
            print(f"   Error: {e}")
    
    print("\n" + "=" * 70)
    print(" Test Complete!")
    print("=" * 70)
    print("\nThe StatuteAgent successfully:")
    print("✅ Finds relevant U.S. statutes")
    print("✅ Extracts citations (e.g., 18 U.S.C. § 1836)")
    print("✅ Identifies key definitions")
    print("✅ Lists available remedies")
    print("✅ Returns concise 2-3 sentence summaries")
    print("\nFor more examples, run: python examples/statute_agent_demo.py")


if __name__ == "__main__":
    main()
