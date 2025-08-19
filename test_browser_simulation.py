#!/usr/bin/env python3
"""
Test that simulates the exact browser request to debug AI chat issues
"""

import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:5000"

def test_browser_simulation():
    """Simulate the exact browser request"""
    print("🧪 Testing browser simulation...")
    
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
            
            # Get user summary (like the browser does)
            print("Getting user summary...")
            summary_response = session.get(f"{BASE_URL}/api/user-summary")
            
            if summary_response.status_code == 200:
                summary_data = summary_response.json()
                print("✓ User summary received")
                print(f"Summary keys: {list(summary_data['summary'].keys())}")
                
                # Simulate the exact browser request
                chat_data = {
                    'message': '⚡ Energy foods?',
                    'context': summary_data['summary'],
                    'context_type': 'food',
                    'chat_history': []
                }
                
                print("Sending AI chat request...")
                print(f"Context type: {chat_data['context_type']}")
                print(f"Context keys: {list(chat_data['context'].keys())}")
                
                start_time = time.time()
                
                chat_response = session.post(f"{BASE_URL}/api/ai-chat", 
                                           json=chat_data,
                                           timeout=30)
                end_time = time.time()
                
                print(f"Response time: {end_time - start_time:.2f}s")
                print(f"Response status: {chat_response.status_code}")
                
                if chat_response.status_code == 200:
                    response_data = chat_response.json()
                    print(f"Response success: {response_data.get('success')}")
                    if response_data.get('success'):
                        print("✓ AI chat working!")
                        print(f"Response length: {len(response_data.get('response', ''))}")
                    else:
                        print(f"❌ AI chat failed: {response_data.get('error')}")
                else:
                    print(f"❌ HTTP error: {chat_response.status_code}")
                    print(f"Response text: {chat_response.text[:500]}...")
                    
            else:
                print(f"❌ Could not get user summary: {summary_response.status_code}")
                
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_browser_simulation()
