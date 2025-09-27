"""
MongoDB Integration Demo
Demonstrates the complete MongoDB integration with agent system.
Shows how to:
1. Create simulations with agent chat histories
2. Create and link research entries
3. Run multi-agent simulations
4. Search and retrieve data from MongoDB
"""

import os
import sys
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.mongoAgent import MongoAgent, MongoMultiAgentSession
from agents.precedentAgent import PrecedentAgent
from agents.statuteAgent import StatuteAgent
from database.mongodb_manager import (
    MongoDBManager,
    SimulationStatus,
    ResearchStatus,
    CaseResearch,
    AgentMessage
)
from dotenv import load_dotenv

load_dotenv()


def demo_single_agent_simulation():
    """Demonstrate single agent simulation with MongoDB."""
    print("\n" + "="*80)
    print("DEMO 1: Single Agent Simulation with MongoDB")
    print("="*80)
    
    # Create a MongoDB-integrated agent
    legal_agent = MongoAgent(
        name="LegalResearchAgent",
        system_prompt="""You are a senior legal researcher specializing in intellectual property 
        and trade secret law. Provide detailed analysis and cite relevant cases.""",
        case_id="WAYMO-V-UBER-2024",
        case_name="Waymo v. Uber - Trade Secret Misappropriation",
        simulation_type="legal_research",
        save_frequency=2  # Save every 2 messages
    )
    
    print(f"\n✓ Created agent: {legal_agent.name}")
    print(f"  Case: {legal_agent.case_name}")
    print(f"  Simulation ID: {legal_agent.current_simulation_id}")
    
    # Conduct research conversation
    queries = [
        "What are the key elements required to prove trade secret misappropriation?",
        "Find precedents similar to Waymo v. Uber involving autonomous vehicle technology",
        "What remedies are available for trade secret misappropriation under federal law?"
    ]
    
    print("\n📝 Conducting legal research...")
    for i, query in enumerate(queries, 1):
        print(f"\n  Query {i}: {query[:60]}...")
        response = legal_agent.chat(query)
        print(f"  Response preview: {response[:150]}...")
    
    # Create a research entry linking to this simulation
    print("\n📚 Creating research entry...")
    research_id = legal_agent.create_research_entry(
        research_topic="Trade Secret Misappropriation in Autonomous Vehicle Industry",
        description="Analysis of trade secret claims in the context of self-driving car technology",
        key_findings=[
            "Trade secrets must derive economic value from secrecy",
            "Reasonable efforts to maintain secrecy are required",
            "Waymo v. Uber established precedent for AV trade secrets",
            "Injunctive relief is commonly granted in clear misappropriation cases"
        ],
        legal_precedents=[
            {
                "case": "Waymo LLC v. Uber Technologies, Inc.",
                "year": "2018",
                "citation": "No. 3:17-cv-00939 (N.D. Cal.)",
                "relevance": "Direct precedent for autonomous vehicle trade secrets"
            },
            {
                "case": "E.I. DuPont de Nemours & Co. v. Kolon Industries",
                "year": "2011",
                "citation": "637 F.3d 435 (4th Cir. 2011)",
                "relevance": "Standards for proving trade secret misappropriation"
            }
        ],
        statutes=[
            {
                "title": "Defend Trade Secrets Act",
                "citation": "18 U.S.C. § 1836",
                "relevance": "Federal cause of action for trade secret misappropriation"
            },
            {
                "title": "Economic Espionage Act",
                "citation": "18 U.S.C. § 1831-1839",
                "relevance": "Criminal penalties for trade secret theft"
            }
        ],
        tags=["trade_secrets", "autonomous_vehicles", "waymo", "uber", "misappropriation"]
    )
    
    print(f"  ✓ Research entry created with ID: {research_id}")
    
    # Complete the simulation
    legal_agent.complete_simulation(
        outcome="Successfully completed legal research on trade secret misappropriation",
        summary="Analyzed key elements, precedents, and remedies for trade secret claims in AV industry"
    )
    
    print("\n✓ Simulation completed and saved to MongoDB")
    
    # Get simulation summary
    summary = legal_agent.get_simulation_summary()
    print(f"\n📊 Simulation Summary:")
    print(f"  - Total messages: {summary['total_messages']}")
    print(f"  - Status: {summary['status']}")
    print(f"  - Outcome: {summary.get('outcome', 'N/A')[:100]}...")
    
    return legal_agent.current_simulation_id, research_id


def demo_multi_agent_negotiation():
    """Demonstrate multi-agent negotiation session."""
    print("\n" + "="*80)
    print("DEMO 2: Multi-Agent Negotiation Session")
    print("="*80)
    
    # Create a multi-agent session
    session = MongoMultiAgentSession(
        case_id="TECHCORP-V-STARTUP-2024",
        case_name="TechCorp v. StartupInc - Settlement Negotiation",
        simulation_type="settlement_negotiation"
    )
    
    print(f"\n✓ Created multi-agent session")
    print(f"  Case: {session.case_name}")
    print(f"  Simulation ID: {session.simulation_id}")
    
    # Create specialized agents
    plaintiff_lawyer = MongoAgent(
        name="PlaintiffLawyer",
        system_prompt="""You represent TechCorp in a trade secret misappropriation case. 
        Your client claims StartupInc stole proprietary algorithms. 
        Seek maximum damages but be open to reasonable settlement.""",
        mongodb_enabled=False  # Session handles MongoDB
    )
    
    defendant_lawyer = MongoAgent(
        name="DefendantLawyer",
        system_prompt="""You represent StartupInc accused of trade secret theft. 
        Your client denies all allegations. Minimize liability and protect your client's reputation.""",
        mongodb_enabled=False
    )
    
    mediator = MongoAgent(
        name="Mediator",
        system_prompt="""You are a neutral mediator helping both parties reach a fair settlement. 
        Focus on finding common ground and creative solutions.""",
        mongodb_enabled=False
    )
    
    # Add agents to session
    session.add_agent(plaintiff_lawyer)
    session.add_agent(defendant_lawyer)
    session.add_agent(mediator)
    
    print("\n👥 Agents in session:")
    for agent_name in session.agents.keys():
        print(f"  - {agent_name}")
    
    # Conduct negotiation
    print("\n💬 Starting negotiation...")
    
    # Mediator opens the session
    print("\n  [Mediator → All]")
    opening = "Welcome to the mediation. Let's start by having each party state their position."
    responses = session.broadcast_message(opening, sender="Mediator")
    for agent, response in responses.items():
        print(f"    {agent}: {response[:100]}...")
    
    # Plaintiff makes initial demand
    print("\n  [PlaintiffLawyer → DefendantLawyer]")
    demand_response = session.agent_interaction(
        from_agent="PlaintiffLawyer",
        to_agent="DefendantLawyer",
        message="We seek $10 million in damages plus an injunction preventing use of our algorithms."
    )
    print(f"    DefendantLawyer: {demand_response[:150]}...")
    
    # Mediator facilitates
    print("\n  [Mediator → All]")
    facilitation = "I see there's a significant gap. Let's explore what a middle ground might look like."
    responses = session.broadcast_message(facilitation, sender="Mediator")
    for agent, response in responses.items():
        print(f"    {agent}: {response[:100]}...")
    
    # Complete the session
    session.complete_session(
        outcome="Parties agreed to continue settlement discussions",
        summary="Initial positions exchanged, significant gap identified, further negotiations scheduled"
    )
    
    print("\n✓ Negotiation session completed and saved")
    
    # Get session summary
    summary = session.get_session_summary()
    print(f"\n📊 Session Summary:")
    print(f"  - Agents involved: {', '.join(summary['agents'])}")
    print(f"  - Total messages: {summary['total_messages']}")
    print(f"  - Status: {summary['status']}")
    
    return session.simulation_id


def demo_database_operations():
    """Demonstrate direct database operations and queries."""
    print("\n" + "="*80)
    print("DEMO 3: Database Operations and Queries")
    print("="*80)
    
    # Initialize database manager
    db = MongoDBManager()
    
    # Get database statistics
    print("\n📈 Database Statistics:")
    stats = db.get_statistics()
    print(f"  - Total simulations: {stats['total_simulations']}")
    print(f"  - Total research entries: {stats['total_research_entries']}")
    print(f"  - Database size: {stats['database_size']:,} bytes")
    
    # Search simulations
    print("\n🔍 Searching for recent simulations...")
    recent_simulations = db.search_simulations(
        status=SimulationStatus.COMPLETED,
        limit=5
    )
    
    if recent_simulations:
        print(f"  Found {len(recent_simulations)} completed simulations:")
        for sim in recent_simulations[:3]:
            print(f"    - {sim.case_name}: {sim.simulation_type} ({len(sim.chat_history)} messages)")
    else:
        print("  No completed simulations found")
    
    # Search research entries
    print("\n🔍 Searching for research entries...")
    research_entries = db.search_research(
        tags=["trade_secrets"],
        has_simulations=True,
        limit=5
    )
    
    if research_entries:
        print(f"  Found {len(research_entries)} research entries with 'trade_secrets' tag:")
        for research in research_entries[:3]:
            print(f"    - {research.research_topic}")
            print(f"      Linked simulations: {len(research.simulation_ids)}")
    else:
        print("  No research entries found with specified criteria")
    
    # Get case summary for a specific case
    print("\n📋 Case Summary for WAYMO-V-UBER-2024:")
    try:
        case_summary = db.get_case_summary("WAYMO-V-UBER-2024")
        if case_summary['total_simulations'] > 0 or case_summary['total_research_entries'] > 0:
            print(f"  - Total simulations: {case_summary['total_simulations']}")
            print(f"  - Total research entries: {case_summary['total_research_entries']}")
            print(f"  - Total messages: {case_summary['total_messages']}")
            print(f"  - Agents involved: {', '.join(case_summary['agents_involved'][:5])}")
        else:
            print("  No data found for this case")
    except Exception as e:
        print(f"  Error getting case summary: {e}")
    
    # Close database connection
    db.close()
    print("\n✓ Database connection closed")


def demo_advanced_agent_integration():
    """Demonstrate integration with specialized agents (PrecedentAgent, StatuteAgent)."""
    print("\n" + "="*80)
    print("DEMO 4: Advanced Agent Integration with MongoDB")
    print("="*80)
    
    # Create a comprehensive legal research session
    session = MongoMultiAgentSession(
        case_id="COMPREHENSIVE-RESEARCH-2024",
        case_name="Comprehensive Legal Research - Trade Secrets",
        simulation_type="legal_research_team"
    )
    
    print(f"\n✓ Created research team session")
    print(f"  Simulation ID: {session.simulation_id}")
    
    # Create specialized MongoDB agents that will use the other tools
    precedent_researcher = MongoAgent(
        name="PrecedentResearcher",
        system_prompt="""You are a legal researcher specializing in finding case precedents. 
        Use your knowledge to find and analyze relevant cases.""",
        mongodb_enabled=False,
        enable_tools=True
    )
    
    statute_researcher = MongoAgent(
        name="StatuteResearcher",
        system_prompt="""You are a legal researcher specializing in statutory law. 
        Find and analyze relevant statutes and regulations.""",
        mongodb_enabled=False,
        enable_tools=True
    )
    
    lead_researcher = MongoAgent(
        name="LeadResearcher",
        system_prompt="""You are the lead legal researcher coordinating the research team. 
        Synthesize findings from precedent and statute research.""",
        mongodb_enabled=False
    )
    
    # Add agents to session
    session.add_agent(precedent_researcher)
    session.add_agent(statute_researcher)
    session.add_agent(lead_researcher)
    
    print("\n👥 Research team assembled:")
    for agent_name in session.agents.keys():
        print(f"  - {agent_name}")
    
    # Conduct coordinated research
    print("\n🔬 Conducting coordinated research...")
    
    # Lead researcher assigns tasks
    print("\n  [LeadResearcher → All]")
    assignment = """We need comprehensive research on trade secret misappropriation. 
    PrecedentResearcher: Find key cases about employee theft of trade secrets.
    StatuteResearcher: Identify relevant federal and state statutes."""
    
    responses = session.broadcast_message(assignment, sender="LeadResearcher")
    for agent, response in responses.items():
        print(f"    {agent}: {response[:100]}...")
    
    # Get precedent research
    print("\n  [PrecedentResearcher → LeadResearcher]")
    precedent_report = session.agent_interaction(
        from_agent="PrecedentResearcher",
        to_agent="LeadResearcher",
        message="I found several key precedents including Waymo v. Uber and DuPont v. Kolon that establish..."
    )
    print(f"    LeadResearcher: {precedent_report[:150]}...")
    
    # Get statute research
    print("\n  [StatuteResearcher → LeadResearcher]")
    statute_report = session.agent_interaction(
        from_agent="StatuteResearcher",
        to_agent="LeadResearcher",
        message="The Defend Trade Secrets Act (18 U.S.C. § 1836) provides federal cause of action..."
    )
    print(f"    LeadResearcher: {statute_report[:150]}...")
    
    # Complete the research session
    session.complete_session(
        outcome="Comprehensive research completed",
        summary="Team identified key precedents and statutes for trade secret case"
    )
    
    print("\n✓ Research team session completed")
    
    # Create a research entry in the database
    db = MongoDBManager()
    
    research = CaseResearch(
        case_id=session.case_id,
        case_name=session.case_name,
        research_topic="Comprehensive Trade Secret Law Analysis",
        description="Multi-agent research on trade secret misappropriation law",
        key_findings=[
            "Waymo v. Uber established clear standards for AV trade secrets",
            "DTSA provides federal cause of action with ex parte seizure remedy",
            "Economic value and reasonable efforts are key elements",
            "Criminal penalties available under Economic Espionage Act"
        ],
        legal_precedents=[
            {"case": "Waymo v. Uber", "year": "2018", "relevance": "AV trade secrets"},
            {"case": "DuPont v. Kolon", "year": "2011", "relevance": "Misappropriation standards"}
        ],
        statutes=[
            {"title": "DTSA", "citation": "18 U.S.C. § 1836"},
            {"title": "EEA", "citation": "18 U.S.C. § 1831-1839"}
        ],
        simulation_ids=[session.simulation_id],
        tags=["comprehensive", "multi_agent", "trade_secrets"]
    )
    
    research_id = db.save_research(research)
    print(f"\n📚 Created comprehensive research entry: {research_id}")
    
    db.close()
    
    return session.simulation_id


def main():
    """Run all demonstrations."""
    print("\n" + "🚀 " + "="*76 + " 🚀")
    print("           MONGODB INTEGRATION DEMONSTRATION")
    print("🚀 " + "="*76 + " 🚀")
    
    try:
        # Check MongoDB connection
        print("\n🔌 Testing MongoDB connection...")
        db = MongoDBManager()
        db.client.admin.command('ping')
        print("✓ Successfully connected to MongoDB Atlas")
        db.close()
        
        # Run demonstrations
        sim_id1, research_id1 = demo_single_agent_simulation()
        sim_id2 = demo_multi_agent_negotiation()
        demo_database_operations()
        sim_id3 = demo_advanced_agent_integration()
        
        # Final summary
        print("\n" + "="*80)
        print("DEMONSTRATION COMPLETE")
        print("="*80)
        print("\n📝 Created during this demo:")
        print(f"  - Single agent simulation: {sim_id1}")
        print(f"  - Research entry: {research_id1}")
        print(f"  - Multi-agent negotiation: {sim_id2}")
        print(f"  - Research team simulation: {sim_id3}")
        
        print("\n💡 Next steps:")
        print("  1. Check MongoDB Atlas to view the created collections and documents")
        print("  2. Use MongoAgent for any agent that needs persistence")
        print("  3. Use MongoMultiAgentSession for coordinated multi-agent scenarios")
        print("  4. Query and analyze historical simulations using MongoDBManager")
        
        print("\n✨ MongoDB integration is fully operational!")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        print("\n⚠️  Make sure:")
        print("  1. MongoDB Atlas is configured and running")
        print("  2. MONGODB_CONNECTION_STRING is set in .env file")
        print("  3. The connection string has proper permissions")
        print("\n📝 Example .env entry:")
        print('  MONGODB_CONNECTION_STRING="mongodb+srv://user:pass@cluster.mongodb.net/dbname?retryWrites=true"')


if __name__ == "__main__":
    main()
