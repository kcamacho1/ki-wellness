# Food Data for Ki Wellness
# =========================

# Basic foods to prioritize USDA search
BASIC_FOODS = [
    'apple', 'banana', 'chicken', 'rice', 'bread', 'milk', 'eggs', 'beef', 'fish', 'pork', 
    'carrot', 'broccoli', 'spinach', 'tomato', 'potato', 'onion', 'garlic', 'cilantro', 'coriander',
    'coconut', 'almond', 'oat', 'quinoa', 'sweet potato', 'avocado', 'blueberry', 'strawberry',
    'salmon', 'tuna', 'shrimp', 'turkey', 'lentil', 'bean', 'pea', 'corn', 'pepper', 'cucumber',
    'lettuce', 'kale', 'cauliflower', 'zucchini', 'mushroom', 'ginger', 'lemon', 'lime', 'orange',
    'olive', 'oil', 'butter', 'ghee'
]

# Fallback food database for common foods
COMMON_FOODS_DB = {
    # Common fruits
    'banana': {
        'name': 'Banana',
        'brand': 'Generic',
        'calories': 89,
        'protein': 1.1,
        'carbs': 22.8,
        'fat': 0.3,
        'fiber': 2.6,
        'sugar': 12.2,
        'sodium': 1,
        'source': 'common_foods'
    },
    'apple': {
        'name': 'Apple',
        'brand': 'Generic',
        'calories': 52,
        'protein': 0.3,
        'carbs': 13.8,
        'fat': 0.2,
        'fiber': 2.4,
        'sugar': 10.4,
        'sodium': 1,
        'source': 'common_foods'
    },
    'orange': {
        'name': 'Orange',
        'brand': 'Generic',
        'calories': 47,
        'protein': 0.9,
        'carbs': 11.8,
        'fat': 0.1,
        'fiber': 2.4,
        'sugar': 9.4,
        'sodium': 0,
        'source': 'common_foods'
    },
    'strawberry': {
        'name': 'Strawberry',
        'brand': 'Generic',
        'calories': 32,
        'protein': 0.7,
        'carbs': 7.7,
        'fat': 0.3,
        'fiber': 2.0,
        'sugar': 4.9,
        'sodium': 1,
        'source': 'common_foods'
    },
    'blueberry': {
        'name': 'Blueberry',
        'brand': 'Generic',
        'calories': 57,
        'protein': 0.7,
        'carbs': 14.5,
        'fat': 0.3,
        'fiber': 2.4,
        'sugar': 10.0,
        'sodium': 1,
        'source': 'common_foods'
    },
    
    # Common vegetables
    'carrot': {
        'name': 'Carrot',
        'brand': 'Generic',
        'calories': 41,
        'protein': 0.9,
        'carbs': 9.6,
        'fat': 0.2,
        'fiber': 2.8,
        'sugar': 4.7,
        'sodium': 69,
        'source': 'common_foods'
    },
    'broccoli': {
        'name': 'Broccoli',
        'brand': 'Generic',
        'calories': 34,
        'protein': 2.8,
        'carbs': 7.0,
        'fat': 0.4,
        'fiber': 2.6,
        'sugar': 1.5,
        'sodium': 33,
        'source': 'common_foods'
    },
    'spinach': {
        'name': 'Spinach',
        'brand': 'Generic',
        'calories': 23,
        'protein': 2.9,
        'carbs': 3.6,
        'fat': 0.4,
        'fiber': 2.2,
        'sugar': 0.4,
        'sodium': 79,
        'source': 'common_foods'
    },
    'tomato': {
        'name': 'Tomato',
        'brand': 'Generic',
        'calories': 18,
        'protein': 0.9,
        'carbs': 3.9,
        'fat': 0.2,
        'fiber': 1.2,
        'sugar': 2.6,
        'sodium': 5,
        'source': 'common_foods'
    },
    'potato': {
        'name': 'Potato',
        'brand': 'Generic',
        'calories': 77,
        'protein': 2.0,
        'carbs': 17.0,
        'fat': 0.1,
        'fiber': 2.2,
        'sugar': 0.8,
        'sodium': 6,
        'source': 'common_foods'
    },
    'cilantro': {
        'name': 'Cilantro',
        'brand': 'Generic',
        'calories': 23,
        'protein': 2.1,
        'carbs': 3.7,
        'fat': 0.5,
        'fiber': 2.8,
        'sugar': 0.9,
        'sodium': 46,
        'source': 'common_foods'
    },
    'coriander': {
        'name': 'Coriander (Cilantro)',
        'brand': 'Generic',
        'calories': 23,
        'protein': 2.1,
        'carbs': 3.7,
        'fat': 0.5,
        'fiber': 2.8,
        'sugar': 0.9,
        'sodium': 46,
        'source': 'common_foods'
    },
    'parsley': {
        'name': 'Parsley',
        'brand': 'Generic',
        'calories': 36,
        'protein': 3.0,
        'carbs': 6.3,
        'fat': 0.8,
        'fiber': 3.3,
        'sugar': 0.9,
        'sodium': 56,
        'source': 'common_foods'
    },
    'basil': {
        'name': 'Basil',
        'brand': 'Generic',
        'calories': 22,
        'protein': 3.2,
        'carbs': 2.6,
        'fat': 0.6,
        'fiber': 1.6,
        'sugar': 0.3,
        'sodium': 4,
        'source': 'common_foods'
    },
    'onion': {
        'name': 'Onion',
        'brand': 'Generic',
        'calories': 40,
        'protein': 1.1,
        'carbs': 9.3,
        'fat': 0.1,
        'fiber': 1.7,
        'sugar': 4.2,
        'sodium': 4,
        'source': 'common_foods'
    },
    'garlic': {
        'name': 'Garlic',
        'brand': 'Generic',
        'calories': 149,
        'protein': 6.4,
        'carbs': 33.0,
        'fat': 0.5,
        'fiber': 2.1,
        'sugar': 1.0,
        'sodium': 17,
        'source': 'common_foods'
    },
    'ginger': {
        'name': 'Ginger',
        'brand': 'Generic',
        'calories': 80,
        'protein': 1.8,
        'carbs': 18.0,
        'fat': 0.8,
        'fiber': 2.0,
        'sugar': 1.7,
        'sodium': 13,
        'source': 'common_foods'
    },
    
    # Common proteins
    'eggs': {
        'name': 'Eggs',
        'brand': 'Generic',
        'calories': 155,
        'protein': 12.6,
        'carbs': 1.1,
        'fat': 11.3,
        'fiber': 0,
        'sugar': 1.1,
        'sodium': 124,
        'source': 'common_foods'
    },
    'salmon': {
        'name': 'Salmon',
        'brand': 'Generic',
        'calories': 208,
        'protein': 25.0,
        'carbs': 0,
        'fat': 12.0,
        'fiber': 0,
        'sugar': 0,
        'sodium': 59,
        'source': 'common_foods'
    },
    
    # Common grains
    'rice': {
        'name': 'White Rice',
        'brand': 'Generic',
        'calories': 130,
        'protein': 2.7,
        'carbs': 28.0,
        'fat': 0.3,
        'fiber': 0.4,
        'sugar': 0.1,
        'sodium': 1,
        'source': 'common_foods'
    },
    'bread': {
        'name': 'Whole Wheat Bread',
        'brand': 'Generic',
        'calories': 247,
        'protein': 13.0,
        'carbs': 41.0,
        'fat': 4.2,
        'fiber': 7.0,
        'sugar': 6.0,
        'sodium': 400,
        'source': 'common_foods'
    },
    'oatmeal': {
        'name': 'Oatmeal',
        'brand': 'Generic',
        'calories': 68,
        'protein': 2.4,
        'carbs': 12.0,
        'fat': 1.4,
        'fiber': 1.7,
        'sugar': 0.3,
        'sodium': 49,
        'source': 'common_foods'
    },
    
    # Common dairy
    'milk': {
        'name': 'Whole Milk',
        'brand': 'Generic',
        'calories': 61,
        'protein': 3.2,
        'carbs': 4.8,
        'fat': 3.3,
        'fiber': 0,
        'sugar': 4.8,
        'sodium': 43,
        'source': 'common_foods'
    },
    'yogurt': {
        'name': 'Plain Yogurt',
        'brand': 'Generic',
        'calories': 59,
        'protein': 10.0,
        'carbs': 3.6,
        'fat': 0.4,
        'fiber': 0,
        'sugar': 3.2,
        'sodium': 36,
        'source': 'common_foods'
    },
    'cheese': {
        'name': 'Cheddar Cheese',
        'brand': 'Generic',
        'calories': 113,
        'protein': 7.0,
        'carbs': 0.4,
        'fat': 9.0,
        'fiber': 0,
        'sugar': 0.4,
        'sodium': 176,
        'source': 'common_foods'
    },
    
    # Existing entries
    'coconut milk': {
        'name': 'Coconut Milk',
        'brand': 'Generic',
        'calories': 230,
        'protein': 2.3,
        'carbs': 5.5,
        'fat': 24.0,
        'fiber': 0,
        'sugar': 3.2,
        'sodium': 15,
        'source': 'common_foods'
    },
    'almond milk': {
        'name': 'Almond Milk',
        'brand': 'Generic',
        'calories': 17,
        'protein': 0.6,
        'carbs': 0.6,
        'fat': 1.5,
        'fiber': 0.3,
        'sugar': 0.2,
        'sodium': 7,
        'source': 'common_foods'
    },
    'oat milk': {
        'name': 'Oat Milk',
        'brand': 'Generic',
        'calories': 43,
        'protein': 1.0,
        'carbs': 7.0,
        'fat': 1.5,
        'fiber': 0.8,
        'sugar': 2.5,
        'sodium': 5,
        'source': 'common_foods'
    },
    'soy milk': {
        'name': 'Soy Milk',
        'brand': 'Generic',
        'calories': 33,
        'protein': 3.3,
        'carbs': 1.8,
        'fat': 1.8,
        'fiber': 0.3,
        'sugar': 1.2,
        'sodium': 4,
        'source': 'common_foods'
    },
    'chicken breast': {
        'name': 'Chicken Breast',
        'brand': 'Generic',
        'calories': 165,
        'protein': 31.0,
        'carbs': 0,
        'fat': 3.6,
        'fiber': 0,
        'sugar': 0,
        'sodium': 74,
        'source': 'common_foods'
    },
    'brown rice': {
        'name': 'Brown Rice',
        'brand': 'Generic',
        'calories': 111,
        'protein': 2.6,
        'carbs': 23.0,
        'fat': 0.9,
        'fiber': 1.8,
        'sugar': 0.4,
        'sodium': 5,
        'source': 'common_foods'
    },
    'quinoa': {
        'name': 'Quinoa',
        'brand': 'Generic',
        'calories': 120,
        'protein': 4.4,
        'carbs': 22.0,
        'fat': 1.9,
        'fiber': 2.8,
        'sugar': 0.9,
        'sodium': 7,
        'source': 'common_foods'
    },
    'sweet potato': {
        'name': 'Sweet Potato',
        'brand': 'Generic',
        'calories': 86,
        'protein': 1.6,
        'carbs': 20.0,
        'fat': 0.1,
        'fiber': 3.0,
        'sugar': 4.2,
        'sodium': 41,
        'source': 'common_foods'
    },
    'avocado': {
        'name': 'Avocado',
        'brand': 'Generic',
        'calories': 160,
        'protein': 2.0,
        'carbs': 8.5,
        'fat': 14.7,
        'fiber': 6.7,
        'sugar': 0.7,
        'sodium': 7,
        'source': 'common_foods'
    },
    'olive oil': {
        'name': 'Olive Oil',
        'brand': 'Generic',
        'calories': 884,
        'protein': 0,
        'carbs': 0,
        'fat': 100.0,
        'fiber': 0,
        'sugar': 0,
        'sodium': 2,
        'source': 'common_foods'
    },
    'coconut oil': {
        'name': 'Coconut Oil',
        'brand': 'Generic',
        'calories': 862,
        'protein': 0,
        'carbs': 0,
        'fat': 100.0,
        'fiber': 0,
        'sugar': 0,
        'sodium': 0,
        'source': 'common_foods'
    },
    'butter': {
        'name': 'Butter',
        'brand': 'Generic',
        'calories': 717,
        'protein': 0.9,
        'carbs': 0.1,
        'fat': 81.0,
        'fiber': 0,
        'sugar': 0.1,
        'sodium': 643,
        'source': 'common_foods'
    },
    'ghee': {
        'name': 'Ghee',
        'brand': 'Generic',
        'calories': 900,
        'protein': 0,
        'carbs': 0,
        'fat': 100.0,
        'fiber': 0,
        'sugar': 0,
        'sodium': 0,
        'source': 'common_foods'
    }
}
