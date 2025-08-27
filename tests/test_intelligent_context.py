#!/usr/bin/env python3
"""
Test intelligent context extraction with different question types
"""

import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:5000"

def test_intelligent_context():
    """Test different question types to see relevant context extraction"""
    print("🧪 Testing Intelligent Context Extraction")
    print("=" * 50)
    
    try:
        session = requests.Session()
        
        # Login
        login_data = {
            'username': 'test_user',
            'password': 'test_password'
        }
        
        login_response = session.post(f"{BASE_URL}/login", data=login_data)
        
        if login_response.status_code == 200:
            print("✓ Login successful")
            
            # Get user summary
            summary_response = session.get(f"{BASE_URL}/api/user-summary")
            if summary_response.status_code != 200:
                print("❌ Could not get user summary")
                return
                
            summary_data = summary_response.json()
            
            # Test different question types
            test_questions = [
                {
                    'message': '⚡ Energy foods?',
                    'context_type': 'food',
                    'expected_focus': 'energy, calories, meal frequency'
                },
                {
                    'message': 'How many calories am I eating?',
                    'context_type': 'food', 
                    'expected_focus': 'total calories, average per meal'
                },
                {
                    'message': 'Is my mood improving?',
                    'context_type': 'mood',
                    'expected_focus': 'mood trend, average mood'
                },
                {
                    'message': 'Am I drinking enough water?',
                    'context_type': 'water',
                    'expected_focus': 'daily average, hydration adequacy'
                },
                {
                    'message': 'What are my health patterns?',
                    'context_type': 'analysis',
                    'expected_focus': 'recent patterns, insights'
                },
                {
                    'message': 'Hello, how are you?',
                    'context_type': 'minimal',
                    'expected_focus': 'minimal context'
                }
            ]
            
            for i, test in enumerate(test_questions, 1):
                print(f"\n{i}. Testing: '{test['message']}'")
                print(f"   Expected focus: {test['expected_focus']}")
                
                chat_data = {
                    'message': test['message'],
                    'context': summary_data['summary'],
                    'context_type': test['context_type'],
                    'chat_history': []
                }
                
                start_time = time.time()
                chat_response = session.post(f"{BASE_URL}/api/ai-chat", 
                                           json=chat_data,
                                           timeout=15)
                end_time = time.time()
                
                if chat_response.status_code == 200:
                    response_data = chat_response.json()
                    if response_data.get('success'):
                        print(f"   ✓ Response time: {end_time - start_time:.2f}s")
                        print(f"   ✓ Response: {response_data['response'][:100]}...")
                    else:
                        print(f"   ❌ Failed: {response_data.get('error')}")
                else:
                    print(f"   ❌ HTTP error: {chat_response.status_code}")
                    
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_intelligent_context()
