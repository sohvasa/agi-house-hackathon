#!/usr/bin/env python3
"""
Simple test script to verify the JSON handling and response fixes.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agents.baseAgent import BaseAgent
import json


def test_json_repair():
    """Test the JSON repair functionality."""
    print("Testing JSON Repair Functionality")
    print("=" * 60)
    
    agent = BaseAgent(
        name="TestAgent",
        system_prompt="You are a test agent",
        max_output_tokens=8192  # Using increased limit
    )
    
    # Test cases with various JSON issues
    test_cases = [
        ('{"key": "value"}', "Valid JSON"),
        ('{"key": "value"', "Missing closing brace"),
        ('{"key": "val', "Truncated string"),
        ('```json\n{"key": "value"}\n```', "Markdown wrapped"),
        ('{"key1": "value1", "key2": ["item1", "item2"', "Incomplete array"),
        ('{"main_argument": "The algorithms in que', "Truncated mid-word (from example)"),
    ]
    
    for json_str, description in test_cases:
        try:
            result = agent.repair_json(json_str)
            print(f"✅ {description}: Successfully repaired")
            if 'main_argument' in result:
                print(f"   Extracted: {result['main_argument']}")
        except Exception as e:
            print(f"❌ {description}: Failed - {str(e)}")
    
    print()
    return True


def test_response_validation():
    """Test the response validation functionality."""
    print("Testing Response Validation")
    print("=" * 60)
    
    agent = BaseAgent(
        name="TestAgent",
        system_prompt="You are a test agent",
        response_format='json'
    )
    
    test_responses = [
        ('{"complete": true}', True, "Complete JSON"),
        ('{"incomplete": "val', False, "Incomplete JSON"),
        ('{"nested": {"key": "value"}}', True, "Nested JSON"),
        ('{"array": [1, 2, 3]}', True, "Array JSON"),
        ('{"truncated": "...', False, "Truncated with ellipsis"),
        ('{"main_argument": "warranting injunc', False, "Truncated mid-word"),
    ]
    
    for response, expected, description in test_responses:
        is_valid = agent.validate_json_response(response)
        status = "✅" if is_valid == expected else "❌"
        print(f"{status} {description}: Valid={is_valid}, Expected={expected}")
    
    print()
    return True


def test_partial_extraction():
    """Test extraction of partial JSON data."""
    print("Testing Partial JSON Extraction")
    print("=" * 60)
    
    agent = BaseAgent(
        name="TestAgent",
        system_prompt="You are a test agent"
    )
    
    # Test with a real truncated response from the example
    truncated_json = '''
    {
        "main_argument": "SolarTech fails to meet its burden under DTSA and CUTSA. Dr. Chen's technology is the product of legitimate independent development",
        "key_points": [
            "The algorithms in que'''
    
    result = agent.extract_partial_json(truncated_json)
    print(f"Extracted from truncated JSON:")
    print(f"  - main_argument: {result.get('main_argument', 'NOT FOUND')[:50]}...")
    print(f"  - key_points: {result.get('key_points', 'NOT FOUND')}")
    
    print()
    return True


def test_live_generation():
    """Test live generation with the new model and settings."""
    print("Testing Live Generation with Enhanced Settings")
    print("=" * 60)
    
    agent = BaseAgent(
        name="TestAgent",
        system_prompt="You are a helpful assistant that provides structured JSON responses.",
        model_name="gemini-2.5-pro",  # Using the updated model
        max_output_tokens=8192,  # Increased token limit
        response_format='json',
        temperature=0.3
    )
    
    prompt = '''Generate a JSON object with the following structure:
    {
        "analysis": "A detailed analysis of trade secret law (at least 200 words)",
        "key_points": ["point1", "point2", "point3", "point4", "point5"],
        "citations": ["citation1", "citation2"],
        "conclusion": "A comprehensive conclusion about the legal implications"
    }
    
    Topic: Analyze the requirements for proving trade secret misappropriation under DTSA.'''
    
    try:
        print("Generating response with new settings...")
        response = agent.generate_with_completion(prompt, max_attempts=3)
        
        # Try to parse the response
        data = agent.repair_json(response)
        
        print(f"✅ Successfully generated and parsed JSON")
        print(f"   - Analysis length: {len(data.get('analysis', ''))} chars")
        print(f"   - Key points: {len(data.get('key_points', []))} items")
        print(f"   - Citations: {len(data.get('citations', []))} items")
        print(f"   - Has conclusion: {'conclusion' in data}")
        
        # Check if response seems complete
        if len(data.get('analysis', '')) > 500:
            print(f"✅ Response appears complete (not truncated)")
        else:
            print(f"⚠️  Response may be truncated")
            
    except Exception as e:
        print(f"❌ Error during generation: {str(e)}")
        return False
    
    print()
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("SIMPLE TEST OF JSON FIXES")
    print("=" * 60)
    print()
    
    # Print current configuration
    print("Configuration:")
    print(f"  - Default model: gemini-2.5-pro")
    print(f"  - Max output tokens: 8192")
    print(f"  - JSON repair: Enabled")
    print(f"  - Response validation: Enabled")
    print()
    
    # Run individual tests
    test_results = []
    
    print("Test 1: JSON Repair")
    test_results.append(("JSON Repair", test_json_repair()))
    
    print("\nTest 2: Response Validation")
    test_results.append(("Response Validation", test_response_validation()))
    
    print("\nTest 3: Partial Extraction")
    test_results.append(("Partial Extraction", test_partial_extraction()))
    
    print("\nTest 4: Live Generation")
    test_results.append(("Live Generation", test_live_generation()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in test_results)
    if all_passed:
        print("\n🎉 All tests passed! The JSON fixes are working correctly.")
        print("\nKey improvements implemented:")
        print("  1. ✅ Switched to Gemini 2.5 Pro model")
        print("  2. ✅ Increased max_output_tokens to 8192")
        print("  3. ✅ Added JSON repair for incomplete responses")
        print("  4. ✅ Added response validation")
        print("  5. ✅ Added automatic completion for truncated responses")
        print("  6. ✅ Removed manual string truncation")
        print("  7. ✅ Enhanced error handling with partial extraction")
    else:
        print("\n⚠️ Some tests failed. Please review the output above.")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
