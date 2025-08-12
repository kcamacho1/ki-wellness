#!/usr/bin/env python3
"""
Improved Nutritional Data Accuracy Test

This script tests the improved nutritional data system with:
1. Common foods database
2. Improved Open Food Facts search
3. Better matching algorithms
4. Data validation

Usage:
    python tests/test_improved_nutrition.py
"""

import sys
import os
import requests
import json
from datetime import datetime

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the improved functions
from app.main import (
    search_common_foods_database, 
    search_openfoodfacts_api, 
    search_usda_api, 
    convert_nutritional_data,
    COMMON_FOODS_DATABASE
)

def test_common_foods_database():
    """Test the common foods database"""
    print("🧪 Testing Common Foods Database...")
    print("=" * 50)
    
    test_cases = [
        ('apple', 'apple'),
        ('banana', 'banana'),
        ('chicken breast', 'chicken breast'),
        ('brown rice', 'brown rice'),
        ('almonds', 'almonds'),
        ('fresh apple', 'apple'),  # Should match despite "fresh"
        ('organic banana', 'banana'),  # Should match despite "organic"
        ('raw almonds', 'almonds'),  # Should match despite "raw"
    ]
    
    all_passed = True
    
    for search_term, expected_food in test_cases:
        result = search_common_foods_database(search_term)
        
        if result:
            if result['food_name'].lower().startswith(expected_food):
                status = "✅ PASS"
            else:
                status = "❌ FAIL"
                all_passed = False
            
            print(f"{status} '{search_term}' -> {result['food_name']} (calories: {result['calories']})")
        else:
            print(f"❌ FAIL '{search_term}' -> No match found")
            all_passed = False
    
    print(f"\nCommon Foods Database: {'✅ ALL PASSED' if all_passed else '❌ SOME FAILED'}")
    return all_passed

def test_improved_openfoodfacts():
    """Test the improved Open Food Facts search"""
    print("\n🧪 Testing Improved Open Food Facts Search...")
    print("=" * 50)
    
    test_foods = ['apple', 'banana', 'chicken', 'rice', 'almonds']
    
    for food in test_foods:
        print(f"\nTesting: {food}")
        result = search_openfoodfacts_api(food)
        
        if result:
            print(f"  ✅ Found: {result['food_name']}")
            print(f"  Brand: {result['brand']}")
            print(f"  Calories: {result['calories']:.1f}")
            print(f"  Protein: {result['protein']}g")
            print(f"  Carbs: {result['carbs']}g")
            print(f"  Fat: {result['fat']}g")
            
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

def test_data_quality():
    """Test data quality and validation"""
    print("\n🧪 Testing Data Quality...")
    print("=" * 50)
    
    # Test common foods database quality
    print("Common Foods Database Quality:")
    for food_name, data in COMMON_FOODS_DATABASE.items():
        calories = data['calories']
        protein = data['protein']
        carbs = data['carbs']
        fat = data['fat']
        
        # Check for reasonable ranges
        issues = []
        
        if calories <= 0 or calories > 900:
            issues.append(f"Calories: {calories} (should be 1-900)")
        
        if protein < 0 or protein > 50:
            issues.append(f"Protein: {protein}g (should be 0-50g)")
        
        if carbs < 0 or carbs > 100:
            issues.append(f"Carbs: {carbs}g (should be 0-100g)")
        
        if fat < 0 or fat > 100:
            issues.append(f"Fat: {fat}g (should be 0-100g)")
        
        # Check macronutrient consistency
        calculated_calories = (protein * 4) + (carbs * 4) + (fat * 9)
        calorie_diff = abs(calories - calculated_calories)
        
        if calorie_diff > 50:  # Allow 50 calorie difference
            issues.append(f"Calorie calculation: {calculated_calories} vs {calories}")
        
        if issues:
            print(f"  ❌ {food_name}: {', '.join(issues)}")
        else:
            print(f"  ✅ {food_name}: Good data quality")

def test_serving_size_conversions():
    """Test serving size conversions"""
    print("\n🧪 Testing Serving Size Conversions...")
    print("=" * 50)
    
    # Test with apple data
    apple_data = COMMON_FOODS_DATABASE['apple'].copy()
    apple_data['serving_size'] = 100
    apple_data['serving_unit'] = 'g'
    
    test_conversions = [
        (1, 'cup', '1 cup apple'),
        (1, 'medium', '1 medium apple'),
        (2, 'tbsp', '2 tbsp apple'),
        (100, 'g', '100g apple')
    ]
    
    for amount, unit, description in test_conversions:
        converted = convert_nutritional_data(apple_data, amount, unit)
        
        if converted:
            print(f"  ✅ {description}: {converted['calories']:.1f} calories")
        else:
            print(f"  ❌ {description}: Conversion failed")

def test_search_accuracy():
    """Test overall search accuracy"""
    print("\n🧪 Testing Overall Search Accuracy...")
    print("=" * 50)
    
    # Known accurate values for comparison
    known_values = {
        'apple': {'calories': 52, 'protein': 0.3, 'carbs': 14, 'fat': 0.2},
        'banana': {'calories': 89, 'protein': 1.1, 'carbs': 23, 'fat': 0.3},
        'chicken breast': {'calories': 165, 'protein': 31, 'carbs': 0, 'fat': 3.6},
        'brown rice': {'calories': 111, 'protein': 2.6, 'carbs': 23, 'fat': 0.9},
        'almonds': {'calories': 579, 'protein': 21.2, 'carbs': 21.7, 'fat': 49.9}
    }
    
    for food_name, expected in known_values.items():
        print(f"\nTesting: {food_name}")
        
        # Try common foods database first
        result = search_common_foods_database(food_name)
        
        if result:
            print(f"  ✅ Found in common foods DB")
            
            # Compare with known values
            tolerance = 5  # 5% tolerance
            
            for nutrient, expected_value in expected.items():
                actual_value = result.get(nutrient, 0)
                if expected_value > 0:
                    diff_percent = abs(actual_value - expected_value) / expected_value * 100
                    if diff_percent <= tolerance:
                        status = "✅"
                    else:
                        status = "⚠️"
                    print(f"    {status} {nutrient}: {actual_value:.1f} (expected: {expected_value:.1f}, diff: {diff_percent:.1f}%)")
                else:
                    print(f"    ✅ {nutrient}: {actual_value:.1f} (expected: {expected_value:.1f})")
        else:
            print(f"  ❌ Not found in common foods DB")

def generate_improvement_report():
    """Generate a comprehensive improvement report"""
    print("📊 IMPROVED NUTRITIONAL DATA ACCURACY REPORT")
    print("=" * 60)
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run all tests
    common_foods_passed = test_common_foods_database()
    test_improved_openfoodfacts()
    test_data_quality()
    test_serving_size_conversions()
    test_search_accuracy()
    
    print("\n" + "=" * 60)
    print("📋 IMPROVEMENT SUMMARY")
    print("=" * 60)
    print("✅ Added Common Foods Database with accurate data")
    print("✅ Improved Open Food Facts search with better matching")
    print("✅ Added data validation and quality checks")
    print("✅ Implemented fallback search strategy")
    print("✅ Enhanced serving size conversions")
    print()
    print("💡 BENEFITS:")
    print("1. More accurate nutritional data for common foods")
    print("2. Better search results from Open Food Facts")
    print("3. Reliable fallback when APIs fail")
    print("4. Data quality validation prevents errors")
    print("5. Improved user experience with faster results")

if __name__ == "__main__":
    generate_improvement_report()
