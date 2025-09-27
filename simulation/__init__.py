"""
Legal Case Simulation Package
==============================
A comprehensive multi-agent system for simulating legal proceedings.
"""

from .simulation import (
    ProsecutorAgent,
    DefenseAgent,
    JudgeAgent,
    ResearchAgent,
    LegalSimulation,
    MonteCarloSimulation,
    CaseEvidence,
    LegalArgument,
    Verdict,
    VerdictOutcome,
    ArgumentType
)

from .montecarlo import (
    SimulationVariables,
    SimulationResult,
    MonteCarloAnalysis,
    EnhancedMonteCarloSimulation,
    test_n1_simulation,
    test_n10_simulation
)

__all__ = [
    # Main simulation classes
    'ProsecutorAgent',
    'DefenseAgent',
    'JudgeAgent',
    'ResearchAgent',
    'LegalSimulation',
    'MonteCarloSimulation',
    
    # Data structures
    'CaseEvidence',
    'LegalArgument',
    'Verdict',
    'VerdictOutcome',
    'ArgumentType',
    
    # Monte Carlo components
    'SimulationVariables',
    'SimulationResult',
    'MonteCarloAnalysis',
    'EnhancedMonteCarloSimulation',
    
    # Test functions
    'test_n1_simulation',
    'test_n10_simulation'
]

__version__ = '1.0.0'
