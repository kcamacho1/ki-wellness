#!/usr/bin/env python3
"""
Test Fuzzy Search and Spelling Correction
=========================================

This test verifies that the fuzzy search and spelling correction
functionality works correctly for food searches.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import NutritionService

def test_spelling_correction():
    """Test spelling correction functionality"""
    print("🧪 Testing Spelling Correction...")
    
    test_cases = [
        ('sourkraut', 'sauerkraut'),
        ('sour kraut', 'sauerkraut'),
        ('brocolli', 'broccoli'),
        ('cauliflour', 'cauliflower'),
        ('zuchini', 'zucchini'),
        ('chicken breast', 'chicken'),
        ('greek yogurt', 'yogurt'),
        ('red apple', 'apple'),
        ('spinach vegetable', 'spinach'),
    ]
    
    for misspelled, expected in test_cases:
        corrected = NutritionService.correct_spelling(misspelled)
        status = "✅" if corrected == expected else "❌"
        print(f"{status} '{misspelled}' -> '{corrected}' (expected: '{expected}')")

def test_enhanced_search_queries():
    """Test enhanced search query generation"""
    print("\n🧪 Testing Enhanced Search Queries...")
    
    test_cases = [
        'sourkraut',
        'brocolli',
        'zuchini',
        'chicken',
        'apple'
    ]
    
    for query in test_cases:
        enhanced = NutritionService.enhance_search_query(query)
        print(f"🔍 '{query}' -> {enhanced}")

def test_fuzzy_search_suggestions():
    """Test fuzzy search suggestions"""
    print("\n🧪 Testing Fuzzy Search Suggestions...")
    
    # Sample food list
    food_list = [
        'sauerkraut', 'broccoli', 'cauliflower', 'zucchini', 'chicken',
        'apple', 'banana', 'yogurt', 'spinach', 'carrot', 'tomato',
        'salmon', 'rice', 'quinoa', 'almond', 'avocado'
    ]
    
    test_queries = [
        'sourkraut',
        'brocolli',
        'zuchini',
        'chicken breast',
        'red apple'
    ]
    
    for query in test_queries:
        suggestions = NutritionService.get_fuzzy_search_suggestions(query, food_list, limit=3)
        print(f"🔍 '{query}' suggestions: {suggestions}")

def test_common_misspellings():
    """Test common misspellings dictionary"""
    print("\n🧪 Testing Common Misspellings Dictionary...")
    
    misspellings = NutritionService.get_common_misspellings()
    
    # Test some key misspellings
    test_cases = [
        'sourkraut',
        'brocolli',
        'cauliflour',
        'zuchini'
    ]
    
    for misspelled in test_cases:
        if misspelled in misspellings:
            print(f"✅ '{misspelled}' -> '{misspellings[misspelled]}'")
        else:
            print(f"❌ '{misspelled}' not found in misspellings")

def main():
    """Run all tests"""
    print("🚀 Testing Fuzzy Search and Spelling Correction")
    print("=" * 50)
    
    try:
        test_spelling_correction()
        test_enhanced_search_queries()
        test_fuzzy_search_suggestions()
        test_common_misspellings()
        
        print("\n✅ All tests completed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
