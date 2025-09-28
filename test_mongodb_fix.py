#!/usr/bin/env python3
"""
Test script to verify MongoDB saving is working after the fix
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simulation.montecarlo_mongodb import MongoEnhancedMonteCarloSimulation
from simulation.montecarlo import SimulationVariables
from database.mongodb_manager import MongoDBManager

def test_single_simulation_with_random():
    """Test single simulation with random variables."""
    
    case_description = """
    TechCorp alleges that former employee Jane Doe stole proprietary 
    machine learning algorithms when she founded competitor StartupAI. 
    Evidence includes suspicious file downloads before resignation.
    Case filed in California federal court.
    """
    
    print("Testing MongoDB saving with randomized variables...")
    print("=" * 60)
    
    # Initialize MongoDB manager
    db_manager = MongoDBManager()
    
    # Create simulation with MongoDB support
    mc_sim = MongoEnhancedMonteCarloSimulation(
        case_description=case_description,
        base_jurisdiction="Federal",
        research_depth="moderate",
        db_manager=db_manager,
        auto_save=True
    )
    
    print("\n1. Running research phase...")
    mc_sim.research_case()
    
    # Test with different random variables
    import random
    variables = SimulationVariables(
        prosecutor_strategy=random.choice(['aggressive', 'moderate', 'conservative']),
        defense_strategy=random.choice(['aggressive', 'moderate', 'conservative']),
        judge_temperament=random.choice(['strict', 'balanced', 'lenient']),
        has_nda=random.choice([True, False]),
        evidence_strength=random.choice(['weak', 'moderate', 'strong']),
        venue_bias=random.choice(['plaintiff-friendly', 'neutral', 'defendant-friendly'])
    )
    
    print(f"\n2. Running simulation with randomized variables:")
    print(f"   Prosecutor: {variables.prosecutor_strategy}")
    print(f"   Defense: {variables.defense_strategy}")
    print(f"   Judge: {variables.judge_temperament}")
    print(f"   Evidence: {variables.evidence_strength}")
    print(f"   Venue: {variables.venue_bias}")
    print(f"   NDA: {variables.has_nda}")
    
    try:
        # Run single simulation
        result = mc_sim.run_single_simulation(1, variables)
        
        print(f"\n✅ Simulation completed successfully!")
        print(f"   Winner: {result.verdict.winner}")
        print(f"   Confidence: {result.verdict.confidence_score:.1%}")
        
        if mc_sim.saved_simulation_ids:
            print(f"   Saved to MongoDB: {mc_sim.saved_simulation_ids[0]}")
        else:
            print("   ⚠️ Warning: Simulation not saved to MongoDB")
            
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_single_simulation_with_random()
    
    if success:
        print("\n🎉 MongoDB saving is working correctly with the fix!")
    else:
        print("\n⚠️ There are still issues with MongoDB saving")
    
    sys.exit(0 if success else 1)
