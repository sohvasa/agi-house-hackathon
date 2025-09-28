# AGI House Hackathon - Multi-Agent System

A comprehensive multi-agent system built with Google Gemini, featuring chat history management, tool calling capabilities (Perplexity search and BrowserUse), and inter-agent communication.

## Features

- **🤖 Base Agent Class**: Flexible agent framework with Gemini integration
- **💬 Chat History Management**: Full conversation tracking with memory limits
- **🔧 Tool Integration**: Built-in support for Perplexity search and BrowserUse
- **🔄 Inter-Agent Communication**: Agents can communicate and collaborate
- **⚡ Async Support**: Asynchronous operations for improved performance
- **💾 Persistence**: Save and load chat histories
- **📝 System Prompts**: Customize agent behavior with initial prompts

## Setup

### Using Conda (Recommended)
```bash
conda create -n hackathon python=3.12
conda activate hackathon
pip install -r requirements.txt
```

### Using venv
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file in the project root:
```env
# Google Gemini API Key (Required)
GEMINI_API_KEY=your_gemini_api_key_here

# Perplexity API Key (Optional - for web search)
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# BrowserUse API Key (Optional - for browser automation)
BROWSER_USE_API_KEY=your_browser_use_api_key_here
```

## Quick Start

### Basic Agent Usage

```python
from agents.baseAgent import BaseAgent

# Create a basic agent
agent = BaseAgent(
    name="Assistant",
    system_prompt="You are a helpful AI assistant.",
    model_name="gemini-2.5-pro",
    temperature=0.7
)

# Chat with the agent
response = agent.chat("What is machine learning?")
print(response)
```

### Agent with Tools

```python
# Create an agent with tool capabilities
research_agent = BaseAgent(
    name="ResearchBot",
    system_prompt="You are a research assistant.",
    enable_tools=True,
    auto_execute_tools=True
)

# The agent will automatically use tools when needed
response = research_agent.chat("What are the latest AI developments?")
```

### Multi-Agent Communication

```python
# Create multiple agents
analyst = BaseAgent(name="Analyst", system_prompt="You analyze data.")
strategist = BaseAgent(name="Strategist", system_prompt="You create strategies.")

# Connect agents
analyst.connect_agent(strategist)

# Send messages between agents
response = analyst.send_to_agent("Strategist", "What's our Q1 strategy?")
```

## BaseAgent Class API

### Constructor Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `name` | str | Required | Agent identifier |
| `system_prompt` | str | "" | Initial system prompt |
| `model_name` | str | "gemini-2.5-pro" | Gemini model ("gemini-2.5-pro", "gemini-2.5-flash") |
| `temperature` | float | 0.7 | Sampling temperature (0-1) |
| `max_output_tokens` | int | 8192 | Maximum response tokens |
| `enable_tools` | bool | True | Enable tool calling |
| `auto_execute_tools` | bool | True | Auto-execute tool calls |
| `memory_limit` | int | None | Max messages in history |

### Key Methods

#### Chat Methods
```python
response = agent.chat(message, metadata)           # Synchronous chat
response = await agent.chat_async(message, metadata)  # Async chat
```

#### Agent Communication
```python
agent1.connect_agent(agent2)                      # Connect agents
response = agent1.send_to_agent("Agent2", message)  # Send to specific agent
responses = agent1.broadcast_to_agents(message)     # Broadcast to all
```

#### History Management
```python
history = agent.get_history("text")     # Get as formatted text
agent.save_history("history.json")      # Save to file
agent.load_history("history.json")      # Load from file
agent.clear_history(keep_system_prompt=True)  # Clear history
```

## Tool Integration

The agent can automatically use tools when needed:

### Perplexity Search
For real-time web information:
```python
response = agent.chat("What are today's top tech news?")
# Agent automatically uses: [TOOL: perplexity_search({"query": "..."})]
```

### BrowserUse
For web page interaction:
```python
response = agent.chat("Go to example.com and extract the main content")
# Agent automatically uses: [TOOL: browser_use({"task": "..."})]
```

## Specialized Agents

### StatuteAgent - Legal Statute Research

The StatuteAgent is a specialized agent optimized for U.S. legal statute research using Perplexity's search capabilities.

### PrecedentAgent - Case Law Analysis

The PrecedentAgent specializes in finding and analyzing case law precedents, providing mini-doc summaries for legal research.

```python
from agents.statuteAgent import StatuteAgent

# Create a legal research agent
statute_agent = StatuteAgent()

# Quick search returns concise 2-3 sentence snippets
result = statute_agent.quick_search(
    "Find the U.S. law that governs trade secret misappropriation"
)
print(result)
# Output: "Defend Trade Secrets Act (18 U.S.C. § 1836) defines 'trade secret' 
# as information with economic value from not being generally known... 
# Remedies include injunction, damages, attorneys' fees."
```

**Key Features:**
- **Quick Search**: Returns concise 2-3 sentence summaries
- **Detailed Analysis**: Extract definitions, provisions, and remedies
- **Statute Comparison**: Compare different laws side-by-side
- **Case Law Research**: Find relevant court decisions
- **Related Statutes**: Discover connected laws and regulations
- **Export Functionality**: Save research to JSON or Markdown

**Example Queries:**
```python
# Various legal searches
agent.quick_search("federal wire fraud statute and penalties")
agent.quick_search("copyright infringement law and remedies")
agent.quick_search("RICO statute and racketeering definition")

# Detailed analysis
info = agent.find_statute("Computer Fraud and Abuse Act")
cases = agent.get_case_law("18 U.S.C. § 1030", num_cases=5)
comparison = agent.compare_statutes("DTSA", "UTSA")
```

Run the StatuteAgent demo:
```bash
python examples/statute_agent_demo.py
```

### PrecedentAgent - Case Law Research

The PrecedentAgent finds and analyzes case law precedents with mini-doc formatting for legal briefs.

```python
from agents.precedentAgent import PrecedentAgent

# Create a precedent research agent
precedent_agent = PrecedentAgent()

# Quick search returns mini-doc format
result = precedent_agent.quick_search(
    "Find a famous case involving trade secret misappropriation"
)
print(result)
# Output: 
# Case: Waymo v. Uber (2017)
# Citation: N.D. Cal., 2017
# Holding: Court granted injunction where employee downloaded 14,000 confidential files.
# Rule: Misappropriation more likely when forensic evidence + NDA.
# Relevance: Supports Plaintiff if NDA + logs exist; weakens Defense unless evidence is circumstantial.
```

**Key Features:**
- **Mini-Doc Format**: Concise case summaries with citation, holding, and rule
- **Case Analysis**: Extracts holdings, rules, facts, and reasoning
- **Relevance Analysis**: Evaluates relevance for plaintiffs and defendants
- **Landmark Cases**: Identifies seminal cases in specific areas of law
- **Circuit Analysis**: Analyzes circuit splits and different approaches
- **Case Comparison**: Compares precedents for similarities and differences
- **Confidence Scoring**: Rates extraction quality for each case

**Example Searches:**
```python
# Find specific types of cases
agent.find_precedents(
    "employee downloaded confidential files trade secret",
    jurisdiction="federal",
    num_cases=5
)

# Get landmark cases in an area
landmark_cases = agent.get_landmark_cases("trade secrets", num_cases=10)

# Analyze circuit splits
circuit_cases = agent.analyze_circuit_split("inevitable disclosure doctrine")

# Compare two cases
comparison = agent.compare_precedents("Waymo v. Uber", "E.I. DuPont v. Kolon")
```

Run the PrecedentAgent test:
```bash
python test_precedent_agent.py
```

## Examples

Run comprehensive BaseAgent examples:
```bash
python examples/agent_examples.py
```

Examples include:
1. **Basic Agent**: Simple conversation with system prompt
2. **Tool Usage**: Automatic web search and browser automation
3. **Multi-Agent System**: Agents collaborating on tasks
4. **History Management**: Saving and loading conversations
5. **Async Operations**: Parallel agent processing
6. **Custom Workflows**: Advanced tool combinations

## Project Structure

```
agi-house-hackathon/
├── agents/
│   ├── baseAgent.py         # Main BaseAgent class
│   ├── statuteAgent.py      # Legal statute research agent
│   └── precedentAgent.py    # Case law precedent agent
├── util/
│   ├── perplexity.py        # Perplexity search integration
│   └── browseruse.py        # Browser automation
├── examples/
│   ├── agent_examples.py    # BaseAgent usage examples
│   └── statute_agent_demo.py # StatuteAgent demonstrations
├── test_precedent_agent.py  # PrecedentAgent test script
├── test_statute_comprehensive.py # StatuteAgent comprehensive test
├── requirements.txt         # Dependencies
├── .env                     # API keys (create this)
└── README.md               # Documentation
```

## API Key Sources

- **Gemini**: https://makersuite.google.com/app/apikey
- **Perplexity**: https://www.perplexity.ai/settings/api
- **BrowserUse**: https://browser-use.com

## Requirements

- Python 3.12+
- See `requirements.txt` for package dependencies

## License

MIT
