# MongoDB Integration Documentation

## Overview

This project includes comprehensive MongoDB integration for persisting agent conversations, simulations, and research data. The integration uses MongoDB Atlas and provides automatic persistence, search capabilities, and multi-agent session management.

## Architecture

### Collections

#### 1. `case_simulations`
Stores complete chat histories from agent simulations.

**Schema:**
```javascript
{
  _id: ObjectId,
  case_id: String,              // Unique case identifier
  case_name: String,            // Human-readable case name
  simulation_type: String,      // Type of simulation (negotiation, litigation, etc.)
  agents_involved: [String],    // List of agent names
  chat_history: [{              // Array of messages
    agent_name: String,
    role: String,              // user, assistant, system, tool
    content: String,
    timestamp: DateTime,
    metadata: Object,
    tool_calls: Array
  }],
  status: String,              // pending, in_progress, completed, failed, paused
  created_at: DateTime,
  updated_at: DateTime,
  completed_at: DateTime,
  outcome: String,             // Optional outcome description
  summary: String,             // Optional summary
  metadata: Object             // Additional metadata
}
```

#### 2. `case_research`
Stores research data with links to related simulations.

**Schema:**
```javascript
{
  _id: ObjectId,
  case_id: String,
  case_name: String,
  research_topic: String,
  description: String,
  key_findings: [String],
  legal_precedents: [{
    case: String,
    year: String,
    citation: String,
    relevance: String
  }],
  statutes: [{
    title: String,
    citation: String,
    section: String,
    relevance: String
  }],
  simulation_ids: [ObjectId],    // Links to case_simulations documents
  status: String,                // draft, active, completed, archived
  created_at: DateTime,
  updated_at: DateTime,
  tags: [String],
  metadata: Object
}
```

## Setup

### 1. MongoDB Atlas Configuration

1. Create a MongoDB Atlas account at [https://www.mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster (free tier is sufficient for development)
3. Set up database access (create a database user)
4. Set up network access (whitelist your IP or allow access from anywhere)
5. Get your connection string from the cluster connect dialog

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
# MongoDB Atlas Configuration
MONGODB_CONNECTION_STRING=mongodb+srv://username:password@cluster.mongodb.net/database?retryWrites=true&w=majority

# Other API Keys
GEMINI_API_KEY=your_gemini_api_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here
```

### 3. Installation

The required package is already in `requirements.txt`:
```bash
pip install pymongo>=4.5.0
```

Or if using conda:
```bash
conda install conda-forge::pymongo
```

## Usage

### 1. Basic MongoDB Agent

```python
from agents.mongoAgent import MongoAgent

# Create a MongoDB-integrated agent
agent = MongoAgent(
    name="LegalAdvisor",
    system_prompt="You are a legal advisor specializing in trade secrets.",
    case_id="CASE-2024-001",
    case_name="TechCorp v. StartupInc",
    simulation_type="consultation"
)

# Chat with the agent (automatically saved to MongoDB)
response = agent.chat("What are the key elements of a trade secret?")

# Create research entry
research_id = agent.create_research_entry(
    research_topic="Trade Secret Elements",
    description="Research on trade secret requirements",
    key_findings=["Economic value", "Reasonable efforts", "Not publicly known"]
)

# Complete and save simulation
agent.complete_simulation(
    outcome="Consultation completed",
    summary="Discussed trade secret elements"
)
```

### 2. Multi-Agent Session

```python
from agents.mongoAgent import MongoMultiAgentSession, MongoAgent

# Create a multi-agent session
session = MongoMultiAgentSession(
    case_id="CASE-2024-002",
    case_name="Settlement Negotiation",
    simulation_type="negotiation"
)

# Create agents
lawyer = MongoAgent(name="Lawyer", mongodb_enabled=False)
negotiator = MongoAgent(name="Negotiator", mongodb_enabled=False)

# Add agents to session
session.add_agent(lawyer)
session.add_agent(negotiator)

# Agent interaction (automatically saved)
response = session.agent_interaction(
    from_agent="Lawyer",
    to_agent="Negotiator",
    message="We need to discuss settlement terms."
)

# Broadcast to all agents
responses = session.broadcast_message("What are your thoughts on $1M settlement?")

# Complete session
session.complete_session(outcome="Agreement reached")
```

### 3. Direct Database Operations

```python
from database.mongodb_manager import MongoDBManager, SimulationStatus

db = MongoDBManager()

# Search simulations
simulations = db.search_simulations(
    case_name="TechCorp",
    status=SimulationStatus.COMPLETED,
    limit=10
)

# Get case summary
summary = db.get_case_summary("CASE-2024-001")

# Link simulation to research
db.link_simulation_to_research(research_id, simulation_id)

# Get statistics
stats = db.get_statistics()

db.close()
```

## Key Features

### Automatic Persistence
- Agents automatically save chat history to MongoDB
- Configurable save frequency (every N messages)
- Automatic status tracking

### Research Management
- Create research entries with key findings
- Link multiple simulations to research
- Tag-based organization
- Legal precedent and statute tracking

### Multi-Agent Support
- Coordinated multi-agent sessions
- Shared simulation context
- Inter-agent communication tracking
- Broadcast messaging

### Search and Retrieval
- Search by case name, agent, status, date range
- Full-text search in chat histories
- Filter by tags and metadata
- Aggregation queries

### Data Relationships
- Research entries link to multiple simulations
- Simulations track all participating agents
- Complete audit trail of conversations
- Case-level aggregation

## API Reference

### MongoAgent Class

#### Methods
- `chat(message)` - Send message and save to MongoDB
- `save_simulation(status)` - Manually save current state
- `complete_simulation(outcome, summary)` - Mark simulation complete
- `create_research_entry(...)` - Create linked research
- `link_to_research(research_id)` - Link to existing research
- `get_simulation_summary()` - Get current simulation info
- `load_simulation(simulation_id)` - Load existing simulation
- `get_case_context()` - Get all case data

### MongoDBManager Class

#### Simulation Operations
- `save_simulation(simulation)` - Save or update simulation
- `get_simulation(simulation_id)` - Retrieve by ID
- `get_simulations_by_case(case_id)` - Get case simulations
- `update_simulation_status(...)` - Update status
- `add_message_to_simulation(...)` - Add message
- `search_simulations(...)` - Search with filters

#### Research Operations
- `save_research(research)` - Save or update research
- `get_research(research_id)` - Retrieve by ID
- `get_research_by_case(case_id)` - Get case research
- `link_simulation_to_research(...)` - Create link
- `get_linked_simulations(research_id)` - Get linked sims
- `search_research(...)` - Search with filters

#### Aggregation Operations
- `get_case_summary(case_id)` - Complete case overview
- `get_statistics()` - Database statistics

## Examples

### Run the Demo
```bash
python examples/mongodb_integration_demo.py
```

This will demonstrate:
1. Single agent simulation with MongoDB
2. Multi-agent negotiation session
3. Database queries and operations
4. Advanced agent integration

## Best Practices

### 1. Case Organization
- Use consistent case IDs across simulations
- Group related simulations under same case
- Tag research for easy retrieval

### 2. Performance
- Use indexes (automatically created)
- Limit search results appropriately
- Save simulations periodically, not after every message

### 3. Data Management
- Complete simulations properly
- Add summaries and outcomes
- Link research to simulations
- Clean up old simulations periodically

### 4. Error Handling
- MongoDB connection is optional (agents work without it)
- Graceful fallback if connection fails
- Automatic reconnection attempts

## Troubleshooting

### Connection Issues
```python
# Test connection
from database.mongodb_manager import MongoDBManager
db = MongoDBManager()
db.client.admin.command('ping')  # Should not raise exception
```

### Common Errors

1. **"MongoDB connection string not provided"**
   - Set `MONGODB_CONNECTION_STRING` in `.env` file

2. **"Failed to connect to MongoDB"**
   - Check connection string format
   - Verify network access settings in Atlas
   - Ensure cluster is running

3. **"Authentication failed"**
   - Verify username and password
   - Check database user permissions

### Debug Mode
```python
# Enable detailed logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

1. **Connection String**: Never commit connection strings to version control
2. **Network Access**: Use IP whitelisting in production
3. **User Permissions**: Create users with minimal required permissions
4. **Data Encryption**: MongoDB Atlas provides encryption at rest
5. **Backup**: Enable automatic backups in Atlas

## Performance Optimization

### Indexes
The following indexes are automatically created:
- `case_id` (ascending)
- `case_name` (ascending)
- `status` (ascending)
- `created_at` (descending)
- `agents_involved` (ascending)
- `tags` (ascending)
- `simulation_ids` (ascending)

### Query Optimization
- Use specific field queries instead of full-text search
- Limit result sets with `limit` parameter
- Use date ranges to narrow searches
- Leverage indexes in query patterns

## Future Enhancements

Potential improvements:
- Real-time collaboration with change streams
- Advanced analytics dashboard
- Automatic summarization of long simulations
- Export to various formats (PDF, Word)
- Integration with vector databases for semantic search
- Automated backup and archival policies

## Support

For issues or questions:
1. Check this documentation
2. Review example code in `examples/mongodb_integration_demo.py`
3. Check MongoDB Atlas documentation
4. Review pymongo documentation at [https://pymongo.readthedocs.io/](https://pymongo.readthedocs.io/)
