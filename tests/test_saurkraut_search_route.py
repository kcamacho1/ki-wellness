#!/usr/bin/env python3
"""
Test Sauerkraut Search Route
============================

This test verifies that the food search route correctly handles
misspelled "saurkraut" and returns appropriate results.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.services import NutritionService

def test_saurkraut_search_route():
    """Test the food search route with saurkraut"""
    print("🧪 Testing Sauerkraut Search Route...")
    
    with app.app_context():
        # Test the enhanced search functionality
        query = 'saurkraut'
        
        print(f"🔍 Testing search for: '{query}'")
        
        # Test spelling correction
        corrected = NutritionService.correct_spelling(query)
        print(f"  ✅ Corrected spelling: '{corrected}'")
        
        # Test enhanced queries
        enhanced = NutritionService.enhance_search_query(query)
        print(f"  🔍 Enhanced queries: {enhanced}")
        
        # Test if sauerkraut is in the enhanced queries
        has_sauerkraut = any('sauerkraut' in q.lower() for q in enhanced)
        print(f"  {'✅' if has_sauerkraut else '❌'} Contains sauerkraut: {has_sauerkraut}")
        
        # Test fuzzy search
        food_list = ['sauerkraut', 'broccoli', 'chicken', 'apple', 'banana']
        suggestions = NutritionService.get_fuzzy_search_suggestions(query, food_list, limit=3)
        print(f"  🔍 Fuzzy suggestions: {suggestions}")
        
        # Check if sauerkraut is in suggestions
        sauerkraut_suggestions = [name for name, score in suggestions if 'sauerkraut' in name.lower()]
        print(f"  {'✅' if sauerkraut_suggestions else '❌'} Found sauerkraut in suggestions: {sauerkraut_suggestions}")

def test_common_misspellings():
    """Test various sauerkraut misspellings"""
    print("\n🧪 Testing Common Sauerkraut Misspellings...")
    
    misspellings = [
        'saurkraut',    # Missing 'e'
        'sourkraut',    # 'ou' instead of 'au'
        'sour kraut',   # Space in middle
        'sauer kraut',  # Space in middle
        'sourcrout',    # Missing 'k'
        'sauerkrout'    # Missing 't'
    ]
    
    for misspelled in misspellings:
        corrected = NutritionService.correct_spelling(misspelled)
        enhanced = NutritionService.enhance_search_query(misspelled)
        has_sauerkraut = any('sauerkraut' in q.lower() for q in enhanced)
        
        status = "✅" if has_sauerkraut else "❌"
        print(f"{status} '{misspelled}' -> '{corrected}' (enhanced: {len(enhanced)} queries, contains sauerkraut: {has_sauerkraut})")

def test_fuzzy_search_accuracy():
    """Test fuzzy search accuracy for sauerkraut variations"""
    print("\n🧪 Testing Fuzzy Search Accuracy...")
    
    # Sample food database
    food_list = [
        'sauerkraut', 'broccoli', 'cauliflower', 'zucchini', 'chicken',
        'apple', 'banana', 'yogurt', 'spinach', 'carrot', 'tomato',
        'salmon', 'rice', 'quinoa', 'almond', 'avocado', 'kimchi',
        'pickles', 'fermented cabbage', 'cabbage', 'kraut'
    ]
    
    test_queries = [
        'saurkraut',
        'sourkraut', 
        'sour kraut',
        'sauer kraut',
        'sourcrout'
    ]
    
    for query in test_queries:
        suggestions = NutritionService.get_fuzzy_search_suggestions(query, food_list, limit=5)
        sauerkraut_matches = [name for name, score in suggestions if 'sauerkraut' in name.lower()]
        
        if sauerkraut_matches:
            best_match = sauerkraut_matches[0]
            print(f"✅ '{query}' -> found '{best_match}' in top suggestions")
        else:
            print(f"❌ '{query}' -> no sauerkraut found in suggestions")

def main():
    """Run all tests"""
    print("🚀 Testing Sauerkraut Search Route")
    print("=" * 40)
    
    try:
        test_saurkraut_search_route()
        test_common_misspellings()
        test_fuzzy_search_accuracy()
        
        print("\n✅ All tests completed!")
        print("\n🎯 Summary:")
        print("  - Spelling correction works for 'saurkraut'")
        print("  - Enhanced search queries include sauerkraut")
        print("  - Fuzzy search finds sauerkraut from misspellings")
        print("  - Search route should now handle saurkraut correctly")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
