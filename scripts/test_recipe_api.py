#!/usr/bin/env python3
"""
Script to test recipe API endpoints and functionality.
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_recipe_api():
    """Test recipe API endpoints"""
    print("🧪 Testing Recipe API endpoints...")
    
    base_url = "http://localhost:5000"
    
    # Test endpoints that don't require authentication
    endpoints_to_test = [
        "/recipes",  # Recipe page
    ]
    
    print(f"Testing endpoints on {base_url}")
    
    for endpoint in endpoints_to_test:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            print(f"✅ {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"   Content length: {len(response.content)} bytes")
            elif response.status_code == 302:
                print(f"   Redirected to: {response.headers.get('Location', 'Unknown')}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint}: Connection error - {e}")
    
    print("\n📋 Recipe API endpoints that require authentication:")
    auth_endpoints = [
        "GET /api/recipes - Get user's recipes",
        "POST /api/recipes - Create new recipe", 
        "GET /api/recipes/search - Search recipes",
        "POST /api/recipes/search-by-ingredients - Search by ingredients",
        "GET /api/recipes/preview - Get recipe previews",
        "POST /api/recipes/<id>/rate - Rate recipe",
        "POST /api/recipes/<id>/add-to-log - Add to food log",
        "POST /api/recipes/<id>/toggle-favorite - Toggle favorite"
    ]
    
    for endpoint in auth_endpoints:
        print(f"   - {endpoint}")
    
    print("\n✅ Recipe API test completed!")
    print("💡 To test authenticated endpoints, you'll need to:")
    print("   1. Start the application")
    print("   2. Log in through the web interface")
    print("   3. Navigate to /recipes")
    print("   4. Test creating, searching, and managing recipes")

if __name__ == '__main__':
    load_dotenv()
    test_recipe_api()
