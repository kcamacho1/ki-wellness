#!/usr/bin/env python3
"""
Simple test for AI chat endpoint
"""

import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:5000"

def test_simple_ai_chat():
    """Test the AI chat endpoint with minimal data"""
    print("🧪 Testing simple AI chat...")
    
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
            
            # Test with minimal context
            chat_data = {
                'message': 'Hello, how are you?',
                'context': {
                    'profile': {'name': 'Test User'},
                    'analysis': {},
                    'chat_history': []
                },
                'context_type': 'minimal',
                'chat_history': []
            }
            
            print("Sending chat request...")
            start_time = time.time()
            
            chat_response = session.post(f"{BASE_URL}/api/ai-chat", 
                                       json=chat_data,
                                       timeout=30)
            end_time = time.time()
            
            print(f"Response time: {end_time - start_time:.2f}s")
            print(f"Response status: {chat_response.status_code}")
            
            if chat_response.status_code == 200:
                response_data = chat_response.json()
                print(f"Response: {response_data}")
                if response_data.get('success'):
                    print("✓ AI chat working!")
                else:
                    print(f"❌ AI chat failed: {response_data.get('error')}")
            else:
                print(f"❌ HTTP error: {chat_response.status_code}")
                print(f"Response text: {chat_response.text}")
                
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_simple_ai_chat()
