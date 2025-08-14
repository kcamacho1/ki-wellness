#!/usr/bin/env python3
"""
Test script to check OpenFoodFacts API status and functionality
"""

import sys
import os
import requests
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import NutritionService

def test_openfoodfacts_api_status():
    """Test if OpenFoodFacts API is accessible"""
    print("🧪 Testing OpenFoodFacts API Status")
    print("=" * 50)
    
    # Test basic API connectivity
    try:
        # Test the search endpoint
        url = "https://world.openfoodfacts.org/cgi/search.pl"
        headers = {
            'User-Agent': 'KiWellness/1.0 (nutrition@kiwellness.org)',
            'Content-Type': 'application/json'
        }
        params = {
            'search_terms': 'apple',
            'search_simple': 1,
            'action': 'process',
            'json': 1,
            'page_size': 1
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            print("✅ OpenFoodFacts search API is accessible")
            data = response.json()
            if data.get('products'):
                print(f"   📊 Found {len(data['products'])} products for 'apple'")
            else:
                print("   ⚠️  No products returned for 'apple'")
        else:
            print(f"❌ OpenFoodFacts search API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing OpenFoodFacts search API: {e}")
        return False
    
    # Test the product endpoint
    try:
        # Test with a known product barcode
        test_barcode = "3017620422003"  # Nutella
        url = f"https://world.openfoodfacts.org/api/v2/product/{test_barcode}"
        headers = {
            'User-Agent': 'KiWellness/1.0 (nutrition@kiwellness.org)',
            'Content-Type': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            print("✅ OpenFoodFacts product API is accessible")
            data = response.json()
            if data.get('status') == 1 and data.get('product'):
                print(f"   📊 Found product: {data['product'].get('product_name', 'Unknown')}")
            else:
                print("   ⚠️  Product not found or invalid response")
        elif response.status_code == 404:
            print("⚠️  OpenFoodFacts product API returned 404 (product not found)")
            print("   This is normal for products not in their database")
        else:
            print(f"❌ OpenFoodFacts product API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing OpenFoodFacts product API: {e}")
        return False
    
    return True

def test_barcode_database():
    """Test our local barcode database"""
    print("\n🧪 Testing Local Barcode Database")
    print("=" * 50)
    
    # Test the Omega 3 trail mix barcode
    barcode = "0828267571602"
    result = NutritionService.search_barcode_database(barcode)
    
    if result:
        print(f"✅ Found barcode {barcode} in local database")
        print(f"   📊 Product: {result.get('food_name')}")
        print(f"   📊 Calories: {result.get('calories')}")
        print(f"   📊 Protein: {result.get('protein')}g")
        print(f"   📊 Carbs: {result.get('carbs')}g")
        print(f"   📊 Fat: {result.get('fat')}g")
        return True
    else:
        print(f"❌ Barcode {barcode} not found in local database")
        return False

def test_search_functionality():
    """Test the search functionality"""
    print("\n🧪 Testing Search Functionality")
    print("=" * 50)
    
    # Test cilantro search
    result = NutritionService.search_common_foods_database('cilantro')
    if result:
        print("✅ Cilantro search working")
        print(f"   📊 Found: {result.get('food_name')}")
    else:
        print("❌ Cilantro search failed")
        return False
    
    # Test OpenFoodFacts search
    try:
        result = NutritionService.search_openfoodfacts_api('apple')
        if result:
            print("✅ OpenFoodFacts search working")
            print(f"   📊 Found: {result.get('food_name', 'Unknown')}")
        else:
            print("⚠️  OpenFoodFacts search returned no results (this may be normal)")
    except Exception as e:
        print(f"❌ OpenFoodFacts search error: {e}")
        return False
    
    return True

def test_barcode_search_flow():
    """Test the complete barcode search flow"""
    print("\n🧪 Testing Barcode Search Flow")
    print("=" * 50)
    
    # Test the Omega 3 trail mix barcode
    barcode = "0828267571602"
    
    # Test local database first
    local_result = NutritionService.search_barcode_database(barcode)
    if local_result:
        print(f"✅ Local database found barcode {barcode}")
        print(f"   📊 Product: {local_result.get('food_name')}")
    else:
        print(f"❌ Local database did not find barcode {barcode}")
    
    # Test OpenFoodFacts as fallback
    try:
        openfoodfacts_result = NutritionService.search_openfoodfacts_by_barcode(barcode)
        if openfoodfacts_result:
            print(f"✅ OpenFoodFacts found barcode {barcode}")
            print(f"   📊 Product: {openfoodfacts_result.get('food_name', 'Unknown')}")
        else:
            print(f"⚠️  OpenFoodFacts did not find barcode {barcode} (expected for this product)")
    except Exception as e:
        print(f"❌ OpenFoodFacts barcode search error: {e}")
    
    return local_result is not None

def main():
    """Run all OpenFoodFacts API tests"""
    print("🚀 Starting OpenFoodFacts API Tests")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_openfoodfacts_api_status()
    test2_passed = test_barcode_database()
    test3_passed = test_search_functionality()
    test4_passed = test_barcode_search_flow()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    tests = [
        ("OpenFoodFacts API Status", test1_passed),
        ("Local Barcode Database", test2_passed),
        ("Search Functionality", test3_passed),
        ("Barcode Search Flow", test4_passed)
    ]
    
    passed_tests = 0
    for test_name, passed in tests:
        if passed:
            print(f"✅ {test_name}: PASSED")
            passed_tests += 1
        else:
            print(f"❌ {test_name}: FAILED")
    
    print(f"\n📊 Results: {passed_tests}/{len(tests)} tests passed")
    
    if passed_tests == len(tests):
        print("\n🎉 All tests passed! OpenFoodFacts API is working correctly.")
        print("   - API endpoints are accessible")
        print("   - Local barcode database is working")
        print("   - Search functionality is working")
        print("   - Barcode search flow is working")
        return True
    else:
        print(f"\n❌ {len(tests) - passed_tests} test(s) failed.")
        print("\n💡 Recommendations:")
        if not test1_passed:
            print("   - Check internet connectivity")
            print("   - OpenFoodFacts API might be down")
        if not test2_passed:
            print("   - Local barcode database needs to be updated")
        if not test3_passed:
            print("   - Search functionality needs debugging")
        if not test4_passed:
            print("   - Barcode search flow needs fixing")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
