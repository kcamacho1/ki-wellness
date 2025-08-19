#!/usr/bin/env python3
"""
Test the integration of health resources in AI chat responses
"""

import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:5000"

def test_resources_integration():
    """Test that AI responses include relevant resources and links"""
    print("🧪 Testing Resources Integration in AI Chat")
    print("=" * 60)
    
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
            
            # Test questions that should trigger different resource types
            test_questions = [
                {
                    'message': '⚡ Energy foods?',
                    'context_type': 'food',
                    'expected_resources': 'nutrition resources + Medium blog'
                },
                {
                    'message': 'How can I improve my mood?',
                    'context_type': 'mood',
                    'expected_resources': 'mood resources + Medium blog'
                },
                {
                    'message': 'Am I drinking enough water?',
                    'context_type': 'water',
                    'expected_resources': 'hydration resources + Medium blog'
                },
                {
                    'message': 'What are good exercise habits?',
                    'context_type': 'minimal',
                    'expected_resources': 'exercise resources + Medium blog'
                }
            ]
            
            for i, test in enumerate(test_questions, 1):
                print(f"\n{i}. Testing: '{test['message']}'")
                print(f"   Expected: {test['expected_resources']}")
                
                chat_data = {
                    'message': test['message'],
                    'context': summary_data['summary'],
                    'context_type': test['context_type'],
                    'chat_history': []
                }
                
                start_time = time.time()
                chat_response = session.post(f"{BASE_URL}/api/ai-chat", 
                                           json=chat_data,
                                           timeout=20)
                end_time = time.time()
                
                if chat_response.status_code == 200:
                    response_data = chat_response.json()
                    if response_data.get('success'):
                        response_text = response_data['response']
                        print(f"   ✓ Response time: {end_time - start_time:.2f}s")
                        print(f"   ✓ Response length: {len(response_text)} chars")
                        
                        # Check if response includes resources
                        if '📚' in response_text or 'Helpful Resources' in response_text:
                            print("   ✓ Resources section found!")
                        else:
                            print("   ⚠ No resources section found")
                            
                        # Check for Medium blog links
                        if 'kiwellness.medium.com' in response_text:
                            print("   ✓ Medium blog link included!")
                        else:
                            print("   ⚠ No Medium blog link found")
                            
                        # Show first 200 chars of response
                        print(f"   Response preview: {response_text[:200]}...")
                        
                    else:
                        print(f"   ❌ Failed: {response_data.get('error')}")
                else:
                    print(f"   ❌ HTTP error: {chat_response.status_code}")
                    
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_resources_integration()
