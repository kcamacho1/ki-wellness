#!/usr/bin/env python3
"""
Test script for Food Journal functionality
"""

import requests
import json
import time
from datetime import datetime

BASE_URL = "http://localhost:5000"

def test_food_search():
    """Test food search functionality"""
    print("🔍 Testing food search...")
    
    # Test 1: Search for apple
    response = requests.post(f"{BASE_URL}/food-journal/search", 
                           json={"food_name": "apple", "serving_size": 1, "serving_unit": "piece"})
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Food search successful!")
            print(f"   Found: {data['data']['food_name']}")
            print(f"   Calories: {data['data']['calories']}")
            print(f"   Source: {data['source']}")
        else:
            print("❌ Food search failed:", data.get('error'))
    else:
        print("❌ Food search request failed:", response.status_code)

def test_add_food_entry():
    """Test adding a food entry"""
    print("\n🍎 Testing add food entry...")
    
    # Use current date and time
    current_datetime = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    entry_data = {
        "food_name": "Test Apple",
        "brand": "Test Brand",
        "serving_size": 1.0,
        "serving_unit": "piece",
        "calories": 95.0,
        "protein": 0.5,
        "carbs": 25.0,
        "fat": 0.3,
        "fiber": 4.0,
        "sugar": 19.0,
        "sodium": 2.0,
        "mood": "😊 Happy",
        "notes": "This is a test entry",
        "consumed_at": current_datetime
    }
    
    response = requests.post(f"{BASE_URL}/food-journal/add", json=entry_data)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            print("✅ Food entry added successfully!")
        else:
            print("❌ Food entry failed:", data.get('error'))
    else:
        print("❌ Food entry request failed:", response.status_code)

def test_get_entries():
    """Test getting food entries"""
    print("\n📋 Testing get food entries...")
    
    response = requests.get(f"{BASE_URL}/food-journal/entries")
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            entries = data.get('entries', [])
            print(f"✅ Retrieved {len(entries)} food entries")
            for entry in entries:
                print(f"   - {entry['food_name']} ({entry['serving_size']} {entry['serving_unit']})")
                print(f"     Mood: {entry.get('mood', 'N/A')}")
                print(f"     Notes: {entry.get('notes', 'N/A')}")
        else:
            print("❌ Get entries failed:", data.get('error'))
    else:
        print("❌ Get entries request failed:", response.status_code)

def test_export_csv():
    """Test CSV export functionality"""
    print("\n📤 Testing CSV export...")
    
    response = requests.get(f"{BASE_URL}/food-journal/export")
    
    if response.status_code == 200:
        print("✅ CSV export successful!")
        print(f"   Content-Type: {response.headers.get('content-type')}")
        print(f"   Content-Length: {len(response.content)} bytes")
    else:
        print("❌ CSV export failed:", response.status_code)

def test_delete_entries():
    """Test deleting food entries"""
    print("\n🗑️ Testing delete entries...")
    
    # First get entries to find IDs to delete
    response = requests.get(f"{BASE_URL}/food-journal/entries")
    if response.status_code == 200:
        data = response.json()
        if data.get('success') and data.get('entries'):
            entry_ids = [entry['id'] for entry in data['entries']]
            
            if entry_ids:
                delete_response = requests.post(f"{BASE_URL}/food-journal/delete", 
                                             json={"entry_ids": entry_ids})
                
                if delete_response.status_code == 200:
                    delete_data = delete_response.json()
                    if delete_data.get('success'):
                        print(f"✅ Deleted {len(entry_ids)} entries successfully!")
                    else:
                        print("❌ Delete failed:", delete_data.get('error'))
                else:
                    print("❌ Delete request failed:", delete_response.status_code)
            else:
                print("ℹ️ No entries to delete")
        else:
            print("ℹ️ No entries found to delete")
    else:
        print("❌ Could not retrieve entries for deletion")

def main():
    """Run all tests"""
    print("🧪 Starting Food Journal Tests...")
    print("=" * 50)
    
    # Test server connectivity
    try:
        response = requests.get(f"{BASE_URL}/food-journal")
        if response.status_code == 200:
            print("✅ Server is running and accessible")
        else:
            print("❌ Server is not responding correctly")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure it's running on localhost:5000")
        return
    
    # Run tests
    test_food_search()
    test_add_food_entry()
    test_get_entries()
    test_export_csv()
    test_delete_entries()
    
    print("\n" + "=" * 50)
    print("🎉 Food Journal tests completed!")

if __name__ == "__main__":
    main()
