// Recipe Management System
if (typeof window.RecipeManager === 'undefined') {
    window.RecipeManager = class RecipeManager {
        constructor() {
            // Prevent multiple instances
            if (window.recipeManager) {
                return window.recipeManager;
            }
            
            this.recipes = [];
            this.currentCategory = 'all';
            this.currentPage = 1;
            this.recipesPerPage = 12;  // Reduced from 20 to 12 for better performance
            this.totalPages = 1;
            this.currentUserId = null;
            this.currentRatingRecipeId = null;
            this.isSearching = false; // Add flag to prevent multiple searches
            this.init();
            
            // Store instance globally
            window.recipeManager = this;
        }

        init() {
            this.getCurrentUserId();
            this.loadMyRecipes(); // Load user's own recipes by default
            this.setupEventListeners();
        }

        showSearchLoading() {
            this.isSearching = true;
            const searchButton = document.getElementById('search-button');
            const searchButtonText = document.getElementById('search-button-text');
            const searchButtonSpinner = document.getElementById('search-button-spinner');
            
            if (searchButton && searchButtonText && searchButtonSpinner) {
                searchButton.disabled = true;
                searchButton.classList.add('opacity-50', 'cursor-not-allowed');
                searchButtonText.textContent = 'Searching...';
                searchButtonSpinner.classList.remove('hidden');
            }
        }

        hideSearchLoading() {
            this.isSearching = false;
            const searchButton = document.getElementById('search-button');
            const searchButtonText = document.getElementById('search-button-text');
            const searchButtonSpinner = document.getElementById('search-button-spinner');
            
            if (searchButton && searchButtonText && searchButtonSpinner) {
                searchButton.disabled = false;
                searchButton.classList.remove('opacity-50', 'cursor-not-allowed');
                searchButtonText.textContent = 'Search';
                searchButtonSpinner.classList.add('hidden');
            }
        }

        showRecipesLoading() {
            const recipesGrid = document.getElementById('recipes-grid');
            if (recipesGrid) {
                recipesGrid.innerHTML = `
                    <div class="loading-state col-span-full text-center py-12">
                        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-ki-green-600 mx-auto mb-4"></div>
                        <p class="text-gray-500">Searching for recipes...</p>
                    </div>
                `;
            }
        }

        hideRecipesLoading() {
            // This will be handled by displayRecipes() when it updates the grid
        }

        refreshRecipeList() {
            // Remove any invalid recipes and refresh the display
            this.recipes = this.recipes.filter(recipe => 
                recipe && recipe.id && recipe.name && 
                typeof recipe.id === 'number' && 
                typeof recipe.name === 'string'
            );
            this.displayRecipes();
        }

        validateRecipeData(recipe) {
            // Validate that recipe has all required fields
            if (!recipe || typeof recipe !== 'object') return false;
            if (!recipe.id || typeof recipe.id !== 'number') return false;
            if (!recipe.name || typeof recipe.name !== 'string') return false;
            if (recipe.id <= 0) return false;
            return true;
        }

        async validateRecipeExists(recipeId) {
            try {
                const response = await fetch(`/api/recipes/${recipeId}`);
                return response.ok;
            } catch (error) {
                console.error(`Error validating recipe ${recipeId}:`, error);
                return false;
            }
        }

        clearStaleCache() {
            // Clear any cached search results that might contain stale data
            if (typeof clear_search_cache === 'function') {
                clear_search_cache();
                // Cache cleared due to stale data
            }
        }

        formatIngredientsPreview(ingredients) {
            if (!ingredients || !Array.isArray(ingredients) || ingredients.length === 0) {
                return '<span class="text-gray-500 text-sm">No ingredients listed</span>';
            }
            
            // Show first 4 ingredients, then indicate if there are more
            const maxIngredients = 4;
            const displayIngredients = ingredients.slice(0, maxIngredients);
            const remainingCount = ingredients.length - maxIngredients;
            
            let ingredientsHtml = displayIngredients.map(ingredient => {
                if (typeof ingredient === 'object' && ingredient.amount && ingredient.unit && (ingredient.food_name || ingredient.name)) {
                    const ingredientName = ingredient.food_name || ingredient.name;
                    return `<span class="inline-block px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-md mr-2 mb-1">${ingredient.amount} ${ingredient.unit} ${ingredientName}</span>`;
                } else if (typeof ingredient === 'string') {
                    return `<span class="inline-block px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded-md mr-2 mb-1">${ingredient}</span>`;
                } else {
                    return '';
                }
            }).filter(html => html).join('');
            
            // Add indicator if there are more ingredients
            if (remainingCount > 0) {
                ingredientsHtml += `<span class="inline-block px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded-md mr-2 mb-1">+${remainingCount} more</span>`;
            }
            
            return ingredientsHtml;
        }

        renderNutritionalProfile(recipe) {
            // Calculate nutrition from ingredients if not provided
            let nutrition = recipe.nutrition;
            if (!nutrition && recipe.ingredients && Array.isArray(recipe.ingredients)) {
                nutrition = this.calculateNutritionFromIngredients(recipe.ingredients);
            }
            
            if (nutrition && (nutrition.calories > 0 || nutrition.protein > 0 || nutrition.carbs > 0 || nutrition.fat > 0)) {
                return `
                    <div class="mb-4">
                        <h5 class="text-sm font-medium text-gray-700 mb-2">Nutrition (per serving):</h5>
                        <div class="grid grid-cols-2 gap-2">
                            <div class="text-center p-2 bg-red-50 rounded-lg">
                                <div class="font-semibold text-red-600 text-sm">${Math.round(nutrition.calories || 0)}</div>
                                <div class="text-xs text-red-500">cal</div>
                            </div>
                            <div class="text-center p-2 bg-blue-50 rounded-lg">
                                <div class="font-semibold text-blue-600 text-sm">${Math.round(nutrition.protein || 0)}g</div>
                                <div class="text-xs text-blue-500">protein</div>
                            </div>
                            <div class="text-center p-2 bg-green-50 rounded-lg">
                                <div class="font-semibold text-green-600 text-sm">${Math.round(nutrition.carbs || 0)}g</div>
                                <div class="text-xs text-green-500">carbs</div>
                            </div>
                            <div class="text-center p-2 bg-yellow-50 rounded-lg">
                                <div class="font-semibold text-yellow-600 text-sm">${Math.round(nutrition.fat || 0)}g</div>
                                <div class="text-xs text-yellow-500">fat</div>
                            </div>
                        </div>
                    </div>
                `;
            } else {
                return `
                    <div class="mb-4">
                        <div class="text-center p-3 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
                            <svg class="w-6 h-6 text-gray-400 mx-auto mb-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                            <p class="text-gray-500 text-xs">Nutritional data not available</p>
                        </div>
                    </div>
                `;
            }
        }

        
        calculateNutritionFromIngredients(ingredients) {
            if (!ingredients || !Array.isArray(ingredients)) {
                return null;
            }
            
            let totalCalories = 0;
            let totalProtein = 0;
            let totalCarbs = 0;
            let totalFat = 0;
            let totalFiber = 0;
            let totalSugar = 0;
            let totalSodium = 0;
            
            ingredients.forEach(ingredient => {
                if (typeof ingredient === 'object' && ingredient.amount) {
                    let calories = ingredient.calories || 0;
                    let protein = ingredient.protein || 0;
                    let carbs = ingredient.carbs || 0;
                    let fat = ingredient.fat || 0;
                    let fiber = ingredient.fiber || 0;
                    let sugar = ingredient.sugar || 0;
                    let sodium = ingredient.sodium || 0;
                    
                    // If no nutritional data, try to estimate from common ingredients
                    if (calories === 0 && protein === 0 && carbs === 0 && fat === 0) {
                        const estimatedNutrition = this.estimateNutritionForIngredient(ingredient);
                        if (estimatedNutrition) {
                            calories = estimatedNutrition.calories;
                            protein = estimatedNutrition.protein;
                            carbs = estimatedNutrition.carbs;
                            fat = estimatedNutrition.fat;
                            fiber = estimatedNutrition.fiber;
                            sugar = estimatedNutrition.sugar;
                            sodium = estimatedNutrition.sodium;
                        }
                    }
                    
                    const amount = ingredient.amount || 1;
                    totalCalories += calories * amount;
                    totalProtein += protein * amount;
                    totalCarbs += carbs * amount;
                    totalFat += fat * amount;
                    totalFiber += fiber * amount;
                    totalSugar += sugar * amount;
                    totalSodium += sodium * amount;
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
            // Basic nutritional estimates for common ingredients (per unit)
            const ingredientName = (ingredient.food_name || ingredient.name || '').toLowerCase();
            const unit = (ingredient.unit || '').toLowerCase();
            
            // Common ingredient nutritional data (per unit)
            const commonIngredients = {
                'chicken': { calories: 165, protein: 31, carbs: 0, fat: 3.6, fiber: 0, sugar: 0, sodium: 74 },
                'chicken breast': { calories: 165, protein: 31, carbs: 0, fat: 3.6, fiber: 0, sugar: 0, sodium: 74 },
                'rice': { calories: 130, protein: 2.7, carbs: 28, fat: 0.3, fiber: 0.4, sugar: 0.1, sodium: 1 },
                'brown rice': { calories: 111, protein: 2.6, carbs: 23, fat: 0.9, fiber: 1.8, sugar: 0.4, sodium: 5 },
                'pasta': { calories: 131, protein: 5, carbs: 25, fat: 1.1, fiber: 1.8, sugar: 0.6, sodium: 1 },
                'olive oil': { calories: 119, protein: 0, carbs: 0, fat: 13.5, fiber: 0, sugar: 0, sodium: 0 },
                'butter': { calories: 102, protein: 0.1, carbs: 0, fat: 11.5, fiber: 0, sugar: 0, sodium: 1 },
                'onion': { calories: 40, protein: 1.1, carbs: 9.3, fat: 0.1, fiber: 1.7, sugar: 4.2, sodium: 4 },
                'garlic': { calories: 149, protein: 6.4, carbs: 33, fat: 0.5, fiber: 2.1, sugar: 1, sodium: 17 },
                'tomato': { calories: 18, protein: 0.9, carbs: 3.9, fat: 0.2, fiber: 1.2, sugar: 2.6, sodium: 5 },
                'carrot': { calories: 41, protein: 0.9, carbs: 9.6, fat: 0.2, fiber: 2.8, sugar: 4.7, sodium: 69 },
                'potato': { calories: 77, protein: 2, carbs: 17, fat: 0.1, fiber: 2.2, sugar: 0.8, sodium: 6 },
                'egg': { calories: 70, protein: 6, carbs: 0.6, fat: 5, fiber: 0, sugar: 0.6, sodium: 70 },
                'milk': { calories: 42, protein: 3.4, carbs: 5, fat: 1, fiber: 0, sugar: 5, sodium: 44 },
                'cheese': { calories: 113, protein: 7, carbs: 1, fat: 9, fiber: 0, sugar: 0.1, sodium: 174 },
                'flour': { calories: 364, protein: 10, carbs: 76, fat: 1, fiber: 2.7, sugar: 0.3, sodium: 2 },
                'sugar': { calories: 387, protein: 0, carbs: 100, fat: 0, fiber: 0, sugar: 100, sodium: 1 },
                'salt': { calories: 0, protein: 0, carbs: 0, fat: 0, fiber: 0, sugar: 0, sodium: 38758 },
                'pepper': { calories: 251, protein: 10, carbs: 64, fat: 3.3, fiber: 25, sugar: 0.6, sodium: 20 },
                'lemon': { calories: 29, protein: 1.1, carbs: 9, fat: 0.3, fiber: 2.8, sugar: 2.5, sodium: 2 }
            };
            
            // Try to find a match
            for (const [key, nutrition] of Object.entries(commonIngredients)) {
                if (ingredientName.includes(key)) {
                    return nutrition;
                }
            }
            
            return null;
        }

        getCurrentUserId() {
            this.currentUserId = window.currentUserId || null;
        }

        getDefaultImageForCategory(category) {
            // Map recipe categories to appropriate stock photos
            const categoryImages = {
                'breakfast': 'smoothie.jpg', // Healthy breakfast options, smoothies
                'lunch': 'salad.jpg', // Light meals, salads
                'dinner': 'pork.jpg', // Main course dishes
                'snack': 'smoothie.jpg', // Healthy snacks, smoothies
                'dessert': 'pasta.jpg', // Sweet treats (using pasta as placeholder)
                'default': 'rice.jpg' // Generic food image
            };
            
            return categoryImages[category] || categoryImages['default'];
        }

        setupEventListeners() {
            // Create Recipe Modal
            const createModal = document.getElementById('create-recipe-modal');
            const createBtn = document.getElementById('create-recipe-btn');
            const closeBtn = document.querySelector('[onclick="closeCreateModal()"]');
            
            if (createBtn) createBtn.addEventListener('click', () => createModal.classList.remove('hidden'));
            if (closeBtn) closeBtn.addEventListener('click', () => createModal.classList.add('hidden'));
            
            // Category filter buttons
            document.querySelectorAll('.recipe-category-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    this.filterByCategory(e.target.dataset.category);
                });
            });
            
            // Search functionality - only on Enter key or button click
            const searchInput = document.getElementById('recipe-search');
            if (searchInput) {
                // Clear search and show all recipes when input is cleared
                searchInput.addEventListener('input', (e) => {
                    if (!e.target.value.trim()) {
                        this.loadRecipes();
                    }
                });
            }

            // Create recipe form submission
            const createForm = document.getElementById('create-recipe-form');
            if (createForm) {
                createForm.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.createRecipe();
                });
            }

            // Image upload handling
            const imageInput = document.getElementById('recipe-image');
            if (imageInput) {
                imageInput.addEventListener('change', (e) => {
                    this.handleImageUpload(e.target.files[0]);
                });
            }
        }

        async loadRecipes() {
            try {
                // Use the new preview endpoint for fast loading with minimal data (includes public recipes)
                const response = await fetch('/api/recipes/preview?include_public=true');
                const data = await response.json();
                
                if (data.success) {
                    // Validate recipe data and filter out invalid entries
                    this.recipes = data.recipes.filter(recipe => this.validateRecipeData(recipe));
                    this.totalPages = data.total_pages || 1;
                    this.displayRecipes();
                } else {
                    this.showToast(data.error || 'Failed to load recipes', 'error');
                }
            } catch (error) {
                console.error('Error loading recipes:', error);
                this.showToast('Failed to load recipes', 'error');
            }
        }

        async loadMyRecipes() {
            try {
                // Load only the user's own recipes
                const response = await fetch('/api/recipes/preview?include_public=false');
                const data = await response.json();
                
                if (data.success) {
                    // Validate recipe data and filter out invalid entries
                    this.recipes = data.recipes.filter(recipe => this.validateRecipeData(recipe));
                    this.totalPages = data.total_pages || 1;
                    this.currentPage = 1;
                    this.currentCategory = 'all';
                    this.displayRecipes();
                    
                    if (this.recipes.length === 0) {
                        this.showToast('You haven\'t created any recipes yet. Click "Create New Recipe" to get started!', 'info');
                    } else {
                        this.showToast(`Loaded ${this.recipes.length} of your recipes`, 'success');
                    }
                } else {
                    this.showToast(data.error || 'Failed to load your recipes', 'error');
                }
            } catch (error) {
                console.error('Error loading my recipes:', error);
                this.showToast('Failed to load your recipes', 'error');
            }
        }

        displayRecipes() {
            const grid = document.getElementById('recipes-grid');
            if (!grid) return;

            // Filter recipes by category
            let filteredRecipes = this.recipes;
            if (this.currentCategory !== 'all') {
                filteredRecipes = this.recipes.filter(recipe => recipe.category === this.currentCategory);
            }

            // Pagination logic
            const startIndex = (this.currentPage - 1) * this.recipesPerPage;
            const endIndex = startIndex + this.recipesPerPage;
            const paginatedRecipes = filteredRecipes.slice(startIndex, endIndex);

            // Display paginated recipes
            grid.innerHTML = paginatedRecipes.map(recipe => `
                <div class="bg-white rounded-xl border border-gray-200 overflow-hidden hover:shadow-lg transition-all duration-200 shadow-sm cursor-pointer" onclick="recipeManager.viewRecipe(${recipe.id})">
                    ${recipe.image_path ? `
                        <div class="h-64 bg-gray-200 overflow-hidden">
                            <img src="${recipe.image_path.startsWith('http') ? recipe.image_path : '/static/' + recipe.image_path}" alt="${recipe.name}" class="w-full h-full object-cover" onerror="this.src='/static/assets/stock-photos/${this.getDefaultImageForCategory(recipe.category)}'">
                        </div>
                    ` : `
                        <div class="h-64 bg-gray-200 overflow-hidden">
                            <img src="/static/assets/stock-photos/${this.getDefaultImageForCategory(recipe.category)}" alt="${recipe.name}" class="w-full h-full object-cover">
                        </div>
                    `}
                    <div class="p-5">
                        <div class="flex items-start justify-between mb-3">
                            <div class="flex-1">
                                <h4 class="font-bold text-gray-900 text-lg mb-2 leading-tight">${recipe.name}</h4>
                                <div class="flex items-center space-x-2 mb-3">
                                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                        ${recipe.category}
                                    </span>
                                    <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                        ${recipe.difficulty}
                                    </span>
                                </div>
                                <div class="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                                    <span class="flex items-center">
                                        <svg class="w-4 h-4 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                                        </svg>
                                        ${recipe.ingredients_count} ingredients
                                    </span>
                                    <span class="flex items-center">
                                        <svg class="w-4 h-4 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                        </svg>
                                        ${recipe.servings} servings
                                    </span>
                                    ${recipe.creator_name ? `
                                        <span class="flex items-center text-ki-green-600 font-medium">
                                            <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                                            </svg>
                                            by ${recipe.creator_name}
                                        </span>
                                    ` : ''}
                                </div>
                                ${recipe.rating_count > 0 ? `
                                    <div class="flex items-center space-x-2 mb-3">
                                        <div class="flex items-center">
                                            ${[1,2,3,4,5].map(star => `
                                                <svg class="w-4 h-4 ${star <= recipe.avg_rating ? 'text-yellow-400 fill-current' : 'text-gray-300'}" viewBox="0 0 20 20">
                                                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                                                </svg>
                                            `).join('')}
                                        </div>
                                        <span class="text-sm text-gray-600 font-medium">${recipe.avg_rating.toFixed(1)} (${recipe.rating_count})</span>
                                    </div>
                                ` : ''}
                            </div>
                            <button onclick="recipeManager.toggleFavorite(${recipe.id})" class="text-gray-400 hover:text-yellow-500 transition-colors duration-200 ml-4" title="${recipe.is_favorite ? 'Remove from favorites' : 'Add to favorites'}">
                                <svg class="w-6 h-6 ${recipe.is_favorite ? 'text-yellow-500 fill-current' : 'text-gray-400'}" viewBox="0 0 20 20">
                                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                                </svg>
                            </button>
                        </div>
                        
                        <!-- Quick Info -->
                        <div class="flex items-center justify-between text-sm text-gray-600 mb-4">
                            <span class="flex items-center">
                                <svg class="w-4 h-4 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                                </svg>
                                ${recipe.ingredients_count} ingredients
                            </span>
                            ${recipe.rating_count > 0 ? `
                                <span class="flex items-center">
                                    <svg class="w-4 h-4 mr-1 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                                    </svg>
                                    ${recipe.avg_rating.toFixed(1)}
                                </span>
                            ` : ''}
                        </div>
                        
                        <!-- Ingredients Preview -->
                        <div class="mb-4">
                            <h5 class="text-sm font-medium text-gray-700 mb-2">Ingredients:</h5>
                            <div class="ingredients-preview">
                                ${this.formatIngredientsPreview(recipe.ingredients)}
                            </div>
                        </div>
                        
                        <!-- Nutritional Profile -->
                        ${this.renderNutritionalProfile(recipe)}
                        
                        <!-- Action Buttons -->
                        <div class="flex space-x-2">
                            <button onclick="recipeManager.addToLog(${recipe.id})" class="flex-1 bg-ki-green-600 text-white py-2.5 px-3 rounded-lg text-sm font-medium hover:bg-ki-green-700 transition-colors">
                                Add to Log
                            </button>
                            ${recipe.is_public && recipe.user_id !== this.currentUserId ? `
                                <button onclick="recipeManager.showRatingModal(${recipe.id})" class="px-3 py-2 text-yellow-600 bg-yellow-50 rounded-lg hover:bg-yellow-100 transition-colors" title="Rate this recipe">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976-2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z"></path>
                                    </svg>
                                </button>
                            ` : ''}
                            ${recipe.user_id === this.currentUserId ? `
                                <button onclick="recipeManager.deleteRecipe(${recipe.id})" class="px-3 py-2 text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition-colors">
                                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                                    </svg>
                                </button>
                            ` : ''}
                        </div>
                    </div>
                </div>
            `).join('');

            // Update pagination controls
            this.updatePagination(filteredRecipes.length);
        }

        updatePagination(totalRecipes) {
            const paginationControls = document.getElementById('pagination-controls');
            const prevButton = document.getElementById('prev-page');
            const nextButton = document.getElementById('next-page');
            const pageInfo = document.getElementById('page-info');
            
            if (!paginationControls) return;
            
            const totalPages = Math.ceil(totalRecipes / this.recipesPerPage);
            
            if (totalPages <= 1) {
                paginationControls.classList.add('hidden');
                return;
            }
            
            paginationControls.classList.remove('hidden');
            
            // Update page info
            pageInfo.textContent = `Page ${this.currentPage} of ${totalPages}`;
            
            // Update button states
            prevButton.disabled = this.currentPage === 1;
            nextButton.disabled = this.currentPage === totalPages;
            
            // Add event listeners
            prevButton.onclick = () => this.goToPage(this.currentPage - 1);
            nextButton.onclick = () => this.goToPage(this.currentPage + 1);
        }

        goToPage(page) {
            this.currentPage = page;
            this.displayRecipes();
        }

        async filterByCategory(category) {
            this.currentCategory = category;
            this.currentPage = 1;
            
            // Update button states
            document.querySelectorAll('.recipe-category-btn').forEach(btn => {
                btn.classList.remove('active', 'bg-ki-green-100', 'text-ki-green-700');
                btn.classList.add('bg-gray-100', 'text-gray-600');
            });
            
            const activeBtn = document.querySelector(`[data-category="${category}"]`);
            if (activeBtn) {
                activeBtn.classList.add('active', 'bg-ki-green-100', 'text-ki-green-700');
                activeBtn.classList.remove('bg-gray-100', 'text-gray-600');
            }
            
            // Load recipes for the selected category
            try {
                // Determine if we should include public recipes based on current tab
                const currentTab = document.querySelector('.search-tab.active');
                const isMyRecipesTab = currentTab && currentTab.id === 'tab-my-recipes';
                const includePublic = !isMyRecipesTab;
                
                const response = await fetch(`/api/recipes/preview?category=${category}&include_public=${includePublic}`);
                const data = await response.json();
                
                if (data.success) {
                    // Validate recipe data and filter out invalid entries
                    this.recipes = data.recipes.filter(recipe => this.validateRecipeData(recipe));
                    this.totalPages = data.total_pages || 1;
                    this.displayRecipes();
                } else {
                    this.showToast(data.error || 'Failed to load recipes', 'error');
                }
            } catch (error) {
                console.error('Error filtering recipes by category:', error);
                this.showToast('Failed to load recipes for this category', 'error');
            }
        }

        async searchRecipes() {
            // Prevent multiple searches
            if (this.isSearching) {
                return;
            }

            const query = document.getElementById('recipe-search').value.trim();
            
            if (!query) {
                this.loadRecipes();
                return;
            }

            // Show loading state
            this.showSearchLoading();
            
            // Show loading in recipes grid
            this.showRecipesLoading();

            // Track search performance
            const searchStartTime = performance.now();

            try {
                // Use optimized search with pagination
                const response = await fetch(`/api/recipes/search?q=${encodeURIComponent(query)}&include_public=true&page=1&per_page=12`);
                const data = await response.json();
                
                // Calculate search time
                const searchTime = Math.round(performance.now() - searchStartTime);
                
                if (data.success) {
                    // Validate recipe data and filter out invalid entries
                    this.recipes = data.recipes.filter(recipe => this.validateRecipeData(recipe));
                    
                    this.currentPage = 1;
                    this.totalPages = data.total_pages || 1;
                    this.displayRecipes();
                    
                    const totalFound = data.total_count || this.recipes.length;
                    this.showToast(`Found ${totalFound} recipes matching "${query}" in ${searchTime}ms`, 'success');
                    
                    // Search completed successfully
                } else {
                    this.showToast(data.error || 'Search failed', 'error');
                }
            } catch (error) {
                console.error('Search error:', error);
                this.showToast('Search failed. Please try again.', 'error');
            } finally {
                // Hide loading state
                this.hideSearchLoading();
                this.hideRecipesLoading();
            }
        }

        async searchByIngredients() {
            // Prevent multiple searches
            if (this.isSearching) {
                return;
            }

            const ingredientsList = document.getElementById('ingredients-list');
            const ingredients = Array.from(ingredientsList.children).map(tag => tag.textContent.trim().replace('×', '').trim());
            
            if (ingredients.length < 3) {
                this.showToast('Please add at least 3 ingredients to search', 'warning');
                return;
            }
            
            // Show loading state
            this.showSearchLoading();
            
            // Show loading in recipes grid
            this.showRecipesLoading();

            // Track search performance
            const searchStartTime = performance.now();

            try {
                const response = await fetch('/api/recipes/search-by-ingredients', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        ingredients: ingredients,
                        include_public: true,
                        page: 1,
                        per_page: 12
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    // Validate recipe data and filter out invalid entries
                    this.recipes = data.recipes.filter(recipe => this.validateRecipeData(recipe));
                    
                    this.currentPage = 1;
                    this.totalPages = data.total_pages || 1;
                    this.displayRecipes();
                    
                    // Calculate search time
                    const searchTime = Math.round(performance.now() - searchStartTime);
                    
                    const totalFound = data.total_found || this.recipes.length;
                    this.showToast(`Found ${totalFound} recipes matching your ingredients in ${searchTime}ms`, 'success');
                    
                    // Log performance for monitoring
                    // Ingredient search completed successfully
                } else {
                    this.showToast(data.error || 'Ingredient search failed', 'error');
                }
            } catch (error) {
                console.error('Ingredient search error:', error);
                this.showToast('Ingredient search failed. Please try again.', 'error');
            } finally {
                // Hide loading state
                this.hideSearchLoading();
                this.hideRecipesLoading();
            }
        }

        async clearSearch() {
            document.getElementById('recipe-search').value = '';
            document.getElementById('ingredients-list').innerHTML = '';
            this.isSearching = false; // Reset search state
            this.hideSearchLoading(); // Ensure loading state is hidden
            await this.loadMyRecipes(); // Return to user's recipes when clearing search
            this.showToast('Search cleared, showing your recipes', 'info');
        }

        async createRecipe() {
            const formData = new FormData();
            const imageFile = document.getElementById('recipe-image').files[0];
            
            // Add form data
            formData.append('name', document.getElementById('recipe-name').value);
            formData.append('category', document.getElementById('recipe-category').value);
            formData.append('difficulty', document.getElementById('recipe-difficulty').value);
            formData.append('servings', document.getElementById('recipe-servings').value);
            formData.append('description', document.getElementById('recipe-description').value);
            formData.append('instructions', document.getElementById('recipe-instructions').value);
            formData.append('is_public', document.getElementById('share-recipe').checked);
            
            // Add image if selected
            if (imageFile) {
                formData.append('image', imageFile);
            }
            
            // Add ingredients
            const ingredientsContainer = document.getElementById('ingredients-container');
            const ingredientRows = ingredientsContainer.querySelectorAll('.ingredient-row');
            
            ingredientRows.forEach((row, index) => {
                const name = row.querySelector('.ingredient-name').value;
                const amount = row.querySelector('.ingredient-amount').value;
                const unit = row.querySelector('.ingredient-unit').value;
                
                if (name && amount && unit) {
                    formData.append(`ingredients[${index}][name]`, name);
                    formData.append(`ingredients[${index}][amount]`, amount);
                    formData.append(`ingredients[${index}][unit]`, unit);
                }
            });
            
            try {
                const response = await fetch('/api/recipes', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showToast('Recipe created successfully!', 'success');
                    closeCreateModal();
                    this.loadRecipes();
                    this.resetCreateForm();
                } else {
                    this.showToast(data.error || 'Failed to create recipe', 'error');
                }
            } catch (error) {
                console.error('Error creating recipe:', error);
                this.showToast('Failed to create recipe', 'error');
            }
        }

        resetCreateForm() {
            document.getElementById('create-recipe-form').reset();
            document.getElementById('ingredients-container').innerHTML = '';
            document.getElementById('image-preview').classList.add('hidden');
            this.addIngredientRow(); // Add one default ingredient row
        }

        addIngredientRow() {
            const container = document.getElementById('ingredients-container');
            const rowCount = container.children.length;
            
            const row = document.createElement('div');
            row.className = 'ingredient-row flex space-x-2';
            row.innerHTML = `
                <input type="text" class="ingredient-name flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ki-green-500 focus:border-ki-green-500" placeholder="Ingredient name" required>
                <input type="number" class="ingredient-amount w-20 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ki-green-500 focus:border-ki-green-500" placeholder="Amount" min="0" step="0.1" required>
                <select class="ingredient-unit px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-ki-green-500 focus:border-ki-green-500" required>
                    <option value="">Unit</option>
                    <option value="g">grams</option>
                    <option value="kg">kilograms</option>
                    <option value="oz">ounces</option>
                    <option value="lb">pounds</option>
                    <option value="cup">cups</option>
                    <option value="tbsp">tablespoons</option>
                    <option value="tsp">teaspoons</option>
                    <option value="whole">whole</option>
                </select>
                ${rowCount > 0 ? `
                    <button type="button" onclick="this.parentElement.remove()" class="px-3 py-2 text-red-600 hover:text-red-800">
                        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                        </svg>
                    </button>
                ` : ''}
            `;
            
            container.appendChild(row);
        }

        handleImageUpload(file) {
            if (!file) return;
            
            if (!file.type.startsWith('image/')) {
                this.showToast('Please select an image file', 'error');
                return;
            }
            
            if (file.size > 10 * 1024 * 1024) { // 10MB limit
                this.showToast('Image size must be less than 10MB', 'error');
                return;
            }
            
            const reader = new FileReader();
            reader.onload = (e) => {
                const preview = document.getElementById('image-preview');
                const previewImg = document.getElementById('preview-img');
                previewImg.src = e.target.result;
                preview.classList.remove('hidden');
            };
            reader.readAsDataURL(file);
        }

        removeImage() {
            document.getElementById('recipe-image').value = '';
            document.getElementById('image-preview').classList.add('hidden');
        }

        async toggleFavorite(recipeId) {
            try {
                const response = await fetch(`/api/recipes/${recipeId}/toggle-favorite`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.loadRecipes(); // Refresh to show updated favorite state
                } else {
                    this.showToast(data.error || 'Failed to update favorite', 'error');
                }
            } catch (error) {
                console.error('Error toggling favorite:', error);
                this.showToast('Failed to update favorite', 'error');
            }
        }

        async addToLog(recipeId) {
            try {
                const response = await fetch(`/api/recipes/${recipeId}/add-to-log`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        servings: 1,
                        time_of_day: 'dinner'
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showToast(data.message, 'success');
                    
                    // Note: Dashboard refresh removed - recipes page is now modular
                } else {
                    this.showToast(data.error || 'Failed to add recipe to log', 'error');
                }
            } catch (error) {
                console.error('Error adding recipe to log:', error);
                this.showToast('Failed to add recipe to log', 'error');
            }
        }

        async viewRecipe(recipeId) {
            try {
                // Fetch complete recipe data from API
                const response = await fetch(`/api/recipes/${recipeId}`);
                
                if (!response.ok) {
                    if (response.status === 404) {
                        this.showToast('Recipe not found or has been removed', 'error');
                        // Remove the recipe from the current list to prevent future errors
                        this.recipes = this.recipes.filter(r => r.id !== recipeId);
                        this.displayRecipes();
                    } else {
                        this.showToast(`Failed to load recipe details (${response.status})`, 'error');
                    }
                    return;
                }
                
                const data = await response.json();
                
                if (!data.success) {
                    this.showToast(data.error || 'Failed to load recipe details', 'error');
                    return;
                }
                
                const recipe = data.recipe;
                
                // Set global variable for modal actions
                window.currentRecipeId = recipeId;
                
                // Populate modal with complete recipe data
                this.populateRecipeModal(recipe);
                
                // Show the modal
                const modal = document.getElementById('recipe-detail-modal');
                if (modal) {
                    modal.classList.remove('hidden');
                }
                
            } catch (error) {
                console.error('Error loading recipe details:', error);
                this.showToast('Failed to load recipe details. Please try again.', 'error');
            }
        }
        
        populateRecipeModal(recipe) {
            // Recipe title
            const titleElement = document.getElementById('modal-recipe-title');
            if (titleElement) {
                titleElement.textContent = recipe.name;
            }
            
            // Recipe image
            const imageContainer = document.getElementById('modal-recipe-image');
            if (imageContainer) {
                if (recipe.image_path) {
                    imageContainer.innerHTML = `<img src="/static/${recipe.image_path}" alt="${recipe.name}" class="w-full h-full object-cover">`;
                } else {
                    imageContainer.innerHTML = `<img src="/static/assets/stock-photos/${this.getDefaultImageForCategory(recipe.category)}" alt="${recipe.name}" class="w-full h-full object-cover">`;
                }
            }
            
            // Basic info
            const ingredientsCountElement = document.getElementById('modal-ingredients-count');
            const servingsElement = document.getElementById('modal-servings');
            const categoryElement = document.getElementById('modal-category');
            const difficultyElement = document.getElementById('modal-difficulty');
            const contributorElement = document.getElementById('modal-contributor');
            const descriptionElement = document.getElementById('modal-description');
            
            if (ingredientsCountElement) ingredientsCountElement.textContent = `${recipe.ingredients_count || 0} ingredients`;
            if (servingsElement) servingsElement.textContent = `${recipe.servings || 1} servings`;
            if (categoryElement) categoryElement.textContent = recipe.category || 'Uncategorized';
            if (difficultyElement) difficultyElement.textContent = recipe.difficulty || 'Not specified';
            if (contributorElement) contributorElement.textContent = recipe.creator_name || 'Unknown';
            if (descriptionElement) descriptionElement.textContent = recipe.description || 'No description available.';
            
            // Rating
            const ratingContainer = document.getElementById('modal-rating');
            if (ratingContainer) {
            if (recipe.rating_count && recipe.rating_count > 0 && recipe.avg_rating) {
                ratingContainer.innerHTML = `
                    <div class="flex items-center space-x-1">
                        ${[1,2,3,4,5].map(star => `
                            <svg class="w-5 h-5 ${star <= recipe.avg_rating ? 'text-yellow-400 fill-current' : 'text-gray-300'}" viewBox="0 0 20 20">
                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"/>
                            </svg>
                        `).join('')}
                        <span class="text-sm text-gray-600 font-medium ml-2">${recipe.avg_rating.toFixed(1)} (${recipe.rating_count})</span>
                    </div>
                `;
            } else {
                ratingContainer.innerHTML = '<span class="text-gray-500 text-sm">No ratings yet</span>';
            }
            }
            
            // Ingredients
            const ingredientsContainer = document.getElementById('modal-ingredients-list');
            if (ingredientsContainer) {
                if (recipe.ingredients && Array.isArray(recipe.ingredients) && recipe.ingredients.length > 0) {
                    ingredientsContainer.innerHTML = recipe.ingredients.map(ingredient => {
                        // Handle both ingredient objects and simple strings
                        if (typeof ingredient === 'object' && ingredient.amount && ingredient.unit && (ingredient.food_name || ingredient.name)) {
                            const ingredientName = ingredient.food_name || ingredient.name;
                            return `
                                <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                                    <div class="w-2 h-2 bg-ki-green-500 rounded-full"></div>
                                    <span class="text-gray-700">${ingredient.amount} ${ingredient.unit} ${ingredientName}</span>
                                </div>
                            `;
                        } else if (typeof ingredient === 'string') {
                            return `
                                <div class="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                                    <div class="w-2 h-2 bg-ki-green-500 rounded-full"></div>
                                    <span class="text-gray-700">${ingredient}</span>
                                </div>
                            `;
                        } else {
                            return '';
                        }
                    }).filter(html => html).join('');
                } else {
                    ingredientsContainer.innerHTML = '<p class="text-gray-500 text-sm">No ingredients listed</p>';
                }
            }
            
            // Nutrition
            const nutritionContainer = document.getElementById('modal-nutrition');
            if (nutritionContainer) {
                // Calculate nutrition from ingredients if not provided
                let nutrition = recipe.nutrition;
                if (!nutrition && recipe.ingredients && Array.isArray(recipe.ingredients)) {
                    nutrition = this.calculateNutritionFromIngredients(recipe.ingredients);
                }
                
                if (nutrition && (nutrition.calories > 0 || nutrition.protein > 0 || nutrition.carbs > 0 || nutrition.fat > 0)) {
                    // Count additional nutrients to determine grid layout
                    const additionalNutrients = [nutrition.fiber, nutrition.sugar, nutrition.sodium].filter(n => n > 0).length;
                    const totalNutrients = 4 + additionalNutrients; // 4 main nutrients + additional ones
                    const gridCols = totalNutrients <= 4 ? 'grid-cols-2' : totalNutrients <= 6 ? 'grid-cols-3' : 'grid-cols-4';
                    
                    nutritionContainer.innerHTML = `
                        <div class="grid ${gridCols} gap-4">
                            <div class="text-center p-4 bg-red-50 rounded-lg">
                                <div class="font-semibold text-red-600 text-lg">${Math.round(nutrition.calories || 0)}</div>
                                <div class="text-sm text-red-500">calories</div>
                            </div>
                            <div class="text-center p-4 bg-blue-50 rounded-lg">
                                <div class="font-semibold text-blue-600 text-lg">${Math.round(nutrition.protein || 0)}g</div>
                                <div class="text-sm text-blue-500">protein</div>
                            </div>
                            <div class="text-center p-4 bg-green-50 rounded-lg">
                                <div class="font-semibold text-green-600 text-lg">${Math.round(nutrition.carbs || 0)}g</div>
                                <div class="text-sm text-green-500">carbs</div>
                            </div>
                            <div class="text-center p-4 bg-yellow-50 rounded-lg">
                                <div class="font-semibold text-yellow-600 text-lg">${Math.round(nutrition.fat || 0)}g</div>
                                <div class="text-sm text-yellow-500">fat</div>
                            </div>
                            ${nutrition.fiber > 0 ? `
                            <div class="text-center p-4 bg-purple-50 rounded-lg">
                                <div class="font-semibold text-purple-600 text-lg">${Math.round(nutrition.fiber || 0)}g</div>
                                <div class="text-sm text-purple-500">fiber</div>
                            </div>
                            ` : ''}
                            ${nutrition.sugar > 0 ? `
                            <div class="text-center p-4 bg-pink-50 rounded-lg">
                                <div class="font-semibold text-pink-600 text-lg">${Math.round(nutrition.sugar || 0)}g</div>
                                <div class="text-sm text-pink-500">sugar</div>
                            </div>
                            ` : ''}
                            ${nutrition.sodium > 0 ? `
                            <div class="text-center p-4 bg-indigo-50 rounded-lg">
                                <div class="font-semibold text-indigo-600 text-lg">${Math.round(nutrition.sodium || 0)}mg</div>
                                <div class="text-sm text-indigo-500">sodium</div>
                            </div>
                            ` : ''}
                        </div>
                    `;
                } else {
                    nutritionContainer.innerHTML = `
                        <div class="text-center p-6 bg-gray-50 rounded-lg">
                            <svg class="w-12 h-12 text-gray-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                            </svg>
                            <p class="text-gray-500 text-sm mb-2">Nutrition information not available</p>
                            <p class="text-gray-400 text-xs">Nutritional data will be calculated from ingredients when available</p>
                        </div>
                    `;
                }
            }
            
            // Nutrition data is already displayed above using the same format as recipe cards
            
            // Instructions
            const instructionsContainer = document.getElementById('modal-instructions');
            if (instructionsContainer) {
                if (recipe.instructions && typeof recipe.instructions === 'string') {
                    // Split instructions by newlines or periods and format them
                    const instructions = recipe.instructions.split(/[.\n]+/).filter(instruction => instruction.trim());
                    instructionsContainer.innerHTML = instructions.map((instruction, index) => `
                        <div class="mb-3 p-3 bg-gray-50 rounded-lg">
                            <span class="font-semibold text-ki-green-600">${index + 1}.</span>
                            <span class="text-gray-700 ml-2">${instruction.trim()}</span>
                        </div>
                    `).join('');
                } else if (Array.isArray(recipe.instructions)) {
                    // Handle case where instructions is an array
                    instructionsContainer.innerHTML = recipe.instructions.map((instruction, index) => `
                        <div class="mb-3 p-3 bg-gray-50 rounded-lg">
                            <span class="font-semibold text-ki-green-600">${index + 1}.</span>
                            <span class="text-gray-700 ml-2">${instruction.instruction || instruction}</span>
                        </div>
                    `).join('');
                } else {
                    instructionsContainer.innerHTML = '<p class="text-gray-500 text-sm">No instructions available</p>';
                }
            }
            
            // Update favorite button text
            const favoriteText = document.getElementById('modal-favorite-text');
            if (favoriteText) {
                favoriteText.textContent = recipe.is_favorite ? 'Remove from Favorites' : 'Add to Favorites';
            }
        }

        async deleteRecipe(recipeId) {
            if (!confirm('Are you sure you want to delete this recipe?')) return;
            
            try {
                const response = await fetch(`/api/recipes/${recipeId}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showToast('Recipe deleted successfully', 'success');
                    this.loadRecipes();
                } else {
                    this.showToast(data.error || 'Failed to delete recipe', 'error');
                }
            } catch (error) {
                console.error('Error deleting recipe:', error);
                this.showToast('Failed to delete recipe', 'error');
            }
        }

        showRatingModal(recipeId) {
            this.currentRatingRecipeId = recipeId;
            document.getElementById('rating-modal').classList.remove('hidden');
            
            // Reset rating
            document.querySelectorAll('.star-btn').forEach(btn => {
                btn.classList.remove('text-yellow-400');
                btn.classList.add('text-gray-300');
            });
            document.getElementById('rating-review').value = '';
        }

        async submitRating() {
            if (!this.currentRatingRecipeId) return;
            
            const rating = document.querySelector('.star-btn.text-yellow-400')?.dataset.rating || 0;
            const review = document.getElementById('rating-review').value.trim();
            
            if (!rating) {
                this.showToast('Please select a rating', 'error');
                return;
            }
            
            try {
                const response = await fetch(`/api/recipes/${this.currentRatingRecipeId}/rate`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        rating: parseInt(rating),
                        review: review
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    this.showToast('Rating submitted successfully!', 'success');
                    closeRatingModal();
                    this.loadRecipes(); // Refresh to show updated rating
                } else {
                    this.showToast(data.error || 'Failed to submit rating', 'error');
                }
            } catch (error) {
                console.error('Error submitting rating:', error);
                this.showToast('Failed to submit rating', 'error');
            }
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
}

// Global functions for star rating
function updateStarDisplay(rating) {
    document.querySelectorAll('.star-btn').forEach((btn, index) => {
        if (index < rating) {
            btn.classList.remove('text-gray-300');
            btn.classList.add('text-yellow-400');
        } else {
            btn.classList.remove('text-yellow-400');
            btn.classList.add('text-gray-300');
        }
    });
}

// Add star rating event listeners
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.star-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const rating = parseInt(this.dataset.rating);
            updateStarDisplay(rating);
        });
    });
});
