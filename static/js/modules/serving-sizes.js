// Predefined Serving Sizes Module
// Common serving sizes for quick food logging
class ServingSizes {
    constructor() {
        this.commonServings = {
            // Bread & Grains
            'bread': [
                { name: '1 slice', amount: 1, unit: 'slice', grams: 28 },
                { name: '2 slices', amount: 2, unit: 'slices', grams: 56 }
            ],
            'toast': [
                { name: '1 slice', amount: 1, unit: 'slice', grams: 28 },
                { name: '2 slices', amount: 2, unit: 'slices', grams: 56 }
            ],
            'bagel': [
                { name: '1/2 bagel', amount: 0.5, unit: 'bagel', grams: 45 },
                { name: '1 whole bagel', amount: 1, unit: 'bagel', grams: 90 }
            ],
            'rice': [
                { name: '1/2 cup cooked', amount: 0.5, unit: 'cup', grams: 90 },
                { name: '1 cup cooked', amount: 1, unit: 'cup', grams: 180 }
            ],
            
            // Fruits
            'apple': [
                { name: '1 medium apple', amount: 1, unit: 'medium', grams: 150 },
                { name: '1 small apple', amount: 1, unit: 'small', grams: 100 }
            ],
            'banana': [
                { name: '1 medium banana', amount: 1, unit: 'medium', grams: 120 },
                { name: '1 small banana', amount: 1, unit: 'small', grams: 90 }
            ],
            'orange': [
                { name: '1 medium orange', amount: 1, unit: 'medium', grams: 130 }
            ],
            
            // Vegetables
            'potato': [
                { name: '1 medium potato', amount: 1, unit: 'medium', grams: 150 },
                { name: '1 small potato', amount: 1, unit: 'small', grams: 100 }
            ],
            'carrot': [
                { name: '1 medium carrot', amount: 1, unit: 'medium', grams: 60 },
                { name: '1 cup chopped', amount: 1, unit: 'cup', grams: 120 }
            ],
            
            // Proteins
            'egg': [
                { name: '1 large egg', amount: 1, unit: 'large', grams: 50 },
                { name: '2 large eggs', amount: 2, unit: 'large', grams: 100 }
            ],
            'chicken breast': [
                { name: '3 oz grilled', amount: 3, unit: 'oz', grams: 85 },
                { name: '4 oz grilled', amount: 4, unit: 'oz', grams: 113 }
            ],
            
            // Snacks
            'crackers': [
                { name: '5 crackers', amount: 5, unit: 'crackers', grams: 15 },
                { name: '10 crackers', amount: 10, unit: 'crackers', grams: 30 }
            ],
            'nuts': [
                { name: '1 oz (small handful)', amount: 1, unit: 'oz', grams: 28 },
                { name: '1/4 cup', amount: 0.25, unit: 'cup', grams: 30 }
            ],
            'pickles': [
                { name: '1 pickle', amount: 1, unit: 'pickle', grams: 35 },
                { name: '3 pickles', amount: 3, unit: 'pickles', grams: 105 },
                { name: '5 pickles', amount: 5, unit: 'pickles', grams: 175 }
            ],
            
            // Dairy
            'milk': [
                { name: '1 cup', amount: 1, unit: 'cup', grams: 240 },
                { name: '1/2 cup', amount: 0.5, unit: 'cup', grams: 120 }
            ],
            'yogurt': [
                { name: '1 cup', amount: 1, unit: 'cup', grams: 240 },
                { name: '6 oz container', amount: 6, unit: 'oz', grams: 170 }
            ],
            'cheese': [
                { name: '1 slice', amount: 1, unit: 'slice', grams: 28 },
                { name: '1 oz', amount: 1, unit: 'oz', grams: 28 }
            ]
        };
        
        // Default serving sizes for foods not in the specific list
        this.defaultServings = [
            { name: '1 cup', amount: 1, unit: 'cup', grams: 150 },
            { name: '1/2 cup', amount: 0.5, unit: 'cup', grams: 75 },
            { name: '1 oz', amount: 1, unit: 'oz', grams: 28 },
            { name: '100g', amount: 100, unit: 'g', grams: 100 }
        ];
    }

    // Get serving size options for a food item
    getServingOptions(foodName) {
        const normalizedName = foodName.toLowerCase().trim();
        
        // Check for exact matches first
        if (this.commonServings[normalizedName]) {
            return this.commonServings[normalizedName];
        }
        
        // Check for partial matches
        for (const [key, servings] of Object.entries(this.commonServings)) {
            if (normalizedName.includes(key) || key.includes(normalizedName)) {
                return servings;
            }
        }
        
        // Return default options if no match found
        return this.defaultServings;
    }

    // Calculate nutrition based on serving size
    calculateNutrition(baseNutrition, selectedServing) {
        if (!baseNutrition || !selectedServing) return baseNutrition;
        
        // Assume base nutrition is per 100g
        const multiplier = selectedServing.grams / 100;
        
        return {
            calories: Math.round((baseNutrition.calories || 0) * multiplier),
            protein: Math.round((baseNutrition.protein || 0) * multiplier * 10) / 10,
            carbs: Math.round((baseNutrition.carbs || 0) * multiplier * 10) / 10,
            fat: Math.round((baseNutrition.fat || 0) * multiplier * 10) / 10,
            fiber: Math.round((baseNutrition.fiber || 0) * multiplier * 10) / 10,
            sugar: Math.round((baseNutrition.sugar || 0) * multiplier * 10) / 10,
            sodium: Math.round((baseNutrition.sodium || 0) * multiplier * 10) / 10
        };
    }

    // Generate HTML for serving size selector
    generateServingSizeSelect(foodName, selectedId = null) {
        const options = this.getServingOptions(foodName);
        
        let html = '<select id="food-serving-size" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ki-green-500 focus:border-transparent">';
        
        options.forEach((serving, index) => {
            const selected = selectedId === index ? 'selected' : '';
            html += `<option value="${index}" ${selected}>${serving.name}</option>`;
        });
        
        html += '</select>';
        return html;
    }

    // Get the selected serving details
    getSelectedServing(foodName, selectedIndex) {
        const options = this.getServingOptions(foodName);
        return options[selectedIndex] || options[0];
    }
}

// Export for use in other modules
window.ServingSizes = ServingSizes;
