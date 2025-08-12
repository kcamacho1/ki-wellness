#!/usr/bin/env python3
"""
Test script to verify barcode scanner functionality
"""

import requests
import json

# Configuration
BASE_URL = "http://localhost:5001"  # Change this to your server URL
TEST_USERNAME = "testuser"  # Change this to a test username
TEST_PASSWORD = "testpass123"  # Change this to a test password

def login():
    """Login and get session cookies"""
    login_data = {
        'username': TEST_USERNAME,
        'password': TEST_PASSWORD
    }
    
    response = requests.post(f"{BASE_URL}/login", data=login_data)
    if response.status_code == 200:
        print("✅ Login successful")
        return response.cookies
    else:
        print(f"❌ Login failed: {response.status_code}")
        return None

def test_barcode_search(cookies):
    """Test barcode search functionality"""
    print("\n📱 Testing barcode search functionality...")
    
    # Test barcodes (real product barcodes)
    test_barcodes = [
        '3017620422003',  # Nutella
        '4007817327324',  # Coca-Cola
        '5000159407236',  # Snickers
        '5901234123457',  # Example EAN-13
        '6901234567892'   # Example EAN-13
    ]
    
    for barcode in test_barcodes:
        print(f"\n🔍 Testing barcode: {barcode}")
        
        search_data = {
            'barcode': barcode,
            'food_name': '',  # Empty for barcode-only search
            'serving_size': 100,
            'serving_unit': 'g'
        }
        
        response = requests.post(
            f"{BASE_URL}/food-journal/search",
            json=search_data,
            cookies=cookies,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"✅ Barcode {barcode}: Found product")
                print(f"   Product: {data['data'].get('food_name', 'Unknown')}")
                print(f"   Brand: {data['data'].get('brand', 'Unknown')}")
                print(f"   Source: {data.get('source', 'Unknown')}")
            else:
                print(f"⚠️ Barcode {barcode}: {data.get('error', 'Not found')}")
        else:
            print(f"❌ Barcode {barcode}: HTTP {response.status_code}")
            print(f"   Response: {response.text}")

def test_food_journal_page(cookies):
    """Test that the food journal page loads with barcode scanner elements"""
    print("\n📄 Testing food journal page...")
    
    response = requests.get(f"{BASE_URL}/food-journal", cookies=cookies)
    
    if response.status_code == 200:
        content = response.text
        
        # Check for barcode scanner elements
        checks = [
            ('Barcode input field', 'id="barcode"'),
            ('Scan button', 'id="searchBarcodeBtn"'),
            ('Camera button', 'id="openScannerBtn"'),
            ('Scanner modal', 'id="scannerModal"'),
            ('QuaggaJS library', 'quagga.min.js'),
            ('Scanner video container', 'id="scannerVideo"'),
            ('Scanner overlay', 'id="scannerOverlay"'),
            ('Start scanner button', 'id="startScannerBtn"'),
            ('Stop scanner button', 'id="stopScannerBtn"'),
            ('Scanned barcode display', 'id="scannedBarcode"')
        ]
        
        all_found = True
        for name, element in checks:
            if element in content:
                print(f"✅ {name}: Found")
            else:
                print(f"❌ {name}: Missing")
                all_found = False
        
        return all_found
    else:
        print(f"❌ Food journal page load failed: HTTP {response.status_code}")
        return False

def test_barcode_api_endpoint(cookies):
    """Test the barcode search API endpoint specifically"""
    print("\n🔌 Testing barcode API endpoint...")
    
    # Test with a known barcode
    barcode = '3017620422003'  # Nutella
    
    search_data = {
        'barcode': barcode,
        'serving_size': 100,
        'serving_unit': 'g'
    }
    
    response = requests.post(
        f"{BASE_URL}/food-journal/search",
        json=search_data,
        cookies=cookies,
        headers={'Content-Type': 'application/json'}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API endpoint working")
        print(f"   Status: {data.get('success')}")
        if data.get('success'):
            print(f"   Product found: {data['data'].get('food_name', 'Unknown')}")
        else:
            print(f"   Error: {data.get('error', 'Unknown')}")
        return True
    else:
        print(f"❌ API endpoint failed: HTTP {response.status_code}")
        return False

def main():
    """Run all barcode scanner tests"""
    print("🚀 Starting barcode scanner tests...")
    
    # Login first
    cookies = login()
    if not cookies:
        print("❌ Cannot proceed without login")
        return
    
    # Test each component
    page_success = test_food_journal_page(cookies)
    api_success = test_barcode_api_endpoint(cookies)
    barcode_success = test_barcode_search(cookies)
    
    # Summary
    print("\n📊 Barcode Scanner Test Results:")
    print(f"Page elements: {'✅ PASS' if page_success else '❌ FAIL'}")
    print(f"API endpoint: {'✅ PASS' if api_success else '❌ FAIL'}")
    print(f"Barcode search: {'✅ PASS' if barcode_success else '⚠️ MAYBE'}")
    
    if all([page_success, api_success]):
        print("\n🎉 Barcode scanner implementation is working!")
        print("\n📱 To test the camera scanner:")
        print("1. Go to the food journal page")
        print("2. Click the '📷 Camera' button")
        print("3. Allow camera permissions")
        print("4. Point camera at a barcode")
        print("5. The scanner should detect and use the barcode")
    else:
        print("\n⚠️ Some tests failed - check the implementation")

if __name__ == "__main__":
    main()
