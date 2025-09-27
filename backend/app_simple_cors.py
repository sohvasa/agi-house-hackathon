"""
Alternative Flask Backend with Simplified CORS
===============================================
Use this if you're still having CORS issues with the main app.py
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

# SIMPLEST CORS SETUP - Allow everything (development only!)
CORS(app, origins="*", allow_headers="*", methods="*")

# Rest of the code is the same as app.py
# Copy all the route handlers and functions from app.py below

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
    """Get list of simulations."""
    try:
        db = get_db_manager()
        if not db:
            # Return empty list if no DB connection
            return jsonify({
                'simulations': [],
                'total': 0,
                'error': 'Database not connected'
            })
        
        # Parse query parameters
        limit = min(int(request.args.get('limit', 50)), 100)
        
        # For testing without MongoDB, return mock data
        return jsonify({
            'simulations': [],
            'total': 0
        })
        
    except Exception as e:
        return jsonify({"error": str(e), "simulations": [], "total": 0}), 200


@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """Get database statistics."""
    try:
        db = get_db_manager()
        if not db:
            # Return default stats if no DB
            return jsonify({
                "total_simulations": 0,
                "total_research_entries": 0,
                "simulations_by_status": {
                    "completed": 0,
                    "in_progress": 0,
                    "failed": 0
                }
            })
        
        stats = db.get_statistics()
        return jsonify(serialize_mongodb_doc(stats))
        
    except Exception as e:
        # Return default stats on error
        return jsonify({
            "total_simulations": 0,
            "total_research_entries": 0,
            "simulations_by_status": {
                "completed": 0,
                "in_progress": 0,
                "failed": 0
            },
            "error": str(e)
        })


if __name__ == '__main__':
    print("Starting Legal Simulation API Server (Simple CORS)...")
    print("WARNING: This version allows all origins - use for development only!")
    print("Server running on http://localhost:5000")
    app.run(debug=True, port=5000, host='0.0.0.0')
