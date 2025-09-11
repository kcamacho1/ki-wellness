/**
 * Recipe Display Module
 * Handles recipe display, pagination, and UI updates
 */

// Prevent duplicate loading
if (typeof window.RecipeDisplay !== 'undefined') {
    // Already loaded, skip silently
} else {
    class RecipeDisplay {
    constructor(recipeManager) {
        this.recipeManager = recipeManager;
    }

    showPlaceholderContent() {
        const grid = document.getElementById('recipes-grid');
        if (!grid) return;

        grid.innerHTML = `
            <div class="col-span-full text-center py-12">
                <div class="max-w-md mx-auto">
                    <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                    </svg>
                    <h3 class="text-lg font-medium text-gray-900 mb-2">Ready to explore your recipes?</h3>
                    <p class="text-gray-600 mb-6">Click "Load My Recipes" to view your personal recipe collection, or create a new recipe to get started!</p>
                    <div class="flex flex-col sm:flex-row gap-3 justify-center">
                        <button onclick="window.recipeManager ? window.recipeManager.loadMyRecipes() : showToast('RecipeManager not ready', 'error')" class="px-6 py-3 bg-ki-green-600 text-white rounded-xl hover:bg-ki-green-700 transition-colors duration-200">
                            Load My Recipes
                        </button>
                        <button id="create-recipe-btn" class="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-all duration-200 shadow-lg hover:shadow-xl">
                            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                            </svg>
                            Create New Recipe
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    showRecipesLoading() {
        const grid = document.getElementById('recipes-grid');
        if (grid) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-ki-green-600 mx-auto mb-4"></div>
                    <p class="text-gray-500">Loading recipes...</p>
                </div>
            `;
        }
    }

    hideRecipesLoading() {
        // This will be handled by displayRecipes() when it updates the grid
    }

    displayRecipes() {
        const grid = document.getElementById('recipes-grid');
        if (!grid) return;

        // Filter recipes by category
        let filteredRecipes = this.recipeManager.recipes;
        if (this.recipeManager.currentCategory !== 'all') {
            filteredRecipes = this.recipeManager.recipes.filter(recipe => 
                recipe.category && recipe.category.toLowerCase() === this.recipeManager.currentCategory.toLowerCase()
            );
        }

        // Calculate pagination
        const startIndex = (this.recipeManager.currentPage - 1) * this.recipeManager.recipesPerPage;
        const endIndex = startIndex + this.recipeManager.recipesPerPage;
        const paginatedRecipes = filteredRecipes.slice(startIndex, endIndex);

        if (paginatedRecipes.length === 0) {
            grid.innerHTML = `
                <div class="col-span-full text-center py-12">
                    <div class="max-w-md mx-auto">
                        <svg class="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                        </svg>
                        <h3 class="text-lg font-medium text-gray-900 mb-2">No recipes found</h3>
                        <p class="text-gray-600 mb-6">Try adjusting your search or create a new recipe!</p>
                        <button id="create-recipe-btn" class="inline-flex items-center px-6 py-3 bg-blue-600 text-white rounded-xl font-semibold hover:bg-blue-700 transition-all duration-200 shadow-lg hover:shadow-xl">
                            <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                            </svg>
                            Create New Recipe
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        // Render recipe cards
        grid.innerHTML = paginatedRecipes.map(recipe => this.createRecipeCard(recipe)).join('');

        // Update pagination
        this.updatePagination(filteredRecipes.length);

        // Load images asynchronously
        this.loadAsyncImages(paginatedRecipes);
    }

    createRecipeCard(recipe) {
        const imageUrl = recipe.image_path || recipe.dynamic_image_url || this.getDefaultImageForCategory(recipe.category);
        const nutrition = recipe.nutrition || {};
        const ingredientsPreview = this.formatIngredientsPreview(recipe.ingredients || []);
        
        return `
            <div class="bg-white rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300 transform hover:-translate-y-1 overflow-hidden">
                <div class="relative">
                    <div class="aspect-w-16 aspect-h-9 bg-gray-200">
                        <img 
                            src="${imageUrl}" 
                            alt="${recipe.name}"
                            class="w-full h-48 object-cover transition-transform duration-300 hover:scale-105"
                            loading="lazy"
                            onerror="this.src='${this.getDefaultImageForCategory(recipe.category)}'"
                        >
                    </div>
                    <div class="absolute top-3 right-3">
                        <button 
                            onclick="window.recipeManager.toggleFavorite(${recipe.id})" 
                            class="p-2 rounded-full bg-white bg-opacity-90 hover:bg-opacity-100 transition-all duration-200 shadow-lg hover:shadow-xl"
                            title="${recipe.is_favorite ? 'Remove from favorites' : 'Add to favorites'}"
                        >
                            <svg class="w-5 h-5 ${recipe.is_favorite ? 'text-red-500 fill-current' : 'text-gray-400'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                            </svg>
                        </button>
                    </div>
                </div>
                
                <div class="p-5">
                    <div class="flex items-start justify-between mb-3">
                        <div class="flex-1">
                            <h4 class="font-bold text-gray-900 text-lg mb-2 leading-tight">${recipe.name}</h4>
                            <div class="flex items-center space-x-2 mb-3">
                                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                                    ${recipe.category || 'Uncategorized'}
                                </span>
                                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                                    ${recipe.difficulty || 'Easy'}
                                </span>
                            </div>
                            <div class="flex items-center space-x-4 text-sm text-gray-600 mb-3">
                                <span class="flex items-center">
                                    <svg class="w-4 h-4 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
                                    </svg>
                                    ${recipe.ingredients_count || 0} ingredients
                                </span>
                                <span class="flex items-center">
                                    <svg class="w-4 h-4 mr-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                                    </svg>
                                    ${recipe.prep_time ? recipe.prep_time + 'm prep' : ''} ${recipe.cook_time ? recipe.cook_time + 'm cook' : ''}
                                </span>
                            </div>
                        </div>
                    </div>
                    
                    ${recipe.description ? `<p class="text-gray-600 text-sm mb-3 line-clamp-2">${recipe.description}</p>` : ''}
                    
                    <div class="mb-4">
                        <h5 class="text-sm font-medium text-gray-700 mb-2">Key Ingredients:</h5>
                        <p class="text-sm text-gray-600">${ingredientsPreview}</p>
                    </div>
                    
                    ${this.renderNutritionalProfile(recipe)}
                    
                    ${recipe.contributor ? `
                        <div class="mb-3 pt-3 border-t border-gray-100">
                            <div class="flex items-center space-x-2 text-sm text-gray-600">
                                <svg class="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path>
                                </svg>
                                <span class="text-xs text-gray-500">Contributor:</span>
                                <span class="font-medium text-gray-700">${recipe.contributor}</span>
                            </div>
                        </div>
                    ` : ''}
                    
                    <div class="flex items-center justify-between pt-4 border-t border-gray-100">
                        <div class="flex items-center space-x-2">
                            <button 
                                onclick="window.recipeManager.addToLog(${recipe.id})" 
                                class="px-3 py-1 text-xs font-medium text-ki-green-700 bg-ki-green-100 rounded-full hover:bg-ki-green-200 transition-colors duration-200"
                            >
                                Add to Log
                            </button>
                            <button 
                                onclick="window.recipeManager.viewRecipe(${recipe.id})" 
                                class="px-3 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-full hover:bg-blue-200 transition-colors duration-200"
                            >
                                View Details
                            </button>
                            ${recipe.is_owner ? `
                                <button 
                                    onclick="window.recipeManager.editRecipe(${recipe.id})" 
                                    class="px-3 py-1 text-xs font-medium text-orange-700 bg-orange-100 rounded-full hover:bg-orange-200 transition-colors duration-200"
                                >
                                    Edit Recipe
                                </button>
                            ` : ''}
                        </div>
                        <div class="flex items-center space-x-1">
                            <svg class="w-4 h-4 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z"></path>
                            </svg>
                            <span class="text-sm font-medium text-gray-700">${recipe.avg_rating || 0}</span>
                            <span class="text-xs text-gray-500">(${recipe.rating_count || 0})</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    formatIngredientsPreview(ingredients) {
        if (!ingredients || ingredients.length === 0) return 'No ingredients listed';
        
        const maxIngredients = 3;
        const preview = ingredients.slice(0, maxIngredients).map(ing => ing.name || ing.food_name).join(', ');
        const remaining = ingredients.length - maxIngredients;
        
        return remaining > 0 ? `${preview} +${remaining} more` : preview;
    }

    renderNutritionalProfile(recipe) {
        const nutrition = recipe.nutrition || {};
        if (!nutrition.calories && !nutrition.protein && !nutrition.carbs && !nutrition.fat) {
            return '';
        }

        return `
            <div class="mb-4 p-3 bg-gray-50 rounded-lg">
                <h5 class="text-sm font-medium text-gray-700 mb-2">Nutrition (per serving):</h5>
                <div class="grid grid-cols-2 gap-2 text-xs">
                    ${nutrition.calories ? `<div class="flex justify-between"><span class="text-gray-600">Calories:</span><span class="font-medium">${Math.round(nutrition.calories)}</span></div>` : ''}
                    ${nutrition.protein ? `<div class="flex justify-between"><span class="text-gray-600">Protein:</span><span class="font-medium">${Math.round(nutrition.protein)}g</span></div>` : ''}
                    ${nutrition.carbs ? `<div class="flex justify-between"><span class="text-gray-600">Carbs:</span><span class="font-medium">${Math.round(nutrition.carbs)}g</span></div>` : ''}
                    ${nutrition.fat ? `<div class="flex justify-between"><span class="text-gray-600">Fat:</span><span class="font-medium">${Math.round(nutrition.fat)}g</span></div>` : ''}
                </div>
            </div>
        `;
    }

    updatePagination(totalRecipes) {
        const paginationControls = document.getElementById('pagination-controls');
        if (!paginationControls) return;

        this.recipeManager.totalPages = Math.ceil(totalRecipes / this.recipeManager.recipesPerPage);
        
        if (this.recipeManager.totalPages <= 1) {
            paginationControls.classList.add('hidden');
            return;
        }

        paginationControls.classList.remove('hidden');
        
        const prevButton = document.getElementById('prev-page');
        const nextButton = document.getElementById('next-page');
        const pageInfo = document.getElementById('page-info');
        
        if (prevButton) {
            prevButton.disabled = this.recipeManager.currentPage === 1;
            prevButton.onclick = () => this.goToPage(this.recipeManager.currentPage - 1);
        }
        
        if (nextButton) {
            nextButton.disabled = this.recipeManager.currentPage === this.recipeManager.totalPages;
            nextButton.onclick = () => this.goToPage(this.recipeManager.currentPage + 1);
        }
        
        if (pageInfo) {
            pageInfo.textContent = `Page ${this.recipeManager.currentPage} of ${this.recipeManager.totalPages}`;
        }
    }

    goToPage(page) {
        this.recipeManager.currentPage = page;
        this.displayRecipes();
    }

    async loadAsyncImages(recipes) {
        // Load images asynchronously for better performance
        recipes.forEach(recipe => {
            const img = document.querySelector(`img[alt="${recipe.name}"]`);
            if (img && !img.complete) {
                let fallbackAttempted = false;
                
                img.addEventListener('load', () => {
                    img.classList.add('opacity-100');
                });
                
                img.addEventListener('error', () => {
                    if (fallbackAttempted) {
                        console.warn('Image loading failed after fallback attempt:', img.src);
                        return;
                    }
                    fallbackAttempted = true;
                    img.src = this.getDefaultImageForCategory(recipe.category);
                });
            }
        });
    }

    getDefaultImageForCategory(category) {
        // Return a placeholder for recipes without images
        // Real images should be added via the Pexels script
        return '/static/assets/stock-photos/placeholder.jpg';
    }
}

    // Export for use in other modules
    window.RecipeDisplay = RecipeDisplay;
}
