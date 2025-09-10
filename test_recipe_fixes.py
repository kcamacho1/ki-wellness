#!/usr/bin/env python3
"""
Test script to verify recipe page fixes
Tests that dashboard calls are removed and nutritional profiles are displayed
"""
import os
import re

def test_dashboard_calls_removed():
    """Test that dashboard API calls are removed from recipes.js"""
    print("🧪 Testing Dashboard API Calls Removal")
    print("=" * 50)
    
    with open('static/js/recipes/recipes.js', 'r') as f:
        content = f.read()
    
    # Check for dashboard manager calls
    dashboard_calls = re.findall(r'window\.dashboardManager', content)
    
    if dashboard_calls:
        print(f"❌ Found {len(dashboard_calls)} dashboard manager calls:")
        for call in dashboard_calls:
            print(f"   - {call}")
        return False
    else:
        print("✅ No dashboard manager calls found")
        return True

def test_nutritional_profile_added():
    """Test that nutritional profile rendering is added"""
    print(f"\n🧪 Testing Nutritional Profile Addition")
    print("=" * 50)
    
    with open('static/js/recipes/recipes.js', 'r') as f:
        content = f.read()
    
    # Check for nutritional profile rendering
    has_render_method = 'renderNutritionalProfile(recipe)' in content
    has_nutrition_call = 'this.renderNutritionalProfile(recipe)' in content
    has_nutrition_display = 'Nutrition (per serving)' in content
    
    print(f"✅ renderNutritionalProfile method: {has_render_method}")
    print(f"✅ Method called in displayRecipes: {has_nutrition_call}")
    print(f"✅ Nutrition display text: {has_nutrition_display}")
    
    return has_render_method and has_nutrition_call and has_nutrition_display

def test_modular_architecture():
    """Test that modular architecture is properly implemented"""
    print(f"\n🧪 Testing Modular Architecture")
    print("=" * 50)
    
    # Check if recipes base template exists
    recipes_base_exists = os.path.exists('templates/layouts/recipes_base.html')
    print(f"✅ Recipes base template: {recipes_base_exists}")
    
    # Check if recipes template uses correct base
    with open('templates/recipes/recipes.html', 'r') as f:
        recipes_content = f.read()
    
    uses_correct_base = 'extends "layouts/recipes_base.html"' in recipes_content
    print(f"✅ Uses recipes base template: {uses_correct_base}")
    
    # Check if base.html doesn't load dashboard resources globally
    with open('templates/base.html', 'r') as f:
        base_content = f.read()
    
    no_global_dashboard = 'dashboard-core.js' not in base_content
    print(f"✅ No global dashboard resources: {no_global_dashboard}")
    
    return recipes_base_exists and uses_correct_base and no_global_dashboard

def main():
    """Run all tests"""
    print("🚀 Recipe Page Fixes Test Suite")
    print("=" * 60)
    
    tests = [
        test_dashboard_calls_removed,
        test_nutritional_profile_added,
        test_modular_architecture
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append(False)
    
    print(f"\n📊 Test Results:")
    print(f"   ✅ Passed: {sum(results)}")
    print(f"   ❌ Failed: {len(results) - sum(results)}")
    
    if all(results):
        print(f"\n🎉 All tests passed! Recipe page fixes are working correctly.")
        print(f"✅ Dashboard API calls removed")
        print(f"✅ Nutritional profiles added to recipe cards")
        print(f"✅ Modular architecture implemented")
    else:
        print(f"\n❌ Some tests failed. Please check the issues above.")
    
    return all(results)

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1)
