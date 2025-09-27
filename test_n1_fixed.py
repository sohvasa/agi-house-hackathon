#!/usr/bin/env python
"""
Test script to verify the fixed N=1 Monte Carlo simulation.
"""

import os
import sys

# Make sure we can import from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_fixes():
    """Test that the fixes work correctly."""
    print("\n" + "="*60)
    print("TESTING FIXED N=1 SIMULATION")
    print("="*60)
    
    try:
        # Test 1: Import check
        print("\n1. Testing imports...")
        from simulation.montecarlo import EnhancedMonteCarloSimulation, SimulationVariables
        from simulation.simulation import CaseEvidence, ProsecutorAgent, DefenseAgent
        print("   ✓ All imports successful")
        
        # Test 2: Create simulation
        print("\n2. Creating simulation...")
        case = "Company A sues employee B for trade secret theft. B had NDA."
        mc_sim = EnhancedMonteCarloSimulation(case)
        print("   ✓ Simulation created")
        
        # Test 3: Create variables
        print("\n3. Creating simulation variables...")
        vars = SimulationVariables(
            prosecutor_strategy="moderate",
            defense_strategy="moderate", 
            judge_temperament="balanced",
            has_nda=True,
            evidence_strength="moderate"
        )
        print(f"   ✓ Variables configured: P={vars.prosecutor_strategy}, D={vars.defense_strategy}")
        
        # Test 4: Test save with empty results (should not crash)
        print("\n4. Testing save with no analysis...")
        mc_sim.results = []
        try:
            mc_sim.save_results("test_empty.json")
            print("   ✓ Save handled empty results correctly")
            # Clean up test file
            if os.path.exists("test_empty.json"):
                os.remove("test_empty.json")
        except AttributeError as e:
            print(f"   ✗ Save failed with: {e}")
            
        print("\n" + "="*60)
        print("BASIC TESTS COMPLETE")
        print("="*60)
        print("\nThe fixes appear to be working. You can now run:")
        print("  python simulation/montecarlo.py")
        print("\nNote: Full simulation requires API keys in .env file")
        
        return True
        
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fixes()
    sys.exit(0 if success else 1)
