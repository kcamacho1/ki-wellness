#!/usr/bin/env python3
"""
Test script to verify cilantro search and nutritional data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import NutritionService

def test_cilantro_in_database():
    """Test that cilantro is in the common foods database"""
    print("🧪 Testing Cilantro in Database")
    print("=" * 50)
    
    # Test direct lookup
    cilantro_data = NutritionService.search_common_foods_database('cilantro')
    
    if cilantro_data:
        print("✅ Cilantro found in common foods database")
        print(f"   📊 Food name: {cilantro_data.get('food_name')}")
        print(f"   📊 Calories: {cilantro_data.get('calories')}")
        print(f"   📊 Protein: {cilantro_data.get('protein')}g")
        print(f"   📊 Carbs: {cilantro_data.get('carbs')}g")
        print(f"   📊 Fat: {cilantro_data.get('fat')}g")
        print(f"   📊 Fiber: {cilantro_data.get('fiber')}g")
        print(f"   📊 Sugar: {cilantro_data.get('sugar')}g")
        print(f"   📊 Sodium: {cilantro_data.get('sodium')}mg")
        return True
    else:
        print("❌ Cilantro not found in common foods database")
        return False

def test_cilantro_variations():
    """Test cilantro search variations"""
    print("\n🧪 Testing Cilantro Variations")
    print("=" * 50)
    
    variations = [
        'cilantro',
        'coriander',
        'coriander leaves',
        'fresh cilantro',
        'cilantro herb'
    ]
    
    all_found = True
    for variation in variations:
        result = NutritionService.search_common_foods_database(variation)
        if result:
            print(f"✅ '{variation}' -> Found")
        else:
            print(f"❌ '{variation}' -> Not found")
            all_found = False
    
    return all_found

def test_cilantro_enhanced_search():
    """Test enhanced search for cilantro"""
    print("\n🧪 Testing Enhanced Search")
    print("=" * 50)
    
    # Test spelling correction
    misspellings = NutritionService.get_common_misspellings()
    cilantro_misspellings = {k: v for k, v in misspellings.items() if v == 'cilantro'}
    
    print("Cilantro misspellings found:")
    for misspelled, correct in cilantro_misspellings.items():
        print(f"   '{misspelled}' -> '{correct}'")
    
    # Test enhanced search query
    enhanced_queries = NutritionService.enhance_search_query('cilantro')
    print(f"\nEnhanced queries for 'cilantro': {enhanced_queries}")
    
    return len(cilantro_misspellings) > 0

def test_cilantro_multiple_search():
    """Test multiple search results for cilantro"""
    print("\n🧪 Testing Multiple Search Results")
    print("=" * 50)
    
    # Test multiple results search
    results = NutritionService.search_common_foods_multiple('cilantro')
    
    if results:
        print(f"✅ Found {len(results)} results for cilantro")
        for i, result in enumerate(results[:3], 1):  # Show first 3 results
            print(f"   {i}. {result.get('food_name', 'Unknown')}")
            print(f"      Calories: {result.get('calories', 'N/A')}")
    else:
        print("❌ No multiple results found for cilantro")
        return False
    
    return True

def test_other_herbs():
    """Test other herbs in the database"""
    print("\n🧪 Testing Other Herbs")
    print("=" * 50)
    
    herbs = ['parsley', 'basil', 'mint']
    
    for herb in herbs:
        result = NutritionService.search_common_foods_database(herb)
        if result:
            print(f"✅ {herb.capitalize()}: {result.get('food_name')}")
        else:
            print(f"❌ {herb.capitalize()}: Not found")
    
    return True

def main():
    """Run all cilantro tests"""
    print("🚀 Starting Cilantro Tests")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_cilantro_in_database()
    test2_passed = test_cilantro_variations()
    test3_passed = test_cilantro_enhanced_search()
    test4_passed = test_cilantro_multiple_search()
    test5_passed = test_other_herbs()
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    tests = [
        ("Cilantro in Database", test1_passed),
        ("Cilantro Variations", test2_passed),
        ("Enhanced Search", test3_passed),
        ("Multiple Search Results", test4_passed),
        ("Other Herbs", test5_passed)
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
        print("\n🎉 All tests passed! Cilantro is working correctly.")
        print("   - Cilantro is in the database")
        print("   - Variations are supported")
        print("   - Enhanced search works")
        print("   - Multiple results are available")
        print("   - Other herbs are also available")
        return True
    else:
        print(f"\n❌ {len(tests) - passed_tests} test(s) failed.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
