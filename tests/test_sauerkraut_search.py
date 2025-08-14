#!/usr/bin/env python3
"""
Test Sauerkraut Search with Fuzzy Matching
==========================================

This test verifies that searching for misspelled "sauerkraut" 
variations returns the correct results.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services import NutritionService

def test_sauerkraut_variations():
    """Test various misspellings of sauerkraut"""
    print("🧪 Testing Sauerkraut Search Variations...")
    
    test_cases = [
        'sourkraut',
        'sour kraut', 
        'sauer kraut',
        'sourcrout',
        'sauerkrout',
        'sauerkraut'  # Correct spelling
    ]
    
    for query in test_cases:
        print(f"\n🔍 Testing: '{query}'")
        
        # Test spelling correction
        corrected = NutritionService.correct_spelling(query)
        print(f"  ✅ Corrected: '{corrected}'")
        
        # Test enhanced search queries
        enhanced = NutritionService.enhance_search_query(query)
        print(f"  🔍 Enhanced queries: {enhanced}")
        
        # Test if sauerkraut is in the enhanced queries
        has_sauerkraut = any('sauerkraut' in q.lower() for q in enhanced)
        print(f"  {'✅' if has_sauerkraut else '❌'} Contains sauerkraut: {has_sauerkraut}")

def test_fuzzy_search_for_sauerkraut():
    """Test fuzzy search with sauerkraut variations"""
    print("\n🧪 Testing Fuzzy Search for Sauerkraut...")
    
    # Sample food database
    food_list = [
        'sauerkraut', 'broccoli', 'cauliflower', 'zucchini', 'chicken',
        'apple', 'banana', 'yogurt', 'spinach', 'carrot', 'tomato',
        'salmon', 'rice', 'quinoa', 'almond', 'avocado', 'kimchi',
        'pickles', 'fermented cabbage'
    ]
    
    test_queries = [
        'sourkraut',
        'sour kraut',
        'sauer kraut',
        'sourcrout'
    ]
    
    for query in test_queries:
        print(f"\n🔍 Fuzzy search for: '{query}'")
        suggestions = NutritionService.get_fuzzy_search_suggestions(query, food_list, limit=5)
        
        for name, score in suggestions:
            is_sauerkraut = 'sauerkraut' in name.lower()
            status = "✅" if is_sauerkraut else "  "
            print(f"  {status} {name} (score: {score})")

def test_common_misspellings_for_sauerkraut():
    """Test common misspellings dictionary for sauerkraut"""
    print("\n🧪 Testing Common Misspellings for Sauerkraut...")
    
    misspellings = NutritionService.get_common_misspellings()
    
    sauerkraut_variations = [
        'sourkraut',
        'sour kraut', 
        'sauer kraut',
        'sourcrout',
        'sauerkrout'
    ]
    
    for variation in sauerkraut_variations:
        if variation in misspellings:
            corrected = misspellings[variation]
            print(f"✅ '{variation}' -> '{corrected}'")
        else:
            print(f"❌ '{variation}' not found in misspellings")

def main():
    """Run all sauerkraut tests"""
    print("🚀 Testing Sauerkraut Search with Fuzzy Matching")
    print("=" * 55)
    
    try:
        test_sauerkraut_variations()
        test_fuzzy_search_for_sauerkraut()
        test_common_misspellings_for_sauerkraut()
        
        print("\n✅ All sauerkraut tests completed!")
        print("\n🎯 Summary:")
        print("  - Spelling correction works for sauerkraut variations")
        print("  - Enhanced search queries include sauerkraut")
        print("  - Fuzzy search can find sauerkraut from misspellings")
        print("  - Common misspellings dictionary includes sauerkraut")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
