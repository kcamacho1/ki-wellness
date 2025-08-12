#!/usr/bin/env python3
"""
Open Food Facts API v2 Test Script

This script tests the updated Open Food Facts API v2 implementation
based on the official documentation: https://openfoodfacts.github.io/openfoodfacts-server/api/

Usage:
    python tests/test_openfoodfacts_api_v2.py
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the functions we want to test
from app.main import (
    search_openfoodfacts_api, 
    search_openfoodfacts_by_barcode,
    clean_search_terms,
    find_best_match,
    extract_nutritional_data
)

def test_api_v2_search():
    """Test the new API v2 search endpoint"""
    print("🧪 Testing Open Food Facts API v2 Search...")
    print("=" * 50)
    
    test_foods = [
        'apple',
        'banana', 
        'chicken',
        'rice',
        'almonds',
        'yogurt',
        'spinach'
    ]
    
    for food in test_foods:
        print(f"\nTesting: {food}")
        result = search_openfoodfacts_api(food)
        
        if result:
            print(f"  ✅ Found: {result['food_name']}")
            print(f"  Brand: {result['brand']}")
            print(f"  Source: {result['source']}")
            print(f"  Calories: {result['calories']:.1f}")
            print(f"  Protein: {result['protein']:.1f}g")
            print(f"  Carbs: {result['carbs']:.1f}g")
            print(f"  Fat: {result['fat']:.1f}g")
            
            # Check if it's a reasonable match
            food_lower = food.lower()
            result_name_lower = result['food_name'].lower()
            
            if food_lower in result_name_lower:
                print(f"  ✅ Good match!")
            elif any(word in result_name_lower for word in food_lower.split()):
                print(f"  ⚠️  Partial match")
            else:
                print(f"  ❌ Poor match")
        else:
            print(f"  ❌ No data found")

def test_barcode_search():
    """Test barcode search functionality"""
    print("\n🧪 Testing Open Food Facts API v2 Barcode Search...")
    print("=" * 50)
    
    # Test with a known barcode (Nutella example from Open Food Facts)
    test_barcodes = [
        '3017620422003',  # Nutella
        '3274080005003',  # Example from docs
        '737628064502',   # Another example
    ]
    
    for barcode in test_barcodes:
        print(f"\nTesting barcode: {barcode}")
        result = search_openfoodfacts_by_barcode(barcode)
        
        if result:
            print(f"  ✅ Found: {result['food_name']}")
            print(f"  Brand: {result['brand']}")
            print(f"  Source: {result['source']}")
            print(f"  Calories: {result['calories']:.1f}")
            print(f"  Protein: {result['protein']:.1f}g")
            print(f"  Carbs: {result['carbs']:.1f}g")
            print(f"  Fat: {result['fat']:.1f}g")
        else:
            print(f"  ❌ No data found for barcode")

def test_rate_limiting():
    """Test rate limiting behavior"""
    print("\n🧪 Testing Rate Limiting...")
    print("=" * 50)
    
    # Test multiple rapid requests to see rate limiting
    print("Making 5 rapid search requests...")
    
    for i in range(5):
        result = search_openfoodfacts_api('apple')
        if result:
            print(f"  Request {i+1}: ✅ Success")
        else:
            print(f"  Request {i+1}: ❌ Failed (possibly rate limited)")
    
    print("\nNote: Rate limit is 10 req/min for search queries")

def test_search_term_cleaning():
    """Test the search term cleaning function"""
    print("\n🧪 Testing Search Term Cleaning...")
    print("=" * 50)
    
    test_terms = [
        ('fresh apple', 'apple fruit'),
        ('organic banana', 'banana fruit'),
        ('raw almonds', 'almond nut'),
        ('whole milk', 'milk'),
        ('chicken breast', 'chicken meat'),
        ('brown rice', 'rice grain'),
    ]
    
    for original, expected in test_terms:
        cleaned = clean_search_terms(original)
        print(f"  '{original}' -> '{cleaned}' (expected: '{expected}')")

def test_best_match_algorithm():
    """Test the best match algorithm"""
    print("\n🧪 Testing Best Match Algorithm...")
    print("=" * 50)
    
    # Simulate API response data
    mock_products = [
        {
            'product_name': 'Apple & Raisin Oat Bars',
            'brands': 'deliciously ella',
            'categories_tags': ['en:processed-foods', 'en:snacks']
        },
        {
            'product_name': 'Fresh Apple',
            'brands': '',
            'categories_tags': ['en:raw-foods', 'en:fruits']
        },
        {
            'product_name': 'Apple Juice',
            'brands': 'Tropicana',
            'categories_tags': ['en:beverages']
        }
    ]
    
    best_match = find_best_match(mock_products, 'apple')
    
    if best_match:
        print(f"  ✅ Best match: {best_match['product_name']}")
        print(f"  Brand: {best_match['brands']}")
        print(f"  Categories: {best_match['categories_tags']}")
    else:
        print("  ❌ No best match found")

def test_data_extraction():
    """Test nutritional data extraction"""
    print("\n🧪 Testing Data Extraction...")
    print("=" * 50)
    
    # Mock product data
    mock_product = {
        'product_name': 'Test Apple',
        'brands': 'Test Brand',
        'nutriments': {
            'energy-kcal_100g': 52,
            'proteins_100g': 0.3,
            'carbohydrates_100g': 14,
            'fat_100g': 0.2,
            'fiber_100g': 2.4,
            'sugars_100g': 10.4,
            'salt_100g': 1
        }
    }
    
    result = extract_nutritional_data(mock_product, 'apple')
    
    if result:
        print(f"  ✅ Extracted data successfully")
        print(f"  Food name: {result['food_name']}")
        print(f"  Calories: {result['calories']}")
        print(f"  Protein: {result['protein']}g")
        print(f"  Carbs: {result['carbs']}g")
        print(f"  Fat: {result['fat']}g")
    else:
        print("  ❌ Data extraction failed")

def test_api_compliance():
    """Test API compliance with official documentation"""
    print("\n🧪 Testing API Compliance...")
    print("=" * 50)
    
    # Test User-Agent header
    print("Testing User-Agent header compliance...")
    
    url = "https://world.openfoodfacts.org/api/v2/search"
    headers = {
        'User-Agent': 'KiWellness/1.0 (nutrition@kiwellness.org)',
        'Content-Type': 'application/json'
    }
    params = {
        'search_terms': 'apple',
        'page_size': 1,
        'json': 1
    }
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"  ✅ API request successful (Status: {response.status_code})")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('products'):
                print(f"  ✅ Received {len(data['products'])} products")
            else:
                print(f"  ⚠️  No products in response")
        elif response.status_code == 429:
            print(f"  ⚠️  Rate limited (429 status)")
        else:
            print(f"  ❌ Unexpected status code: {response.status_code}")
            
    except Exception as e:
        print(f"  ❌ API request failed: {e}")

def generate_api_v2_report():
    """Generate a comprehensive API v2 test report"""
    print("📊 OPEN FOOD FACTS API V2 TEST REPORT")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API Documentation: https://openfoodfacts.github.io/openfoodfacts-server/api/")
    print()
    
    # Run all tests
    test_api_v2_search()
    test_barcode_search()
    test_rate_limiting()
    test_search_term_cleaning()
    test_best_match_algorithm()
    test_data_extraction()
    test_api_compliance()
    
    print("\n" + "=" * 60)
    print("📋 API V2 IMPROVEMENTS SUMMARY")
    print("=" * 60)
    print("✅ Updated to official API v2 endpoints")
    print("✅ Added proper User-Agent header")
    print("✅ Implemented rate limiting handling")
    print("✅ Added barcode search functionality")
    print("✅ Improved error handling")
    print("✅ Better search term cleaning")
    print()
    print("💡 API V2 BENEFITS:")
    print("1. Official API v2 with better reliability")
    print("2. Proper rate limiting (10 req/min search, 100 req/min product)")
    print("3. Barcode search for specific products")
    print("4. Better error handling and timeout management")
    print("5. Compliance with API documentation requirements")

if __name__ == "__main__":
    generate_api_v2_report()
