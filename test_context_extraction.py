#!/usr/bin/env python3
"""
Test context extraction directly
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, _extract_relevant_context

def test_context_extraction():
    """Test the context extraction function directly"""
    print("🧪 Testing Context Extraction Function")
    print("=" * 50)
    
    # Sample context data
    sample_context = {
        'profile': {
            'name': 'Test User',
            'age': 30,
            'health_goals': 'Lose weight and improve mood'
        },
        'food_summary': {
            'total_entries': 5,
            'avg_calories': 350,
            'total_calories': 1750,
            'common_foods': ['apple', 'chicken', 'rice']
        },
        'mood_summary': {
            'total_entries': 7,
            'avg_mood': 7.5,
            'mood_trend': 'improving'
        },
        'water_summary': {
            'total_entries': 7,
            'avg_daily_water': 1800
        }
    }
    
    # Test different question types
    test_cases = [
        ('⚡ Energy foods?', 'food'),
        ('How many calories am I eating?', 'food'),
        ('Is my mood improving?', 'mood'),
        ('Am I drinking enough water?', 'water'),
        ('What are my health goals?', 'minimal'),
        ('Hello, how are you?', 'minimal')
    ]
    
    for message, context_type in test_cases:
        print(f"\nQuestion: '{message}'")
        print(f"Context Type: {context_type}")
        
        relevant_context = _extract_relevant_context(message, sample_context, context_type)
        
        if relevant_context:
            print(f"✓ Relevant Context: {relevant_context}")
        else:
            print("✓ No relevant context (minimal)")
        
        print("-" * 30)

if __name__ == "__main__":
    with app.app_context():
        test_context_extraction()
