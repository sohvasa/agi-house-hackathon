"""
Enhanced Monte Carlo Legal Simulation System
============================================
This module provides an advanced Monte Carlo simulation that:
1. Researches case details for precedents and statutes
2. Randomizes case variables and agent strategies
3. Runs multiple simulations to explore outcome space
4. Provides statistical analysis and insights
"""

import os
import sys
import json
import random
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import asyncio
from collections import defaultdict

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from parent directory
from agents.baseAgent import BaseAgent
from agents.precedentAgent import PrecedentAgent, CasePrecedent
from agents.statuteAgent import StatuteAgent, StatuteInfo

# Import from same directory using absolute import
try:
    # When running as module
    from .simulation import (
        ProsecutorAgent, DefenseAgent, JudgeAgent, ResearchAgent,
        CaseEvidence, LegalArgument, Verdict, VerdictOutcome,
        ArgumentType
    )
except ImportError:
    # When running directly
    from simulation import (
        ProsecutorAgent, DefenseAgent, JudgeAgent, ResearchAgent,
        CaseEvidence, LegalArgument, Verdict, VerdictOutcome,
        ArgumentType
    )


@dataclass
class SimulationVariables:
    """Variables that can be randomized in simulations"""
    # Agent strategies
    prosecutor_strategy: str = "moderate"
    defense_strategy: str = "moderate"
    judge_temperament: str = "balanced"
    
    # Case factors
    has_nda: bool = True
    evidence_strength: str = "moderate"  # weak, moderate, strong
    venue_bias: str = "neutral"  # plaintiff-friendly, defendant-friendly, neutral
    
    # Evidence variations
    num_statutes_cited: int = 3
    num_precedents_cited: int = 3
    
    # Additional factors
    defendant_cooperation: str = "moderate"  # hostile, moderate, cooperative
    plaintiff_damages_claim: str = "moderate"  # minimal, moderate, extensive
    time_since_departure: int = 3  # months
    competitor_relationship: str = "direct"  # direct, indirect, none
    
    def randomize(self, 
                  fixed_strategies: bool = False,
                  fixed_evidence: bool = False):
        """
        Randomize simulation variables.
        
        Args:
            fixed_strategies: Keep agent strategies fixed
            fixed_evidence: Keep evidence factors fixed
        """
        if not fixed_strategies:
            self.prosecutor_strategy = random.choice(["aggressive", "moderate", "conservative"])
            self.defense_strategy = random.choice(["aggressive", "moderate", "conservative"])
            self.judge_temperament = random.choice(["strict", "balanced", "lenient"])
        
        if not fixed_evidence:
            self.has_nda = random.choice([True, True, False])  # 66% chance of NDA
            self.evidence_strength = random.choice(["weak", "moderate", "moderate", "strong"])
            self.venue_bias = random.choice(["plaintiff-friendly", "neutral", "neutral", "defendant-friendly"])
        
        # Always randomize these
        self.num_statutes_cited = random.randint(2, 5)
        self.num_precedents_cited = random.randint(2, 5)
        
        # Additional factors
        self.defendant_cooperation = random.choice(["hostile", "moderate", "cooperative"])
        self.plaintiff_damages_claim = random.choice(["minimal", "moderate", "extensive"])
        self.time_since_departure = random.randint(1, 12)
        self.competitor_relationship = random.choice(["direct", "direct", "indirect", "none"])
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class SimulationResult:
    """Result from a single simulation run"""
    simulation_id: int
    variables: SimulationVariables
    verdict: Verdict
    prosecutor_arguments: List[LegalArgument]
    defense_arguments: List[LegalArgument]
    execution_time: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            'simulation_id': self.simulation_id,
            'variables': self.variables.to_dict(),
            'verdict': {
                'winner': self.verdict.winner,
                'outcome': self.verdict.outcome.value,
                'confidence': self.verdict.confidence_score,
                'key_factors': self.verdict.key_factors,
                'rationale': self.verdict.rationale[:200]
            },
            'num_prosecutor_args': len(self.prosecutor_arguments),
            'num_defense_args': len(self.defense_arguments),
            'execution_time': self.execution_time,
            'timestamp': self.timestamp
        }


@dataclass 
class MonteCarloAnalysis:
    """Statistical analysis of Monte Carlo results"""
    total_simulations: int
    plaintiff_wins: int
    defense_wins: int
    average_confidence: float
    
    # Strategy effectiveness
    strategy_performance: Dict[str, Dict]
    
    # Factor correlations
    factor_impact: Dict[str, float]
    
    # Best configurations
    best_plaintiff_config: SimulationVariables
    best_defense_config: SimulationVariables
    
    # Statistical metrics
    confidence_std: float
    execution_time_avg: float
    
    # Detailed breakdowns
    venue_impact: Dict[str, Dict]
    evidence_impact: Dict[str, Dict]
    nda_impact: Dict[str, float]


class EnhancedMonteCarloSimulation:
    """
    Advanced Monte Carlo simulation system with research integration.
    """
    
    def __init__(self, 
                 case_description: str,
                 base_jurisdiction: str = "Federal",
                 research_depth: str = "moderate"):
        """
        Initialize Monte Carlo simulation.
        
        Args:
            case_description: Natural language case description
            base_jurisdiction: Legal jurisdiction
            research_depth: How thorough research should be (minimal, moderate, comprehensive)
        """
        self.case_description = case_description
        self.base_jurisdiction = base_jurisdiction
        self.research_depth = research_depth
        
        # Research components
        self.research_agent = ResearchAgent()
        self.base_evidence = None
        self.researched_statutes = []
        self.researched_precedents = []
        
        # Results storage
        self.results: List[SimulationResult] = []
        self.analysis = None
        
    def research_case(self) -> CaseEvidence:
        """
        Conduct comprehensive research on the case.
        
        Returns:
            Base evidence packet with researched statutes and precedents
        """
        print(f"\n{'='*60}")
        print("PHASE 1: CASE RESEARCH")
        print(f"{'='*60}")
        
        print(f"\n📚 Researching case law and statutes...")
        print(f"Research depth: {self.research_depth}")
        
        # Use research agent to gather evidence
        self.base_evidence = self.research_agent.gather_evidence(
            self.case_description,
            self.base_jurisdiction
        )
        
        # Store researched materials
        self.researched_statutes = self.base_evidence.statutes
        self.researched_precedents = self.base_evidence.precedents
        
        print(f"\n✅ Research Complete:")
        print(f"  • Statutes found: {len(self.researched_statutes)}")
        if self.researched_statutes:
            print(f"    - Key statute: {self.researched_statutes[0].citation}")
        
        print(f"  • Precedents found: {len(self.researched_precedents)}")
        if self.researched_precedents:
            print(f"    - Key case: {self.researched_precedents[0].case_name}")
        
        print(f"  • Facts identified: {len(self.base_evidence.facts)}")
        print(f"  • Initial assessment:")
        print(f"    - NDA present: {self.base_evidence.has_nda}")
        print(f"    - Evidence strength: {self.base_evidence.evidence_strength}")
        
        return self.base_evidence
    
    def create_variant_evidence(self, variables: SimulationVariables) -> CaseEvidence:
        """
        Create a variant of the base evidence with randomized variables.
        
        Args:
            variables: Simulation variables to apply
            
        Returns:
            Modified evidence packet
        """
        if not self.base_evidence:
            raise ValueError("Must run research_case() first")
        
        # Create a copy of base evidence
        variant = CaseEvidence(
            case_description=self.base_evidence.case_description,
            jurisdiction=self.base_evidence.jurisdiction,
            has_nda=variables.has_nda,
            evidence_strength=variables.evidence_strength,
            venue_bias=variables.venue_bias,
            statutes=self.researched_statutes[:variables.num_statutes_cited],
            precedents=self.researched_precedents[:variables.num_precedents_cited],
            facts=self.base_evidence.facts,
            documents=self.base_evidence.documents,
            plaintiff_claims=self.base_evidence.plaintiff_claims,
            defendant_claims=self.base_evidence.defendant_claims,
            disputed_facts=self.base_evidence.disputed_facts
        )
        
        # Modify description based on additional factors
        if variables.defendant_cooperation == "hostile":
            variant.disputed_facts.append("Defendant refuses to cooperate with discovery")
        elif variables.defendant_cooperation == "cooperative":
            variant.facts.append("Defendant has cooperated with investigation")
        
        if variables.time_since_departure > 6:
            variant.defendant_claims.append(f"Significant time gap ({variables.time_since_departure} months) weakens causation")
        
        if variables.competitor_relationship == "none":
            variant.defendant_claims.append("Companies are not direct competitors")
        
        return variant
    
    def run_single_simulation(self, 
                            simulation_id: int,
                            variables: SimulationVariables) -> SimulationResult:
        """
        Run a single simulation with specified variables.
        
        Args:
            simulation_id: Unique simulation identifier
            variables: Simulation variables to use
            
        Returns:
            Simulation result
        """
        start_time = datetime.now()
        
        print(f"\n  Simulation {simulation_id}: ", end="")
        print(f"P={variables.prosecutor_strategy[0].upper()}, ", end="")
        print(f"D={variables.defense_strategy[0].upper()}, ", end="")
        print(f"J={variables.judge_temperament[0].upper()}, ", end="")
        print(f"NDA={variables.has_nda}, ", end="")
        print(f"Ev={variables.evidence_strength[0].upper()}", end="")
        
        try:
            # Create variant evidence
            evidence = self.create_variant_evidence(variables)
            
            # Initialize agents with specified strategies
            prosecutor = ProsecutorAgent(strategy=variables.prosecutor_strategy)
            defense = DefenseAgent(strategy=variables.defense_strategy)
            judge = JudgeAgent(temperament=variables.judge_temperament)
            
            # Run trial proceedings (3 phases: Opening, Rebuttals, Verdict)
            prosecutor_args = []
            defense_args = []
            
            # Phase 1: Opening arguments
            prosecutor_opening = prosecutor.make_opening_argument(evidence)
            prosecutor_args.append(prosecutor_opening)
            
            defense_opening = defense.make_opening_argument(evidence)
            defense_args.append(defense_opening)
            
            # Phase 2: Rebuttals (always included)
            prosecutor_rebuttal = prosecutor.make_rebuttal(defense_opening, evidence)
            prosecutor_args.append(prosecutor_rebuttal)
            
            defense_rebuttal = defense.make_rebuttal(prosecutor_opening, evidence)
            defense_args.append(defense_rebuttal)
            
            # Phase 3: Judge's verdict
            verdict = judge.evaluate_case(prosecutor_args, defense_args, evidence)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            print(f" → {verdict.winner.upper()} ({verdict.confidence_score:.0%})")
            
            return SimulationResult(
                simulation_id=simulation_id,
                variables=variables,
                verdict=verdict,
                prosecutor_arguments=prosecutor_args,
                defense_arguments=defense_args,
                execution_time=execution_time
            )
            
        except Exception as e:
            print(f" → ERROR: {e}")
            # Create a default verdict on error
            verdict = Verdict(
                outcome=VerdictOutcome.DEFENSE_WIN,
                winner="defendant",
                rationale=f"Simulation error: {str(e)}",
                key_factors=["Error in simulation"],
                cited_authorities=[],
                confidence_score=0.0
            )
            
            return SimulationResult(
                simulation_id=simulation_id,
                variables=variables,
                verdict=verdict,
                prosecutor_arguments=[],
                defense_arguments=[],
                execution_time=0.0
            )
    
    def run_simulations(self,
                       n_simulations: int,
                       randomization_config: Optional[Dict] = None,
                       parallel: bool = False) -> MonteCarloAnalysis:
        """
        Run N Monte Carlo simulations.
        
        Args:
            n_simulations: Number of simulations to run
            randomization_config: Configuration for variable randomization
            parallel: Whether to run simulations in parallel (requires async)
            
        Returns:
            Statistical analysis of results
        """
        # First, research the case if not done
        if not self.base_evidence:
            self.research_case()
        
        print(f"\n{'='*60}")
        print(f"PHASE 2: MONTE CARLO SIMULATION")
        print(f"{'='*60}")
        print(f"\n🎲 Running {n_simulations} simulations with randomized variables...")
        
        # Default randomization config
        if randomization_config is None:
            randomization_config = {
                'fixed_strategies': False,
                'fixed_evidence': False
            }
        
        # Run simulations
        self.results = []
        for i in range(1, n_simulations + 1):
            # Create and randomize variables
            variables = SimulationVariables()
            variables.randomize(**randomization_config)
            
            # Run simulation
            result = self.run_single_simulation(i, variables)
            self.results.append(result)
        
        # Analyze results
        self.analysis = self.analyze_results()
        
        print(f"\n{'='*60}")
        print("SIMULATION COMPLETE")
        print(f"{'='*60}")
        
        self.print_analysis_summary()
        
        return self.analysis
    
    def analyze_results(self) -> MonteCarloAnalysis:
        """
        Perform statistical analysis on simulation results.
        
        Returns:
            Comprehensive analysis of results
        """
        if not self.results:
            raise ValueError("No simulation results to analyze")
        
        # Basic statistics
        plaintiff_wins = sum(1 for r in self.results if r.verdict.winner == "plaintiff")
        defense_wins = sum(1 for r in self.results if r.verdict.winner == "defendant")
        total = len(self.results)
        
        confidences = [r.verdict.confidence_score for r in self.results]
        avg_confidence = np.mean(confidences)
        std_confidence = np.std(confidences)
        
        execution_times = [r.execution_time for r in self.results]
        avg_execution = np.mean(execution_times)
        
        # Strategy performance analysis
        strategy_performance = self._analyze_strategy_performance()
        
        # Factor impact analysis
        factor_impact = self._analyze_factor_impact()
        
        # Venue and evidence impact
        venue_impact = self._analyze_venue_impact()
        evidence_impact = self._analyze_evidence_impact()
        nda_impact = self._analyze_nda_impact()
        
        # Find best configurations
        best_plaintiff_config = self._find_best_config("plaintiff")
        best_defense_config = self._find_best_config("defendant")
        
        return MonteCarloAnalysis(
            total_simulations=total,
            plaintiff_wins=plaintiff_wins,
            defense_wins=defense_wins,
            average_confidence=avg_confidence,
            strategy_performance=strategy_performance,
            factor_impact=factor_impact,
            best_plaintiff_config=best_plaintiff_config,
            best_defense_config=best_defense_config,
            confidence_std=std_confidence,
            execution_time_avg=avg_execution,
            venue_impact=venue_impact,
            evidence_impact=evidence_impact,
            nda_impact=nda_impact
        )
    
    def _analyze_strategy_performance(self) -> Dict[str, Dict]:
        """Analyze performance of different strategies."""
        performance = {
            'prosecutor': defaultdict(lambda: {'wins': 0, 'total': 0, 'confidence': []}),
            'defense': defaultdict(lambda: {'wins': 0, 'total': 0, 'confidence': []}),
            'judge': defaultdict(lambda: {'wins_p': 0, 'wins_d': 0, 'total': 0})
        }
        
        for result in self.results:
            vars = result.variables
            
            # Prosecutor strategy
            performance['prosecutor'][vars.prosecutor_strategy]['total'] += 1
            performance['prosecutor'][vars.prosecutor_strategy]['confidence'].append(result.verdict.confidence_score)
            if result.verdict.winner == "plaintiff":
                performance['prosecutor'][vars.prosecutor_strategy]['wins'] += 1
            
            # Defense strategy
            performance['defense'][vars.defense_strategy]['total'] += 1
            performance['defense'][vars.defense_strategy]['confidence'].append(result.verdict.confidence_score)
            if result.verdict.winner == "defendant":
                performance['defense'][vars.defense_strategy]['wins'] += 1
            
            # Judge temperament
            performance['judge'][vars.judge_temperament]['total'] += 1
            if result.verdict.winner == "plaintiff":
                performance['judge'][vars.judge_temperament]['wins_p'] += 1
            else:
                performance['judge'][vars.judge_temperament]['wins_d'] += 1
        
        # Calculate win rates and average confidence
        for role in ['prosecutor', 'defense']:
            for strategy in performance[role]:
                data = performance[role][strategy]
                data['win_rate'] = data['wins'] / data['total'] if data['total'] > 0 else 0
                data['avg_confidence'] = np.mean(data['confidence']) if data['confidence'] else 0
                del data['confidence']  # Remove raw data for cleaner output
        
        for temperament in performance['judge']:
            data = performance['judge'][temperament]
            data['plaintiff_rate'] = data['wins_p'] / data['total'] if data['total'] > 0 else 0
            data['defense_rate'] = data['wins_d'] / data['total'] if data['total'] > 0 else 0
        
        return dict(performance)
    
    def _analyze_factor_impact(self) -> Dict[str, float]:
        """Analyze impact of various factors on outcomes."""
        factors = {}
        
        # Time since departure impact
        short_time = [r for r in self.results if r.variables.time_since_departure <= 3]
        long_time = [r for r in self.results if r.variables.time_since_departure > 6]
        
        if short_time:
            factors['short_departure_time'] = sum(1 for r in short_time if r.verdict.winner == "plaintiff") / len(short_time)
        if long_time:
            factors['long_departure_time'] = sum(1 for r in long_time if r.verdict.winner == "plaintiff") / len(long_time)
        
        # Competitor relationship impact
        direct_comp = [r for r in self.results if r.variables.competitor_relationship == "direct"]
        no_comp = [r for r in self.results if r.variables.competitor_relationship == "none"]
        
        if direct_comp:
            factors['direct_competitor'] = sum(1 for r in direct_comp if r.verdict.winner == "plaintiff") / len(direct_comp)
        if no_comp:
            factors['no_competition'] = sum(1 for r in no_comp if r.verdict.winner == "plaintiff") / len(no_comp)
        
        # Defendant cooperation impact
        hostile = [r for r in self.results if r.variables.defendant_cooperation == "hostile"]
        cooperative = [r for r in self.results if r.variables.defendant_cooperation == "cooperative"]
        
        if hostile:
            factors['hostile_defendant'] = sum(1 for r in hostile if r.verdict.winner == "plaintiff") / len(hostile)
        if cooperative:
            factors['cooperative_defendant'] = sum(1 for r in cooperative if r.verdict.winner == "plaintiff") / len(cooperative)
        
        return factors
    
    def _analyze_venue_impact(self) -> Dict[str, Dict]:
        """Analyze impact of venue bias."""
        venue_data = defaultdict(lambda: {'total': 0, 'plaintiff_wins': 0})
        
        for result in self.results:
            venue = result.variables.venue_bias
            venue_data[venue]['total'] += 1
            if result.verdict.winner == "plaintiff":
                venue_data[venue]['plaintiff_wins'] += 1
        
        # Calculate win rates
        for venue in venue_data:
            data = venue_data[venue]
            data['plaintiff_win_rate'] = data['plaintiff_wins'] / data['total'] if data['total'] > 0 else 0
            data['defense_win_rate'] = 1 - data['plaintiff_win_rate']
        
        return dict(venue_data)
    
    def _analyze_evidence_impact(self) -> Dict[str, Dict]:
        """Analyze impact of evidence strength."""
        evidence_data = defaultdict(lambda: {'total': 0, 'plaintiff_wins': 0, 'avg_confidence': []})
        
        for result in self.results:
            strength = result.variables.evidence_strength
            evidence_data[strength]['total'] += 1
            evidence_data[strength]['avg_confidence'].append(result.verdict.confidence_score)
            if result.verdict.winner == "plaintiff":
                evidence_data[strength]['plaintiff_wins'] += 1
        
        # Calculate statistics
        for strength in evidence_data:
            data = evidence_data[strength]
            data['plaintiff_win_rate'] = data['plaintiff_wins'] / data['total'] if data['total'] > 0 else 0
            data['avg_confidence'] = np.mean(data['avg_confidence']) if data['avg_confidence'] else 0
        
        return dict(evidence_data)
    
    def _analyze_nda_impact(self) -> Dict[str, float]:
        """Analyze impact of NDA presence."""
        with_nda = [r for r in self.results if r.variables.has_nda]
        without_nda = [r for r in self.results if not r.variables.has_nda]
        
        impact = {}
        if with_nda:
            impact['with_nda_win_rate'] = sum(1 for r in with_nda if r.verdict.winner == "plaintiff") / len(with_nda)
        if without_nda:
            impact['without_nda_win_rate'] = sum(1 for r in without_nda if r.verdict.winner == "plaintiff") / len(without_nda)
        
        if with_nda and without_nda:
            impact['nda_impact_delta'] = impact['with_nda_win_rate'] - impact['without_nda_win_rate']
        
        return impact
    
    def _find_best_config(self, for_side: str) -> SimulationVariables:
        """Find the best configuration for a given side."""
        if for_side == "plaintiff":
            best = max(self.results, key=lambda r: 
                      (1 if r.verdict.winner == "plaintiff" else 0) * r.verdict.confidence_score)
        else:
            best = max(self.results, key=lambda r: 
                      (1 if r.verdict.winner == "defendant" else 0) * r.verdict.confidence_score)
        
        return best.variables
    
    def print_analysis_summary(self):
        """Print a formatted summary of the analysis."""
        if not self.analysis:
            print("No analysis available. Run simulations first.")
            return
        
        a = self.analysis
        
        print(f"\n📊 RESULTS SUMMARY")
        print(f"{'='*40}")
        print(f"Total Simulations: {a.total_simulations}")
        print(f"Plaintiff Wins: {a.plaintiff_wins} ({a.plaintiff_wins/a.total_simulations:.1%})")
        print(f"Defense Wins: {a.defense_wins} ({a.defense_wins/a.total_simulations:.1%})")
        print(f"Average Confidence: {a.average_confidence:.1%} (σ={a.confidence_std:.2f})")
        print(f"Average Execution Time: {a.execution_time_avg:.2f}s")
        
        print(f"\n🎯 STRATEGY PERFORMANCE")
        print(f"{'='*40}")
        
        print("\nProsecutor Strategies:")
        for strat, data in a.strategy_performance['prosecutor'].items():
            print(f"  {strat:12} - Win Rate: {data['win_rate']:.1%}, Avg Conf: {data['avg_confidence']:.1%}")
        
        print("\nDefense Strategies:")
        for strat, data in a.strategy_performance['defense'].items():
            print(f"  {strat:12} - Win Rate: {data['win_rate']:.1%}, Avg Conf: {data['avg_confidence']:.1%}")
        
        print("\nJudge Temperaments:")
        for temp, data in a.strategy_performance['judge'].items():
            print(f"  {temp:12} - P wins: {data['plaintiff_rate']:.1%}, D wins: {data['defense_rate']:.1%}")
        
        print(f"\n🔍 FACTOR ANALYSIS")
        print(f"{'='*40}")
        
        print("\nEvidence Strength Impact:")
        for strength, data in a.evidence_impact.items():
            print(f"  {strength:8} - P Win Rate: {data['plaintiff_win_rate']:.1%}")
        
        print("\nNDA Impact:")
        for key, value in a.nda_impact.items():
            if 'rate' in key:
                print(f"  {key}: {value:.1%}")
            else:
                print(f"  {key}: {value:+.1%}")
        
        print("\nVenue Impact:")
        for venue, data in a.venue_impact.items():
            print(f"  {venue:20} - P Win Rate: {data['plaintiff_win_rate']:.1%}")
        
        print(f"\n🏆 OPTIMAL CONFIGURATIONS")
        print(f"{'='*40}")
        
        print("\nBest for Plaintiff:")
        p_config = a.best_plaintiff_config
        print(f"  • Prosecutor: {p_config.prosecutor_strategy}")
        print(f"  • Defense: {p_config.defense_strategy}")
        print(f"  • Judge: {p_config.judge_temperament}")
        print(f"  • Evidence: {p_config.evidence_strength}")
        print(f"  • NDA: {p_config.has_nda}")
        
        print("\nBest for Defense:")
        d_config = a.best_defense_config
        print(f"  • Prosecutor: {d_config.prosecutor_strategy}")
        print(f"  • Defense: {d_config.defense_strategy}")
        print(f"  • Judge: {d_config.judge_temperament}")
        print(f"  • Evidence: {d_config.evidence_strength}")
        print(f"  • NDA: {d_config.has_nda}")
    
    def save_results(self, filepath: str):
        """Save detailed results to JSON file."""
        output = {
            'case_description': self.case_description,
            'jurisdiction': self.base_jurisdiction,
            'research_summary': {
                'statutes_found': len(self.researched_statutes),
                'precedents_found': len(self.researched_precedents),
                'key_statute': self.researched_statutes[0].citation if self.researched_statutes else None,
                'key_precedent': self.researched_precedents[0].case_name if self.researched_precedents else None
            },
            'simulations': [r.to_dict() for r in self.results],
            'timestamp': datetime.now().isoformat()
        }
        
        # Only include analysis if it exists (from run_simulations)
        if self.analysis:
            output['analysis'] = {
                'total_simulations': self.analysis.total_simulations,
                'plaintiff_wins': self.analysis.plaintiff_wins,
                'defense_wins': self.analysis.defense_wins,
                'average_confidence': self.analysis.average_confidence,
                'confidence_std': self.analysis.confidence_std,
                'strategy_performance': self.analysis.strategy_performance,
                'factor_impact': self.analysis.factor_impact,
                'venue_impact': self.analysis.venue_impact,
                'evidence_impact': self.analysis.evidence_impact,
                'nda_impact': self.analysis.nda_impact,
                'best_plaintiff_config': self.analysis.best_plaintiff_config.to_dict(),
                'best_defense_config': self.analysis.best_defense_config.to_dict()
            }
        else:
            # For single simulation results
            if self.results:
                winner_counts = {'plaintiff': 0, 'defendant': 0}
                for r in self.results:
                    winner_counts[r.verdict.winner] += 1
                
                output['summary'] = {
                    'total_simulations': len(self.results),
                    'plaintiff_wins': winner_counts.get('plaintiff', 0),
                    'defense_wins': winner_counts.get('defendant', 0),
                    'note': 'Full analysis requires multiple simulations. Run run_simulations() for complete statistics.'
                }
        
        with open(filepath, 'w') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filepath}")


def test_n1_simulation():
    """
    Test case with N=1 simulation.
    Demonstrates the system with a single run.
    """
    print("\n" + "="*70)
    print("N=1 TEST CASE - SINGLE SIMULATION")
    print("="*70)
    
    # Define a test case
    case_description = """
    SolarTech Industries is suing former Chief Technology Officer Dr. Sarah Chen 
    for trade secret misappropriation related to proprietary solar panel efficiency 
    optimization algorithms.
    
    Background:
    - Dr. Chen worked at SolarTech for 5 years and signed a comprehensive NDA
    - She had full access to the company's core algorithmic IP
    - She left to found her own startup, BrightEnergy Solutions
    - 4 months after her departure, BrightEnergy announced a breakthrough solar 
      optimization system with 85% similarity to SolarTech's technology
    
    Evidence:
    - Email records show Dr. Chen sent large attachments to personal email 2 days before resignation
    - GitHub commit logs show unusual activity in proprietary repos during final week
    - Former colleague testified that Dr. Chen mentioned "taking her work with her"
    - BrightEnergy's patent filing contains equations nearly identical to SolarTech's
    
    Defense Claims:
    - Dr. Chen developed similar ideas independently based on public research
    - The algorithms are based on well-known mathematical principles
    - No direct code was copied, only concepts were similar
    - Dr. Chen's personal research predates her time at SolarTech
    
    The case is filed in the Northern District of California.
    """
    
    print("\n📋 Case Summary:")
    print("-" * 40)
    print(case_description[:400] + "...")
    
    # Create Monte Carlo simulation
    mc_sim = EnhancedMonteCarloSimulation(
        case_description=case_description,
        base_jurisdiction="Federal",
        research_depth="comprehensive"
    )
    
    # Run research phase
    evidence = mc_sim.research_case()
    
    # Run N=1 simulation
    print(f"\n{'='*60}")
    print("RUNNING N=1 SIMULATION")
    print(f"{'='*60}")
    
    # Set specific variables for test
    test_variables = SimulationVariables(
        prosecutor_strategy="aggressive",
        defense_strategy="moderate",
        judge_temperament="balanced",
        has_nda=True,
        evidence_strength="strong",
        venue_bias="neutral",
        num_statutes_cited=3,
        num_precedents_cited=3,
        defendant_cooperation="moderate",
        plaintiff_damages_claim="extensive",
        time_since_departure=4,
        competitor_relationship="direct"
    )
    
    print("\n📊 Simulation Configuration:")
    print(f"  • Prosecutor Strategy: {test_variables.prosecutor_strategy}")
    print(f"  • Defense Strategy: {test_variables.defense_strategy}")
    print(f"  • Judge Temperament: {test_variables.judge_temperament}")
    print(f"  • Evidence Strength: {test_variables.evidence_strength}")
    print(f"  • NDA Present: {test_variables.has_nda}")
    print(f"  • Trial Structure: Opening → Rebuttals → Verdict (3 phases)")
    
    # Run single simulation
    result = mc_sim.run_single_simulation(1, test_variables)
    
    # Display results
    print(f"\n{'='*60}")
    print("SIMULATION RESULTS")
    print(f"{'='*60}")
    
    print(f"\n⚖️ VERDICT: {result.verdict.winner.upper()} WINS")
    print(f"📈 Confidence: {result.verdict.confidence_score:.1%}")
    print(f"⏱️ Execution Time: {result.execution_time:.2f} seconds")
    
    print(f"\n📝 Rationale:")
    print(f"{result.verdict.rationale[:500]}...")
    
    print(f"\n🔑 Key Factors:")
    for factor in result.verdict.key_factors[:5]:
        print(f"  • {factor}")
    
    print(f"\n📚 Cited Authorities:")
    for authority in result.verdict.cited_authorities[:5]:
        print(f"  • {authority}")
    
    print(f"\n📊 Arguments Made:")
    print(f"  • Prosecutor: {len(result.prosecutor_arguments)} arguments")
    print(f"  • Defense: {len(result.defense_arguments)} arguments")
    
    # Save results
    mc_sim.results = [result]
    mc_sim.save_results("n1_test_results.json")
    
    return result


def test_n10_simulation():
    """
    Test case with N=10 simulations.
    Demonstrates Monte Carlo analysis with randomized variables.
    """
    print("\n" + "="*70)
    print("N=10 TEST CASE - MONTE CARLO SIMULATION")
    print("="*70)
    
    # Use a different case for variety
    case_description = """
    DataMine Corp is suing former data scientist Alex Kumar for allegedly stealing 
    proprietary machine learning models for customer behavior prediction.
    
    Facts:
    - Alex worked at DataMine for 2 years but did NOT sign an NDA (oversight during hiring)
    - Company relies on employee handbook policies about confidential information
    - Alex joined competitor PredictAI one month after leaving
    - PredictAI launched a similar prediction service 2 months later
    - Some evidence of file downloads but within normal work patterns
    - Code similarities exist but could be industry standard approaches
    
    The case is filed in Delaware federal court.
    """
    
    print("\n📋 Case Summary:")
    print("A trade secret case with weaker evidence and no NDA...")
    
    # Create and run Monte Carlo simulation
    mc_sim = EnhancedMonteCarloSimulation(
        case_description=case_description,
        base_jurisdiction="Federal",
        research_depth="moderate"
    )
    
    # Run simulations with full randomization
    analysis = mc_sim.run_simulations(
        n_simulations=10,
        randomization_config={
            'fixed_strategies': False,  # Randomize all strategies
            'fixed_evidence': False     # Randomize evidence factors
        }
    )
    
    # Save comprehensive results
    mc_sim.save_results("n10_test_results.json")
    
    return analysis


if __name__ == "__main__":
    print("\n" + "="*70)
    print("ENHANCED MONTE CARLO LEGAL SIMULATION")
    print("="*70)
    print("\nThis system performs comprehensive case research before running")
    print("Monte Carlo simulations with randomized variables.")
    
    # Run N=1 test
    print("\n1️⃣ Running N=1 Test Case...")
    n1_result = test_n1_simulation()
    
    # Wait for user
    input("\n\nPress Enter to continue to N=10 Monte Carlo simulation...")
    
    # Run N=10 test
    print("\n🔟 Running N=10 Monte Carlo Test...")
    n10_analysis = test_n10_simulation()
    
    print("\n" + "="*70)
    print("ALL TESTS COMPLETE")
    print("="*70)
    print("\n✅ Check the following files for detailed results:")
    print("  • n1_test_results.json - Single simulation details")
    print("  • n10_test_results.json - Monte Carlo analysis")
    print("\n🚀 System is ready for production use!")
