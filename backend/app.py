"""
Flask Backend for Legal Simulation System
==========================================
Provides REST API endpoints for running simulations and retrieving results from MongoDB.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional
from bson.objectid import ObjectId
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mongodb_manager import MongoDBManager, SimulationStatus
from simulation.montecarlo_mongodb import MongoEnhancedMonteCarloSimulation
from simulation.montecarlo import SimulationVariables

app = Flask(__name__)

# Configure CORS with explicit settings - Allow both localhost and 127.0.0.1
CORS(app, 
     resources={
         r"/api/*": {
             "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
             "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
             "allow_headers": ["Content-Type", "Authorization", "Accept"],
             "supports_credentials": True,
             "max_age": 3600
         },
         r"/health": {
             "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
             "methods": ["GET", "OPTIONS"],
             "allow_headers": ["Content-Type"],
             "supports_credentials": True
         }
     },
     origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
     supports_credentials=True)

# Global MongoDB manager
db_manager = None


def get_db_manager():
    """Get or create MongoDB manager instance."""
    global db_manager
    if db_manager is None:
        try:
            db_manager = MongoDBManager()
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
    return db_manager


def serialize_mongodb_doc(doc):
    """Convert MongoDB document to JSON-serializable format."""
    if isinstance(doc, dict):
        return {k: serialize_mongodb_doc(v) for k, v in doc.items()}
    elif isinstance(doc, list):
        return [serialize_mongodb_doc(item) for item in doc]
    elif isinstance(doc, ObjectId):
        return str(doc)
    elif isinstance(doc, datetime):
        return doc.isoformat()
    else:
        return doc


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "mongodb": "connected" if get_db_manager() else "disconnected"
    })


@app.route('/api/simulations', methods=['GET'])
def get_simulations():
    """
    Get list of simulations with optional filtering.
    Query params:
    - limit: Maximum number of results (default 50)
    - case_name: Filter by case name
    - status: Filter by status
    - simulation_type: Filter by type
    """
    try:
        db = get_db_manager()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Parse query parameters
        limit = min(int(request.args.get('limit', 50)), 100)
        case_name = request.args.get('case_name')
        status = request.args.get('status')
        simulation_type = request.args.get('simulation_type')
        
        # Build search parameters
        search_params = {
            'limit': limit
        }
        if case_name:
            search_params['case_name'] = case_name
        if status and status != 'all':
            search_params['status'] = SimulationStatus(status)
        if simulation_type:
            search_params['simulation_type'] = simulation_type
        
        # Search simulations
        simulations = db.search_simulations(**search_params)
        
        # Convert to JSON-serializable format
        results = []
        for sim in simulations:
            sim_dict = {
                'id': str(sim._id),
                'case_id': sim.case_id,
                'case_name': sim.case_name,
                'simulation_type': sim.simulation_type,
                'agents_involved': sim.agents_involved,
                'status': sim.status.value,
                'created_at': sim.created_at.isoformat(),
                'outcome': sim.outcome,
                'summary': sim.summary,
                'message_count': len(sim.chat_history)
            }
            if sim.metadata:
                sim_dict['metadata'] = serialize_mongodb_doc(sim.metadata)
            results.append(sim_dict)
        
        return jsonify({
            'simulations': results,
            'total': len(results)
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/simulation/<simulation_id>', methods=['GET'])
def get_simulation_detail(simulation_id):
    """Get detailed information about a specific simulation."""
    try:
        db = get_db_manager()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Retrieve simulation
        simulation = db.get_simulation(simulation_id)
        if not simulation:
            return jsonify({"error": "Simulation not found"}), 404
        
        # Convert chat history to structured format
        messages = []
        for msg in simulation.chat_history:
            message_dict = {
                'agent_name': msg.agent_name,
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            }
            if msg.metadata:
                message_dict['metadata'] = serialize_mongodb_doc(msg.metadata)
            messages.append(message_dict)
        
        result = {
            'id': str(simulation._id),
            'case_id': simulation.case_id,
            'case_name': simulation.case_name,
            'simulation_type': simulation.simulation_type,
            'agents_involved': simulation.agents_involved,
            'status': simulation.status.value,
            'created_at': simulation.created_at.isoformat(),
            'updated_at': simulation.updated_at.isoformat(),
            'outcome': simulation.outcome,
            'summary': simulation.summary,
            'messages': messages,
            'metadata': serialize_mongodb_doc(simulation.metadata) if simulation.metadata else {}
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/run-simulation', methods=['POST'])
def run_simulation():
    """
    Run a new simulation.
    Request body:
    {
        "case_description": "Description of the case...",
        "jurisdiction": "Federal" (optional),
        "num_simulations": 1,
        "prosecutor_strategy": "moderate",
        "defense_strategy": "moderate",
        "judge_temperament": "balanced",
        "has_nda": true,
        "evidence_strength": "moderate"
    }
    """
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('case_description'):
            return jsonify({"error": "case_description is required"}), 400
        
        db = get_db_manager()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Extract parameters
        case_description = data['case_description']
        jurisdiction = data.get('jurisdiction', 'Federal')
        num_simulations = data.get('num_simulations', 1)
        
        # Create simulation variables
        variables = SimulationVariables(
            prosecutor_strategy=data.get('prosecutor_strategy', 'moderate'),
            defense_strategy=data.get('defense_strategy', 'moderate'),
            judge_temperament=data.get('judge_temperament', 'balanced'),
            has_nda=data.get('has_nda', True),
            evidence_strength=data.get('evidence_strength', 'moderate'),
            venue_bias=data.get('venue_bias', 'neutral')
        )
        
        # Create Monte Carlo simulation with MongoDB support
        mc_sim = MongoEnhancedMonteCarloSimulation(
            case_description=case_description,
            base_jurisdiction=jurisdiction,
            research_depth="moderate",
            db_manager=db,
            auto_save=True
        )
        
        # Run research (this may take some time)
        mc_sim.research_case()
        
        # Run simulation(s)
        if num_simulations == 1:
            # Single simulation
            result = mc_sim.run_single_simulation(1, variables)
            
            # Get the saved simulation ID
            sim_id = mc_sim.saved_simulation_ids[0] if mc_sim.saved_simulation_ids else None
            
            return jsonify({
                'status': 'success',
                'simulation_id': str(sim_id) if sim_id else None,
                'monte_carlo_id': mc_sim.monte_carlo_id,
                'winner': result.verdict.winner,
                'confidence': result.verdict.confidence_score,
                'execution_time': result.execution_time
            })
        else:
            # Multiple simulations (Monte Carlo)
            analysis = mc_sim.run_simulations(
                n_simulations=min(num_simulations, 10),  # Limit to 10 for API
                randomization_config={
                    'fixed_strategies': False,
                    'fixed_evidence': False
                }
            )
            
            return jsonify({
                'status': 'success',
                'monte_carlo_id': mc_sim.monte_carlo_id,
                'monte_carlo_doc_id': str(mc_sim.monte_carlo_doc_id) if mc_sim.monte_carlo_doc_id else None,
                'total_simulations': analysis.total_simulations,
                'plaintiff_wins': analysis.plaintiff_wins,
                'defense_wins': analysis.defense_wins,
                'average_confidence': analysis.average_confidence,
                'simulation_ids': [str(sid) for sid in mc_sim.saved_simulation_ids]
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/monte-carlo/<monte_carlo_id>', methods=['GET'])
def get_monte_carlo(monte_carlo_id):
    """Get Monte Carlo run details by ID."""
    try:
        db = get_db_manager()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
        
        # Search for research document with this Monte Carlo ID
        research_docs = db.search_research(
            research_topic="Monte Carlo",
            limit=100
        )
        
        for doc in research_docs:
            if doc.metadata and doc.metadata.get("monte_carlo_id") == monte_carlo_id:
                # Found the Monte Carlo document
                simulations = []
                for sim_id in doc.simulation_ids:
                    sim = db.get_simulation(sim_id)
                    if sim:
                        simulations.append({
                            'id': str(sim._id),
                            'simulation_number': sim.metadata.get('simulation_id') if sim.metadata else None,
                            'outcome': sim.outcome,
                            'confidence': sim.metadata.get('verdict', {}).get('confidence', 0) if sim.metadata else 0,
                            'variables': sim.metadata.get('variables', {}) if sim.metadata else {}
                        })
                
                result = {
                    'monte_carlo_id': monte_carlo_id,
                    'document_id': str(doc._id),
                    'case_name': doc.case_name,
                    'created_at': doc.created_at.isoformat(),
                    'status': doc.status.value,
                    'key_findings': doc.key_findings,
                    'simulations': simulations,
                    'analysis': doc.metadata.get('analysis', {}) if doc.metadata else {}
                }
                
                return jsonify(result)
        
        return jsonify({"error": "Monte Carlo run not found"}), 404
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get database statistics."""
    try:
        db = get_db_manager()
        if not db:
            return jsonify({"error": "Database connection failed"}), 500
        
        stats = db.get_statistics()
        return jsonify(serialize_mongodb_doc(stats))
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    print("Starting Legal Simulation API Server...")
    print("Server running on http://localhost:5000")
    app.run(debug=True, port=5000)
