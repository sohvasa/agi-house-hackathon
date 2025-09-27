"""
Simple test script for Monte Carlo simulation
Tests the N=1 case without full API dependencies
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_monte_carlo_structure():
    """Test that Monte Carlo simulation structure is valid."""
    print("\n" + "="*60)
    print("TESTING MONTE CARLO SIMULATION STRUCTURE")
    print("="*60)
    
    try:
        # Import the modules
        from simulation.montecarlo import (
            SimulationVariables,
            SimulationResult, 
            EnhancedMonteCarloSimulation,
            MonteCarloAnalysis
        )
        print("✓ Monte Carlo modules imported successfully")
        
        # Test SimulationVariables
        vars = SimulationVariables()
        print(f"✓ SimulationVariables created: {vars.prosecutor_strategy}, {vars.defense_strategy}")
        
        # Test randomization
        vars.randomize()
        print(f"✓ Variables randomized: P={vars.prosecutor_strategy}, D={vars.defense_strategy}")
        
        # Test Monte Carlo simulation creation
        case = "Test case: Company A sues employee B for trade secrets."
        mc_sim = EnhancedMonteCarloSimulation(case)
        print(f"✓ Monte Carlo simulation created for case")
        
        print("\n✅ All structural tests passed!")
        print("\nNote: Full simulation requires API keys for:")
        print("  • GEMINI_API_KEY - for agent reasoning")
        print("  • PERPLEXITY_API_KEY - for legal research (optional)")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("\nMake sure to install numpy: pip install numpy")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_simulation_imports():
    """Test that all simulation components can be imported."""
    print("\n" + "="*60)
    print("TESTING SIMULATION IMPORTS")
    print("="*60)
    
    try:
        from simulation.simulation import (
            ProsecutorAgent,
            DefenseAgent,
            JudgeAgent,
            ResearchAgent,
            LegalSimulation,
            CaseEvidence,
            LegalArgument,
            Verdict
        )
        print("✓ Main simulation components imported")
        
        from simulation.montecarlo import (
            EnhancedMonteCarloSimulation,
            SimulationVariables,
            SimulationResult,
            MonteCarloAnalysis
        )
        print("✓ Monte Carlo components imported")
        
        # Check for required dependencies
        try:
            import numpy as np
            print(f"✓ NumPy installed: version {np.__version__}")
        except ImportError:
            print("✗ NumPy not installed - run: pip install numpy")
            return False
        
        try:
            import google.generativeai as genai
            print("✓ Google Generative AI installed")
        except ImportError:
            print("⚠ Google Generative AI not installed - needed for full simulation")
        
        return True
        
    except Exception as e:
        print(f"✗ Import failed: {e}")
        return False


def main():
    print("\n" + "="*70)
    print("MONTE CARLO SIMULATION - SIMPLE TEST")
    print("="*70)
    
    # Run tests
    import_success = test_simulation_imports()
    structure_success = test_monte_carlo_structure()
    
    if import_success and structure_success:
        print("\n" + "="*70)
        print("✅ ALL TESTS PASSED")
        print("="*70)
        print("\nThe Monte Carlo simulation system is properly structured.")
        print("To run a full simulation with N=1:")
        print("\n  python -c \"from simulation.montecarlo import test_n1_simulation; test_n1_simulation()\"")
        print("\nOr run the complete test:")
        print("\n  python simulation/montecarlo.py")
    else:
        print("\n" + "="*70)
        print("⚠ SOME TESTS FAILED")
        print("="*70)
        print("\nPlease address the issues above before running full simulations.")


if __name__ == "__main__":
    main()
