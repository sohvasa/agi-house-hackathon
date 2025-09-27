"""
Example: Retrieving and Analyzing Saved Monte Carlo Simulations
================================================================
This script demonstrates how to retrieve saved Monte Carlo simulations
from MongoDB and perform analysis on the stored data.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from bson import ObjectId

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mongodb_manager import (
    MongoDBManager,
    CaseSimulation,
    CaseResearch,
    ResearchStatus
)


def retrieve_monte_carlo_by_id(db_manager: MongoDBManager, 
                               monte_carlo_id: str) -> Optional[Dict]:
    """
    Retrieve a Monte Carlo run by its ID.
    
    Args:
        db_manager: MongoDB manager instance
        monte_carlo_id: The Monte Carlo ID (e.g., "MC_20241027_143022")
        
    Returns:
        Dictionary with Monte Carlo details or None
    """
    # Search for research document with this Monte Carlo ID
    research_docs = db_manager.search_research(
        research_topic="Monte Carlo",
        status=ResearchStatus.COMPLETED
    )
    
    for doc in research_docs:
        if doc.metadata and doc.metadata.get("monte_carlo_id") == monte_carlo_id:
            # Found the Monte Carlo document
            print(f"\n📄 Found Monte Carlo: {monte_carlo_id}")
            print(f"   Document ID: {doc._id}")
            print(f"   Case: {doc.case_name}")
            print(f"   Created: {doc.created_at}")
            
            # Get all linked simulations
            simulations = []
            for sim_id in doc.simulation_ids:
                sim = db_manager.get_simulation(sim_id)
                if sim:
                    simulations.append(sim)
            
            return {
                "research_doc": doc,
                "simulations": simulations,
                "analysis": doc.metadata.get("analysis", {})
            }
    
    print(f"❌ Monte Carlo ID not found: {monte_carlo_id}")
    return None


def retrieve_recent_monte_carlos(db_manager: MongoDBManager, 
                                days: int = 7) -> List[CaseResearch]:
    """
    Retrieve all Monte Carlo runs from the last N days.
    
    Args:
        db_manager: MongoDB manager instance
        days: Number of days to look back
        
    Returns:
        List of CaseResearch documents
    """
    # Get all research documents
    all_research = db_manager.search_research(
        research_topic="Monte Carlo",
        limit=100
    )
    
    # Filter by date and Monte Carlo type
    cutoff_date = datetime.now() - timedelta(days=days)
    recent_monte_carlos = []
    
    for doc in all_research:
        if (doc.created_at >= cutoff_date and 
            doc.metadata and 
            "monte_carlo_id" in doc.metadata):
            recent_monte_carlos.append(doc)
    
    return recent_monte_carlos


def analyze_stored_simulations(simulations: List[CaseSimulation]) -> Dict:
    """
    Analyze a list of stored simulations.
    
    Args:
        simulations: List of CaseSimulation objects
        
    Returns:
        Analysis dictionary
    """
    if not simulations:
        return {"error": "No simulations to analyze"}
    
    # Extract results
    results = {
        "total": len(simulations),
        "plaintiff_wins": 0,
        "defendant_wins": 0,
        "strategies": {
            "prosecutor": {},
            "defense": {},
            "judge": {}
        },
        "confidence_scores": [],
        "execution_times": []
    }
    
    for sim in simulations:
        # Count wins
        if sim.outcome == "plaintiff":
            results["plaintiff_wins"] += 1
        elif sim.outcome == "defendant":
            results["defendant_wins"] += 1
        
        # Extract metadata
        if sim.metadata:
            # Get strategies
            vars = sim.metadata.get("variables", {})
            if "prosecutor_strategy" in vars:
                strat = vars["prosecutor_strategy"]
                results["strategies"]["prosecutor"][strat] = \
                    results["strategies"]["prosecutor"].get(strat, 0) + 1
            
            if "defense_strategy" in vars:
                strat = vars["defense_strategy"]
                results["strategies"]["defense"][strat] = \
                    results["strategies"]["defense"].get(strat, 0) + 1
            
            if "judge_temperament" in vars:
                temp = vars["judge_temperament"]
                results["strategies"]["judge"][temp] = \
                    results["strategies"]["judge"].get(temp, 0) + 1
            
            # Get execution time
            if "execution_time" in sim.metadata:
                results["execution_times"].append(sim.metadata["execution_time"])
        
        # Extract confidence from verdict message
        for msg in sim.chat_history:
            if msg.agent_name == "JudgeAgent" and msg.metadata:
                if "confidence" in msg.metadata:
                    results["confidence_scores"].append(msg.metadata["confidence"])
    
    # Calculate statistics
    if results["confidence_scores"]:
        results["avg_confidence"] = sum(results["confidence_scores"]) / len(results["confidence_scores"])
    
    if results["execution_times"]:
        results["avg_execution_time"] = sum(results["execution_times"]) / len(results["execution_times"])
    
    results["plaintiff_win_rate"] = results["plaintiff_wins"] / results["total"] if results["total"] > 0 else 0
    
    return results


def display_monte_carlo_summary(mc_data: Dict):
    """
    Display a nice summary of a Monte Carlo run.
    
    Args:
        mc_data: Dictionary with Monte Carlo data
    """
    research = mc_data["research_doc"]
    simulations = mc_data["simulations"]
    stored_analysis = mc_data["analysis"]
    
    print("\n" + "="*70)
    print("MONTE CARLO SIMULATION SUMMARY")
    print("="*70)
    
    print(f"\n📊 Basic Information:")
    print(f"  • Monte Carlo ID: {research.metadata.get('monte_carlo_id', 'N/A')}")
    print(f"  • Case: {research.case_name}")
    print(f"  • Total Simulations: {len(simulations)}")
    print(f"  • Created: {research.created_at}")
    print(f"  • Status: {research.status.value}")
    
    # Key findings
    if research.key_findings:
        print(f"\n🔑 Key Findings:")
        for finding in research.key_findings[:5]:
            print(f"  • {finding}")
    
    # Perform fresh analysis on stored simulations
    fresh_analysis = analyze_stored_simulations(simulations)
    
    print(f"\n📈 Results Analysis:")
    print(f"  • Plaintiff Wins: {fresh_analysis['plaintiff_wins']} ({fresh_analysis['plaintiff_win_rate']:.1%})")
    print(f"  • Defendant Wins: {fresh_analysis['defendant_wins']}")
    if "avg_confidence" in fresh_analysis:
        print(f"  • Average Confidence: {fresh_analysis['avg_confidence']:.1%}")
    if "avg_execution_time" in fresh_analysis:
        print(f"  • Average Execution Time: {fresh_analysis['avg_execution_time']:.2f}s")
    
    # Strategy breakdown
    print(f"\n🎯 Strategy Usage:")
    for role, strategies in fresh_analysis["strategies"].items():
        if strategies:
            print(f"  {role.capitalize()}:")
            for strat, count in strategies.items():
                print(f"    • {strat}: {count} times")
    
    # Show a few simulation details
    print(f"\n📋 Sample Simulation Details (first 3):")
    for i, sim in enumerate(simulations[:3], 1):
        vars = sim.metadata.get("variables", {}) if sim.metadata else {}
        print(f"  Simulation {i}:")
        print(f"    • Winner: {sim.outcome}")
        print(f"    • Strategies: P={vars.get('prosecutor_strategy', 'N/A')}, "
              f"D={vars.get('defense_strategy', 'N/A')}")
        print(f"    • Evidence: {vars.get('evidence_strength', 'N/A')}, "
              f"NDA={vars.get('has_nda', 'N/A')}")


def query_simulations_by_criteria(db_manager: MongoDBManager):
    """
    Example queries to find specific simulations.
    """
    print("\n" + "="*70)
    print("EXAMPLE QUERIES")
    print("="*70)
    
    # Query 1: Find all Monte Carlo simulations
    print("\n1. All Monte Carlo trial simulations:")
    mc_sims = db_manager.search_simulations(
        simulation_type="monte_carlo_trial",
        limit=10
    )
    print(f"   Found {len(mc_sims)} Monte Carlo simulations")
    
    # Query 2: Find completed simulations with plaintiff wins
    print("\n2. Recent plaintiff victories:")
    recent_wins = []
    recent_sims = db_manager.search_simulations(
        status=SimulationStatus.COMPLETED,
        date_from=datetime.now() - timedelta(days=7),
        limit=50
    )
    for sim in recent_sims:
        if sim.outcome == "plaintiff":
            recent_wins.append(sim)
    print(f"   Found {len(recent_wins)} plaintiff wins in last 7 days")
    
    # Query 3: Find simulations with specific agents
    print("\n3. Simulations with JudgeAgent:")
    judge_sims = db_manager.search_simulations(
        agent_name="JudgeAgent",
        limit=10
    )
    print(f"   Found {len(judge_sims)} simulations with JudgeAgent")
    
    return mc_sims


def main():
    """Main function to demonstrate retrieval capabilities."""
    print("\n" + "="*70)
    print("MONTE CARLO RETRIEVAL AND ANALYSIS")
    print("="*70)
    
    # Check for MongoDB connection
    if not os.getenv("MONGODB_CONNECTION_STRING"):
        print("\n⚠ MONGODB_CONNECTION_STRING not set in environment")
        print("Please configure MongoDB connection first.")
        return
    
    # Connect to MongoDB
    try:
        db_manager = MongoDBManager()
        print("\n✓ Connected to MongoDB")
        
        # Get database statistics
        stats = db_manager.get_statistics()
        print(f"\n📊 Database Statistics:")
        print(f"  • Total Simulations: {stats['total_simulations']}")
        print(f"  • Total Research Entries: {stats['total_research_entries']}")
        
        if stats['total_simulations'] == 0:
            print("\n⚠ No simulations found in database.")
            print("Run a Monte Carlo simulation first:")
            print("  python simulation/montecarlo_mongodb.py")
            db_manager.close()
            return
        
        # Example 1: Get recent Monte Carlo runs
        print("\n" + "-"*40)
        print("Recent Monte Carlo Runs (last 7 days):")
        print("-"*40)
        
        recent_mcs = retrieve_recent_monte_carlos(db_manager, days=7)
        if recent_mcs:
            print(f"Found {len(recent_mcs)} recent Monte Carlo runs:")
            for mc in recent_mcs[:5]:
                mc_id = mc.metadata.get("monte_carlo_id", "Unknown")
                sim_count = len(mc.simulation_ids)
                print(f"  • {mc_id}: {sim_count} simulations - {mc.case_name[:50]}...")
            
            # Analyze the most recent one
            if recent_mcs:
                latest = recent_mcs[0]
                latest_id = latest.metadata.get("monte_carlo_id")
                if latest_id:
                    print(f"\nAnalyzing most recent: {latest_id}")
                    mc_data = retrieve_monte_carlo_by_id(db_manager, latest_id)
                    if mc_data:
                        display_monte_carlo_summary(mc_data)
        else:
            print("No recent Monte Carlo runs found.")
        
        # Example 2: Query simulations
        print("\n" + "-"*40)
        print("Query Examples:")
        print("-"*40)
        query_simulations_by_criteria(db_manager)
        
        # Close connection
        db_manager.close()
        print("\n✓ MongoDB connection closed")
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*70)
    print("RETRIEVAL COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()
    
    print("\n💡 Tips:")
    print("• Use monte_carlo_id to retrieve specific runs")
    print("• Query by date range, status, or agents")
    print("• Analyze stored simulations for patterns")
    print("• Export results for external analysis")
