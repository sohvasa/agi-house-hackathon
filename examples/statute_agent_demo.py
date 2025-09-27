"""
Demonstration of the StatuteAgent for legal research.
Shows various capabilities for finding and analyzing U.S. statutes.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.statuteAgent import StatuteAgent
import json


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)


def demo_quick_search():
    """Demonstrate the quick search feature for common legal queries"""
    print_section("Quick Statute Search - Concise Snippets")
    
    agent = StatuteAgent(name="LegalResearchBot")
    
    # Various legal queries
    queries = [
        "Find the U.S. law that governs trade secret misappropriation, its citation, definitions of trade secret and misappropriation, and remedies",
        "What federal statute covers wire fraud and what are the penalties?",
        "Find the law for copyright infringement and available remedies",
        "What is the federal anti-kickback statute in healthcare?",
        "Find the Foreign Corrupt Practices Act and its main provisions",
        "What law governs insider trading and securities fraud?",
        "Find RICO statute and what constitutes racketeering",
        "What is the federal whistleblower protection statute?"
    ]
    
    for query in queries:
        print(f"\n📋 Query: {query}")
        try:
            result = agent.quick_search(query)
            print(f"📖 Result: {result}\n")
            print("-" * 70)
        except Exception as e:
            print(f"❌ Error: {e}\n")


def demo_detailed_statute_analysis():
    """Demonstrate detailed statute analysis capabilities"""
    print_section("Detailed Statute Analysis")
    
    agent = StatuteAgent()
    
    # Analyze the Defend Trade Secrets Act
    print("\n🔍 Analyzing: Defend Trade Secrets Act (DTSA)")
    
    statute_info = agent.find_statute(
        "Defend Trade Secrets Act trade secret misappropriation federal law",
        jurisdiction="federal"
    )
    
    print(f"\n📚 Title: {statute_info.title}")
    print(f"📌 Citation: {statute_info.citation}")
    print(f"🔗 Source: {statute_info.source_url if statute_info.source_url else 'N/A'}")
    
    if statute_info.definitions:
        print("\n📝 Key Definitions:")
        for term, definition in list(statute_info.definitions.items())[:3]:
            print(f"   • '{term.title()}':")
            print(f"     {definition[:150]}...")
    
    if statute_info.key_provisions:
        print("\n⚖️ Key Provisions:")
        for i, provision in enumerate(statute_info.key_provisions[:3], 1):
            print(f"   {i}. {provision[:100]}...")
    
    if statute_info.remedies:
        print("\n💼 Available Remedies:")
        for remedy in statute_info.remedies[:4]:
            print(f"   • {remedy[:100]}...")
    
    print(f"\n📄 Summary: {statute_info.snippet}")


def demo_statute_comparison():
    """Demonstrate comparing different statutes"""
    print_section("Statute Comparison")
    
    agent = StatuteAgent()
    
    print("\n⚖️ Comparing Federal vs State Trade Secret Laws")
    
    comparison = agent.compare_statutes(
        "Federal Defend Trade Secrets Act (DTSA)",
        "Uniform Trade Secrets Act (UTSA)",
        comparison_points=["scope", "remedies", "requirements"]
    )
    
    print(f"\n📊 Comparison: {comparison['statute1']} vs {comparison['statute2']}")
    print(f"\n📝 Overview:")
    print(f"   {comparison['overview'][:300]}...")
    
    if "scope_comparison" in comparison:
        print(f"\n🎯 Scope Comparison:")
        print(f"   {comparison['scope_comparison'][:200]}...")
    
    if "remedies_comparison" in comparison:
        print(f"\n💰 Remedies Comparison:")
        print(f"   {comparison['remedies_comparison'][:200]}...")


def demo_find_related_statutes():
    """Demonstrate finding related statutes"""
    print_section("Finding Related Statutes")
    
    agent = StatuteAgent()
    
    base_statute = "Computer Fraud and Abuse Act (CFAA)"
    print(f"\n🔍 Finding statutes related to: {base_statute}")
    
    # Find similar statutes
    similar = agent.find_related_statutes(base_statute, "similar")
    print(f"\n📚 Similar Statutes:")
    for statute in similar[:5]:
        print(f"   • {statute['citation']}")
        print(f"     Relationship: {statute['relationship']}")
        print(f"     {statute['description']}")
    
    # Find implementing regulations
    print(f"\n📋 Implementing Regulations:")
    implementing = agent.find_related_statutes(base_statute, "implementing")
    for statute in implementing[:3]:
        print(f"   • {statute['citation']}")


def demo_case_law_research():
    """Demonstrate finding relevant case law"""
    print_section("Case Law Research")
    
    agent = StatuteAgent()
    
    statute = "18 U.S.C. § 1030 (Computer Fraud and Abuse Act)"
    print(f"\n⚖️ Finding case law for: {statute}")
    
    # Federal cases
    federal_cases = agent.get_case_law(statute, num_cases=3, jurisdiction="federal")
    print(f"\n📚 Federal Cases:")
    for case in federal_cases:
        print(f"   • {case['name']}")
        print(f"     Citation: {case['citation']}")
        print(f"     Relevance: {case['relevance']}")
    
    # Supreme Court cases
    scotus_cases = agent.get_case_law(statute, num_cases=2, jurisdiction="supreme court")
    print(f"\n🏛️ Supreme Court Cases:")
    for case in scotus_cases:
        print(f"   • {case['name']}")
        print(f"     Citation: {case['citation']}")


def demo_comprehensive_analysis():
    """Demonstrate comprehensive statute analysis"""
    print_section("Comprehensive Statute Analysis")
    
    agent = StatuteAgent()
    
    citation = "15 U.S.C. § 78j(b)"  # Securities Exchange Act Section 10(b)
    print(f"\n📊 Comprehensive Analysis of: {citation}")
    print("(Securities fraud / Rule 10b-5)")
    
    analysis = agent.analyze_statute(
        citation,
        aspects=["definitions", "elements", "defenses", "remedies", "jurisdiction"]
    )
    
    print(f"\n📌 Citation: {analysis['citation']}")
    print(f"📅 Analysis Date: {analysis['analysis_date'][:10]}")
    
    for aspect in ["definitions", "elements", "defenses", "remedies", "jurisdiction"]:
        if aspect in analysis:
            print(f"\n{aspect.upper()}:")
            print(f"   {analysis[aspect][:250]}...")


def demo_specialized_searches():
    """Demonstrate specialized legal searches"""
    print_section("Specialized Legal Searches")
    
    agent = StatuteAgent()
    
    # Criminal law search
    print("\n🚔 Criminal Law Statutes:")
    criminal_queries = [
        "federal conspiracy statute",
        "mail and wire fraud statutes",
        "money laundering statute"
    ]
    
    for query in criminal_queries:
        result = agent.quick_search(query)
        print(f"\n   Query: {query}")
        print(f"   → {result}")
    
    # Business law search
    print("\n\n💼 Business Law Statutes:")
    business_queries = [
        "Sherman Antitrust Act provisions",
        "Sarbanes-Oxley Act requirements",
        "Dodd-Frank whistleblower provisions"
    ]
    
    for query in business_queries:
        result = agent.quick_search(query)
        print(f"\n   Query: {query}")
        print(f"   → {result}")
    
    # IP law search
    print("\n\n🎨 Intellectual Property Statutes:")
    ip_queries = [
        "patent infringement statute",
        "trademark dilution federal law",
        "DMCA safe harbor provisions"
    ]
    
    for query in ip_queries:
        result = agent.quick_search(query)
        print(f"\n   Query: {query}")
        print(f"   → {result}")


def demo_export_research():
    """Demonstrate exporting research results"""
    print_section("Export Research Results")
    
    agent = StatuteAgent()
    
    # Perform several searches to build history
    print("\n📚 Building research history...")
    
    searches = [
        "Securities Exchange Act",
        "RICO statute",
        "False Claims Act"
    ]
    
    for search in searches:
        agent.quick_search(search)
        print(f"   ✓ Researched: {search}")
    
    # Export to markdown
    markdown_file = agent.export_research(format="markdown")
    print(f"\n📄 Research exported to Markdown: {markdown_file}")
    
    # Export to JSON
    json_file = agent.export_research(format="json")
    print(f"📊 Research exported to JSON: {json_file}")
    
    # Display a preview of the JSON export
    with open(json_file, 'r') as f:
        data = json.load(f)
        print(f"\n📋 Export Preview:")
        print(f"   • Agent: {data['agent']}")
        print(f"   • Export Date: {data['export_date'][:10]}")
        print(f"   • Search History Items: {len(data['search_history'])}")
        print(f"   • Cached Results: {len(data['cached_results'])}")


def main():
    """Run all demonstrations"""
    print("\n" + "=" * 70)
    print(" STATUTE AGENT DEMONSTRATION")
    print(" Legal Research Assistant for U.S. Federal and State Law")
    print("=" * 70)
    
    # Check for API key
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("\n⚠️  WARNING: PERPLEXITY_API_KEY not found in environment")
        print("   The StatuteAgent requires Perplexity API access for legal research")
        print("   Please set your API key in the .env file to run this demo\n")
        return
    
    print("\nThis demo showcases various legal research capabilities:")
    print("  • Quick statute searches with concise snippets")
    print("  • Detailed statute analysis with definitions and remedies")
    print("  • Comparing different statutes")
    print("  • Finding related laws and regulations")
    print("  • Researching relevant case law")
    print("  • Comprehensive legal analysis")
    print("  • Exporting research results")
    
    try:
        # Run demonstrations
        demos = [
            ("Quick Search", demo_quick_search),
            ("Detailed Analysis", demo_detailed_statute_analysis),
            ("Statute Comparison", demo_statute_comparison),
            ("Related Statutes", demo_find_related_statutes),
            ("Case Law Research", demo_case_law_research),
            ("Comprehensive Analysis", demo_comprehensive_analysis),
            ("Specialized Searches", demo_specialized_searches),
            ("Export Research", demo_export_research)
        ]
        
        for i, (name, demo_func) in enumerate(demos, 1):
            print(f"\n\n{'='*70}")
            print(f" Demo {i}/{len(demos)}: {name}")
            print('='*70)
            
            response = input("\nPress Enter to run this demo (or 's' to skip, 'q' to quit): ")
            
            if response.lower() == 'q':
                print("\nExiting demo...")
                break
            elif response.lower() == 's':
                print(f"Skipping {name}...")
                continue
            
            demo_func()
            
            if i < len(demos):
                input("\nPress Enter to continue to the next demo...")
        
        print("\n" + "=" * 70)
        print(" DEMONSTRATION COMPLETE")
        print("=" * 70)
        print("\nThe StatuteAgent is ready for legal research tasks!")
        print("Use it to quickly find statutes, analyze laws, and research case law.\n")
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
