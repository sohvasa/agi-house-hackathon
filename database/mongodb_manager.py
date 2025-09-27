"""
MongoDB Manager - Handles database connections and operations for case simulations and research.
Implements two main collections:
1. case_simulations: Stores chat history from multiple agent simulations
2. case_research: Stores research data with links to related simulations
"""

import os
import json
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict, field
from enum import Enum
import pymongo
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from bson import ObjectId
from dotenv import load_dotenv

load_dotenv()


class SimulationStatus(Enum):
    """Status of a simulation"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ResearchStatus(Enum):
    """Status of research"""
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"


@dataclass
class AgentMessage:
    """Represents a message in the simulation chat history"""
    agent_name: str
    role: str  # user, assistant, system, tool
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for MongoDB storage"""
        data = {
            "agent_name": self.agent_name,
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp,
        }
        if self.metadata:
            data["metadata"] = self.metadata
        if self.tool_calls:
            data["tool_calls"] = self.tool_calls
        return data


@dataclass
class CaseSimulation:
    """Represents a complete case simulation with multiple agents"""
    case_id: str
    case_name: str
    simulation_type: str  # e.g., "negotiation", "litigation", "mediation"
    agents_involved: List[str]
    chat_history: List[AgentMessage]
    status: SimulationStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    outcome: Optional[str] = None
    summary: Optional[str] = None
    _id: Optional[ObjectId] = None
    
    def to_mongodb_doc(self) -> Dict[str, Any]:
        """Convert to MongoDB document"""
        doc = {
            "case_id": self.case_id,
            "case_name": self.case_name,
            "simulation_type": self.simulation_type,
            "agents_involved": self.agents_involved,
            "chat_history": [msg.to_dict() for msg in self.chat_history],
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.completed_at:
            doc["completed_at"] = self.completed_at
        if self.metadata:
            doc["metadata"] = self.metadata
        if self.outcome:
            doc["outcome"] = self.outcome
        if self.summary:
            doc["summary"] = self.summary
        if self._id:
            doc["_id"] = self._id
        return doc
    
    @classmethod
    def from_mongodb_doc(cls, doc: Dict[str, Any]) -> 'CaseSimulation':
        """Create from MongoDB document"""
        chat_history = []
        for msg_dict in doc.get("chat_history", []):
            chat_history.append(AgentMessage(
                agent_name=msg_dict["agent_name"],
                role=msg_dict["role"],
                content=msg_dict["content"],
                timestamp=msg_dict["timestamp"],
                metadata=msg_dict.get("metadata"),
                tool_calls=msg_dict.get("tool_calls")
            ))
        
        return cls(
            case_id=doc["case_id"],
            case_name=doc["case_name"],
            simulation_type=doc["simulation_type"],
            agents_involved=doc["agents_involved"],
            chat_history=chat_history,
            status=SimulationStatus(doc["status"]),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            completed_at=doc.get("completed_at"),
            metadata=doc.get("metadata"),
            outcome=doc.get("outcome"),
            summary=doc.get("summary"),
            _id=doc.get("_id")
        )


@dataclass
class CaseResearch:
    """Represents research data for a case with links to simulations"""
    case_id: str
    case_name: str
    research_topic: str
    description: str
    key_findings: List[str]
    legal_precedents: List[Dict[str, Any]]
    statutes: List[Dict[str, Any]]
    simulation_ids: List[ObjectId] = field(default_factory=list)  # Links to case_simulations
    status: ResearchStatus = ResearchStatus.DRAFT
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: Optional[Dict[str, Any]] = None
    tags: List[str] = field(default_factory=list)
    _id: Optional[ObjectId] = None
    
    def to_mongodb_doc(self) -> Dict[str, Any]:
        """Convert to MongoDB document"""
        doc = {
            "case_id": self.case_id,
            "case_name": self.case_name,
            "research_topic": self.research_topic,
            "description": self.description,
            "key_findings": self.key_findings,
            "legal_precedents": self.legal_precedents,
            "statutes": self.statutes,
            "simulation_ids": self.simulation_ids,
            "status": self.status.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": self.tags
        }
        if self.metadata:
            doc["metadata"] = self.metadata
        if self._id:
            doc["_id"] = self._id
        return doc
    
    @classmethod
    def from_mongodb_doc(cls, doc: Dict[str, Any]) -> 'CaseResearch':
        """Create from MongoDB document"""
        return cls(
            case_id=doc["case_id"],
            case_name=doc["case_name"],
            research_topic=doc["research_topic"],
            description=doc["description"],
            key_findings=doc["key_findings"],
            legal_precedents=doc["legal_precedents"],
            statutes=doc["statutes"],
            simulation_ids=doc["simulation_ids"],
            status=ResearchStatus(doc["status"]),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
            metadata=doc.get("metadata"),
            tags=doc.get("tags", []),
            _id=doc.get("_id")
        )


class MongoDBManager:
    """
    MongoDB Manager for handling database operations.
    Manages two collections:
    - case_simulations: Stores agent chat histories
    - case_research: Stores research data with links to simulations
    """
    
    def __init__(self, 
                 connection_string: Optional[str] = None,
                 database_name: str = "legal_agent_system",
                 create_indexes: bool = True):
        """
        Initialize MongoDB connection.
        
        Args:
            connection_string: MongoDB connection string (defaults to env variable)
            database_name: Name of the database to use
            create_indexes: Whether to create indexes on initialization
        """
        # Get connection string from environment if not provided
        if connection_string is None:
            connection_string = os.getenv("MONGODB_CONNECTION_STRING")
            if not connection_string:
                raise ValueError(
                    "MongoDB connection string not provided. "
                    "Set MONGODB_CONNECTION_STRING environment variable or pass connection_string parameter."
                )
        
        # Initialize MongoDB client
        try:
            self.client = MongoClient(connection_string, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            print(f"Successfully connected to MongoDB Atlas")
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise
        
        # Set database and collections
        self.db = self.client[database_name]
        self.simulations_collection = self.db["case_simulations"]
        self.research_collection = self.db["case_research"]
        
        # Create indexes if requested
        if create_indexes:
            self._create_indexes()
    
    def _create_indexes(self):
        """Create indexes for better query performance"""
        try:
            # Indexes for case_simulations collection
            self.simulations_collection.create_index([("case_id", ASCENDING)])
            self.simulations_collection.create_index([("case_name", ASCENDING)])
            self.simulations_collection.create_index([("status", ASCENDING)])
            self.simulations_collection.create_index([("created_at", DESCENDING)])
            self.simulations_collection.create_index([("agents_involved", ASCENDING)])
            self.simulations_collection.create_index(
                [("case_id", ASCENDING), ("simulation_type", ASCENDING)],
                unique=False
            )
            
            # Indexes for case_research collection
            self.research_collection.create_index([("case_id", ASCENDING)])
            self.research_collection.create_index([("case_name", ASCENDING)])
            self.research_collection.create_index([("status", ASCENDING)])
            self.research_collection.create_index([("created_at", DESCENDING)])
            self.research_collection.create_index([("tags", ASCENDING)])
            self.research_collection.create_index([("simulation_ids", ASCENDING)])
            
            print("Successfully created database indexes")
        except Exception as e:
            print(f"Error creating indexes: {e}")
    
    # ==================== Simulation Operations ====================
    
    def save_simulation(self, simulation: CaseSimulation) -> ObjectId:
        """
        Save or update a case simulation.
        
        Args:
            simulation: CaseSimulation object to save
            
        Returns:
            ObjectId of the saved simulation
        """
        simulation.updated_at = datetime.now()
        doc = simulation.to_mongodb_doc()
        
        if simulation._id:
            # Update existing simulation
            self.simulations_collection.replace_one(
                {"_id": simulation._id},
                doc
            )
            return simulation._id
        else:
            # Insert new simulation
            result = self.simulations_collection.insert_one(doc)
            return result.inserted_id
    
    def get_simulation(self, simulation_id: Union[str, ObjectId]) -> Optional[CaseSimulation]:
        """
        Retrieve a simulation by ID.
        
        Args:
            simulation_id: ObjectId or string ID of the simulation
            
        Returns:
            CaseSimulation object or None if not found
        """
        if isinstance(simulation_id, str):
            simulation_id = ObjectId(simulation_id)
        
        doc = self.simulations_collection.find_one({"_id": simulation_id})
        if doc:
            return CaseSimulation.from_mongodb_doc(doc)
        return None
    
    def get_simulations_by_case(self, case_id: str) -> List[CaseSimulation]:
        """
        Get all simulations for a specific case.
        
        Args:
            case_id: ID of the case
            
        Returns:
            List of CaseSimulation objects
        """
        docs = self.simulations_collection.find({"case_id": case_id})
        return [CaseSimulation.from_mongodb_doc(doc) for doc in docs]
    
    def update_simulation_status(self, 
                                 simulation_id: Union[str, ObjectId],
                                 status: SimulationStatus,
                                 outcome: Optional[str] = None,
                                 summary: Optional[str] = None) -> bool:
        """
        Update the status of a simulation.
        
        Args:
            simulation_id: ID of the simulation
            status: New status
            outcome: Optional outcome description
            summary: Optional summary
            
        Returns:
            True if update successful
        """
        if isinstance(simulation_id, str):
            simulation_id = ObjectId(simulation_id)
        
        update_doc = {
            "$set": {
                "status": status.value,
                "updated_at": datetime.now()
            }
        }
        
        if status == SimulationStatus.COMPLETED:
            update_doc["$set"]["completed_at"] = datetime.now()
        
        if outcome:
            update_doc["$set"]["outcome"] = outcome
        
        if summary:
            update_doc["$set"]["summary"] = summary
        
        result = self.simulations_collection.update_one(
            {"_id": simulation_id},
            update_doc
        )
        
        return result.modified_count > 0
    
    def add_message_to_simulation(self,
                                  simulation_id: Union[str, ObjectId],
                                  message: AgentMessage) -> bool:
        """
        Add a message to an existing simulation's chat history.
        
        Args:
            simulation_id: ID of the simulation
            message: AgentMessage to add
            
        Returns:
            True if message added successfully
        """
        if isinstance(simulation_id, str):
            simulation_id = ObjectId(simulation_id)
        
        result = self.simulations_collection.update_one(
            {"_id": simulation_id},
            {
                "$push": {"chat_history": message.to_dict()},
                "$set": {"updated_at": datetime.now()}
            }
        )
        
        return result.modified_count > 0
    
    def search_simulations(self,
                          case_name: Optional[str] = None,
                          agent_name: Optional[str] = None,
                          status: Optional[SimulationStatus] = None,
                          simulation_type: Optional[str] = None,
                          date_from: Optional[datetime] = None,
                          date_to: Optional[datetime] = None,
                          limit: int = 100) -> List[CaseSimulation]:
        """
        Search simulations with various filters.
        
        Args:
            case_name: Filter by case name (partial match)
            agent_name: Filter by agent involvement
            status: Filter by status
            simulation_type: Filter by simulation type
            date_from: Filter by creation date (from)
            date_to: Filter by creation date (to)
            limit: Maximum number of results
            
        Returns:
            List of matching CaseSimulation objects
        """
        query = {}
        
        if case_name:
            query["case_name"] = {"$regex": case_name, "$options": "i"}
        
        if agent_name:
            query["agents_involved"] = agent_name
        
        if status:
            query["status"] = status.value
        
        if simulation_type:
            query["simulation_type"] = simulation_type
        
        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query["$gte"] = date_from
            if date_to:
                date_query["$lte"] = date_to
            query["created_at"] = date_query
        
        docs = self.simulations_collection.find(query).limit(limit).sort("created_at", -1)
        return [CaseSimulation.from_mongodb_doc(doc) for doc in docs]
    
    # ==================== Research Operations ====================
    
    def save_research(self, research: CaseResearch) -> ObjectId:
        """
        Save or update case research.
        
        Args:
            research: CaseResearch object to save
            
        Returns:
            ObjectId of the saved research
        """
        research.updated_at = datetime.now()
        doc = research.to_mongodb_doc()
        
        if research._id:
            # Update existing research
            self.research_collection.replace_one(
                {"_id": research._id},
                doc
            )
            return research._id
        else:
            # Insert new research
            result = self.research_collection.insert_one(doc)
            return result.inserted_id
    
    def get_research(self, research_id: Union[str, ObjectId]) -> Optional[CaseResearch]:
        """
        Retrieve research by ID.
        
        Args:
            research_id: ObjectId or string ID of the research
            
        Returns:
            CaseResearch object or None if not found
        """
        if isinstance(research_id, str):
            research_id = ObjectId(research_id)
        
        doc = self.research_collection.find_one({"_id": research_id})
        if doc:
            return CaseResearch.from_mongodb_doc(doc)
        return None
    
    def get_research_by_case(self, case_id: str) -> List[CaseResearch]:
        """
        Get all research for a specific case.
        
        Args:
            case_id: ID of the case
            
        Returns:
            List of CaseResearch objects
        """
        docs = self.research_collection.find({"case_id": case_id})
        return [CaseResearch.from_mongodb_doc(doc) for doc in docs]
    
    def link_simulation_to_research(self,
                                   research_id: Union[str, ObjectId],
                                   simulation_id: Union[str, ObjectId]) -> bool:
        """
        Link a simulation to research.
        
        Args:
            research_id: ID of the research
            simulation_id: ID of the simulation to link
            
        Returns:
            True if linking successful
        """
        if isinstance(research_id, str):
            research_id = ObjectId(research_id)
        if isinstance(simulation_id, str):
            simulation_id = ObjectId(simulation_id)
        
        result = self.research_collection.update_one(
            {"_id": research_id},
            {
                "$addToSet": {"simulation_ids": simulation_id},
                "$set": {"updated_at": datetime.now()}
            }
        )
        
        return result.modified_count > 0
    
    def unlink_simulation_from_research(self,
                                       research_id: Union[str, ObjectId],
                                       simulation_id: Union[str, ObjectId]) -> bool:
        """
        Remove a simulation link from research.
        
        Args:
            research_id: ID of the research
            simulation_id: ID of the simulation to unlink
            
        Returns:
            True if unlinking successful
        """
        if isinstance(research_id, str):
            research_id = ObjectId(research_id)
        if isinstance(simulation_id, str):
            simulation_id = ObjectId(simulation_id)
        
        result = self.research_collection.update_one(
            {"_id": research_id},
            {
                "$pull": {"simulation_ids": simulation_id},
                "$set": {"updated_at": datetime.now()}
            }
        )
        
        return result.modified_count > 0
    
    def get_linked_simulations(self, research_id: Union[str, ObjectId]) -> List[CaseSimulation]:
        """
        Get all simulations linked to a research entry.
        
        Args:
            research_id: ID of the research
            
        Returns:
            List of linked CaseSimulation objects
        """
        research = self.get_research(research_id)
        if not research:
            return []
        
        simulations = []
        for sim_id in research.simulation_ids:
            sim = self.get_simulation(sim_id)
            if sim:
                simulations.append(sim)
        
        return simulations
    
    def search_research(self,
                       case_name: Optional[str] = None,
                       research_topic: Optional[str] = None,
                       status: Optional[ResearchStatus] = None,
                       tags: Optional[List[str]] = None,
                       has_simulations: Optional[bool] = None,
                       limit: int = 100) -> List[CaseResearch]:
        """
        Search research with various filters.
        
        Args:
            case_name: Filter by case name (partial match)
            research_topic: Filter by research topic (partial match)
            status: Filter by status
            tags: Filter by tags (any match)
            has_simulations: Filter by whether research has linked simulations
            limit: Maximum number of results
            
        Returns:
            List of matching CaseResearch objects
        """
        query = {}
        
        if case_name:
            query["case_name"] = {"$regex": case_name, "$options": "i"}
        
        if research_topic:
            query["research_topic"] = {"$regex": research_topic, "$options": "i"}
        
        if status:
            query["status"] = status.value
        
        if tags:
            query["tags"] = {"$in": tags}
        
        if has_simulations is not None:
            if has_simulations:
                query["simulation_ids"] = {"$ne": []}
            else:
                query["simulation_ids"] = []
        
        docs = self.research_collection.find(query).limit(limit).sort("created_at", -1)
        return [CaseResearch.from_mongodb_doc(doc) for doc in docs]
    
    # ==================== Aggregation Operations ====================
    
    def get_case_summary(self, case_id: str) -> Dict[str, Any]:
        """
        Get a comprehensive summary of a case including all research and simulations.
        
        Args:
            case_id: ID of the case
            
        Returns:
            Dictionary containing case summary
        """
        simulations = self.get_simulations_by_case(case_id)
        research = self.get_research_by_case(case_id)
        
        summary = {
            "case_id": case_id,
            "total_simulations": len(simulations),
            "total_research_entries": len(research),
            "simulation_types": list(set(sim.simulation_type for sim in simulations)),
            "agents_involved": list(set(
                agent for sim in simulations for agent in sim.agents_involved
            )),
            "research_topics": [r.research_topic for r in research],
            "total_messages": sum(len(sim.chat_history) for sim in simulations),
            "simulations": [
                {
                    "id": str(sim._id),
                    "type": sim.simulation_type,
                    "status": sim.status.value,
                    "agents": sim.agents_involved,
                    "message_count": len(sim.chat_history),
                    "created_at": sim.created_at.isoformat()
                }
                for sim in simulations
            ],
            "research": [
                {
                    "id": str(r._id),
                    "topic": r.research_topic,
                    "status": r.status.value,
                    "linked_simulations": len(r.simulation_ids),
                    "created_at": r.created_at.isoformat()
                }
                for r in research
            ]
        }
        
        return summary
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Dictionary containing database statistics
        """
        stats = {
            "total_simulations": self.simulations_collection.count_documents({}),
            "total_research_entries": self.research_collection.count_documents({}),
            "simulations_by_status": {},
            "research_by_status": {},
            "database_size": self.db.command("dbstats")["dataSize"]
        }
        
        # Count simulations by status
        for status in SimulationStatus:
            count = self.simulations_collection.count_documents({"status": status.value})
            stats["simulations_by_status"][status.value] = count
        
        # Count research by status
        for status in ResearchStatus:
            count = self.research_collection.count_documents({"status": status.value})
            stats["research_by_status"][status.value] = count
        
        return stats
    
    # ==================== Cleanup Operations ====================
    
    def delete_simulation(self, simulation_id: Union[str, ObjectId]) -> bool:
        """
        Delete a simulation.
        
        Args:
            simulation_id: ID of the simulation to delete
            
        Returns:
            True if deletion successful
        """
        if isinstance(simulation_id, str):
            simulation_id = ObjectId(simulation_id)
        
        result = self.simulations_collection.delete_one({"_id": simulation_id})
        
        # Also remove references from research entries
        self.research_collection.update_many(
            {"simulation_ids": simulation_id},
            {"$pull": {"simulation_ids": simulation_id}}
        )
        
        return result.deleted_count > 0
    
    def delete_research(self, research_id: Union[str, ObjectId]) -> bool:
        """
        Delete a research entry.
        
        Args:
            research_id: ID of the research to delete
            
        Returns:
            True if deletion successful
        """
        if isinstance(research_id, str):
            research_id = ObjectId(research_id)
        
        result = self.research_collection.delete_one({"_id": research_id})
        return result.deleted_count > 0
    
    def cleanup_old_simulations(self, days_old: int = 30) -> int:
        """
        Clean up old simulations.
        
        Args:
            days_old: Number of days to consider a simulation old
            
        Returns:
            Number of simulations deleted
        """
        cutoff_date = datetime.now() - timedelta(days=days_old)
        result = self.simulations_collection.delete_many({
            "created_at": {"$lt": cutoff_date},
            "status": {"$in": [SimulationStatus.COMPLETED.value, SimulationStatus.FAILED.value]}
        })
        return result.deleted_count
    
    def close(self):
        """Close the MongoDB connection"""
        self.client.close()
        print("MongoDB connection closed")


# Example usage and testing
if __name__ == "__main__":
    from datetime import timedelta
    
    # Initialize MongoDB Manager
    print("Initializing MongoDB Manager...")
    db_manager = MongoDBManager()
    
    # Example 1: Create and save a simulation
    print("\n" + "="*60)
    print("Example 1: Creating and Saving a Simulation")
    print("="*60)
    
    # Create sample messages
    messages = [
        AgentMessage(
            agent_name="LawyerAgent",
            role="assistant",
            content="I believe we have a strong case based on the precedent set in Waymo v. Uber.",
            timestamp=datetime.now()
        ),
        AgentMessage(
            agent_name="NegotiatorAgent",
            role="assistant",
            content="Let's explore a settlement option that protects our client's interests.",
            timestamp=datetime.now()
        )
    ]
    
    # Create simulation
    simulation = CaseSimulation(
        case_id="CASE-2024-001",
        case_name="TechCorp v. StartupInc - Trade Secret Dispute",
        simulation_type="negotiation",
        agents_involved=["LawyerAgent", "NegotiatorAgent", "ResearchAgent"],
        chat_history=messages,
        status=SimulationStatus.IN_PROGRESS,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        metadata={"jurisdiction": "California", "case_type": "trade_secret"}
    )
    
    # Save simulation
    sim_id = db_manager.save_simulation(simulation)
    print(f"Saved simulation with ID: {sim_id}")
    
    # Example 2: Create and save research
    print("\n" + "="*60)
    print("Example 2: Creating and Saving Research")
    print("="*60)
    
    research = CaseResearch(
        case_id="CASE-2024-001",
        case_name="TechCorp v. StartupInc - Trade Secret Dispute",
        research_topic="Trade Secret Misappropriation Precedents",
        description="Research on relevant case law for trade secret misappropriation in tech industry",
        key_findings=[
            "Waymo v. Uber established clear standards for proving misappropriation",
            "Intent is a crucial factor in determining damages",
            "Preliminary injunctions are common in clear misappropriation cases"
        ],
        legal_precedents=[
            {
                "case": "Waymo v. Uber",
                "year": "2018",
                "relevance": "Direct precedent for autonomous vehicle trade secrets"
            }
        ],
        statutes=[
            {
                "title": "Defend Trade Secrets Act",
                "section": "18 U.S.C. § 1836",
                "relevance": "Federal cause of action for trade secret misappropriation"
            }
        ],
        simulation_ids=[sim_id],  # Link to the simulation we just created
        tags=["trade_secrets", "tech_industry", "california"]
    )
    
    research_id = db_manager.save_research(research)
    print(f"Saved research with ID: {research_id}")
    
    # Example 3: Add message to existing simulation
    print("\n" + "="*60)
    print("Example 3: Adding Message to Simulation")
    print("="*60)
    
    new_message = AgentMessage(
        agent_name="ResearchAgent",
        role="assistant",
        content="Found additional precedent: E.I. DuPont v. Kolon Industries supports our position.",
        timestamp=datetime.now(),
        metadata={"source": "legal_database"}
    )
    
    success = db_manager.add_message_to_simulation(sim_id, new_message)
    print(f"Message added: {success}")
    
    # Example 4: Search simulations
    print("\n" + "="*60)
    print("Example 4: Searching Simulations")
    print("="*60)
    
    simulations = db_manager.search_simulations(
        case_name="TechCorp",
        status=SimulationStatus.IN_PROGRESS
    )
    print(f"Found {len(simulations)} simulations")
    for sim in simulations:
        print(f"  - {sim.case_name}: {len(sim.chat_history)} messages")
    
    # Example 5: Get case summary
    print("\n" + "="*60)
    print("Example 5: Case Summary")
    print("="*60)
    
    summary = db_manager.get_case_summary("CASE-2024-001")
    print(f"Case Summary:")
    print(f"  Total Simulations: {summary['total_simulations']}")
    print(f"  Total Research Entries: {summary['total_research_entries']}")
    print(f"  Total Messages: {summary['total_messages']}")
    print(f"  Agents Involved: {', '.join(summary['agents_involved'])}")
    
    # Example 6: Get database statistics
    print("\n" + "="*60)
    print("Example 6: Database Statistics")
    print("="*60)
    
    stats = db_manager.get_statistics()
    print(f"Database Statistics:")
    print(f"  Total Simulations: {stats['total_simulations']}")
    print(f"  Total Research Entries: {stats['total_research_entries']}")
    print(f"  Database Size: {stats['database_size']} bytes")
    
    # Close connection
    db_manager.close()
    
    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60)
