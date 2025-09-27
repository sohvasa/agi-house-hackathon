# Legal Case Simulation System

A sophisticated multi-agent framework for simulating legal proceedings in trade secret misappropriation cases. The system features autonomous legal agents (prosecutor, defense, judge) that argue cases based on real statutes and precedents.

## Overview

This simulation system models legal proceedings through the interaction of specialized AI agents, each with distinct roles and strategies. It supports both single-trial simulations and Monte Carlo analysis for strategy optimization.

## Key Components

### 1. **Agent Types**

#### Prosecutor Agent
- **Role**: Argues for trade secret misappropriation
- **Strategies**: 
  - `aggressive`: Emphasizes every piece of evidence, seeks maximum remedies
  - `moderate`: Balanced approach, focuses on strongest arguments
  - `conservative`: Cautious approach, acknowledges weaknesses
- **Capabilities**: 
  - Cites relevant statutes (DTSA, UTSA)
  - References case precedents
  - Makes opening arguments and rebuttals

#### Defense Agent
- **Role**: Argues against misappropriation claims
- **Strategies**:
  - `aggressive`: Vigorously challenges all evidence
  - `moderate`: Reasonable challenges to weak points
  - `conservative`: Measured approach, may propose settlements
- **Capabilities**:
  - Questions trade secret qualification
  - Highlights missing evidence
  - Provides alternative explanations

#### Judge Agent
- **Role**: Evaluates arguments and renders verdict
- **Temperaments**:
  - `strict`: Rigorous application of law
  - `balanced`: Fair consideration of all factors
  - `lenient`: Considers broader equitable factors
- **Output**: Binary verdict with confidence score and reasoning

#### Research Agent
- **Role**: Gathers evidence by coordinating with existing agents
- **Capabilities**:
  - Interfaces with PrecedentAgent for case law
  - Uses StatuteAgent for statutory research
  - Prepares comprehensive evidence packets

### 2. **Simulation Process**

The simulation follows a structured legal proceeding:

```
1. Evidence Gathering (Research Agent)
   ↓
2. Opening Arguments
   - Prosecutor presents case
   - Defense responds
   ↓
3. Rebuttals (Optional)
   - Each side addresses opponent's arguments
   ↓
4. Judge's Verdict
   - Evaluation of all arguments
   - Final decision with reasoning
```

### 3. **Case Evidence Structure**

```python
@dataclass
class CaseEvidence:
    case_description: str
    jurisdiction: str
    has_nda: bool
    evidence_strength: str  # weak/moderate/strong
    venue_bias: str  # plaintiff-friendly/neutral/defendant-friendly
    statutes: List[StatuteInfo]
    precedents: List[CasePrecedent]
    facts: List[str]
    plaintiff_claims: List[str]
    defendant_claims: List[str]
```

## Usage Examples

### Single Trial Simulation

```python
from simulation.simulation import LegalSimulation

# Define your case
case_description = """
TechCorp alleges that former employee John Doe misappropriated 
trade secrets when joining competitor. John had signed an NDA 
and downloaded proprietary code before leaving...
"""

# Configure simulation
sim = LegalSimulation(
    prosecutor_strategy="aggressive",
    defense_strategy="moderate",
    judge_temperament="balanced"
)

# Run simulation
evidence = sim.prepare_case(case_description)
verdict = sim.run_trial(include_rebuttals=True)

print(f"Winner: {verdict.winner}")
print(f"Confidence: {verdict.confidence_score:.2%}")
```

### Monte Carlo Simulation

```python
from simulation.simulation import MonteCarloSimulation

# Create simulator
mc_sim = MonteCarloSimulation()

# Run multiple simulations with varying strategies
results = mc_sim.run_simulations(
    case_description=case_description,
    num_simulations=20,
    vary_strategies=True,
    fixed_judge=None  # Also vary judge temperament
)

# Analyze results
print(f"Plaintiff win rate: {results['analysis']['plaintiff_win_rate']:.1%}")
print(f"Best prosecutor strategy: {results['analysis']['best_prosecutor_strategy']}")
```

## Strategy Variables

Each agent has a configurable strategy that affects its behavior:

### Prosecutor Strategies
- **Aggressive**: Maximum pressure, cites all possible violations
- **Moderate**: Balanced approach, focuses on strong points
- **Conservative**: Careful approach, only strongest arguments

### Defense Strategies
- **Aggressive**: Challenges everything, seeks dismissal
- **Moderate**: Reasonable challenges, fair outcomes
- **Conservative**: Acknowledges strengths, narrows claims

### Judge Temperaments
- **Strict**: Letter of the law, high burden of proof
- **Balanced**: Weighs all factors fairly
- **Lenient**: Considers equity and proportionality

## Monte Carlo Analysis

The Monte Carlo simulation explores different strategy combinations to find optimal approaches:

```python
# Analyze strategy effectiveness
results = mc_sim.run_simulations(case, num_simulations=50)

# Results include:
# - Win rates for each strategy
# - Optimal strategy combinations
# - Confidence distributions
# - Statistical analysis
```

## Output Formats

### Verdict Structure
```python
@dataclass
class Verdict:
    outcome: VerdictOutcome  # PLAINTIFF_WIN/DEFENSE_WIN
    winner: str
    rationale: str
    key_factors: List[str]
    cited_authorities: List[str]
    confidence_score: float
```

### Trial Summary
```json
{
  "case": "Case description...",
  "strategies": {
    "prosecutor": "aggressive",
    "defense": "moderate",
    "judge": "balanced"
  },
  "verdict": {
    "winner": "plaintiff",
    "confidence": 0.75,
    "key_factors": ["Strong NDA", "Clear evidence"]
  }
}
```

## Requirements

- Python 3.8+
- Google Gemini API key (for agent reasoning)
- Perplexity API key (optional, for enhanced research)
- See `requirements.txt` for full dependencies

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set up API keys in .env
echo "GEMINI_API_KEY=your_key_here" >> .env
echo "PERPLEXITY_API_KEY=your_key_here" >> .env  # Optional

# Run test suite
python test_simulation.py

# Run demo
python examples/simulation_demo.py
```

## Advanced Features

### Custom Evidence Injection
You can provide pre-gathered evidence instead of using the Research Agent:

```python
evidence = CaseEvidence(
    case_description="Your case...",
    has_nda=True,
    evidence_strength="strong",
    statutes=[...],  # Your statute objects
    precedents=[...]  # Your precedent objects
)

sim.case_evidence = evidence
verdict = sim.run_trial()
```

### Async Support
The base agents support async operations for parallel processing:

```python
async def run_async_trial():
    # Agents can process asynchronously
    prosecutor_arg = await prosecutor.make_opening_argument_async(evidence)
    defense_arg = await defense.make_opening_argument_async(evidence)
```

### Strategy Optimization
Find optimal strategies for specific case types:

```python
# Test all strategy combinations
strategies = ["aggressive", "moderate", "conservative"]
best_outcome = None
best_config = None

for p_strat in strategies:
    for d_strat in strategies:
        sim = LegalSimulation(p_strat, d_strat, "balanced")
        verdict = sim.run_trial()
        # Track best configuration...
```

## Extending the System

### Adding New Agent Types
```python
class MediatorAgent(BaseAgent):
    def __init__(self, style="facilitative"):
        super().__init__(
            name="Mediator",
            system_prompt="You facilitate settlement discussions..."
        )
    
    def propose_settlement(self, arguments):
        # Settlement logic
        pass
```

### Custom Strategies
```python
# Add new strategy to agent
strategy_prompts = {
    "creative": "You find innovative legal arguments..."
}
```

## Limitations

1. **API Dependencies**: Requires API keys for full functionality
2. **Legal Accuracy**: Simulations are for demonstration/research, not legal advice
3. **Evidence Quality**: Depends on the quality of research agents
4. **Computational Cost**: Monte Carlo simulations can be expensive with many trials

## Future Enhancements

- [ ] Support for more case types beyond trade secrets
- [ ] Integration with real legal databases
- [ ] Multi-round negotiations
- [ ] Jury simulation
- [ ] Settlement negotiations
- [ ] Appeals process simulation
- [ ] Machine learning for strategy optimization
- [ ] Real case outcome prediction

## Contributing

Contributions are welcome! Areas for improvement:
- Additional agent strategies
- More sophisticated evidence gathering
- Enhanced natural language processing
- Statistical analysis tools
- Visualization of results

## License

This is a research/educational tool. Not for actual legal use.

## Contact

For questions or collaboration opportunities, please open an issue on the repository.
