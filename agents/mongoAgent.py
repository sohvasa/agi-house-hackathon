"""
MongoDB-Integrated Agent - Extends BaseAgent with MongoDB persistence capabilities.
Automatically saves agent conversations to MongoDB and links them to research entries.
"""

import os
import sys
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from bson import ObjectId

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from agents.baseAgent import BaseAgent, Message, MessageRole
from database.mongodb_manager import (
    MongoDBManager, 
    CaseSimulation, 
    CaseResearch,
    AgentMessage,
    SimulationStatus,
    ResearchStatus
)


class MongoAgent(BaseAgent):
    """
    Extended agent class with MongoDB integration.
    Automatically persists conversations to MongoDB and manages case simulations.
    """
    
    def __init__(self,
                 name: str,
                 system_prompt: str = "",
                 model_name: str = "gemini-2.5-flash",
                 temperature: float = 0.7,
                 max_output_tokens: int = 2048,
                 enable_tools: bool = True,
                 auto_execute_tools: bool = True,
                 memory_limit: Optional[int] = None,
                 # MongoDB specific parameters
                 mongodb_enabled: bool = True,
                 case_id: Optional[str] = None,
                 case_name: Optional[str] = None,
                 simulation_type: str = "general",
                 auto_save: bool = True,
                 save_frequency: int = 5):  # Save every N messages
        """
        Initialize MongoDB-integrated agent.
        
        Args:
            name: Agent identifier name
            system_prompt: Initial system prompt for the agent
            model_name: Gemini model to use
            temperature: Sampling temperature
            max_output_tokens: Maximum tokens in response
            enable_tools: Whether to enable tool calling
            auto_execute_tools: Whether to automatically execute tool calls
            memory_limit: Maximum number of messages to keep in history
            mongodb_enabled: Whether to enable MongoDB integration
            case_id: ID of the case this simulation belongs to
            case_name: Name of the case
            simulation_type: Type of simulation (negotiation, litigation, etc.)
            auto_save: Whether to automatically save to MongoDB
            save_frequency: How often to save (every N messages)
        """
        # Initialize base agent
        super().__init__(
            name=name,
            system_prompt=system_prompt,
            model_name=model_name,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            enable_tools=enable_tools,
            auto_execute_tools=auto_execute_tools,
            memory_limit=memory_limit
        )
        
        # MongoDB integration
        self.mongodb_enabled = mongodb_enabled
        self.case_id = case_id or f"CASE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.case_name = case_name or f"Case {self.case_id}"
        self.simulation_type = simulation_type
        self.auto_save = auto_save
        self.save_frequency = save_frequency
        
        # Initialize MongoDB connection if enabled
        self.db_manager = None
        self.current_simulation = None
        self.current_simulation_id = None
        self.message_count_since_save = 0
        
        if mongodb_enabled:
            try:
                self.db_manager = MongoDBManager()
                self._initialize_simulation()
            except Exception as e:
                print(f"Warning: Could not connect to MongoDB: {e}")
                print("Continuing without MongoDB integration.")
                self.mongodb_enabled = False
    
    def _initialize_simulation(self):
        """Initialize a new simulation in MongoDB."""
        if not self.db_manager:
            return
        
        self.current_simulation = CaseSimulation(
            case_id=self.case_id,
            case_name=self.case_name,
            simulation_type=self.simulation_type,
            agents_involved=[self.name],
            chat_history=[],
            status=SimulationStatus.IN_PROGRESS,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={
                "model": self.model_name,
                "temperature": self.temperature,
                "system_prompt": self.system_prompt[:500] if self.system_prompt else None
            }
        )
        
        # Save initial simulation
        self.current_simulation_id = self.db_manager.save_simulation(self.current_simulation)
        print(f"Created new simulation with ID: {self.current_simulation_id}")
    
    def _save_message_to_mongodb(self, message: Message):
        """Save a message to MongoDB."""
        if not self.mongodb_enabled or not self.db_manager:
            return
        
        # Convert to MongoDB AgentMessage
        agent_message = AgentMessage(
            agent_name=self.name,
            role=message.role.value,
            content=message.content,
            timestamp=message.timestamp,
            metadata=message.metadata,
            tool_calls=message.tool_calls
        )
        
        # Add to current simulation
        if self.current_simulation:
            self.current_simulation.chat_history.append(agent_message)
            self.message_count_since_save += 1
            
            # Auto-save if needed
            if self.auto_save and self.message_count_since_save >= self.save_frequency:
                self.save_simulation()
    
    def _add_message(self,
                    role: MessageRole,
                    content: str,
                    metadata: Optional[Dict[str, Any]] = None,
                    tool_calls: Optional[List[Dict[str, Any]]] = None,
                    tool_call_id: Optional[str] = None):
        """Override to add MongoDB persistence."""
        # Call parent method first
        super()._add_message(role, content, metadata, tool_calls, tool_call_id)
        
        # Save to MongoDB if enabled
        if self.mongodb_enabled:
            # Get the last message added
            last_message = self.chat_history[-1] if self.chat_history else None
            if last_message:
                self._save_message_to_mongodb(last_message)
    
    def save_simulation(self, status: Optional[SimulationStatus] = None) -> Optional[ObjectId]:
        """
        Manually save the current simulation to MongoDB.
        
        Args:
            status: Optional status update for the simulation
            
        Returns:
            ObjectId of the saved simulation or None
        """
        if not self.mongodb_enabled or not self.db_manager or not self.current_simulation:
            return None
        
        if status:
            self.current_simulation.status = status
            if status == SimulationStatus.COMPLETED:
                self.current_simulation.completed_at = datetime.now()
        
        self.current_simulation.updated_at = datetime.now()
        
        # Save to MongoDB
        sim_id = self.db_manager.save_simulation(self.current_simulation)
        self.message_count_since_save = 0
        
        print(f"Saved simulation to MongoDB (ID: {sim_id})")
        return sim_id
    
    def complete_simulation(self, outcome: Optional[str] = None, summary: Optional[str] = None):
        """
        Mark the simulation as completed and save final state.
        
        Args:
            outcome: Description of the simulation outcome
            summary: Summary of the simulation
        """
        if not self.mongodb_enabled or not self.db_manager:
            return
        
        if outcome:
            self.current_simulation.outcome = outcome
        if summary:
            self.current_simulation.summary = summary
        
        self.save_simulation(status=SimulationStatus.COMPLETED)
        print(f"Simulation completed and saved to MongoDB")
    
    def link_to_research(self, research_id: Union[str, ObjectId]) -> bool:
        """
        Link this simulation to a research entry.
        
        Args:
            research_id: ID of the research entry to link to
            
        Returns:
            True if linking successful
        """
        if not self.mongodb_enabled or not self.db_manager or not self.current_simulation_id:
            return False
        
        success = self.db_manager.link_simulation_to_research(
            research_id, 
            self.current_simulation_id
        )
        
        if success:
            print(f"Linked simulation to research ID: {research_id}")
        
        return success
    
    def create_research_entry(self,
                            research_topic: str,
                            description: str,
                            key_findings: List[str],
                            legal_precedents: Optional[List[Dict[str, Any]]] = None,
                            statutes: Optional[List[Dict[str, Any]]] = None,
                            tags: Optional[List[str]] = None) -> Optional[ObjectId]:
        """
        Create a new research entry and link current simulation to it.
        
        Args:
            research_topic: Topic of the research
            description: Description of the research
            key_findings: List of key findings
            legal_precedents: Optional list of legal precedents
            statutes: Optional list of statutes
            tags: Optional tags for categorization
            
        Returns:
            ObjectId of the created research entry or None
        """
        if not self.mongodb_enabled or not self.db_manager:
            return None
        
        research = CaseResearch(
            case_id=self.case_id,
            case_name=self.case_name,
            research_topic=research_topic,
            description=description,
            key_findings=key_findings,
            legal_precedents=legal_precedents or [],
            statutes=statutes or [],
            simulation_ids=[self.current_simulation_id] if self.current_simulation_id else [],
            tags=tags or []
        )
        
        research_id = self.db_manager.save_research(research)
        print(f"Created research entry with ID: {research_id}")
        
        return research_id
    
    def get_simulation_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the current simulation.
        
        Returns:
            Dictionary containing simulation summary
        """
        if not self.current_simulation:
            return {"error": "No active simulation"}
        
        summary = {
            "simulation_id": str(self.current_simulation_id) if self.current_simulation_id else None,
            "case_id": self.case_id,
            "case_name": self.case_name,
            "simulation_type": self.simulation_type,
            "status": self.current_simulation.status.value,
            "agents_involved": self.current_simulation.agents_involved,
            "total_messages": len(self.current_simulation.chat_history),
            "created_at": self.current_simulation.created_at.isoformat(),
            "updated_at": self.current_simulation.updated_at.isoformat()
        }
        
        if self.current_simulation.outcome:
            summary["outcome"] = self.current_simulation.outcome
        if self.current_simulation.summary:
            summary["summary"] = self.current_simulation.summary
        
        return summary
    
    def load_simulation(self, simulation_id: Union[str, ObjectId]) -> bool:
        """
        Load an existing simulation from MongoDB.
        
        Args:
            simulation_id: ID of the simulation to load
            
        Returns:
            True if loading successful
        """
        if not self.mongodb_enabled or not self.db_manager:
            return False
        
        simulation = self.db_manager.get_simulation(simulation_id)
        if not simulation:
            print(f"Simulation {simulation_id} not found")
            return False
        
        # Set current simulation
        self.current_simulation = simulation
        self.current_simulation_id = simulation._id
        self.case_id = simulation.case_id
        self.case_name = simulation.case_name
        self.simulation_type = simulation.simulation_type
        
        # Restore chat history
        self.chat_history = []
        for agent_msg in simulation.chat_history:
            message = Message(
                role=MessageRole(agent_msg.role),
                content=agent_msg.content,
                timestamp=agent_msg.timestamp,
                metadata=agent_msg.metadata,
                tool_calls=agent_msg.tool_calls
            )
            self.chat_history.append(message)
        
        print(f"Loaded simulation {simulation_id} with {len(self.chat_history)} messages")
        return True
    
    def search_related_simulations(self, 
                                  limit: int = 5) -> List[CaseSimulation]:
        """
        Search for related simulations in the same case.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of related simulations
        """
        if not self.mongodb_enabled or not self.db_manager:
            return []
        
        return self.db_manager.search_simulations(
            case_name=self.case_name,
            limit=limit
        )
    
    def get_case_context(self) -> Dict[str, Any]:
        """
        Get full context for the current case including all simulations and research.
        
        Returns:
            Dictionary containing case context
        """
        if not self.mongodb_enabled or not self.db_manager:
            return {"error": "MongoDB not enabled"}
        
        return self.db_manager.get_case_summary(self.case_id)
    
    def export_to_json(self, filepath: str):
        """
        Export current simulation to JSON file.
        
        Args:
            filepath: Path to save the JSON file
        """
        import json
        
        export_data = {
            "simulation": self.get_simulation_summary(),
            "chat_history": [msg.to_dict() for msg in self.chat_history],
            "case_context": self.get_case_context() if self.mongodb_enabled else None
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"Exported simulation to {filepath}")
    
    def __del__(self):
        """Cleanup on deletion - save any pending changes and close connection."""
        if self.mongodb_enabled and self.db_manager:
            # Save any pending messages
            if self.message_count_since_save > 0:
                self.save_simulation()
            
            # Close MongoDB connection
            self.db_manager.close()
    
    def __repr__(self) -> str:
        mongo_status = "MongoDB-enabled" if self.mongodb_enabled else "MongoDB-disabled"
        return f"MongoAgent(name='{self.name}', model='{self.model_name}', {mongo_status}, case='{self.case_name}')"


# Multi-agent collaboration with MongoDB persistence
class MongoMultiAgentSession:
    """
    Manages a multi-agent session with MongoDB persistence.
    All agents in the session share the same case and simulation.
    """
    
    def __init__(self,
                 case_id: Optional[str] = None,
                 case_name: Optional[str] = None,
                 simulation_type: str = "multi_agent_collaboration"):
        """
        Initialize a multi-agent session.
        
        Args:
            case_id: ID of the case
            case_name: Name of the case
            simulation_type: Type of simulation
        """
        self.case_id = case_id or f"CASE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.case_name = case_name or f"Case {self.case_id}"
        self.simulation_type = simulation_type
        
        # Initialize MongoDB manager
        self.db_manager = MongoDBManager()
        
        # Initialize simulation
        self.simulation = CaseSimulation(
            case_id=self.case_id,
            case_name=self.case_name,
            simulation_type=self.simulation_type,
            agents_involved=[],
            chat_history=[],
            status=SimulationStatus.IN_PROGRESS,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        self.simulation_id = self.db_manager.save_simulation(self.simulation)
        self.agents: Dict[str, MongoAgent] = {}
        
        print(f"Created multi-agent session with simulation ID: {self.simulation_id}")
    
    def add_agent(self, agent: MongoAgent):
        """
        Add an agent to the session.
        
        Args:
            agent: MongoAgent to add to the session
        """
        # Configure agent for this session
        agent.case_id = self.case_id
        agent.case_name = self.case_name
        agent.current_simulation = self.simulation
        agent.current_simulation_id = self.simulation_id
        agent.db_manager = self.db_manager
        
        # Add to agents dictionary
        self.agents[agent.name] = agent
        
        # Update simulation with new agent
        if agent.name not in self.simulation.agents_involved:
            self.simulation.agents_involved.append(agent.name)
            self.db_manager.save_simulation(self.simulation)
        
        print(f"Added agent '{agent.name}' to session")
    
    def agent_interaction(self,
                         from_agent: str,
                         to_agent: str,
                         message: str) -> str:
        """
        Have one agent send a message to another.
        
        Args:
            from_agent: Name of sending agent
            to_agent: Name of receiving agent
            message: Message to send
            
        Returns:
            Response from the receiving agent
        """
        if from_agent not in self.agents or to_agent not in self.agents:
            return "Error: Agent not found in session"
        
        sender = self.agents[from_agent]
        receiver = self.agents[to_agent]
        
        # Log sender's message
        sender_msg = AgentMessage(
            agent_name=from_agent,
            role="assistant",
            content=f"To {to_agent}: {message}",
            timestamp=datetime.now(),
            metadata={"interaction_type": "agent_to_agent", "target": to_agent}
        )
        self.simulation.chat_history.append(sender_msg)
        
        # Get response from receiver
        response = receiver.chat(f"Message from {from_agent}: {message}")
        
        # Log receiver's response
        receiver_msg = AgentMessage(
            agent_name=to_agent,
            role="assistant",
            content=response,
            timestamp=datetime.now(),
            metadata={"interaction_type": "agent_response", "responding_to": from_agent}
        )
        self.simulation.chat_history.append(receiver_msg)
        
        # Save to MongoDB
        self.db_manager.save_simulation(self.simulation)
        
        return response
    
    def broadcast_message(self, message: str, sender: Optional[str] = None) -> Dict[str, str]:
        """
        Broadcast a message to all agents.
        
        Args:
            message: Message to broadcast
            sender: Optional sender name
            
        Returns:
            Dictionary of responses from all agents
        """
        responses = {}
        
        for agent_name, agent in self.agents.items():
            if agent_name == sender:
                continue
            
            # Get response from agent
            response = agent.chat(message)
            responses[agent_name] = response
            
            # Log to simulation
            msg = AgentMessage(
                agent_name=agent_name,
                role="assistant",
                content=response,
                timestamp=datetime.now(),
                metadata={"interaction_type": "broadcast_response"}
            )
            self.simulation.chat_history.append(msg)
        
        # Save to MongoDB
        self.db_manager.save_simulation(self.simulation)
        
        return responses
    
    def complete_session(self, outcome: Optional[str] = None, summary: Optional[str] = None):
        """
        Complete the multi-agent session.
        
        Args:
            outcome: Outcome of the session
            summary: Summary of the session
        """
        self.simulation.status = SimulationStatus.COMPLETED
        self.simulation.completed_at = datetime.now()
        
        if outcome:
            self.simulation.outcome = outcome
        if summary:
            self.simulation.summary = summary
        
        self.db_manager.save_simulation(self.simulation)
        print(f"Session completed and saved to MongoDB")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the session.
        
        Returns:
            Dictionary containing session summary
        """
        return {
            "simulation_id": str(self.simulation_id),
            "case_id": self.case_id,
            "case_name": self.case_name,
            "agents": list(self.agents.keys()),
            "total_messages": len(self.simulation.chat_history),
            "status": self.simulation.status.value,
            "created_at": self.simulation.created_at.isoformat()
        }


# Example usage
if __name__ == "__main__":
    # Example 1: Single MongoDB-integrated agent
    print("="*60)
    print("Example 1: Single MongoDB Agent")
    print("="*60)
    
    agent = MongoAgent(
        name="LegalAdvisor",
        system_prompt="You are a legal advisor helping with trade secret cases.",
        case_id="CASE-2024-TEST",
        case_name="Test Case - Trade Secret Dispute",
        simulation_type="consultation"
    )
    
    # Have a conversation
    response1 = agent.chat("What are the key elements of a trade secret claim?")
    print(f"Agent response: {response1[:200]}...")
    
    response2 = agent.chat("How can we prove misappropriation?")
    print(f"Agent response: {response2[:200]}...")
    
    # Create research entry
    research_id = agent.create_research_entry(
        research_topic="Trade Secret Elements and Proof",
        description="Research on establishing trade secret claims",
        key_findings=[
            "Trade secrets must have economic value",
            "Reasonable efforts to maintain secrecy required",
            "Misappropriation can be through improper acquisition or disclosure"
        ],
        tags=["trade_secrets", "misappropriation", "evidence"]
    )
    
    # Complete simulation
    agent.complete_simulation(
        outcome="Consultation completed successfully",
        summary="Discussed key elements of trade secret claims and proof requirements"
    )
    
    # Example 2: Multi-agent session
    print("\n" + "="*60)
    print("Example 2: Multi-Agent Session")
    print("="*60)
    
    # Create session
    session = MongoMultiAgentSession(
        case_id="CASE-2024-MULTI",
        case_name="Multi-Agent Negotiation Test",
        simulation_type="negotiation"
    )
    
    # Create agents
    lawyer = MongoAgent(
        name="LawyerAgent",
        system_prompt="You are a lawyer representing the plaintiff in a trade secret case.",
        mongodb_enabled=False  # Session will handle MongoDB
    )
    
    negotiator = MongoAgent(
        name="NegotiatorAgent",
        system_prompt="You are a negotiator seeking to find a fair settlement.",
        mongodb_enabled=False
    )
    
    # Add agents to session
    session.add_agent(lawyer)
    session.add_agent(negotiator)
    
    # Agent interaction
    response = session.agent_interaction(
        from_agent="LawyerAgent",
        to_agent="NegotiatorAgent",
        message="We need to discuss potential settlement terms for the trade secret case."
    )
    print(f"Negotiator response: {response[:200]}...")
    
    # Broadcast message
    responses = session.broadcast_message(
        "What are your thoughts on a $1M settlement?",
        sender="Moderator"
    )
    for agent_name, resp in responses.items():
        print(f"{agent_name}: {resp[:150]}...")
    
    # Complete session
    session.complete_session(
        outcome="Agreed to settlement negotiations",
        summary="Both parties agreed to explore settlement options"
    )
    
    print("\n" + "="*60)
    print("Examples complete! Check MongoDB for saved data.")
    print("="*60)
