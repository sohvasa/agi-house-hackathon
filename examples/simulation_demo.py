"""
Demonstration of Legal Case Simulation System
=============================================
This script shows how to use the multi-agent legal simulation system
for both single trials and Monte Carlo simulations.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.simulation import (
    LegalSimulation, 
    MonteCarloSimulation,
    CaseEvidence,
    VerdictOutcome
)
import json


def demo_single_trial():
    """
    Demonstrate a single trial with specific agent strategies.
    """
    print("\n" + "="*70)
    print("DEMO: Single Trial Simulation")
    print("="*70)
    
    # Define a trade secret misappropriation case
    case_description = """
    CloudTech Solutions, a cloud infrastructure company, is suing former senior engineer 
    Alex Chen for trade secret misappropriation. Alex signed a comprehensive NDA and 
    non-compete agreement when he joined CloudTech. He had access to proprietary 
    distributed database architecture designs and optimization algorithms.
    
    Two months after Alex left to join rival company DataStream Inc., DataStream 
    announced a new database product with remarkably similar architecture. 
    
    Evidence includes:
    - Email records showing Alex sent personal emails with attachments days before leaving
    - Git logs showing unusual access patterns to proprietary repos in his final week  
    - LinkedIn posts from DataStream engineers thanking Alex for "revolutionary insights"
    - Technical analysis showing 70% architectural similarity between products
    
    However, Alex claims he developed similar ideas independently at DataStream,
    and that the architectures are based on publicly available research papers.
    
    The case is filed in the Northern District of California, which has strong 
    protections for employee mobility but also respects trade secret rights.
    """
    
    print("\nCase Summary:")
    print("-" * 40)
    print(case_description[:300] + "...")
    
    # Configure simulation with specific strategies
    print("\nSimulation Configuration:")
    print("  • Prosecutor Strategy: aggressive")
    print("  • Defense Strategy: moderate") 
    print("  • Judge Temperament: balanced")
    
    # Create and run simulation
    sim = LegalSimulation(
        prosecutor_strategy="aggressive",
        defense_strategy="moderate", 
        judge_temperament="balanced"
    )
    
    # Prepare case (gather evidence)
    print("\n" + "-"*40)
    print("Phase 1: Evidence Gathering")
    print("-"*40)
    evidence = sim.prepare_case(case_description, jurisdiction="Federal")
    
    # Run trial proceedings
    print("\n" + "-"*40)
    print("Phase 2: Trial Proceedings")
    print("-"*40)
    verdict = sim.run_trial(include_rebuttals=True)
    
    # Display results
    print("\n" + "="*70)
    print("TRIAL RESULTS SUMMARY")
    print("="*70)
    
    summary = sim.get_trial_summary()
    print(f"\n📊 Final Verdict: {verdict.winner.upper()} wins")
    print(f"📈 Judge's Confidence: {verdict.confidence_score:.1%}")
    print(f"\n📝 Key Factors in Decision:")
    for factor in verdict.key_factors[:3]:
        print(f"   • {factor}")
    
    print(f"\n⚖️ Legal Authorities Cited:")
    for authority in verdict.cited_authorities[:3]:
        print(f"   • {authority}")
    
    # Save detailed results
    output_file = "demo_trial_results.json"
    sim.save_results(output_file)
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    return verdict


def demo_monte_carlo():
    """
    Demonstrate Monte Carlo simulation with multiple strategy combinations.
    """
    print("\n" + "="*70)
    print("DEMO: Monte Carlo Simulation") 
    print("="*70)
    
    # Define a more ambiguous case for interesting variations
    case_description = """
    StartupAI claims that former CTO Maria Rodriguez took their proprietary 
    natural language processing algorithms to her new company, NeuralNext.
    
    Key facts:
    - Maria was a co-founder but left after disagreements with the board
    - No formal NDA was signed (startup was informal in early days)
    - Maria claims she invented the algorithms before joining StartupAI
    - Some code similarities exist but could be coincidental
    - Evidence of downloads exists but Maria had legitimate access as CTO
    - The technology involves some open-source components
    
    The case is in Texas federal court, which tends to favor business interests
    but also values inventor rights. The evidence is mixed and interpretable
    in multiple ways.
    """
    
    print("\nCase Summary:")
    print("-" * 40)
    print("An ambiguous trade secret case with mixed evidence...")
    print("No NDA, disputed inventorship, moderate evidence strength")
    
    print("\nMonte Carlo Configuration:")
    print("  • Simulations: 10 trials")
    print("  • Varying prosecutor and defense strategies")
    print("  • Varying judge temperaments")
    print("  • Analyzing win rates and optimal strategies")
    
    # Create Monte Carlo simulator
    mc_sim = MonteCarloSimulation()
    
    # Run simulations
    results = mc_sim.run_simulations(
        case_description=case_description,
        num_simulations=10,  # Run 10 different strategy combinations
        vary_strategies=True,  # Randomize strategies
        fixed_judge=None  # Also vary judge temperament
    )
    
    # Display analysis
    print("\n" + "="*70)
    print("MONTE CARLO RESULTS ANALYSIS")
    print("="*70)
    
    analysis = results['analysis']
    print(f"\n📊 Overall Statistics:")
    print(f"   • Total Simulations: {len(results['results'])}")
    print(f"   • Plaintiff Win Rate: {analysis['plaintiff_win_rate']:.1%}")
    print(f"   • Defense Win Rate: {analysis['defense_win_rate']:.1%}")
    print(f"   • Average Judge Confidence: {analysis['avg_confidence']:.1%}")
    
    print(f"\n🎯 Optimal Strategies:")
    print(f"   • Best Prosecutor Strategy: {analysis['best_prosecutor_strategy']}")
    print(f"   • Best Defense Strategy: {analysis['best_defense_strategy']}")
    
    print(f"\n📈 Strategy Performance:")
    for side in ['prosecutor', 'defense']:
        print(f"\n   {side.capitalize()} Strategies:")
        for strategy, stats in analysis['strategy_stats'][side].items():
            win_rate = stats['wins'] / stats['total'] if stats['total'] > 0 else 0
            print(f"     • {strategy}: {win_rate:.1%} win rate ({stats['wins']}/{stats['total']})")
    
    # Save results
    output_file = "demo_monte_carlo_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Detailed results saved to: {output_file}")
    
    return results


def demo_custom_case():
    """
    Demonstrate how to run a simulation with a custom case description.
    """
    print("\n" + "="*70)
    print("DEMO: Custom Case Input")
    print("="*70)
    
    print("\nYou can create your own case description. Here's an example template:\n")
    
    template = """
    [Company A] is suing [Former Employee] for trade secret misappropriation.
    
    Key Facts:
    - Employment details (role, access level, agreements signed)
    - What information was allegedly taken
    - Evidence of misappropriation
    - Defendant's response/defense
    - Relevant circumstances (timing, competition, damages)
    
    Jurisdiction: [Federal/State] court in [Location]
    """
    
    print(template)
    
    # Example custom case
    custom_case = """
    PharmaCorp is suing former researcher Dr. James Liu for allegedly stealing 
    drug formulation data for a new cancer treatment. Dr. Liu signed an NDA and 
    IP assignment agreement. Three months after joining competitor MedRival, 
    MedRival announced a similar drug entering trials. 
    
    Evidence includes Dr. Liu's unusual database access in his last week and 
    USB device logs. However, Dr. Liu claims the formulations are based on his 
    prior published research from his university days.
    
    The case is in Massachusetts federal court.
    """
    
    print("\nRunning simulation with custom case...")
    print("-" * 40)
    
    # Quick simulation
    sim = LegalSimulation(
        prosecutor_strategy="moderate",
        defense_strategy="aggressive",
        judge_temperament="strict"
    )
    
    evidence = sim.prepare_case(custom_case)
    verdict = sim.run_trial(include_rebuttals=False)  # Skip rebuttals for speed
    
    print(f"\n✅ Verdict: {verdict.winner.upper()} wins")
    print(f"   Confidence: {verdict.confidence_score:.1%}")
    
    return verdict


def main():
    """
    Main demonstration script.
    """
    print("\n" + "="*70)
    print(" LEGAL CASE SIMULATION SYSTEM - DEMONSTRATION")
    print("="*70)
    print("\nThis demo will show three different simulation modes:")
    print("1. Single trial with specific strategies")
    print("2. Monte Carlo simulation with strategy exploration")  
    print("3. Custom case input example")
    
    # Get user choice
    print("\nWhich demo would you like to run?")
    print("1. Single Trial")
    print("2. Monte Carlo Simulation")
    print("3. Custom Case")
    print("4. All Demos")
    
    choice = input("\nEnter choice (1-4) or press Enter for all: ").strip()
    
    if choice == "1":
        demo_single_trial()
    elif choice == "2":
        demo_monte_carlo()
    elif choice == "3":
        demo_custom_case()
    else:
        print("\nRunning all demonstrations...")
        demo_single_trial()
        input("\nPress Enter to continue to Monte Carlo demo...")
        demo_monte_carlo()
        input("\nPress Enter to continue to custom case demo...")
        demo_custom_case()
    
    print("\n" + "="*70)
    print("DEMONSTRATION COMPLETE")
    print("="*70)
    print("\nYou can now use this system with your own cases and strategies!")
    print("Check the generated JSON files for detailed results.")


if __name__ == "__main__":
    main()
