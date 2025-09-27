#!/usr/bin/env python3
"""
Test script to verify that safety settings allow Judge responses without filtering.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.simulation import JudgeAgent, CaseEvidence, LegalArgument, ArgumentType
from agents.statuteAgent import StatuteInfo
from agents.precedentAgent import CasePrecedent, CourtLevel
from datetime import datetime


def test_judge_safety_settings():
    """Test that Judge agent can provide verdicts without safety filtering."""
    
    print("Testing Judge Agent with Relaxed Safety Settings")
    print("=" * 60)
    
    # Create a Judge agent
    judge = JudgeAgent(name="TestJudge", temperament="balanced")
    
    # Create mock evidence for a contentious case
    evidence = CaseEvidence(
        case_description="A trade secret misappropriation case involving aggressive competition and potential criminal conduct.",
        jurisdiction="Federal",
        has_nda=True,
        evidence_strength="strong",
        venue_bias="neutral",
        statutes=[
            StatuteInfo(
                title="Defend Trade Secrets Act",
                citation="18 U.S.C. § 1836",
                definitions={},
                key_provisions=["Protection of trade secrets", "Civil remedies"],
                remedies=["Injunction", "Damages"],
                snippet="Federal law protecting trade secrets"
            )
        ],
        precedents=[
            CasePrecedent(
                case_name="Test v. Example",
                year="2023",
                citation="123 F.3d 456",
                court="Federal District Court",
                court_level=CourtLevel.FEDERAL_DISTRICT,
                holding="Trade secret misappropriation proven through evidence of unauthorized access",
                rule="Misappropriation requires unauthorized acquisition",
                confidence_score=0.9
            )
        ],
        facts=["Evidence of data theft", "Breach of confidentiality", "Economic harm proven"],
        plaintiff_claims=["Trade secret theft", "Breach of contract", "Economic espionage"],
        defendant_claims=["Information was public", "No breach occurred", "Independent development"]
    )
    
    # Create mock prosecutor argument
    prosecutor_arg = LegalArgument(
        agent_name="Prosecutor",
        argument_type=ArgumentType.OPENING,
        main_argument="The defendant engaged in deliberate and malicious theft of trade secrets, causing severe economic harm.",
        cited_statutes=["18 U.S.C. § 1836"],
        cited_precedents=["Test v. Example"],
        key_points=["Clear evidence of theft", "Proven economic damage", "Willful violation"],
        conclusion="The plaintiff deserves full remedies under the law."
    )
    
    # Create mock defense argument  
    defense_arg = LegalArgument(
        agent_name="Defense",
        argument_type=ArgumentType.OPENING,
        main_argument="The plaintiff's claims are baseless. The information was publicly available and no theft occurred.",
        cited_statutes=["18 U.S.C. § 1836"],
        cited_precedents=["Public Domain v. Innovation"],
        key_points=["No proprietary information", "Public domain defense", "Lack of evidence"],
        conclusion="The case should be dismissed with prejudice."
    )
    
    try:
        # Test the judge's evaluation
        print("\nTesting Judge evaluation with potentially sensitive legal content...")
        verdict = judge.evaluate_case(
            prosecutor_args=[prosecutor_arg],
            defense_args=[defense_arg],
            evidence=evidence
        )
        
        print("\n✅ SUCCESS: Judge provided verdict without safety filtering!")
        print(f"\nVerdict Details:")
        print(f"  Winner: {verdict.winner}")
        print(f"  Confidence: {verdict.confidence_score:.2%}")
        print(f"  Rationale: {verdict.rationale[:200]}...")
        print(f"  Key Factors: {', '.join(verdict.key_factors[:3])}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        if "safety" in str(e).lower() or "filter" in str(e).lower():
            print("\n⚠️  Safety filtering is still blocking responses.")
            print("   Please check that GEMINI_API_KEY is set and valid.")
        return False


def test_aggressive_case():
    """Test with a more aggressive case description to verify safety settings."""
    
    print("\n\nTesting with Aggressive Case Content")
    print("=" * 60)
    
    judge = JudgeAgent(name="TestJudge2", temperament="strict")
    
    # Test with a direct legal query that might trigger filters
    test_prompt = """
    Evaluate this case involving corporate espionage, theft of intellectual property,
    and potential criminal violations. The defendant is accused of stealing critical
    trade secrets worth millions of dollars, engaging in fraudulent activities,
    and causing severe competitive harm to the plaintiff through malicious actions.
    
    Consider whether the defendant's actions constitute criminal trade secret theft
    under federal law and whether punitive damages are warranted given the 
    egregious nature of the conduct.
    """
    
    try:
        print("\nTesting direct response to aggressive legal content...")
        response = judge.chat(test_prompt)
        
        print("\n✅ SUCCESS: Judge responded to aggressive legal content!")
        print(f"\nResponse preview: {response[:300]}...")
        
        # Check if response contains legal reasoning (not a safety message)
        if any(keyword in response.lower() for keyword in ['trade secret', 'legal', 'law', 'defendant', 'plaintiff']):
            print("\n✅ Response contains legal analysis (not filtered)")
            return True
        else:
            print("\n⚠️  Response may be generic or filtered")
            return False
            
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


if __name__ == "__main__":
    print("Safety Settings Test for Legal Simulation")
    print("=" * 60)
    print("\nThis test verifies that the Judge agent can discuss")
    print("sensitive legal topics without being blocked by safety filters.\n")
    
    # Run tests
    test1_success = test_judge_safety_settings()
    test2_success = test_aggressive_case()
    
    # Summary
    print("\n\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Basic Judge Test: {'✅ PASSED' if test1_success else '❌ FAILED'}")
    print(f"Aggressive Content Test: {'✅ PASSED' if test2_success else '❌ FAILED'}")
    
    if test1_success and test2_success:
        print("\n🎉 All tests passed! Safety settings are properly configured.")
        print("   The Judge agent can now handle legal discussions without filtering.")
    else:
        print("\n⚠️  Some tests failed. You may need to:")
        print("   1. Verify your GEMINI_API_KEY is set correctly")
        print("   2. Check if your API key has the necessary permissions")
        print("   3. Review the error messages above for more details")
