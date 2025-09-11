/**
 * Recipe Utils Module
 * Utility functions and helpers for recipe management
 */

// Prevent duplicate loading
if (typeof window.RecipeUtils !== 'undefined') {
    // Already loaded, skip silently
} else {
    class RecipeUtils {
    constructor(recipeManager) {
        this.recipeManager = recipeManager;
    }

    validateRecipeData(recipe) {
        // Validate that recipe has all required fields
        if (!recipe || typeof recipe !== 'object') return false;
        if (!recipe.id || typeof recipe.id !== 'number') return false;
        if (!recipe.name || typeof recipe.name !== 'string') return false;
        if (recipe.name.trim().length === 0) return false;
        
        return true;
    }

    async validateRecipeExists(recipeId) {
        try {
            const response = await fetch(`/api/recipes/${recipeId}`);
            const data = await response.json();
            return data.success;
        } catch (error) {
            console.error('Error validating recipe:', error);
            return false;
        }
    }

    clearStaleCache() {
        // Clear any stale cache data
        if (this.recipeManager.recipes) {
            this.recipeManager.recipes = this.recipeManager.recipes.filter(recipe => 
                recipe && recipe.id && recipe.name && 
                typeof recipe.id === 'number' && 
                typeof recipe.name === 'string'
            );
        }
    }

    getCurrentUserId() {
        // Get user ID from meta tag or global variable
        const userIdMeta = document.querySelector('meta[name="user-id"]');
        return userIdMeta ? parseInt(userIdMeta.content) : null;
    }

    getCSRFToken() {
        // Get CSRF token from meta tag
        const csrfMeta = document.querySelector('meta[name="csrf-token"]');
        return csrfMeta ? csrfMeta.content : '';
    }

    convertR2UrlToProxy(url) {
        if (!url) return null;
        
        // If it's already a proxy URL, return as is
        if (url.includes('/api/proxy-image/')) {
            return url;
        }
        
        // If it's an R2 URL, convert to proxy
        if (url.includes('.r2.cloudflarestorage.com') || url.includes('r2.dev')) {
            const encodedUrl = encodeURIComponent(url);
            return `/api/proxy-image/${encodedUrl}`;
        }
        
        // If it's a local URL, return as is
        if (url.startsWith('/static/') || url.startsWith('/uploads/')) {
            return url;
        }
        
        // For external URLs, use proxy
        const encodedUrl = encodeURIComponent(url);
        return `/api/proxy-image/${encodedUrl}`;
    }

    getDefaultImageForCategory(category) {
        // Return a placeholder for recipes without images
        // Real images should be added via the Pexels script
        return '/static/assets/stock-photos/placeholder.jpg';
    }

    // getSmartPlaceholderImage removed - Pexels API only used in separate script

    async loadImageWithFallback(recipe, container) {
        if (!container) return;
        
        const img = container.querySelector('img');
        if (!img) return;
        
        // Prevent infinite loops by tracking if we've already tried fallbacks
        let fallbackAttempted = false;
        
        // Try to load the image
        img.onload = () => {
            img.classList.add('opacity-100');
        };
        
        img.onerror = async () => {
            if (fallbackAttempted) {
                // Already tried fallback, stop here to prevent infinite loop
                console.warn('Image loading failed after fallback attempt:', img.src);
                return;
            }
            
            fallbackAttempted = true;
            
            // Use category-based placeholder image
            img.src = this.getDefaultImageForCategory(recipe.category);
        };
        
        // Set initial source
        const imageUrl = recipe.image_path || recipe.dynamic_image_url;
        if (imageUrl) {
            img.src = this.convertR2UrlToProxy(imageUrl);
        } else {
            img.src = this.getDefaultImageForCategory(recipe.category);
        }
    }

    calculateNutritionFromIngredients(ingredients) {
        let totalCalories = 0;
        let totalProtein = 0;
        let totalCarbs = 0;
        let totalFat = 0;
        let totalFiber = 0;
        let totalSugar = 0;
        let totalSodium = 0;

        ingredients.forEach(ingredient => {
            if (ingredient.calories || ingredient.protein || ingredient.carbs || ingredient.fat) {
                // Use existing nutrition data
                const calories = ingredient.calories || 0;
                const protein = ingredient.protein || 0;
                const carbs = ingredient.carbs || 0;
                const fat = ingredient.fat || 0;
                const fiber = ingredient.fiber || 0;
                const sugar = ingredient.sugar || 0;
                const sodium = ingredient.sodium || 0;
                
                const amount = ingredient.amount || 1;
                totalCalories += calories * amount;
                totalProtein += protein * amount;
                totalCarbs += carbs * amount;
                totalFat += fat * amount;
                totalFiber += fiber * amount;
                totalSugar += sugar * amount;
                totalSodium += sodium * amount;
            } else {
                // Estimate nutrition based on ingredient name
                const estimatedNutrition = this.estimateNutritionForIngredient(ingredient);
                if (estimatedNutrition) {
                    const calories = estimatedNutrition.calories;
                    const protein = estimatedNutrition.protein;
                    const carbs = estimatedNutrition.carbs;
                    const fat = estimatedNutrition.fat;
                    const fiber = estimatedNutrition.fiber;
                    const sugar = estimatedNutrition.sugar;
                    const sodium = estimatedNutrition.sodium;
                    
                    const amount = ingredient.amount || 1;
                    totalCalories += calories * amount;
                    totalProtein += protein * amount;
                    totalCarbs += carbs * amount;
                    totalFat += fat * amount;
                    totalFiber += fiber * amount;
                    totalSugar += sugar * amount;
                    totalSodium += sodium * amount;
                }
            }
        });
        
        return {
            calories: totalCalories,
            protein: totalProtein,
            carbs: totalCarbs,
            fat: totalFat,
            fiber: totalFiber,
            sugar: totalSugar,
            sodium: totalSodium
        };
    }

    estimateNutritionForIngredient(ingredient) {
        const name = (ingredient.name || ingredient.food_name || '').toLowerCase();
        const amount = ingredient.amount || 1;
        const unit = ingredient.unit || 'g';
        
        // Convert to grams for estimation
        let grams = amount;
        if (unit === 'kg') grams = amount * 1000;
        else if (unit === 'oz') grams = amount * 28.35;
        else if (unit === 'lb') grams = amount * 453.59;
        else if (unit === 'cup') grams = amount * 120; // Approximate
        else if (unit === 'tbsp') grams = amount * 15;
        else if (unit === 'tsp') grams = amount * 5;
        else if (unit === 'whole') grams = amount * 100; // Approximate
        else if (unit === 'slice') grams = amount * 25; // Approximate
        else if (unit === 'piece') grams = amount * 50; // Approximate
        
        // Basic nutrition estimates per 100g
        const estimates = {
            'chicken': { calories: 165, protein: 31, carbs: 0, fat: 3.6, fiber: 0, sugar: 0, sodium: 74 },
            'beef': { calories: 250, protein: 26, carbs: 0, fat: 15, fiber: 0, sugar: 0, sodium: 72 },
            'fish': { calories: 206, protein: 22, carbs: 0, fat: 12, fiber: 0, sugar: 0, sodium: 61 },
            'egg': { calories: 155, protein: 13, carbs: 1.1, fat: 11, fiber: 0, sugar: 1.1, sodium: 124 },
            'milk': { calories: 42, protein: 3.4, carbs: 5, fat: 1, fiber: 0, sugar: 5, sodium: 44 },
            'cheese': { calories: 113, protein: 7, carbs: 1, fat: 9, fiber: 0, sugar: 1, sodium: 621 },
            'bread': { calories: 265, protein: 9, carbs: 49, fat: 3.2, fiber: 2.7, sugar: 5.7, sodium: 681 },
            'rice': { calories: 130, protein: 2.7, carbs: 28, fat: 0.3, fiber: 0.4, sugar: 0.1, sodium: 1 },
            'pasta': { calories: 131, protein: 5, carbs: 25, fat: 1.1, fiber: 1.8, sugar: 0.6, sodium: 1 },
            'potato': { calories: 77, protein: 2, carbs: 17, fat: 0.1, fiber: 2.2, sugar: 0.8, sodium: 6 },
            'tomato': { calories: 18, protein: 0.9, carbs: 3.9, fat: 0.2, fiber: 1.2, sugar: 2.6, sodium: 5 },
            'onion': { calories: 40, protein: 1.1, carbs: 9.3, fat: 0.1, fiber: 1.7, sugar: 4.2, sodium: 4 },
            'carrot': { calories: 41, protein: 0.9, carbs: 9.6, fat: 0.2, fiber: 2.8, sugar: 4.7, sodium: 69 },
            'apple': { calories: 52, protein: 0.3, carbs: 14, fat: 0.2, fiber: 2.4, sugar: 10, sodium: 1 },
            'banana': { calories: 89, protein: 1.1, carbs: 23, fat: 0.3, fiber: 2.6, sugar: 12, sodium: 1 },
            'oil': { calories: 884, protein: 0, carbs: 0, fat: 100, fiber: 0, sugar: 0, sodium: 0 },
            'butter': { calories: 717, protein: 0.9, carbs: 0.1, fat: 81, fiber: 0, sugar: 0.1, sodium: 11 },
            'sugar': { calories: 387, protein: 0, carbs: 100, fat: 0, fiber: 0, sugar: 100, sodium: 1 },
            'salt': { calories: 0, protein: 0, carbs: 0, fat: 0, fiber: 0, sugar: 0, sodium: 38758 }
        };
        
        // Find matching ingredient
        for (const [key, nutrition] of Object.entries(estimates)) {
            if (name.includes(key)) {
                const factor = grams / 100; // Convert to per-gram basis
                return {
                    calories: nutrition.calories * factor,
                    protein: nutrition.protein * factor,
                    carbs: nutrition.carbs * factor,
                    fat: nutrition.fat * factor,
                    fiber: nutrition.fiber * factor,
                    sugar: nutrition.sugar * factor,
                    sodium: nutrition.sodium * factor
                };
            }
        }
        
        // Default estimate for unknown ingredients
        return {
            calories: grams * 1.5, // Rough estimate
            protein: grams * 0.1,
            carbs: grams * 0.2,
            fat: grams * 0.05,
            fiber: grams * 0.02,
            sugar: grams * 0.1,
            sodium: grams * 0.5
        };
    }

    showToast(message, type = 'info') {
        // Use the global showToast function
        if (typeof showToast === 'function') {
            showToast(message, type);
        } else {
            console.log(`${type.toUpperCase()}: ${message}`);
        }
    }
}

    // Export for use in other modules
    window.RecipeUtils = RecipeUtils;
}
