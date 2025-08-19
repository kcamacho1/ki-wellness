#!/usr/bin/env python3
"""
Test script for the optimized AI chat system
"""

import requests
import json
import time

# Test configuration
BASE_URL = "http://localhost:5000"
TEST_USERNAME = "test_user"
TEST_PASSWORD = "test_password"

def test_user_summary_endpoint():
    """Test the new user summary endpoint"""
    print("🧪 Testing /api/user-summary endpoint...")
    
    try:
        # First, we need to login to get a session
        session = requests.Session()
        
        # Login
        login_data = {
            'username': TEST_USERNAME,
            'password': TEST_PASSWORD
        }
        
        login_response = session.post(f"{BASE_URL}/login", data=login_data)
        
        if login_response.status_code == 200:
            print("✓ Login successful")
            
            # Test user summary endpoint
            summary_response = session.get(f"{BASE_URL}/api/user-summary")
            
            if summary_response.status_code == 200:
                data = summary_response.json()
                if data.get('success'):
                    print("✓ User summary endpoint working")
                    print(f"  - Profile: {data['summary']['profile']['name']}")
                    print(f"  - Food entries: {data['summary']['food_summary']['total_entries']}")
                    print(f"  - Mood entries: {data['summary']['mood_summary']['total_entries']}")
                    print(f"  - Water entries: {data['summary']['water_summary']['total_entries']}")
                    return True
                else:
                    print(f"❌ User summary failed: {data.get('error')}")
            else:
                print(f"❌ User summary request failed: {summary_response.status_code}")
        else:
            print(f"❌ Login failed: {login_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error testing user summary: {e}")
    
    return False

def test_optimized_ai_chat():
    """Test the optimized AI chat endpoint"""
    print("\n🧪 Testing optimized /api/ai-chat endpoint...")
    
    try:
        session = requests.Session()
        
        # Login
        login_data = {
            'username': TEST_USERNAME,
            'password': TEST_PASSWORD
        }
        
        login_response = session.post(f"{BASE_URL}/login", data=login_data)
        
        if login_response.status_code == 200:
            print("✓ Login successful")
            
            # Test different context types
            test_messages = [
                {
                    'message': 'How am I doing with my food intake?',
                    'context_type': 'food'
                },
                {
                    'message': 'What is my mood trend?',
                    'context_type': 'mood'
                },
                {
                    'message': 'Am I drinking enough water?',
                    'context_type': 'water'
                },
                {
                    'message': 'Hello, how are you?',
                    'context_type': 'minimal'
                }
            ]
            
            for test in test_messages:
                print(f"\n  Testing: '{test['message']}' (context: {test['context_type']})")
                
                # First get user summary
                summary_response = session.get(f"{BASE_URL}/api/user-summary")
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    
                    # Prepare chat request
                    chat_data = {
                        'message': test['message'],
                        'context': summary_data['summary'],
                        'context_type': test['context_type'],
                        'chat_history': []
                    }
                    
                    # Test AI chat
                    start_time = time.time()
                    chat_response = session.post(f"{BASE_URL}/api/ai-chat", 
                                               json=chat_data,
                                               timeout=15)
                    end_time = time.time()
                    
                    if chat_response.status_code == 200:
                        response_data = chat_response.json()
                        if response_data.get('success'):
                            print(f"    ✓ Response received in {end_time - start_time:.2f}s")
                            print(f"    ✓ Response length: {len(response_data['response'])} chars")
                        else:
                            print(f"    ❌ Chat failed: {response_data.get('error')}")
                    else:
                        print(f"    ❌ Chat request failed: {chat_response.status_code}")
                else:
                    print(f"    ❌ Could not get user summary")
                    
    except Exception as e:
        print(f"❌ Error testing AI chat: {e}")
    
    return False

def test_performance_comparison():
    """Compare performance between old and new approach"""
    print("\n🧪 Testing performance comparison...")
    
    try:
        session = requests.Session()
        
        # Login
        login_data = {
            'username': TEST_USERNAME,
            'password': TEST_PASSWORD
        }
        
        login_response = session.post(f"{BASE_URL}/login", data=login_data)
        
        if login_response.status_code == 200:
            print("✓ Login successful")
            
            # Test optimized approach
            print("\n  Testing optimized approach (user-summary + context-aware chat):")
            
            start_time = time.time()
            
            # Get user summary
            summary_response = session.get(f"{BASE_URL}/api/user-summary")
            summary_time = time.time()
            
            if summary_response.status_code == 200:
                summary_data = summary_response.json()
                print(f"    ✓ User summary: {summary_time - start_time:.2f}s")
                
                # Test chat with minimal context
                chat_data = {
                    'message': 'Hello, how are you?',
                    'context': summary_data['summary'],
                    'context_type': 'minimal',
                    'chat_history': []
                }
                
                chat_response = session.post(f"{BASE_URL}/api/ai-chat", 
                                           json=chat_data,
                                           timeout=15)
                chat_time = time.time()
                
                if chat_response.status_code == 200:
                    response_data = chat_response.json()
                    if response_data.get('success'):
                        print(f"    ✓ AI chat: {chat_time - summary_time:.2f}s")
                        print(f"    ✓ Total time: {chat_time - start_time:.2f}s")
                        print(f"    ✓ Total response size: {len(json.dumps(summary_data)) + len(response_data['response'])} chars")
                    else:
                        print(f"    ❌ Chat failed: {response_data.get('error')}")
                else:
                    print(f"    ❌ Chat request failed: {chat_response.status_code}")
            else:
                print(f"    ❌ Could not get user summary")
                
    except Exception as e:
        print(f"❌ Error testing performance: {e}")
    
    return False

def main():
    """Run all tests"""
    print("🚀 Testing Optimized AI Chat System")
    print("=" * 50)
    
    # Wait a moment for the server to be ready
    print("Waiting for server to be ready...")
    time.sleep(2)
    
    # Test user summary endpoint
    test_user_summary_endpoint()
    
    # Test optimized AI chat
    test_optimized_ai_chat()
    
    # Test performance comparison
    test_performance_comparison()
    
    print("\n" + "=" * 50)
    print("✅ Testing completed!")

if __name__ == "__main__":
    main()
