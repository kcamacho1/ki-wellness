#!/usr/bin/env python3
"""
Manual Nutritional Data Test Script

This script allows you to manually test specific food items and compare
the results with known nutritional values.

Usage:
    python tests/manual_nutrition_test.py
"""

import sys
import os

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the functions we want to test
from app.main import search_openfoodfacts_api, search_usda_api, convert_nutritional_data

def test_specific_food(food_name, serving_size=100, serving_unit='g'):
    """Test a specific food item"""
    print(f"\n🧪 Testing: {food_name}")
    print(f"   Serving: {serving_size} {serving_unit}")
    print("=" * 50)
    
    # Test Open Food Facts API
    print("📊 Open Food Facts API Results:")
    of_data = search_openfoodfacts_api(food_name)
    
    if of_data:
        print(f"   ✅ Found: {of_data['food_name']}")
        print(f"   Brand: {of_data['brand']}")
        print(f"   Per 100g:")
        print(f"     Calories: {of_data['calories']:.1f}")
        print(f"     Protein: {of_data['protein']:.1f}g")
        print(f"     Carbs: {of_data['carbs']:.1f}g")
        print(f"     Fat: {of_data['fat']:.1f}g")
        print(f"     Fiber: {of_data['fiber']:.1f}g")
        print(f"     Sugar: {of_data['sugar']:.1f}g")
        
        # Convert to user's serving size
        if serving_size != 100 or serving_unit != 'g':
            converted = convert_nutritional_data(of_data, serving_size, serving_unit)
            if converted:
                print(f"\n   For {serving_size} {serving_unit}:")
                print(f"     Calories: {converted['calories']:.1f}")
                print(f"     Protein: {converted['protein']:.1f}g")
                print(f"     Carbs: {converted['carbs']:.1f}g")
                print(f"     Fat: {converted['fat']:.1f}g")
    else:
        print("   ❌ No data found")
    
    # Test USDA API
    print(f"\n📊 USDA API Results:")
    usda_data = search_usda_api(food_name)
    
    if usda_data:
        print(f"   ✅ Found: {usda_data['food_name']}")
        print(f"   Brand: {usda_data['brand']}")
        print(f"   Per 100g:")
        print(f"     Calories: {usda_data['calories']:.1f}")
        print(f"     Protein: {usda_data['protein']:.1f}g")
        print(f"     Carbs: {usda_data['carbs']:.1f}g")
        print(f"     Fat: {usda_data['fat']:.1f}g")
        print(f"     Fiber: {usda_data['fiber']:.1f}g")
        print(f"     Sugar: {usda_data['sugar']:.1f}g")
        
        # Convert to user's serving size
        if serving_size != 100 or serving_unit != 'g':
            converted = convert_nutritional_data(usda_data, serving_size, serving_unit)
            if converted:
                print(f"\n   For {serving_size} {serving_unit}:")
                print(f"     Calories: {converted['calories']:.1f}")
                print(f"     Protein: {converted['protein']:.1f}g")
                print(f"     Carbs: {converted['carbs']:.1f}g")
                print(f"     Fat: {converted['fat']:.1f}g")
    else:
        print("   ❌ No data found (check USDA_API_KEY environment variable)")

def interactive_test():
    """Interactive testing mode"""
    print("🍎 Manual Nutritional Data Testing")
    print("=" * 40)
    print("Enter food items to test (or 'quit' to exit)")
    print()
    
    while True:
        food_name = input("Enter food name: ").strip()
        
        if food_name.lower() in ['quit', 'exit', 'q']:
            break
        
        if not food_name:
            continue
        
        # Get serving size
        try:
            serving_input = input("Enter serving size (default: 100g): ").strip()
            if serving_input:
                if ' ' in serving_input:
                    parts = serving_input.split(' ')
                    serving_size = float(parts[0])
                    serving_unit = parts[1]
                else:
                    serving_size = float(serving_input)
                    serving_unit = 'g'
            else:
                serving_size = 100
                serving_unit = 'g'
        except ValueError:
            print("Invalid serving size, using 100g")
            serving_size = 100
            serving_unit = 'g'
        
        test_specific_food(food_name, serving_size, serving_unit)
        print("\n" + "-" * 50)

def quick_test():
    """Quick test of common foods"""
    test_foods = [
        ("apple", 100, "g"),
        ("banana", 1, "medium"),
        ("chicken breast", 100, "g"),
        ("brown rice", 1, "cup"),
        ("almonds", 1, "oz"),
        ("yogurt", 1, "cup"),
        ("spinach", 1, "cup"),
        ("salmon", 100, "g"),
        ("quinoa", 1, "cup"),
        ("avocado", 1, "medium")
    ]
    
    print("🍎 Quick Test of Common Foods")
    print("=" * 40)
    
    for food_name, serving_size, serving_unit in test_foods:
        test_specific_food(food_name, serving_size, serving_unit)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            quick_test()
        else:
            # Test specific food from command line
            food_name = sys.argv[1]
            serving_size = float(sys.argv[2]) if len(sys.argv) > 2 else 100
            serving_unit = sys.argv[3] if len(sys.argv) > 3 else 'g'
            test_specific_food(food_name, serving_size, serving_unit)
    else:
        print("Usage:")
        print("  python tests/manual_nutrition_test.py                    # Interactive mode")
        print("  python tests/manual_nutrition_test.py quick              # Quick test common foods")
        print("  python tests/manual_nutrition_test.py apple 100 g        # Test specific food")
        print()
        interactive_test()
