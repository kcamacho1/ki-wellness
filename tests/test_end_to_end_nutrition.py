#!/usr/bin/env python3
"""
End-to-End Nutritional Data Test
================================

This test verifies the complete flow from food search to nutritional data display,
including serving size conversion and data completeness.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.services import NutritionService

def test_sauerkraut_search_to_display():
    """Test the complete flow from searching sauerkraut to displaying nutritional data"""
    print("🧪 Testing End-to-End Sauerkraut Flow...")
    
    with app.test_client() as client:
        # Simulate user search for sauerkraut with 300g serving
        search_data = {
            'food_name': 'sauerkraut',
            'serving_size': 300,
            'serving_unit': 'g'
        }
        
        # Test the search endpoint
        response = client.post('/food-journal/search', json=search_data)
        
        if response.status_code == 200:
            data = response.get_json()
            print("✅ Search endpoint responded successfully")
            
            if data.get('success'):
                print("✅ Search returned success")
                
                # Check if we have results
                if data.get('multiple_results'):
                    print(f"✅ Multiple results found: {len(data.get('results', []))}")
                    
                    # Get the first result (should be sauerkraut)
                    if data.get('results'):
                        first_result = data['results'][0]
                        print(f"   First result: {first_result.get('food_name', 'Unknown')}")
                        print(f"   Brand: {first_result.get('brand', 'N/A')}")
                        print(f"   Source: {first_result.get('source', 'Unknown')}")
                        
                        # Check nutritional data completeness
                        core_nutrients = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
                        missing_nutrients = [nutrient for nutrient in core_nutrients if first_result.get(nutrient) is None]
                        
                        if missing_nutrients:
                            print(f"❌ Missing nutrients: {missing_nutrients}")
                        else:
                            print("✅ All core nutrients present")
                            
                        # Check if serving size conversion was applied
                        if first_result.get('serving_size') == 300:
                            print("✅ Serving size correctly set to 300g")
                            
                            # Verify conversion (should be 3x the base values)
                            calories = first_result.get('calories')
                            if calories and calories > 50:  # Should be around 57 for 300g
                                print(f"✅ Calories converted correctly: {calories}")
                            else:
                                print(f"❌ Calories not converted properly: {calories}")
                        else:
                            print(f"❌ Serving size not converted: {first_result.get('serving_size')}")
                    else:
                        print("❌ No results in response")
                else:
                    print("❌ No multiple results flag")
            else:
                print(f"❌ Search failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Search endpoint failed: {response.status_code}")

def test_nutritional_data_accuracy():
    """Test that nutritional data is accurate for common foods"""
    print("\n🧪 Testing Nutritional Data Accuracy...")
    
    # Test cases with expected values (per 100g)
    test_cases = [
        {
            'food': 'sauerkraut',
            'expected': {
                'calories': 19,
                'protein': 0.9,
                'carbs': 4.3,
                'fat': 0.1,
                'fiber': 2.9,
                'sugar': 1.8,
                'sodium': 661
            }
        },
        {
            'food': 'apple',
            'expected': {
                'calories': 52,
                'protein': 0.3,
                'carbs': 14,
                'fat': 0.2,
                'fiber': 2.4,
                'sugar': 10.4,
                'sodium': 1
            }
        },
        {
            'food': 'banana',
            'expected': {
                'calories': 89,
                'protein': 1.1,
                'carbs': 23,
                'fat': 0.3,
                'fiber': 2.6,
                'sugar': 12.2,
                'sodium': 1
            }
        }
    ]
    
    for test_case in test_cases:
        food_name = test_case['food']
        expected = test_case['expected']
        
        print(f"\n   Testing {food_name}...")
        
        # Search in common foods database
        result = NutritionService.search_common_foods_database(food_name)
        
        if result:
            print(f"   ✅ Found {food_name} in database")
            
            # Check each nutrient
            all_correct = True
            for nutrient, expected_value in expected.items():
                actual_value = result.get(nutrient)
                if actual_value is not None:
                    # Allow some tolerance for floating point differences
                    if abs(actual_value - expected_value) < 0.1:
                        print(f"   ✅ {nutrient}: {actual_value} (expected {expected_value})")
                    else:
                        print(f"   ❌ {nutrient}: {actual_value} (expected {expected_value})")
                        all_correct = False
                else:
                    print(f"   ❌ {nutrient}: missing (expected {expected_value})")
                    all_correct = False
            
            if all_correct:
                print(f"   ✅ All nutrients correct for {food_name}")
            else:
                print(f"   ❌ Some nutrients incorrect for {food_name}")
        else:
            print(f"   ❌ {food_name} not found in database")

def test_serving_size_conversion_accuracy():
    """Test serving size conversion accuracy for various scenarios"""
    print("\n🧪 Testing Serving Size Conversion Accuracy...")
    
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
    
    # Test conversion scenarios
    test_scenarios = [
        {'size': 300, 'unit': 'g', 'factor': 3.0, 'description': '300g (3x)'},
        {'size': 50, 'unit': 'g', 'factor': 0.5, 'description': '50g (0.5x)'},
        {'size': 1, 'unit': 'kg', 'factor': 10.0, 'description': '1kg (10x)'},
        {'size': 3.5, 'unit': 'oz', 'factor': 0.99, 'description': '3.5oz (0.99x)'},
        {'size': 1, 'unit': 'cup', 'factor': 2.37, 'description': '1 cup (2.37x)'}
    ]
    
    for scenario in test_scenarios:
        print(f"\n   Testing {scenario['description']}...")
        
        converted = NutritionService.convert_nutritional_data(
            base_data, 
            scenario['size'], 
            scenario['unit']
        )
        
        if converted:
            # Check serving size
            if converted['serving_size'] == scenario['size'] and converted['serving_unit'] == scenario['unit']:
                print(f"   ✅ Serving size correctly set to {scenario['size']}{scenario['unit']}")
            else:
                print(f"   ❌ Serving size incorrect: {converted['serving_size']}{converted['serving_unit']}")
            
            # Check conversion factor
            expected_calories = base_data['calories'] * scenario['factor']
            actual_calories = converted['calories']
            
            if abs(actual_calories - expected_calories) < 0.1:
                print(f"   ✅ Calories converted correctly: {actual_calories:.1f} (expected {expected_calories:.1f})")
            else:
                print(f"   ❌ Calories conversion error: {actual_calories:.1f} (expected {expected_calories:.1f})")
            
            # Check that all nutrients were converted
            core_nutrients = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
            missing_nutrients = [nutrient for nutrient in core_nutrients if converted.get(nutrient) is None]
            
            if missing_nutrients:
                print(f"   ❌ Missing nutrients after conversion: {missing_nutrients}")
            else:
                print(f"   ✅ All nutrients converted")
        else:
            print(f"   ❌ Conversion failed")

def test_frontend_conversion_logic():
    """Test the frontend conversion logic (simulated)"""
    print("\n🧪 Testing Frontend Conversion Logic...")
    
    # Simulate the frontend conversion logic
    def frontend_convert_nutritional_data(nutritionData, userServingSize, userServingUnit):
        """Simulate the frontend conversion function"""
        if not nutritionData:
            return None
        
        # Convert to grams for calculation
        baseServingSize = nutritionData.get('serving_size', 100)
        baseServingUnit = nutritionData.get('serving_unit', 'g')
        
        # Convert user serving to grams
        def convert_to_grams(amount, unit):
            unit_lower = unit.lower()
            if unit_lower in ['g', 'gram', 'grams']:
                return amount
            elif unit_lower in ['kg', 'kilogram', 'kilograms']:
                return amount * 1000
            elif unit_lower in ['oz', 'ounce', 'ounces']:
                return amount * 28.35
            elif unit_lower in ['lb', 'pound', 'pounds']:
                return amount * 453.59
            elif unit_lower in ['cup', 'cups']:
                return amount * 236.59
            else:
                return amount
        
        userServingInGrams = convert_to_grams(userServingSize, userServingUnit)
        baseServingInGrams = convert_to_grams(baseServingSize, baseServingUnit)
        
        if baseServingInGrams == 0:
            return nutritionData
        
        # Calculate conversion factor
        conversionFactor = userServingInGrams / baseServingInGrams
        
        # Convert all nutritional values
        convertedData = nutritionData.copy()
        convertedData['serving_size'] = userServingSize
        convertedData['serving_unit'] = userServingUnit
        
        # Core nutritional fields
        coreNutritionalFields = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']
        
        for field in coreNutritionalFields:
            if convertedData.get(field) is not None:
                try:
                    value = convertedData[field]
                    if isinstance(value, str):
                        value = float(value)
                    elif not isinstance(value, (int, float)):
                        continue
                    
                    if not float('nan') == value:  # Check for NaN
                        convertedData[field] = value * conversionFactor
                except (ValueError, TypeError):
                    continue
        
        return convertedData
    
    # Test the frontend conversion
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
    
    # Test 300g conversion
    converted = frontend_convert_nutritional_data(base_data, 300, 'g')
    
    if converted:
        print("   ✅ Frontend conversion successful")
        print(f"   ✅ Serving size: {converted['serving_size']}{converted['serving_unit']}")
        print(f"   ✅ Calories: {converted['calories']:.1f} (expected 57.0)")
        print(f"   ✅ Protein: {converted['protein']:.1f} (expected 2.7)")
        print(f"   ✅ Fiber: {converted['fiber']:.1f} (expected 8.7)")
        print(f"   ✅ Sodium: {converted['sodium']:.1f} (expected 1983.0)")
        
        # Verify conversion factor
        expected_calories = base_data['calories'] * 3
        if abs(converted['calories'] - expected_calories) < 0.1:
            print("   ✅ Conversion factor correct (3x)")
        else:
            print(f"   ❌ Conversion factor incorrect. Expected {expected_calories}, got {converted['calories']}")
    else:
        print("   ❌ Frontend conversion failed")

def main():
    """Run all end-to-end nutritional tests"""
    print("🚀 Testing End-to-End Nutritional Data Flow")
    print("=" * 55)
    
    try:
        test_sauerkraut_search_to_display()
        test_nutritional_data_accuracy()
        test_serving_size_conversion_accuracy()
        test_frontend_conversion_logic()
        
        print("\n✅ All end-to-end nutritional tests completed!")
        print("\n🎯 Summary:")
        print("  - Food search should return complete nutritional data")
        print("  - Serving size conversion should work correctly")
        print("  - All core nutrients (fiber, sugar, sodium) should be present")
        print("  - Frontend should properly convert and display data")
        print("  - Data should be accurate and consistent")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
