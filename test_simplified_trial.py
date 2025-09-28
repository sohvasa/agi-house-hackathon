#!/usr/bin/env python3
"""
Test script to verify simplified trial structure
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.simulation import LegalSimulation

def test_simplified_trial():
    """Test the simplified 3-phase trial structure"""
    
    print("\n" + "="*60)
    print("TESTING SIMPLIFIED TRIAL STRUCTURE")
    print("="*60)
    print("\nTrial structure: Opening → Rebuttals → Verdict (3 phases)")
    print("NO closing arguments or additional rounds")
    
    # Simple test case
    case_description = """
    TechCorp alleges that former employee John Smith took proprietary 
    source code when he left to join competitor StartupInc. John had 
    signed an NDA and had access to critical algorithms. Evidence shows 
    suspicious file transfers before his departure.
    """
    
    print("\n📋 Test Case:")
    print(case_description)
    
    # Create simulation
    sim = LegalSimulation(
        prosecutor_strategy="moderate",
        defense_strategy="moderate", 
        judge_temperament="balanced"
    )
    
    # Prepare case
    print("\n⚙️ Preparing case evidence...")
    evidence = sim.prepare_case(case_description)
    
    # Run trial - now with fixed 3-phase structure
    print("\n🏛️ Running trial with 3 phases...")
    verdict = sim.run_trial()  # No include_rebuttals parameter needed
    
    # Verify we have exactly 2 arguments from each side (opening + rebuttal)
    print(f"\n✅ Verification:")
    print(f"  • Prosecutor arguments: {len(sim.arguments['prosecutor'])} (should be 2)")
    print(f"  • Defense arguments: {len(sim.arguments['defense'])} (should be 2)")
    
    assert len(sim.arguments['prosecutor']) == 2, "Prosecutor should have exactly 2 arguments"
    assert len(sim.arguments['defense']) == 2, "Defense should have exactly 2 arguments"
    
    print(f"\n🎯 Trial completed successfully!")
    print(f"  • Winner: {verdict.winner}")
    print(f"  • Confidence: {verdict.confidence_score:.1%}")
    
    return True

if __name__ == "__main__":
    try:
        success = test_simplified_trial()
        if success:
            print("\n✅ ALL TESTS PASSED - Trial structure is simplified to 3 phases")
            print("   Phase 1: Opening Arguments")
            print("   Phase 2: Rebuttals") 
            print("   Phase 3: Judge's Verdict")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
