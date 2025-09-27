#!/usr/bin/env python
"""
Simple runner script for N=1 Monte Carlo test
Run this from the project root directory.
"""

import os
import sys

# Make sure we can import from the current directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def main():
    try:
        # Import the test function
        from simulation.montecarlo import test_n1_simulation
        
        print("Starting N=1 Monte Carlo Simulation Test")
        print("=" * 70)
        
        # Run the test
        result = test_n1_simulation()
        
        print("\n" + "=" * 70)
        print("Test completed successfully!")
        
        if result:
            print(f"Final verdict: {result.verdict.winner.upper()} wins")
            print(f"Confidence: {result.verdict.confidence_score:.1%}")
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("\nMake sure you have all required dependencies installed:")
        print("  pip install numpy")
        print("  pip install google-generativeai")
        print("  pip install python-dotenv")
        
    except Exception as e:
        print(f"Error running simulation: {e}")
        print("\nMake sure you have set up your API keys in .env file:")
        print("  GEMINI_API_KEY=your_key_here")

if __name__ == "__main__":
    main()
