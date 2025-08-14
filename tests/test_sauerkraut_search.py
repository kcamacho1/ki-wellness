#!/usr/bin/env python3
"""
Test Sauerkraut Search and Nutritional Data
===========================================

This test verifies that sauerkraut search returns complete nutritional data
with proper serving size conversion.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import NutritionService

def test_sauerkraut_search():
    """Test sauerkraut search and nutritional data extraction"""
    print("🧪 Testing Sauerkraut Search and Nutritional Data...")
    
    # Test OpenFoodFacts search
    print("\n🔍 Testing OpenFoodFacts search for 'sauerkraut'...")
    of_results = NutritionService.search_openfoodfacts_multiple('sauerkraut')
    
    if of_results:
        print(f"✅ Found {len(of_results)} OpenFoodFacts results")
        
        # Check the first result
        first_result = of_results[0]
        print(f"   First result: {first_result.get('food_name', 'Unknown')}")
        print(f"   Brand: {first_result.get('brand', 'N/A')}")
        
        # Check nutritional data completeness
        core_nutrients = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
        print("\n   Nutritional data:")
        for nutrient in core_nutrients:
            value = first_result.get(nutrient)
            if value is not None:
                print(f"   ✅ {nutrient}: {value}")
            else:
                print(f"   ❌ {nutrient}: missing")
    else:
        print("❌ No OpenFoodFacts results found")
    
    # Test common foods search
    print("\n🔍 Testing common foods search for 'sauerkraut'...")
    cf_results = NutritionService.search_common_foods_multiple('sauerkraut')
    
    if cf_results:
        print(f"✅ Found {len(cf_results)} common foods results")
        
        # Check the first result
        first_result = cf_results[0]
        print(f"   First result: {first_result.get('food_name', 'Unknown')}")
        
        # Check nutritional data completeness
        core_nutrients = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
        print("\n   Nutritional data:")
        for nutrient in core_nutrients:
            value = first_result.get(nutrient)
            if value is not None:
                print(f"   ✅ {nutrient}: {value}")
            else:
                print(f"   ❌ {nutrient}: missing")
    else:
        print("❌ No common foods results found")

def test_serving_size_conversion():
    """Test serving size conversion for sauerkraut"""
    print("\n🧪 Testing Serving Size Conversion...")
    
    # Get sauerkraut data
    sauerkraut_data = NutritionService.search_common_foods_database('sauerkraut')
    
    if sauerkraut_data:
        print("✅ Found sauerkraut data for conversion test")
        print(f"   Original serving: {sauerkraut_data['serving_size']}{sauerkraut_data['serving_unit']}")
        print(f"   Original calories: {sauerkraut_data['calories']}")
        print(f"   Original fiber: {sauerkraut_data['fiber']}")
        print(f"   Original sodium: {sauerkraut_data['sodium']}")
        
        # Test conversion to 300g
        converted = NutritionService.convert_nutritional_data(sauerkraut_data, 300, 'g')
        
        if converted:
            print(f"\n   Converted serving: {converted['serving_size']}{converted['serving_unit']}")
            print(f"   Converted calories: {converted['calories']}")
            print(f"   Converted fiber: {converted['fiber']}")
            print(f"   Converted sodium: {converted['sodium']}")
            
            # Verify conversion factor (should be 3x)
            expected_calories = sauerkraut_data['calories'] * 3
            if abs(converted['calories'] - expected_calories) < 0.1:
                print("   ✅ Conversion factor correct (3x)")
            else:
                print(f"   ❌ Conversion factor incorrect. Expected {expected_calories}, got {converted['calories']}")
        else:
            print("   ❌ Conversion failed")
    else:
        print("❌ No sauerkraut data found for conversion test")

def test_enhanced_search():
    """Test enhanced search with spelling variations"""
    print("\n🧪 Testing Enhanced Search...")
    
    # Test enhanced search queries
    enhanced_queries = NutritionService.enhance_search_query('sauerkraut')
    print(f"   Enhanced queries: {enhanced_queries}")
    
    # Test each query
    for query in enhanced_queries:
        print(f"\n   Testing query: '{query}'")
        
        # Try OpenFoodFacts
        of_results = NutritionService.search_openfoodfacts_multiple(query)
        if of_results:
            print(f"   ✅ OpenFoodFacts: {len(of_results)} results")
        else:
            print(f"   ❌ OpenFoodFacts: no results")
        
        # Try common foods
        cf_results = NutritionService.search_common_foods_multiple(query)
        if cf_results:
            print(f"   ✅ Common foods: {len(cf_results)} results")
        else:
            print(f"   ❌ Common foods: no results")

def main():
    """Run all sauerkraut tests"""
    print("🚀 Testing Sauerkraut Search and Nutritional Data")
    print("=" * 55)
    
    try:
        test_sauerkraut_search()
        test_serving_size_conversion()
        test_enhanced_search()
        
        print("\n✅ All sauerkraut tests completed!")
        print("\n🎯 Summary:")
        print("  - Sauerkraut should be found in both OpenFoodFacts and common foods")
        print("  - All core nutrients (fiber, sugar, sodium) should be present")
        print("  - Serving size conversion should work correctly")
        print("  - Enhanced search should find results with spelling variations")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
