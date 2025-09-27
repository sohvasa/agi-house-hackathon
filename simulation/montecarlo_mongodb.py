"""
MongoDB Integration for Monte Carlo Legal Simulations
=====================================================
This module extends the Monte Carlo simulation to save results to MongoDB,
storing individual simulations and linking them in a master Monte Carlo document.
"""

import os
import sys
from typing import Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, field
from bson import ObjectId

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mongodb_manager import (
    MongoDBManager, 
    CaseSimulation, 
    CaseResearch,
    AgentMessage,
    SimulationStatus,
    ResearchStatus
)
from simulation.montecarlo import (
    EnhancedMonteCarloSimulation,
    SimulationVariables,
    SimulationResult,
    MonteCarloAnalysis
)
from simulation.enhanced_trial import EnhancedLegalSimulation
from datetime import timedelta


@dataclass
class MonteCarloDocument:
    """
    Represents a complete Monte Carlo simulation run in MongoDB.
    Links to individual simulation documents.
    """
    monte_carlo_id: str
    case_description: str
    jurisdiction: str
    total_simulations: int
    simulation_ids: List[ObjectId]  # References to individual simulations
    analysis: Optional[Dict] = None
    research_summary: Optional[Dict] = None
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    status: str = "pending"
    metadata: Optional[Dict] = None
    _id: Optional[ObjectId] = None
    
    def to_mongodb_doc(self) -> Dict:
        """Convert to MongoDB document."""
        doc = {
            "monte_carlo_id": self.monte_carlo_id,
            "case_description": self.case_description,
            "jurisdiction": self.jurisdiction,
            "total_simulations": self.total_simulations,
            "simulation_ids": self.simulation_ids,
            "created_at": self.created_at,
            "status": self.status
        }
        if self.analysis:
            doc["analysis"] = self.analysis
        if self.research_summary:
            doc["research_summary"] = self.research_summary
        if self.completed_at:
            doc["completed_at"] = self.completed_at
        if self.metadata:
            doc["metadata"] = self.metadata
        if self._id:
            doc["_id"] = self._id
        return doc


class MongoEnhancedMonteCarloSimulation(EnhancedMonteCarloSimulation):
    """
    Enhanced Monte Carlo simulation with MongoDB storage capabilities.
    Extends the base Monte Carlo class to save results to MongoDB.
    """
    
    def __init__(self, 
                 case_description: str,
                 base_jurisdiction: str = "Federal",
                 research_depth: str = "moderate",
                 db_manager: Optional[MongoDBManager] = None,
                 auto_save: bool = True):
        """
        Initialize Monte Carlo simulation with MongoDB support.
        
        Args:
            case_description: Natural language case description
            base_jurisdiction: Legal jurisdiction
            research_depth: How thorough research should be
            db_manager: MongoDB manager instance (creates new if None)
            auto_save: Whether to automatically save to MongoDB
        """
        super().__init__(case_description, base_jurisdiction, research_depth)
        
        # MongoDB setup
        self.db_manager = db_manager or MongoDBManager()
        self.auto_save = auto_save
        
        # Storage tracking
        self.saved_simulation_ids: List[ObjectId] = []
        self.monte_carlo_doc_id: Optional[ObjectId] = None
        self.monte_carlo_id = f"MC_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _convert_to_case_simulation(self, 
                                   result: SimulationResult,
                                   case_id: str) -> CaseSimulation:
        """
        Convert a SimulationResult to a CaseSimulation for MongoDB storage.
        Uses enhanced formatting for full content and proper timestamps.
        
        Args:
            result: SimulationResult from the simulation
            case_id: Case identifier
            
        Returns:
            CaseSimulation object ready for MongoDB
        """
        # Create an enhanced simulation helper for formatting
        enhanced_sim = EnhancedLegalSimulation(
            prosecutor_strategy=result.variables.prosecutor_strategy,
            defense_strategy=result.variables.defense_strategy,
            judge_temperament=result.variables.judge_temperament
        )
        enhanced_sim.case_evidence = self.evidence
        
        # Generate messages with proper timestamps
        start_time = datetime.now()
        messages = []
        time_offset = 0
        
        # Interleave prosecutor and defense arguments properly
        max_args = max(len(result.prosecutor_arguments), len(result.defense_arguments))
        
        for i in range(max_args):
            # Add prosecutor argument if available
            if i < len(result.prosecutor_arguments):
                arg = result.prosecutor_arguments[i]
                # Get full content (not truncated)
                full_content = enhanced_sim._get_full_argument_content(arg)
                
                messages.append(AgentMessage(
                    agent_name="Prosecutor",
                    role="assistant",
                    content=full_content,
                    timestamp=start_time + timedelta(seconds=time_offset),
                    metadata={
                        "argument_type": arg.argument_type.value,
                        "cited_statutes": arg.cited_statutes,
                        "cited_precedents": arg.cited_precedents,
                        "key_points": arg.key_points,
                        "phase": f"round_{i+1}"
                    }
                ))
                time_offset += 30  # 30 seconds per argument
            
            # Add defense argument if available
            if i < len(result.defense_arguments):
                arg = result.defense_arguments[i]
                # Get full content (not truncated)
                full_content = enhanced_sim._get_full_argument_content(arg)
                
                messages.append(AgentMessage(
                    agent_name="Defense",
                    role="assistant",
                    content=full_content,
                    timestamp=start_time + timedelta(seconds=time_offset),
                    metadata={
                        "argument_type": arg.argument_type.value,
                        "cited_statutes": arg.cited_statutes,
                        "cited_precedents": arg.cited_precedents,
                        "key_points": arg.key_points,
                        "phase": f"round_{i+1}"
                    }
                ))
                time_offset += 30  # 30 seconds per argument
        
        # Add verdict with full formatting
        full_verdict = enhanced_sim._format_full_verdict(result.verdict)
        messages.append(AgentMessage(
            agent_name="Judge",
            role="assistant",
            content=full_verdict,
            timestamp=start_time + timedelta(seconds=time_offset),
            metadata={
                "verdict": result.verdict.winner,
                "confidence": result.verdict.confidence_score,
                "key_factors": result.verdict.key_factors,
                "cited_authorities": result.verdict.cited_authorities,
                "phase": "verdict"
            }
        ))
        
        # Create CaseSimulation with properly ordered messages
        return CaseSimulation(
            case_id=case_id,
            case_name=f"Simulation #{result.simulation_id} - {self.case_description[:50]}",
            simulation_type="monte_carlo_trial",
            agents_involved=["Prosecutor", "Defense", "Judge"],
            chat_history=messages,  # Already in proper time order
            status=SimulationStatus.COMPLETED,
            created_at=start_time,
            updated_at=datetime.now(),
            completed_at=start_time + timedelta(seconds=time_offset),
            metadata={
                "monte_carlo_id": self.monte_carlo_id,
                "simulation_id": result.simulation_id,
                "variables": result.variables.to_dict(),
                "execution_time": result.execution_time,
                "total_messages": len(messages),
                "trial_duration_seconds": time_offset
            },
            outcome=result.verdict.winner,
            summary=f"Verdict: {result.verdict.winner} wins with {result.verdict.confidence_score:.1%} confidence"
        )
    
    def run_single_simulation(self, 
                            simulation_id: int,
                            variables: SimulationVariables) -> SimulationResult:
        """
        Run a single simulation and optionally save to MongoDB.
        For single simulations (n=1), uses enhanced trial for richer dialogue.
        
        Args:
            simulation_id: Unique simulation identifier
            variables: Simulation variables to use
            
        Returns:
            SimulationResult
        """
        # Check if this is a single simulation request
        is_single_sim = (simulation_id == 1 and not hasattr(self, '_is_monte_carlo_batch'))
        
        if is_single_sim and self.auto_save and self.db_manager:
            # Use enhanced trial for better dialogue in single simulations
            print("  Using enhanced trial format for richer dialogue...")
            
            # Create enhanced simulation
            enhanced_sim = EnhancedLegalSimulation(
                prosecutor_strategy=variables.prosecutor_strategy,
                defense_strategy=variables.defense_strategy,
                judge_temperament=variables.judge_temperament
            )
            
            # Set evidence
            enhanced_sim.case_evidence = self.evidence
            
            # Run extended trial with more exchanges
            messages, verdict = enhanced_sim.run_extended_trial(
                num_exchanges=3,  # 3 rounds of back-and-forth for single sim
                include_procedural=True  # Include judge's procedural messages
            )
            
            # Create result for compatibility
            result = SimulationResult(
                simulation_id=simulation_id,
                variables=variables,
                prosecutor_arguments=[],  # Already captured in messages
                defense_arguments=[],  # Already captured in messages
                verdict=verdict,
                execution_time=len(messages) * 2  # Approximate time
            )
            
            # Save enhanced trial to MongoDB
            try:
                case_sim = enhanced_sim.convert_to_case_simulation(
                    messages,
                    f"CASE_{self.monte_carlo_id}",
                    simulation_id
                )
                
                sim_id = self.db_manager.save_simulation(case_sim)
                self.saved_simulation_ids.append(sim_id)
                print(f"    → Saved enhanced trial to MongoDB: {sim_id}")
                print(f"    → Total messages: {len(messages)}")
                
            except Exception as e:
                print(f"    ⚠ Failed to save to MongoDB: {e}")
            
            return result
        
        # For Monte Carlo batch simulations, use standard format
        result = super().run_single_simulation(simulation_id, variables)
        
        # Save to MongoDB if auto_save is enabled
        if self.auto_save and self.db_manager:
            try:
                # Convert to CaseSimulation with enhanced formatting
                case_sim = self._convert_to_case_simulation(
                    result, 
                    f"CASE_{self.monte_carlo_id}"
                )
                
                # Save to MongoDB
                sim_id = self.db_manager.save_simulation(case_sim)
                self.saved_simulation_ids.append(sim_id)
                print(f"    → Saved to MongoDB: {sim_id}")
                
            except Exception as e:
                print(f"    ⚠ Failed to save to MongoDB: {e}")
        
        return result
    
    def run_simulations(self,
                       n_simulations: int,
                       randomization_config: Optional[Dict] = None,
                       parallel: bool = False) -> MonteCarloAnalysis:
        """
        Run N Monte Carlo simulations and save to MongoDB.
        
        Args:
            n_simulations: Number of simulations to run
            randomization_config: Configuration for variable randomization
            parallel: Whether to run simulations in parallel
            
        Returns:
            Statistical analysis of results
        """
        # Mark this as a batch Monte Carlo run
        if n_simulations > 1:
            self._is_monte_carlo_batch = True
        
        # Create initial Monte Carlo document in MongoDB
        if self.auto_save and self.db_manager:
            self._create_monte_carlo_document(n_simulations)
        
        # Run simulations (this will save individual simulations)
        analysis = super().run_simulations(n_simulations, randomization_config, parallel)
        
        # Update Monte Carlo document with results
        if self.auto_save and self.db_manager:
            self._update_monte_carlo_document(analysis)
        
        # Clear the batch flag
        if hasattr(self, '_is_monte_carlo_batch'):
            delattr(self, '_is_monte_carlo_batch')
        
        return analysis
    
    def _create_monte_carlo_document(self, n_simulations: int):
        """Create initial Monte Carlo document in MongoDB."""
        try:
            # Create research entry for the Monte Carlo run
            research = CaseResearch(
                case_id=f"CASE_{self.monte_carlo_id}",
                case_name=f"Monte Carlo: {self.case_description[:100]}",
                research_topic="Monte Carlo Simulation Analysis",
                description=f"Monte Carlo simulation with {n_simulations} trials for: {self.case_description}",
                key_findings=[],  # Will be updated after completion
                legal_precedents=[],  # Will be filled from research
                statutes=[],  # Will be filled from research
                simulation_ids=[],  # Will be populated as simulations complete
                status=ResearchStatus.ACTIVE,
                tags=["monte_carlo", "simulation", self.base_jurisdiction.lower()],
                metadata={
                    "monte_carlo_id": self.monte_carlo_id,
                    "planned_simulations": n_simulations,
                    "research_depth": self.research_depth
                }
            )
            
            self.monte_carlo_doc_id = self.db_manager.save_research(research)
            print(f"\n📄 Created Monte Carlo document: {self.monte_carlo_doc_id}")
            
        except Exception as e:
            print(f"⚠ Failed to create Monte Carlo document: {e}")
    
    def _update_monte_carlo_document(self, analysis: MonteCarloAnalysis):
        """Update Monte Carlo document with final results."""
        if not self.monte_carlo_doc_id or not self.db_manager:
            return
        
        try:
            # Get the existing research document
            research = self.db_manager.get_research(self.monte_carlo_doc_id)
            if not research:
                return
            
            # Update with results
            research.simulation_ids = self.saved_simulation_ids
            research.status = ResearchStatus.COMPLETED
            
            # Add key findings from analysis
            research.key_findings = [
                f"Plaintiff win rate: {analysis.plaintiff_wins}/{analysis.total_simulations} ({analysis.plaintiff_wins/analysis.total_simulations:.1%})",
                f"Defense win rate: {analysis.defense_wins}/{analysis.total_simulations} ({analysis.defense_wins/analysis.total_simulations:.1%})",
                f"Average confidence: {analysis.average_confidence:.1%}",
                f"Best prosecutor strategy: {analysis.best_plaintiff_config.prosecutor_strategy}",
                f"Best defense strategy: {analysis.best_defense_config.defense_strategy}",
                f"NDA impact: {analysis.nda_impact.get('nda_impact_delta', 0):.1%} increase in plaintiff wins"
            ]
            
            # Add researched legal materials
            if self.researched_precedents:
                research.legal_precedents = [
                    {
                        "case_name": p.case_name,
                        "year": p.year,
                        "citation": p.citation,
                        "holding": p.holding[:200] if p.holding else ""
                    }
                    for p in self.researched_precedents[:5]
                ]
            
            if self.researched_statutes:
                research.statutes = [
                    {
                        "title": s.title,
                        "citation": s.citation,
                        "snippet": s.snippet[:200] if s.snippet else ""
                    }
                    for s in self.researched_statutes[:5]
                ]
            
            # Update metadata with full analysis
            research.metadata["analysis"] = {
                "total_simulations": analysis.total_simulations,
                "plaintiff_wins": analysis.plaintiff_wins,
                "defense_wins": analysis.defense_wins,
                "average_confidence": analysis.average_confidence,
                "confidence_std": analysis.confidence_std,
                "execution_time_avg": analysis.execution_time_avg,
                "strategy_performance": analysis.strategy_performance,
                "factor_impact": analysis.factor_impact,
                "venue_impact": analysis.venue_impact,
                "evidence_impact": analysis.evidence_impact,
                "nda_impact": analysis.nda_impact
            }
            
            # Save updated document
            self.db_manager.save_research(research)
            print(f"\n📊 Updated Monte Carlo document with analysis results")
            
        except Exception as e:
            print(f"⚠ Failed to update Monte Carlo document: {e}")
    
    def get_saved_simulations(self) -> List[CaseSimulation]:
        """
        Retrieve all saved simulations from MongoDB.
        
        Returns:
            List of CaseSimulation objects
        """
        if not self.db_manager:
            return []
        
        simulations = []
        for sim_id in self.saved_simulation_ids:
            sim = self.db_manager.get_simulation(sim_id)
            if sim:
                simulations.append(sim)
        
        return simulations
    
    def get_monte_carlo_summary(self) -> Optional[Dict]:
        """
        Get comprehensive summary of the Monte Carlo run from MongoDB.
        
        Returns:
            Dictionary containing full Monte Carlo summary
        """
        if not self.monte_carlo_doc_id or not self.db_manager:
            return None
        
        research = self.db_manager.get_research(self.monte_carlo_doc_id)
        if not research:
            return None
        
        # Get all linked simulations
        simulations = self.get_saved_simulations()
        
        summary = {
            "monte_carlo_id": self.monte_carlo_id,
            "document_id": str(self.monte_carlo_doc_id),
            "case_description": self.case_description,
            "jurisdiction": self.base_jurisdiction,
            "total_simulations": len(simulations),
            "status": research.status.value,
            "created_at": research.created_at.isoformat(),
            "key_findings": research.key_findings,
            "simulation_details": [
                {
                    "id": str(sim._id),
                    "simulation_number": sim.metadata.get("simulation_id"),
                    "winner": sim.outcome,
                    "confidence": sim.metadata.get("verdict", {}).get("confidence", 0),
                    "prosecutor_strategy": sim.metadata.get("variables", {}).get("prosecutor_strategy"),
                    "defense_strategy": sim.metadata.get("variables", {}).get("defense_strategy"),
                    "judge_temperament": sim.metadata.get("variables", {}).get("judge_temperament"),
                    "has_nda": sim.metadata.get("variables", {}).get("has_nda"),
                    "evidence_strength": sim.metadata.get("variables", {}).get("evidence_strength")
                }
                for sim in simulations
            ],
            "analysis": research.metadata.get("analysis", {})
        }
        
        return summary


def run_mongodb_monte_carlo_example():
    """
    Example of running a Monte Carlo simulation with MongoDB storage.
    """
    print("\n" + "="*70)
    print("MONTE CARLO SIMULATION WITH MONGODB STORAGE")
    print("="*70)
    
    # Define test case
    case_description = """
    CloudStorage Inc. is suing former engineer Mike Johnson for trade secret theft.
    Mike had access to proprietary distributed storage algorithms and signed an NDA.
    He joined competitor DataVault two months after leaving, and DataVault launched
    a similar product within 6 months. Evidence includes suspicious file downloads
    and code similarities, but Mike claims independent development.
    """
    
    print("\n📋 Case Description:")
    print(case_description[:200] + "...")
    
    # Initialize MongoDB manager
    print("\n🔗 Connecting to MongoDB...")
    try:
        db_manager = MongoDBManager()
        print("✓ Connected to MongoDB")
    except Exception as e:
        print(f"✗ MongoDB connection failed: {e}")
        print("Make sure MONGODB_CONNECTION_STRING is set in .env")
        return
    
    # Create Monte Carlo simulation with MongoDB support
    print("\n🎲 Creating Monte Carlo simulation...")
    mc_sim = MongoEnhancedMonteCarloSimulation(
        case_description=case_description,
        base_jurisdiction="Federal",
        research_depth="moderate",
        db_manager=db_manager,
        auto_save=True  # Automatically save to MongoDB
    )
    
    # Run research phase
    print("\n📚 Researching case...")
    evidence = mc_sim.research_case()
    
    # Run Monte Carlo simulations
    print("\n🎯 Running Monte Carlo simulations...")
    analysis = mc_sim.run_simulations(
        n_simulations=5,  # Small number for demo
        randomization_config={
            'fixed_strategies': False,
            'fixed_evidence': False
        }
    )
    
    # Get summary from MongoDB
    print("\n📊 Retrieving MongoDB Summary...")
    summary = mc_sim.get_monte_carlo_summary()
    
    if summary:
        print(f"\nMonte Carlo ID: {summary['monte_carlo_id']}")
        print(f"MongoDB Document ID: {summary['document_id']}")
        print(f"Total Simulations Saved: {summary['total_simulations']}")
        print(f"Status: {summary['status']}")
        
        print(f"\nKey Findings:")
        for finding in summary['key_findings'][:3]:
            print(f"  • {finding}")
        
        print(f"\nSimulation Results:")
        for sim in summary['simulation_details'][:5]:
            print(f"  Sim #{sim['simulation_number']}: {sim['winner']} wins "
                  f"({sim['confidence']:.1%}) | "
                  f"P:{sim['prosecutor_strategy']}, D:{sim['defense_strategy']}")
    
    # Query saved simulations directly
    print(f"\n🔍 Querying saved simulations...")
    saved_sims = db_manager.search_simulations(
        case_name="Simulation",
        simulation_type="monte_carlo_trial",
        limit=5
    )
    print(f"Found {len(saved_sims)} saved simulations in MongoDB")
    
    # Get case summary from MongoDB
    case_id = f"CASE_{mc_sim.monte_carlo_id}"
    case_summary = db_manager.get_case_summary(case_id)
    print(f"\n📈 Case Summary for {case_id}:")
    print(f"  Total messages across all simulations: {case_summary['total_messages']}")
    print(f"  Agents involved: {', '.join(case_summary['agents_involved'])}")
    
    # Close MongoDB connection
    db_manager.close()
    
    print("\n" + "="*70)
    print("MONGODB MONTE CARLO COMPLETE")
    print("="*70)
    print(f"\n✅ Successfully saved {len(mc_sim.saved_simulation_ids)} simulations to MongoDB")
    print(f"📄 Monte Carlo document ID: {mc_sim.monte_carlo_doc_id}")
    
    return mc_sim, summary


if __name__ == "__main__":
    # Run the example
    mc_sim, summary = run_mongodb_monte_carlo_example()
    
    print("\n💡 To retrieve this Monte Carlo run later:")
    print(f"   1. Use document ID: {mc_sim.monte_carlo_doc_id}")
    print(f"   2. Or search by monte_carlo_id: {mc_sim.monte_carlo_id}")
    print("\n🔗 All simulations are linked and can be queried individually or as a group.")
