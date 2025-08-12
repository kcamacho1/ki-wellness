#!/usr/bin/env python3
"""
Nutritional Data Accuracy Test Script

This script tests the accuracy of nutritional data retrieved from:
1. Open Food Facts API
2. USDA API
3. Unit conversion functions
4. Serving size calculations

Usage:
    python tests/test_nutritional_data.py
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the functions we want to test
from app.main import search_openfoodfacts_api, search_usda_api, convert_nutritional_data, convert_to_grams

# Known nutritional values for testing (per 100g)
KNOWN_FOODS = {
    'apple': {
        'calories': 52,
        'protein': 0.3,
        'carbs': 14,
        'fat': 0.2,
        'fiber': 2.4,
        'sugar': 10.4,
        'source': 'usda'
    },
    'banana': {
        'calories': 89,
        'protein': 1.1,
        'carbs': 23,
        'fat': 0.3,
        'fiber': 2.6,
        'sugar': 12.2,
        'source': 'usda'
    },
    'chicken breast': {
        'calories': 165,
        'protein': 31,
        'carbs': 0,
        'fat': 3.6,
        'fiber': 0,
        'sugar': 0,
        'source': 'usda'
    },
    'brown rice': {
        'calories': 111,
        'protein': 2.6,
        'carbs': 23,
        'fat': 0.9,
        'fiber': 1.8,
        'sugar': 0.4,
        'source': 'usda'
    },
    'almonds': {
        'calories': 579,
        'protein': 21.2,
        'carbs': 21.7,
        'fat': 49.9,
        'fiber': 12.5,
        'sugar': 4.4,
        'source': 'usda'
    }
}

# Test serving sizes and conversions
SERVING_SIZE_TESTS = [
    {'amount': 1, 'unit': 'cup', 'expected_grams': 236.59},
    {'amount': 2, 'unit': 'tbsp', 'expected_grams': 29.58},
    {'amount': 3, 'unit': 'tsp', 'expected_grams': 14.79},
    {'amount': 100, 'unit': 'g', 'expected_grams': 100},
    {'amount': 1, 'unit': 'oz', 'expected_grams': 28.35},
    {'amount': 0.5, 'unit': 'lb', 'expected_grams': 226.795},
]

def test_unit_conversions():
    """Test the convert_to_grams function"""
    print("🧪 Testing Unit Conversions...")
    print("=" * 50)
    
    all_passed = True
    
    for test in SERVING_SIZE_TESTS:
        amount = test['amount']
        unit = test['unit']
        expected = test['expected_grams']
        
        result = convert_to_grams(amount, unit)
        tolerance = 0.01  # Allow small rounding differences
        
        if abs(result - expected) <= tolerance:
            status = "✅ PASS"
        else:
            status = "❌ FAIL"
            all_passed = False
        
        print(f"{status} {amount} {unit} = {result:.2f}g (expected: {expected:.2f}g)")
    
    print(f"\nUnit Conversion Tests: {'✅ ALL PASSED' if all_passed else '❌ SOME FAILED'}")
    return all_passed

def test_nutritional_conversion():
    """Test the convert_nutritional_data function"""
    print("\n🧪 Testing Nutritional Data Conversion...")
    print("=" * 50)
    
    # Test data: 100g apple
    base_nutrition = {
        'food_name': 'Apple',
        'serving_size': 100,
        'serving_unit': 'g',
        'calories': 52,
        'protein': 0.3,
        'carbs': 14,
        'fat': 0.2,
        'fiber': 2.4,
        'sugar': 10.4
    }
    
    # Test converting to 1 cup (236.59g)
    converted = convert_nutritional_data(base_nutrition, 1, 'cup')
    
    if converted:
        print("✅ Conversion successful")
        print(f"   Original: 100g apple")
        print(f"   Converted: 1 cup apple")
        print(f"   Calories: {converted['calories']:.1f} (expected: ~123)")
        print(f"   Protein: {converted['protein']:.1f}g (expected: ~0.7g)")
        print(f"   Carbs: {converted['carbs']:.1f}g (expected: ~33g)")
        print(f"   Fat: {converted['fat']:.1f}g (expected: ~0.5g)")
    else:
        print("❌ Conversion failed")
        return False
    
    return True

def test_api_accuracy(food_name, known_values):
    """Test API accuracy for a specific food"""
    print(f"\n🧪 Testing {food_name.title()}...")
    print("-" * 30)
    
    # Test Open Food Facts API
    print("Testing Open Food Facts API...")
    of_data = search_openfoodfacts_api(food_name)
    
    if of_data:
        print("✅ Open Food Facts API returned data")
        print(f"   Food name: {of_data['food_name']}")
        print(f"   Brand: {of_data['brand']}")
        print(f"   Source: {of_data['source']}")
        
        # Compare with known values
        tolerance = 20  # Allow 20% tolerance for API variations
        
        for nutrient, known_value in known_values.items():
            if nutrient == 'source':
                continue
                
            api_value = of_data.get(nutrient)
            if api_value is not None:
                difference = abs(api_value - known_value)
                percentage_diff = (difference / known_value) * 100 if known_value > 0 else 0
                
                if percentage_diff <= tolerance:
                    status = "✅"
                else:
                    status = "⚠️"
                
                print(f"   {status} {nutrient}: {api_value:.1f} (known: {known_value:.1f}, diff: {percentage_diff:.1f}%)")
            else:
                print(f"   ❌ {nutrient}: No data available")
    else:
        print("❌ Open Food Facts API failed or no data found")
    
    # Test USDA API (if API key is available)
    print("\nTesting USDA API...")
    usda_data = search_usda_api(food_name)
    
    if usda_data:
        print("✅ USDA API returned data")
        print(f"   Food name: {usda_data['food_name']}")
        print(f"   Brand: {usda_data['brand']}")
        print(f"   Source: {usda_data['source']}")
        
        # Compare with known values
        for nutrient, known_value in known_values.items():
            if nutrient == 'source':
                continue
                
            api_value = usda_data.get(nutrient)
            if api_value is not None:
                difference = abs(api_value - known_value)
                percentage_diff = (difference / known_value) * 100 if known_value > 0 else 0
                
                if percentage_diff <= tolerance:
                    status = "✅"
                else:
                    status = "⚠️"
                
                print(f"   {status} {nutrient}: {api_value:.1f} (known: {known_value:.1f}, diff: {percentage_diff:.1f}%)")
            else:
                print(f"   ❌ {nutrient}: No data available")
    else:
        print("❌ USDA API failed or no data found (check USDA_API_KEY environment variable)")

def test_common_foods():
    """Test accuracy for common foods"""
    print("\n🧪 Testing Common Foods Accuracy...")
    print("=" * 50)
    
    for food_name, known_values in KNOWN_FOODS.items():
        test_api_accuracy(food_name, known_values)

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n🧪 Testing Edge Cases...")
    print("=" * 50)
    
    # Test empty/null inputs
    print("Testing empty/null inputs...")
    
    # Test convert_to_grams with invalid units
    result = convert_to_grams(100, 'invalid_unit')
    print(f"Invalid unit test: 100 invalid_unit = {result}g (should default to 100)")
    
    # Test convert_nutritional_data with None
    result = convert_nutritional_data(None, 1, 'cup')
    print(f"None nutrition data test: {result} (should be None)")
    
    # Test with zero serving size
    base_nutrition = {
        'serving_size': 0,
        'serving_unit': 'g',
        'calories': 100
    }
    result = convert_nutritional_data(base_nutrition, 1, 'cup')
    print(f"Zero serving size test: {result} (should be None)")

def generate_test_report():
    """Generate a comprehensive test report"""
    print("📊 NUTRITIONAL DATA ACCURACY TEST REPORT")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python version: {sys.version}")
    print()
    
    # Run all tests
    unit_tests_passed = test_unit_conversions()
    conversion_tests_passed = test_nutritional_conversion()
    test_common_foods()
    test_edge_cases()
    
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    print(f"Unit Conversions: {'✅ PASSED' if unit_tests_passed else '❌ FAILED'}")
    print(f"Nutritional Conversions: {'✅ PASSED' if conversion_tests_passed else '❌ FAILED'}")
    print()
    print("💡 RECOMMENDATIONS:")
    print("1. Check USDA_API_KEY environment variable for USDA API access")
    print("2. Monitor API response times and reliability")
    print("3. Consider caching frequently searched foods")
    print("4. Add data source attribution in the UI")
    print("5. Implement fallback to manual entry when APIs fail")

if __name__ == "__main__":
    generate_test_report()
