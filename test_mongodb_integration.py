#!/usr/bin/env python
"""
Test MongoDB Integration for Monte Carlo Simulations
This script tests the MongoDB storage without running full simulations.
"""

import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_mongodb_connection():
    """Test basic MongoDB connection."""
    print("\n" + "="*60)
    print("1. TESTING MONGODB CONNECTION")
    print("="*60)
    
    try:
        from database.mongodb_manager import MongoDBManager
        
        # Check for connection string
        conn_string = os.getenv("MONGODB_CONNECTION_STRING")
        if not conn_string:
            print("⚠ MONGODB_CONNECTION_STRING not set in environment")
            print("\nTo set up MongoDB:")
            print("1. Create a free MongoDB Atlas account at: https://www.mongodb.com/cloud/atlas")
            print("2. Create a cluster and get your connection string")
            print("3. Add to .env file:")
            print('   MONGODB_CONNECTION_STRING="mongodb+srv://username:password@cluster.mongodb.net/"')
            return False
        
        # Try to connect
        print("Attempting to connect to MongoDB...")
        db_manager = MongoDBManager()
        print("✓ Successfully connected to MongoDB")
        
        # Get statistics
        stats = db_manager.get_statistics()
        print(f"\nDatabase Statistics:")
        print(f"  • Total Simulations: {stats['total_simulations']}")
        print(f"  • Total Research Entries: {stats['total_research_entries']}")
        
        db_manager.close()
        return True
        
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        return False


def test_simulation_structure():
    """Test the MongoDB-enhanced simulation structure."""
    print("\n" + "="*60)
    print("2. TESTING SIMULATION STRUCTURE")
    print("="*60)
    
    try:
        from simulation.montecarlo_mongodb import (
            MongoEnhancedMonteCarloSimulation,
            MonteCarloDocument
        )
        from simulation.montecarlo import SimulationVariables
        
        print("✓ Successfully imported MongoDB-enhanced classes")
        
        # Test creating a simulation (without running it)
        case = "Test case: Company A vs Employee B"
        mc_sim = MongoEnhancedMonteCarloSimulation(
            case_description=case,
            auto_save=False  # Don't auto-save for this test
        )
        print(f"✓ Created Monte Carlo simulation")
        print(f"  • Monte Carlo ID: {mc_sim.monte_carlo_id}")
        print(f"  • Case: {case[:50]}...")
        
        # Test variables
        vars = SimulationVariables()
        print(f"✓ Created simulation variables")
        print(f"  • Prosecutor: {vars.prosecutor_strategy}")
        print(f"  • Defense: {vars.defense_strategy}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("\nMake sure all dependencies are installed:")
        print("  pip install pymongo numpy")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_mock_save():
    """Test saving mock simulation data to MongoDB."""
    print("\n" + "="*60)
    print("3. TESTING MOCK SAVE TO MONGODB")
    print("="*60)
    
    try:
        from database.mongodb_manager import (
            MongoDBManager,
            CaseSimulation,
            CaseResearch,
            AgentMessage,
            SimulationStatus,
            ResearchStatus
        )
        
        # Check connection
        if not os.getenv("MONGODB_CONNECTION_STRING"):
            print("⚠ Skipping - MongoDB connection string not set")
            return False
        
        # Connect to MongoDB
        db_manager = MongoDBManager()
        print("✓ Connected to MongoDB")
        
        # Create a mock simulation
        mock_messages = [
            AgentMessage(
                agent_name="ProsecutorAgent",
                role="assistant",
                content="The evidence clearly shows misappropriation under DTSA.",
                timestamp=datetime.now()
            ),
            AgentMessage(
                agent_name="DefenseAgent",
                role="assistant",
                content="There is no proof of improper acquisition.",
                timestamp=datetime.now()
            ),
            AgentMessage(
                agent_name="JudgeAgent",
                role="assistant",
                content="Based on the arguments, I find for the plaintiff.",
                timestamp=datetime.now(),
                metadata={"verdict": "plaintiff", "confidence": 0.75}
            )
        ]
        
        mock_sim = CaseSimulation(
            case_id="TEST_CASE_001",
            case_name="Test Mock Simulation",
            simulation_type="monte_carlo_trial",
            agents_involved=["ProsecutorAgent", "DefenseAgent", "JudgeAgent"],
            chat_history=mock_messages,
            status=SimulationStatus.COMPLETED,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            completed_at=datetime.now(),
            outcome="plaintiff",
            summary="Mock simulation for testing"
        )
        
        # Save to MongoDB
        sim_id = db_manager.save_simulation(mock_sim)
        print(f"✓ Saved mock simulation to MongoDB")
        print(f"  • Simulation ID: {sim_id}")
        
        # Create and save a research document that links to it
        mock_research = CaseResearch(
            case_id="TEST_CASE_001",
            case_name="Test Mock Monte Carlo",
            research_topic="Monte Carlo Test",
            description="Testing MongoDB integration",
            key_findings=["MongoDB integration works", "Simulations can be linked"],
            legal_precedents=[],
            statutes=[],
            simulation_ids=[sim_id],
            status=ResearchStatus.COMPLETED,
            tags=["test", "mock", "monte_carlo"]
        )
        
        research_id = db_manager.save_research(mock_research)
        print(f"✓ Saved mock research document")
        print(f"  • Research ID: {research_id}")
        print(f"  • Linked simulations: 1")
        
        # Retrieve and verify
        retrieved_sim = db_manager.get_simulation(sim_id)
        retrieved_research = db_manager.get_research(research_id)
        
        if retrieved_sim and retrieved_research:
            print(f"✓ Successfully retrieved saved documents")
            print(f"  • Simulation messages: {len(retrieved_sim.chat_history)}")
            print(f"  • Research findings: {len(retrieved_research.key_findings)}")
            
            # Clean up test data (optional)
            # db_manager.delete_simulation(sim_id)
            # db_manager.delete_research(research_id)
            # print("✓ Cleaned up test data")
        
        db_manager.close()
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("MONGODB INTEGRATION TEST SUITE")
    print("="*70)
    
    # Run tests
    tests_passed = 0
    tests_total = 3
    
    if test_mongodb_connection():
        tests_passed += 1
    
    if test_simulation_structure():
        tests_passed += 1
    
    if test_mock_save():
        tests_passed += 1
    
    # Summary
    print("\n" + "="*70)
    print(f"TEST RESULTS: {tests_passed}/{tests_total} passed")
    print("="*70)
    
    if tests_passed == tests_total:
        print("\n✅ All tests passed! MongoDB integration is ready.")
        print("\nTo run a full Monte Carlo simulation with MongoDB:")
        print("  python simulation/montecarlo_mongodb.py")
    else:
        print("\n⚠ Some tests failed. Check the errors above.")
        
        if not os.getenv("MONGODB_CONNECTION_STRING"):
            print("\n📝 MongoDB Setup Instructions:")
            print("1. Go to https://www.mongodb.com/cloud/atlas")
            print("2. Create a free account and cluster")
            print("3. Get your connection string")
            print("4. Add to .env file:")
            print('   MONGODB_CONNECTION_STRING="your_connection_string_here"')
    
    print("\n💡 Features available with MongoDB integration:")
    print("  • Save each simulation as a separate document")
    print("  • Link all simulations in a Monte Carlo run")
    print("  • Query simulations by various criteria")
    print("  • Store full chat histories and analysis")
    print("  • Track research and link to simulations")


if __name__ == "__main__":
    main()
