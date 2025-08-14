#!/usr/bin/env python3
"""
Test Decimal Formatting
======================

This test verifies that nutritional values are properly formatted to 2 decimal places.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import NutritionService

def test_decimal_formatting():
    """Test that nutritional values are rounded to 2 decimal places"""
    print("🧪 Testing Decimal Formatting...")
    
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
    
    # Test conversion to 300g (should show 3x values with 2 decimal places)
    converted_data = NutritionService.convert_nutritional_data(base_data, 300, 'g')
    
    if converted_data:
        print("✅ Conversion successful")
        print(f"   Original serving: {base_data['serving_size']}{base_data['serving_unit']}")
        print(f"   New serving: {converted_data['serving_size']}{converted_data['serving_unit']}")
        print(f"   Calories: {base_data['calories']} → {converted_data['calories']}")
        print(f"   Protein: {base_data['protein']} → {converted_data['protein']}")
        print(f"   Carbs: {base_data['carbs']} → {converted_data['carbs']}")
        print(f"   Fat: {base_data['fat']} → {converted_data['fat']}")
        print(f"   Fiber: {base_data['fiber']} → {converted_data['fiber']}")
        print(f"   Sugar: {base_data['sugar']} → {converted_data['sugar']}")
        print(f"   Sodium: {base_data['sodium']} → {converted_data['sodium']}")
        
        # Check that values are properly rounded
        expected_values = {
            'calories': 57.0,
            'protein': 2.7,
            'carbs': 12.9,
            'fat': 0.3,
            'fiber': 8.7,
            'sugar': 5.4,
            'sodium': 1983.0
        }
        
        print("\n   Checking decimal formatting:")
        for field, expected in expected_values.items():
            actual = converted_data[field]
            if abs(actual - expected) < 0.01:  # Allow small rounding differences
                print(f"   ✅ {field}: {actual} (expected ~{expected})")
            else:
                print(f"   ❌ {field}: {actual} (expected ~{expected})")
    else:
        print("❌ Conversion failed")

def test_edge_cases():
    """Test edge cases for decimal formatting"""
    print("\n🧪 Testing Edge Cases...")
    
    # Test with very small values
    small_data = {
        'food_name': 'Test Food',
        'serving_size': 100,
        'serving_unit': 'g',
        'calories': 0.123456789,
        'protein': 0.987654321,
        'carbs': 1.111111111,
        'fat': 0.000000001,
        'fiber': 2.999999999,
        'sugar': 1.500000000,
        'sodium': 100.123456789
    }
    
    # Convert to 50g (should show 0.5x values)
    converted_data = NutritionService.convert_nutritional_data(small_data, 50, 'g')
    
    if converted_data:
        print("✅ Edge case conversion successful")
        print(f"   Calories: {small_data['calories']} → {converted_data['calories']}")
        print(f"   Protein: {small_data['protein']} → {converted_data['protein']}")
        print(f"   Carbs: {small_data['carbs']} → {converted_data['carbs']}")
        print(f"   Fat: {small_data['fat']} → {converted_data['fat']}")
        print(f"   Fiber: {small_data['fiber']} → {converted_data['fiber']}")
        print(f"   Sugar: {small_data['sugar']} → {converted_data['sugar']}")
        print(f"   Sodium: {small_data['sodium']} → {converted_data['sodium']}")
        
        # Check that all values are properly rounded to 2 decimal places
        for field, value in converted_data.items():
            if isinstance(value, (int, float)) and field in ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium']:
                # Check if the value has more than 2 decimal places
                decimal_str = str(value).split('.')
                if len(decimal_str) > 1 and len(decimal_str[1]) > 2:
                    print(f"   ❌ {field}: {value} has more than 2 decimal places")
                else:
                    print(f"   ✅ {field}: {value} properly formatted")
    else:
        print("❌ Edge case conversion failed")

def main():
    """Run all decimal formatting tests"""
    print("🚀 Testing Decimal Formatting")
    print("=" * 40)
    
    try:
        test_decimal_formatting()
        test_edge_cases()
        
        print("\n✅ All decimal formatting tests completed!")
        print("\n🎯 Summary:")
        print("  - Nutritional values should be rounded to 2 decimal places")
        print("  - No excessive decimal digits should be displayed")
        print("  - Edge cases should be handled properly")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
