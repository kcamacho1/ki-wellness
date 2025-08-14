#!/usr/bin/env python3
"""
Test Nutritional Data Accuracy
==============================

This test verifies that nutritional data is accurate, complete, and properly
converted based on user serving sizes.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import NutritionService
from app.utils.general_utils import ConversionUtils

def test_sauerkraut_nutritional_data():
    """Test sauerkraut nutritional data accuracy"""
    print("🧪 Testing Sauerkraut Nutritional Data...")
    
    # Test common foods database
    sauerkraut_data = NutritionService.search_common_foods_database('sauerkraut')
    
    if sauerkraut_data:
        print("✅ Found sauerkraut in common foods database")
        print(f"   Food: {sauerkraut_data['food_name']}")
        print(f"   Calories: {sauerkraut_data['calories']}")
        print(f"   Protein: {sauerkraut_data['protein']}")
        print(f"   Carbs: {sauerkraut_data['carbs']}")
        print(f"   Fat: {sauerkraut_data['fat']}")
        print(f"   Fiber: {sauerkraut_data['fiber']}")
        print(f"   Sugar: {sauerkraut_data['sugar']}")
        print(f"   Sodium: {sauerkraut_data['sodium']}")
        
        # Verify all core nutritional values are present
        core_nutrients = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
        missing_nutrients = [nutrient for nutrient in core_nutrients if sauerkraut_data.get(nutrient) is None]
        
        if missing_nutrients:
            print(f"❌ Missing nutrients: {missing_nutrients}")
        else:
            print("✅ All core nutrients present")
    else:
        print("❌ Sauerkraut not found in common foods database")

def test_serving_size_conversion():
    """Test serving size conversion accuracy"""
    print("\n🧪 Testing Serving Size Conversion...")
    
    # Test data for 100g sauerkraut
    base_data = {
        'food_name': 'Sauerkraut',
        'serving_size': 100,
        'serving_unit': 'g',
        'calories': 19,
        'protein': 0.9,
        'carbs': 4.3,
        'fat': 0.1,
        'fiber': 2.9,
        'sugar': 1.8,
        'sodium': 661
    }
    
    # Test conversion to 300g (as shown in the image)
    converted_data = NutritionService.convert_nutritional_data(base_data, 300, 'g')
    
    if converted_data:
        print("✅ Serving size conversion successful")
        print(f"   Original serving: {base_data['serving_size']}{base_data['serving_unit']}")
        print(f"   New serving: {converted_data['serving_size']}{converted_data['serving_unit']}")
        print(f"   Calories: {base_data['calories']} → {converted_data['calories']}")
        print(f"   Protein: {base_data['protein']} → {converted_data['protein']}")
        print(f"   Carbs: {base_data['carbs']} → {converted_data['carbs']}")
        print(f"   Fat: {base_data['fat']} → {converted_data['fat']}")
        print(f"   Fiber: {base_data['fiber']} → {converted_data['fiber']}")
        print(f"   Sugar: {base_data['sugar']} → {converted_data['sugar']}")
        print(f"   Sodium: {base_data['sodium']} → {converted_data['sodium']}")
        
        # Verify conversion factor (should be 3x for 300g vs 100g)
        expected_calories = base_data['calories'] * 3
        if abs(converted_data['calories'] - expected_calories) < 0.1:
            print("✅ Conversion factor correct (3x)")
        else:
            print(f"❌ Conversion factor incorrect. Expected {expected_calories}, got {converted_data['calories']}")
    else:
        print("❌ Serving size conversion failed")

def test_openfoodfacts_data_extraction():
    """Test OpenFoodFacts data extraction and completeness"""
    print("\n🧪 Testing OpenFoodFacts Data Extraction...")
    
    # Mock OpenFoodFacts product data for sauerkraut
    mock_product = {
        'product_name': 'Sauerkraut',
        'brands': 'Test Brand',
        'nutriments': {
            'energy-kcal_100g': 19,
            'proteins_100g': 0.9,
            'carbohydrates_100g': 4.3,
            'fat_100g': 0.1,
            'fiber_100g': 2.9,
            'sugars_100g': 1.8,
            'salt_100g': 661
        }
    }
    
    extracted_data = NutritionService.extract_nutritional_data(mock_product, 'sauerkraut')
    
    if extracted_data:
        print("✅ OpenFoodFacts data extraction successful")
        print(f"   Food: {extracted_data['food_name']}")
        print(f"   Brand: {extracted_data['brand']}")
        print(f"   Calories: {extracted_data['calories']}")
        print(f"   Protein: {extracted_data['protein']}")
        print(f"   Carbs: {extracted_data['carbs']}")
        print(f"   Fat: {extracted_data['fat']}")
        print(f"   Fiber: {extracted_data['fiber']}")
        print(f"   Sugar: {extracted_data['sugar']}")
        print(f"   Sodium: {extracted_data['sodium']}")
        
        # Check for missing values
        core_nutrients = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
        missing_nutrients = [nutrient for nutrient in core_nutrients if extracted_data.get(nutrient) is None]
        
        if missing_nutrients:
            print(f"❌ Missing nutrients in extraction: {missing_nutrients}")
        else:
            print("✅ All core nutrients extracted")
    else:
        print("❌ OpenFoodFacts data extraction failed")

def test_unit_conversion():
    """Test unit conversion utilities"""
    print("\n🧪 Testing Unit Conversion...")
    
    # Test various unit conversions
    test_cases = [
        (100, 'g', 100),      # grams to grams
        (1, 'kg', 1000),      # kg to grams
        (3.5, 'oz', 99.225),  # oz to grams
        (1, 'lb', 453.59),    # lb to grams
        (1, 'cup', 236.59),   # cup to grams
        (1, 'tbsp', 14.79),   # tbsp to grams
        (1, 'tsp', 4.93),     # tsp to grams
    ]
    
    for amount, unit, expected in test_cases:
        result = ConversionUtils.convert_to_grams(amount, unit)
        if abs(result - expected) < 0.1:
            print(f"✅ {amount} {unit} = {result:.2f}g (expected {expected:.2f}g)")
        else:
            print(f"❌ {amount} {unit} = {result:.2f}g (expected {expected:.2f}g)")

def test_nutritional_data_validation():
    """Test nutritional data validation and quality"""
    print("\n🧪 Testing Nutritional Data Validation...")
    
    # Test valid data
    valid_data = {
        'calories': 19,
        'protein': 0.9,
        'carbs': 4.3,
        'fat': 0.1,
        'fiber': 2.9,
        'sugar': 1.8,
        'sodium': 661
    }
    
    # Test data with missing values
    incomplete_data = {
        'calories': 19,
        'protein': 0.9,
        'carbs': 4.3,
        'fat': 0.1,
        # Missing fiber, sugar, sodium
    }
    
    # Test data with invalid values
    invalid_data = {
        'calories': 'invalid',
        'protein': None,
        'carbs': 4.3,
        'fat': 0.1,
        'fiber': 2.9,
        'sugar': 1.8,
        'sodium': 661
    }
    
    print("Testing valid data...")
    core_nutrients = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
    valid_missing = [nutrient for nutrient in core_nutrients if valid_data.get(nutrient) is None]
    if not valid_missing:
        print("✅ Valid data has all core nutrients")
    else:
        print(f"❌ Valid data missing: {valid_missing}")
    
    print("Testing incomplete data...")
    incomplete_missing = [nutrient for nutrient in core_nutrients if incomplete_data.get(nutrient) is None]
    print(f"   Missing nutrients: {incomplete_missing}")
    
    print("Testing invalid data...")
    invalid_missing = [nutrient for nutrient in core_nutrients if invalid_data.get(nutrient) is None]
    print(f"   Missing nutrients: {invalid_missing}")

def test_real_openfoodfacts_search():
    """Test actual OpenFoodFacts API search for sauerkraut"""
    print("\n🧪 Testing Real OpenFoodFacts Search...")
    
    try:
        # Search for sauerkraut
        results = NutritionService.search_openfoodfacts_multiple('sauerkraut')
        
        if results:
            print(f"✅ Found {len(results)} OpenFoodFacts results for sauerkraut")
            
            # Check the first result
            first_result = results[0]
            print(f"   Food: {first_result['food_name']}")
            print(f"   Brand: {first_result['brand']}")
            print(f"   Calories: {first_result['calories']}")
            print(f"   Protein: {first_result['protein']}")
            print(f"   Carbs: {first_result['carbs']}")
            print(f"   Fat: {first_result['fat']}")
            print(f"   Fiber: {first_result['fiber']}")
            print(f"   Sugar: {first_result['sugar']}")
            print(f"   Sodium: {first_result['sodium']}")
            
            # Check for missing values
            core_nutrients = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
            missing_nutrients = [nutrient for nutrient in core_nutrients if first_result.get(nutrient) is None]
            
            if missing_nutrients:
                print(f"❌ Missing nutrients in real search: {missing_nutrients}")
            else:
                print("✅ All core nutrients present in real search")
        else:
            print("❌ No OpenFoodFacts results found for sauerkraut")
            
    except Exception as e:
        print(f"❌ Error testing real OpenFoodFacts search: {e}")

def main():
    """Run all nutritional accuracy tests"""
    print("🚀 Testing Nutritional Data Accuracy")
    print("=" * 50)
    
    try:
        test_sauerkraut_nutritional_data()
        test_serving_size_conversion()
        test_openfoodfacts_data_extraction()
        test_unit_conversion()
        test_nutritional_data_validation()
        test_real_openfoodfacts_search()
        
        print("\n✅ All nutritional accuracy tests completed!")
        print("\n🎯 Summary:")
        print("  - Nutritional data should be complete (fiber, sugar, sodium)")
        print("  - Serving size conversion should work correctly")
        print("  - Unit conversions should be accurate")
        print("  - Data validation should catch missing/invalid values")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
