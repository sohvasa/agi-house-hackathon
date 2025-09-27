#!/usr/bin/env python3
"""
Test the enhanced StatuteAgent with comprehensive legal research capabilities.
Demonstrates both quick searches and detailed lawyer-level research.
"""

import os
import json
from dotenv import load_dotenv
from agents.statuteAgent import StatuteAgent

# Load environment variables
load_dotenv()


def print_section(title: str, level: int = 1):
    """Print formatted section headers"""
    if level == 1:
        print("\n" + "=" * 80)
        print(f" {title}")
        print("=" * 80)
    else:
        print("\n" + "-" * 60)
        print(f" {title}")
        print("-" * 60)


def test_quick_vs_comprehensive():
    """Compare quick search vs comprehensive research for the same query"""
    
    agent = StatuteAgent()
    query = "Find the U.S. law that governs trade secret misappropriation, its citation, definitions of trade secret and misappropriation, and remedies"
    
    print_section("COMPARISON: Quick Search vs Comprehensive Research")
    
    # Quick search
    print_section("Quick Search Result", 2)
    quick_result = agent.quick_search(query)
    print(f"\n{quick_result}")
    print(f"\n📏 Length: {len(quick_result)} characters")
    
    # Comprehensive research
    print_section("Comprehensive Research Result", 2)
    comprehensive = agent.comprehensive_research(query, include_case_law=True, num_cases=3)
    
    # Display comprehensive results
    statute = comprehensive['statute']
    
    print(f"\n📚 TITLE: {statute['title']}")
    print(f"📌 CITATION: {statute['citation']}")
    print(f"🔗 SOURCE: {statute['source_url'] if statute['source_url'] else 'N/A'}")
    
    # Definitions
    if statute['definitions']:
        print(f"\n📝 DEFINITIONS ({len(statute['definitions'])} found):")
        for term, definition in list(statute['definitions'].items())[:3]:
            print(f"\n  '{term.upper()}':")
            print(f"  {definition[:200]}{'...' if len(definition) > 200 else ''}")
    
    # Key provisions
    if statute['key_provisions']:
        print(f"\n⚖️ KEY PROVISIONS ({len(statute['key_provisions'])} found):")
        for i, provision in enumerate(statute['key_provisions'][:3], 1):
            print(f"\n  {i}. {provision[:150]}{'...' if len(provision) > 150 else ''}")
    
    # Remedies
    if statute['remedies']:
        print(f"\n💼 REMEDIES ({len(statute['remedies'])} found):")
        for remedy in statute['remedies'][:3]:
            print(f"  • {remedy[:150]}{'...' if len(remedy) > 150 else ''}")
    
    # Full text info
    if statute['full_text']:
        print(f"\n📜 FULL STATUTORY TEXT:")
        print(f"  Length: {len(statute['full_text'])} characters")
        print(f"  Preview: {statute['full_text'][:300]}...")
    
    # Sections
    if statute['sections']:
        print(f"\n📑 STATUTORY SECTIONS ({len(statute['sections'])} found):")
        for section_id, section_text in list(statute['sections'].items())[:3]:
            print(f"  • {section_id}: {section_text[:100]}...")
    
    # Legislative history
    if statute['legislative_history']:
        print(f"\n📚 LEGISLATIVE HISTORY:")
        print(f"  {statute['legislative_history'][:300]}...")
    
    # Interpretive notes
    if statute['interpretive_notes']:
        print(f"\n⚖️ JUDICIAL INTERPRETATION:")
        print(f"  {statute['interpretive_notes'][:300]}...")
    
    # Case law
    if 'case_law' in comprehensive and comprehensive['case_law']:
        print(f"\n👨‍⚖️ RELEVANT CASE LAW ({len(comprehensive['case_law'])} cases):")
        for case in comprehensive['case_law'][:3]:
            print(f"  • {case['name']}")
            print(f"    Citation: {case['citation']}")
            print(f"    Relevance: {case['relevance']}")
    
    # Related statutes
    if 'related_statutes' in comprehensive and comprehensive['related_statutes']:
        print(f"\n📋 RELATED STATUTES:")
        for related in comprehensive['related_statutes']:
            print(f"  • {related['citation']} ({related['relationship']})")
    
    # Show analysis summary
    print_section("Generated Legal Analysis Summary", 2)
    print(comprehensive['analysis_summary'][:1500])
    if len(comprehensive['analysis_summary']) > 1500:
        print("\n[... truncated for display ...]")


def test_different_statutes():
    """Test comprehensive research on different types of statutes"""
    
    agent = StatuteAgent()
    
    test_cases = [
        {
            "name": "Computer Fraud",
            "query": "Computer Fraud and Abuse Act full text provisions penalties"
        },
        {
            "name": "Securities Fraud",
            "query": "Securities Exchange Act section 10(b) Rule 10b-5 insider trading"
        },
        {
            "name": "RICO",
            "query": "RICO statute racketeering pattern criminal enterprise"
        }
    ]
    
    print_section("TESTING DIFFERENT STATUTES")
    
    for test in test_cases:
        print_section(f"Researching: {test['name']}", 2)
        
        # Get comprehensive research
        research = agent.comprehensive_research(test['query'], include_case_law=False)
        statute = research['statute']
        
        print(f"\n📚 {statute['title']}")
        print(f"📌 {statute['citation']}")
        print(f"\n📝 Summary: {statute['summary']}")
        
        # Show some key content
        if statute['definitions']:
            print(f"\n🔍 Key Terms Defined: {', '.join(list(statute['definitions'].keys())[:5])}")
        
        if statute['key_provisions']:
            print(f"\n⚖️ Number of Provisions: {len(statute['key_provisions'])}")
        
        if statute['full_text']:
            print(f"\n📜 Full Text Length: {len(statute['full_text'])} characters")


def test_state_vs_federal():
    """Test jurisdiction differences"""
    
    agent = StatuteAgent()
    
    print_section("JURISDICTION COMPARISON: Federal vs State")
    
    # Federal statute
    print_section("Federal Trade Secret Law", 2)
    federal = agent.comprehensive_research(
        "trade secret misappropriation",
        jurisdiction="federal",
        include_case_law=False
    )
    print(f"📚 {federal['statute']['title']}")
    print(f"📌 {federal['statute']['citation']}")
    print(f"📝 {federal['statute']['summary']}")
    
    # California state law
    print_section("California Trade Secret Law", 2)
    california = agent.comprehensive_research(
        "trade secret misappropriation",
        jurisdiction="California",
        include_case_law=False
    )
    print(f"📚 {california['statute']['title']}")
    print(f"📌 {california['statute']['citation']}")
    print(f"📝 {california['statute']['summary']}")


def save_research_for_lawyer():
    """Save comprehensive research to file for lawyer review"""
    
    agent = StatuteAgent()
    
    print_section("SAVING RESEARCH FOR LAWYER REVIEW")
    
    # Perform comprehensive research
    query = "Federal wire fraud statute elements interstate commerce requirement penalties"
    print(f"\n🔍 Researching: {query}")
    
    research = agent.comprehensive_research(query, include_case_law=True, num_cases=5)
    
    # Save to JSON file
    filename = "wire_fraud_research.json"
    with open(filename, 'w') as f:
        json.dump(research, f, indent=2, default=str)
    
    print(f"\n✅ Research saved to: {filename}")
    print(f"📊 File contains:")
    print(f"  • Full statutory text: {'Yes' if research['statute']['full_text'] else 'No'}")
    print(f"  • Sections: {len(research['statute']['sections']) if research['statute']['sections'] else 0}")
    print(f"  • Definitions: {len(research['statute']['definitions']) if research['statute']['definitions'] else 0}")
    print(f"  • Provisions: {len(research['statute']['key_provisions']) if research['statute']['key_provisions'] else 0}")
    print(f"  • Case law: {len(research.get('case_law', [])) if 'case_law' in research else 0} cases")
    print(f"  • Related statutes: {len(research.get('related_statutes', [])) if 'related_statutes' in research else 0}")
    
    # Save summary to markdown
    md_filename = "wire_fraud_summary.md"
    with open(md_filename, 'w') as f:
        f.write(f"# Legal Research Summary\n\n")
        f.write(f"**Query**: {query}\n")
        f.write(f"**Date**: {research['timestamp']}\n")
        f.write(f"**Jurisdiction**: {research['jurisdiction']}\n\n")
        f.write("---\n\n")
        f.write(research['analysis_summary'])
    
    print(f"📄 Summary saved to: {md_filename}")
    
    return filename, md_filename


def main():
    # Check for API key
    if not os.getenv("PERPLEXITY_API_KEY"):
        print("⚠️  Error: PERPLEXITY_API_KEY not found in .env file")
        print("Please add your Perplexity API key to use the StatuteAgent")
        return
    
    print("=" * 80)
    print(" COMPREHENSIVE STATUTE AGENT TEST")
    print(" Enhanced Legal Research for Lawyer Agents")
    print("=" * 80)
    
    try:
        # Run tests
        test_quick_vs_comprehensive()
        
        response = input("\n\nPress Enter to test different statutes (or 'q' to quit): ")
        if response.lower() != 'q':
            test_different_statutes()
        
        response = input("\n\nPress Enter to test jurisdictions (or 'q' to quit): ")
        if response.lower() != 'q':
            test_state_vs_federal()
        
        response = input("\n\nPress Enter to save research files (or 'q' to quit): ")
        if response.lower() != 'q':
            json_file, md_file = save_research_for_lawyer()
            print(f"\n📚 Research files created:")
            print(f"  1. {json_file} - Complete research data")
            print(f"  2. {md_file} - Human-readable summary")
        
        print("\n" + "=" * 80)
        print(" TEST COMPLETE")
        print("=" * 80)
        print("\n✅ The enhanced StatuteAgent provides:")
        print("  • Quick 2-3 sentence snippets for rapid lookup")
        print("  • Full statutory text and sections")
        print("  • Detailed definitions and provisions")
        print("  • Legislative history and judicial interpretations")
        print("  • Relevant case law citations")
        print("  • Related statutes")
        print("  • Comprehensive analysis summaries")
        print("\n🎯 Perfect for preliminary legal research by lawyer agents!")
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
