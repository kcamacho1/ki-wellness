/**
 * Recipe Manager - Main orchestrator class
 * Coordinates all recipe-related functionality using modular components
 */

// Prevent duplicate loading
if (typeof window.RecipeManager !== 'undefined') {
    // Already loaded, skip silently
} else {
    class RecipeManager {
    constructor() {
        // Initialize modules
        this.form = new RecipeForm(this);
        this.display = new RecipeDisplay(this);
        this.search = new RecipeSearch(this);
        this.utils = new RecipeUtils(this);
        
        // State management
        this.recipes = [];
        this.currentPage = 1;
        this.totalPages = 1;
        this.recipesPerPage = 12;
        this.currentCategory = 'all';
        this.currentUserId = null;
        this.currentRatingRecipeId = null;
        this.isSearching = false;
        
        this.init();
        
        // Store instance globally
        window.recipeManager = this;
    }

    init() {
        this.getCurrentUserId();
        this.setupEventListeners();
        this.showPlaceholderContent(); // Show placeholder instead of loading recipes
    }

    getCurrentUserId() {
        this.currentUserId = this.utils.getCurrentUserId();
    }

    getCSRFToken() {
        return this.utils.getCSRFToken();
    }

    setupEventListeners() {
        // Form submission
        const createForm = document.getElementById('create-recipe-form');
        if (createForm) {
            createForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.form.createRecipe();
            });
        }

        // Image upload
        const imageInput = document.getElementById('recipe-image');
        if (imageInput) {
            imageInput.addEventListener('change', (e) => {
                this.form.handleImageUpload(e.target.files[0]);
            });
        }

        // Search functionality
        const searchButton = document.getElementById('search-button');
        if (searchButton) {
            searchButton.addEventListener('click', () => this.search.searchRecipes());
        }

        const searchInput = document.getElementById('recipe-search');
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.search.searchRecipes();
                }
            });
        }

        // Ingredient search
        const ingredientSearchButton = document.getElementById('ingredient-search-button');
        if (ingredientSearchButton) {
            ingredientSearchButton.addEventListener('click', () => this.search.searchByIngredients());
        }

        const ingredientInput = document.getElementById('ingredient-input');
        if (ingredientInput) {
            ingredientInput.addEventListener('keypress', (e) => this.search.handleIngredientKeyPress(e));
        }

        // Category filtering
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const category = e.target.getAttribute('data-category');
                this.search.filterByCategory(category);
            });
        });

        // Create recipe button
        const createRecipeBtn = document.getElementById('create-recipe-btn');
        if (createRecipeBtn) {
            createRecipeBtn.addEventListener('click', () => {
                document.getElementById('create-recipe-modal').classList.remove('hidden');
                this.form.resetCreateForm();
            });
        }

        // Clear search button
        const clearSearchBtn = document.getElementById('clear-search');
        if (clearSearchBtn) {
            clearSearchBtn.addEventListener('click', () => this.search.clearSearch());
        }
    }

    // Delegate methods to appropriate modules
    showPlaceholderContent() {
        this.display.showPlaceholderContent();
    }

    showRecipesLoading() {
        this.display.showRecipesLoading();
    }

    hideRecipesLoading() {
        this.display.hideRecipesLoading();
    }

    displayRecipes() {
        this.display.displayRecipes();
    }

    async loadRecipes() {
        await this.loadMyRecipes();
    }

    async loadMyRecipes() {
        try {
            // Show loading state
            this.showRecipesLoading();
            
            // Load only the user's own recipes
            const response = await fetch('/api/recipes/preview?include_public=false');
            const data = await response.json();
            
            if (data.success) {
                // Validate recipe data and filter out invalid entries
                this.recipes = data.recipes.filter(recipe => this.utils.validateRecipeData(recipe));
                this.totalPages = data.total_pages || 1;
                this.currentPage = 1;
                this.currentCategory = 'all';
                this.displayRecipes();
                
                if (this.recipes.length === 0) {
                    this.utils.showToast('You haven\'t created any recipes yet. Click "Create New Recipe" to get started!', 'info');
                } else {
                    this.utils.showToast(`Loaded ${this.recipes.length} of your recipes`, 'success');
                }
            } else {
                this.utils.showToast(data.error || 'Failed to load your recipes', 'error');
                this.showPlaceholderContent(); // Show placeholder on error
            }
        } catch (error) {
            console.error('Error loading my recipes:', error);
            this.utils.showToast('Failed to load your recipes', 'error');
            this.showPlaceholderContent(); // Show placeholder on error
        }
    }

    async loadCommunityRecipes() {
        try {
            // Load only community/public recipes (exclude user's own recipes)
            const response = await fetch('/api/recipes/preview?include_public=true');
            const data = await response.json();
            
            if (data.success) {
                // Filter out user's own recipes
                this.recipes = data.recipes.filter(recipe => 
                    this.utils.validateRecipeData(recipe) && recipe.user_id !== this.currentUserId
                );
                this.totalPages = Math.ceil(this.recipes.length / this.recipesPerPage);
                this.currentPage = 1;
                this.currentCategory = 'all';
                this.displayRecipes();
                
                if (this.recipes.length === 0) {
                    this.utils.showToast('No community recipes available yet. Be the first to share a recipe!', 'info');
                } else {
                    this.utils.showToast(`Loaded ${this.recipes.length} community recipes`, 'success');
                }
            } else {
                this.utils.showToast('Failed to load community recipes', 'error');
            }
        } catch (error) {
            console.error('Error loading community recipes:', error);
            this.utils.showToast('Failed to load community recipes', 'error');
        }
    }

    async loadFavorites() {
        try {
            // Show loading state
            this.showRecipesLoading();
            
            // Load user's favorite recipes
            const response = await fetch('/api/recipes/favorites');
            const data = await response.json();
            
            if (data.success) {
                // Validate recipe data and filter out invalid entries
                this.recipes = data.recipes.filter(recipe => this.utils.validateRecipeData(recipe));
                this.totalPages = Math.ceil(this.recipes.length / this.recipesPerPage);
                this.currentPage = 1;
                this.currentCategory = 'all';
                this.displayRecipes();
                
                if (this.recipes.length === 0) {
                    this.utils.showToast('You haven\'t favorited any recipes yet. Click the heart icon on recipes you like!', 'info');
                } else {
                    this.utils.showToast(`Loaded ${this.recipes.length} favorite recipes`, 'success');
                }
            } else {
                this.utils.showToast(data.error || 'Failed to load favorite recipes', 'error');
                this.showPlaceholderContent(); // Show placeholder on error
            }
        } catch (error) {
            console.error('Error loading favorite recipes:', error);
            this.utils.showToast('Failed to load favorite recipes', 'error');
            this.showPlaceholderContent(); // Show placeholder on error
        }
    }

    // Recipe actions
    async toggleFavorite(recipeId) {
        try {
            const response = await fetch(`/api/recipes/${recipeId}/toggle-favorite`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Update local recipe data
                const recipe = this.recipes.find(r => r.id === recipeId);
                if (recipe) {
                    recipe.is_favorite = data.is_favorite;
                    this.displayRecipes(); // Refresh display
                }
                
                // Update heart icon in modal if modal is open for this recipe
                if (window.currentRecipeId === recipeId) {
                    const favoriteHeart = document.getElementById('modal-favorite-heart');
                    if (favoriteHeart) {
                        if (data.is_favorite) {
                            // Filled heart (favorited)
                            favoriteHeart.innerHTML = `
                                <svg class="w-6 h-6 text-red-500" fill="currentColor" viewBox="0 0 24 24">
                                    <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"></path>
                                </svg>
                            `;
                            favoriteHeart.classList.remove('text-gray-400');
                            favoriteHeart.classList.add('text-red-500');
                        } else {
                            // Outline heart (not favorited)
                            favoriteHeart.innerHTML = `
                                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                                </svg>
                            `;
                            favoriteHeart.classList.remove('text-red-500');
                            favoriteHeart.classList.add('text-gray-400');
                        }
                    }
                }
                
                this.utils.showToast(data.is_favorite ? 'Added to favorites!' : 'Removed from favorites!', 'success');
            } else {
                this.utils.showToast(data.error || 'Failed to update favorite status', 'error');
            }
        } catch (error) {
            console.error('Error toggling favorite:', error);
            this.utils.showToast('Failed to update favorite status', 'error');
        }
    }

    async addToLog(recipeId) {
        console.log('addToLog called with recipeId:', recipeId);
        if (!recipeId) {
            this.utils.showToast('Error: Recipe ID is missing', 'error');
            return;
        }
        
        // Show serving size selection modal instead of directly adding
        this.showServingSizeModal(recipeId);
    }
    
    showServingSizeModal(recipeId) {
        // Find the recipe data
        const recipe = this.recipes.find(r => r.id === recipeId);
        if (!recipe) {
            this.utils.showToast('Recipe not found', 'error');
            return;
        }
        
        // Store current recipe for the modal
        window.currentRecipeForLogId = recipeId;
        window.currentRecipeForLog = recipe;
        
        // Update modal with recipe information
        document.getElementById('serving-modal-recipe-name').textContent = recipe.name;
        
        // Reset form
        document.getElementById('serving-count').value = '1';
        document.getElementById('serving-time-of-day').value = 'dinner';
        
        // Update nutrition preview
        this.updateNutritionPreview();
        
        // Show modal
        document.getElementById('serving-size-modal').classList.remove('hidden');
    }
    
    updateNutritionPreview() {
        if (window.currentRecipeForLog) {
            const servings = parseFloat(document.getElementById('serving-count').value) || 1;
            const nutrition = window.currentRecipeForLog.nutrition || {};
            
            document.getElementById('serving-preview-calories').textContent = Math.round(nutrition.calories * servings);
            document.getElementById('serving-preview-protein').textContent = Math.round(nutrition.protein * servings) + 'g';
            document.getElementById('serving-preview-carbs').textContent = Math.round(nutrition.carbs * servings) + 'g';
            document.getElementById('serving-preview-fat').textContent = Math.round(nutrition.fat * servings) + 'g';
        }
    }
    
    async addToLogWithServings(recipeId, servings, timeOfDay) {
        console.log('addToLogWithServings called with recipeId:', recipeId, 'servings:', servings, 'timeOfDay:', timeOfDay);
        if (!recipeId) {
            this.utils.showToast('Error: Recipe ID is missing', 'error');
            return;
        }
        
        try {
            const response = await fetch(`/api/recipes/${recipeId}/add-to-log`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    servings: servings,
                    time_of_day: timeOfDay
                })
            });
            
            const data = await response.json();
            console.log('Add to log response:', data);
            
            if (data.success) {
                this.utils.showToast(`Recipe added to your food log! (${servings} serving${servings !== 1 ? 's' : ''})`, 'success');
                // Close the modal
                document.getElementById('serving-size-modal').classList.add('hidden');
                
                // Refresh dashboard if available
                if (window.dashboardManager && window.dashboardManager.refreshNutritionData) {
                    window.dashboardManager.refreshNutritionData();
                }
            } else {
                this.utils.showToast(data.error || 'Failed to add recipe to log', 'error');
            }
        } catch (error) {
            console.error('Error adding to log:', error);
            this.utils.showToast('Failed to add recipe to log', 'error');
        }
    }

    async viewRecipe(recipeId) {
        try {
            const response = await fetch(`/api/recipes/${recipeId}`);
            
            if (!response.ok) {
                if (response.status === 404) {
                    this.utils.showToast('Recipe not found or has been removed', 'error');
                    // Remove the recipe from the current list to prevent future errors
                    this.recipes = this.recipes.filter(r => r.id !== recipeId);
                    this.displayRecipes();
                } else {
                    this.utils.showToast(`Failed to load recipe details (${response.status})`, 'error');
                }
                return;
            }

            const data = await response.json();
            
            if (data.success) {
                this.populateRecipeModal(data.recipe);
                document.getElementById('recipe-detail-modal').classList.remove('hidden');
            } else {
                this.utils.showToast(data.error || 'Failed to load recipe details', 'error');
            }
        } catch (error) {
            console.error('Error loading recipe details:', error);
            this.utils.showToast('Failed to load recipe details', 'error');
        }
    }

    populateRecipeModal(recipe) {
        // Populate recipe details in modal with null checks
        const titleEl = document.getElementById('modal-recipe-title');
        if (titleEl) titleEl.textContent = recipe.name;
        
        const categoryEl = document.getElementById('modal-category');
        if (categoryEl) categoryEl.textContent = recipe.category || 'Uncategorized';
        
        const difficultyEl = document.getElementById('modal-difficulty');
        if (difficultyEl) difficultyEl.textContent = recipe.difficulty || 'Easy';
        
        const servingsEl = document.getElementById('modal-servings');
        if (servingsEl) servingsEl.textContent = `${recipe.servings || 1} servings`;
        
        const descriptionEl = document.getElementById('modal-description');
        if (descriptionEl) descriptionEl.textContent = recipe.description || 'No description available';
        
        // Update ingredients count
        const ingredientsCountEl = document.getElementById('modal-ingredients-count');
        if (ingredientsCountEl) ingredientsCountEl.textContent = `${recipe.ingredients ? recipe.ingredients.length : 0} ingredients`;
        
        // Populate ingredients
        const ingredientsList = document.getElementById('modal-ingredients-list');
        if (ingredientsList) {
            ingredientsList.innerHTML = '';
            if (recipe.ingredients && recipe.ingredients.length > 0) {
                recipe.ingredients.forEach(ingredient => {
                    const li = document.createElement('li');
                    li.className = 'flex justify-between items-center py-2 border-b border-gray-100';
                    li.innerHTML = `
                        <span class="text-gray-700">${ingredient.name || ingredient.food_name}</span>
                        <span class="text-gray-500 font-medium">${ingredient.amount} ${ingredient.unit}</span>
                    `;
                    ingredientsList.appendChild(li);
                });
            } else {
                ingredientsList.innerHTML = '<li class="text-gray-500 py-2">No ingredients listed</li>';
            }
        }
        
        // Populate instructions
        const instructionsContainer = document.getElementById('modal-instructions');
        if (instructionsContainer) {
            instructionsContainer.innerHTML = '';
            if (recipe.instructions && recipe.instructions.length > 0) {
                recipe.instructions.forEach((instruction, index) => {
                    const div = document.createElement('div');
                    div.className = 'mb-4';
                    div.innerHTML = `
                        <div class="flex">
                            <span class="flex-shrink-0 w-8 h-8 bg-ki-green-100 text-ki-green-800 rounded-full flex items-center justify-center text-sm font-medium mr-3">
                                ${index + 1}
                            </span>
                            <p class="text-gray-700">${instruction.instruction || instruction}</p>
                        </div>
                    `;
                    instructionsContainer.appendChild(div);
                });
            } else {
                instructionsContainer.innerHTML = '<p class="text-gray-500">No instructions available</p>';
            }
        }
        
        // Populate nutrition info
        const nutrition = recipe.nutrition || {};
        const nutritionContainer = document.getElementById('modal-nutrition');
        if (nutritionContainer) {
            nutritionContainer.innerHTML = `
                <div class="bg-gray-50 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-gray-900">${Math.round(nutrition.calories || 0)}</div>
                    <div class="text-sm text-gray-600">Calories</div>
                </div>
                <div class="bg-gray-50 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-gray-900">${Math.round(nutrition.protein || 0)}g</div>
                    <div class="text-sm text-gray-600">Protein</div>
                </div>
                <div class="bg-gray-50 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-gray-900">${Math.round(nutrition.carbs || 0)}g</div>
                    <div class="text-sm text-gray-600">Carbs</div>
                </div>
                <div class="bg-gray-50 rounded-lg p-4 text-center">
                    <div class="text-2xl font-bold text-gray-900">${Math.round(nutrition.fat || 0)}g</div>
                    <div class="text-sm text-gray-600">Fat</div>
                </div>
            `;
        }
        
        // Set up action buttons - these are handled by onclick attributes in the template
        // Update the global currentRecipeId for the modal buttons
        window.currentRecipeId = recipe.id;
        console.log('Recipe modal opened with ID:', recipe.id, 'window.currentRecipeId:', window.currentRecipeId);
        
        // Update favorite heart icon state
        const favoriteHeart = document.getElementById('modal-favorite-heart');
        if (favoriteHeart) {
            if (recipe.is_favorite) {
                // Filled heart (favorited)
                favoriteHeart.innerHTML = `
                    <svg class="w-6 h-6 text-red-500" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"></path>
                    </svg>
                `;
                favoriteHeart.classList.remove('text-gray-400');
                favoriteHeart.classList.add('text-red-500');
            } else {
                // Outline heart (not favorited)
                favoriteHeart.innerHTML = `
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"></path>
                    </svg>
                `;
                favoriteHeart.classList.remove('text-red-500');
                favoriteHeart.classList.add('text-gray-400');
            }
        }
        
        // Populate contributor info
        const contributorElement = document.getElementById('modal-contributor');
        if (contributorElement) {
            contributorElement.textContent = recipe.contributor || recipe.user_name || recipe.username || 'Unknown';
        }
        
        // Show/hide edit controls based on ownership
        const editControls = document.getElementById('modal-edit-controls');
        if (editControls) {
            if (recipe.is_owner) {
                editControls.classList.remove('hidden');
            } else {
                editControls.classList.add('hidden');
            }
        }
        
        // Show/hide rate controls for all recipes (allow all users to rate)
        const rateControls = document.getElementById('modal-rate-controls');
        if (rateControls) {
            // Show rating controls for all recipes - users can rate any recipe
            rateControls.classList.remove('hidden');
        }
        
        // Populate recipe image
        const imageContainer = document.getElementById('modal-recipe-image');
        if (imageContainer && recipe.image_path) {
            imageContainer.innerHTML = `
                <img src="${recipe.image_path}" alt="${recipe.name}" class="w-full h-full object-cover">
            `;
        } else if (imageContainer) {
            imageContainer.innerHTML = `
                <div class="w-full h-full bg-gray-200 flex items-center justify-center">
                    <svg class="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
                    </svg>
                </div>
            `;
        }
        
        // Populate rating
        const ratingContainer = document.getElementById('modal-rating');
        if (ratingContainer) {
            const rating = recipe.avg_rating || recipe.average_rating || 0;
            const ratingCount = recipe.rating_count || 0;
            let starsHtml = '';
            for (let i = 1; i <= 5; i++) {
                if (i <= rating) {
                    starsHtml += '<span class="text-yellow-400">★</span>';
                } else {
                    starsHtml += '<span class="text-gray-300">★</span>';
                }
            }
            ratingContainer.innerHTML = `
                <div class="flex items-center space-x-1">
                    ${starsHtml}
                    <span class="text-sm font-medium text-gray-700 ml-1">${rating}</span>
                    <span class="text-sm text-gray-600 ml-1">(${ratingCount} ${ratingCount === 1 ? 'rating' : 'ratings'})</span>
                </div>
            `;
        }
    }

    async editRecipe(recipeId) {
        try {
            // Close the detail modal first
            this.closeRecipeDetailModal();
            
            // Show a simple edit modal or redirect to edit page
            // For now, we'll show an alert with instructions
            this.utils.showToast('Recipe editing feature coming soon! For now, you can delete and recreate the recipe.', 'info');
            
            // TODO: Implement full recipe editing modal
            // This would involve:
            // 1. Creating an edit modal similar to the create modal
            // 2. Pre-populating the form with existing recipe data
            // 3. Handling image updates via the new image endpoint
            // 4. Updating the recipe via PUT request
            
        } catch (error) {
            console.error('Error editing recipe:', error);
            this.utils.showToast('Failed to edit recipe', 'error');
        }
    }

    async deleteRecipe(recipeId) {
        if (!confirm('Are you sure you want to delete this recipe? This action cannot be undone.')) {
            return;
        }

        try {
            const response = await fetch(`/api/recipes/${recipeId}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.utils.showToast('Recipe deleted successfully', 'success');
                // Remove from local list
                this.recipes = this.recipes.filter(r => r.id !== recipeId);
                this.displayRecipes();
            } else {
                this.utils.showToast(data.error || 'Failed to delete recipe', 'error');
            }
        } catch (error) {
            console.error('Error deleting recipe:', error);
            this.utils.showToast('Failed to delete recipe', 'error');
        }
    }

    showRatingModal(recipeId) {
        this.currentRatingRecipeId = recipeId;
        document.getElementById('rating-modal').classList.remove('hidden');
        
        // Reset the rating form
        this.resetRatingForm();
        
        // Add event listeners for star rating
        this.setupStarRating();
    }
    
    resetRatingForm() {
        // Clear any selected rating
        const radioButtons = document.querySelectorAll('input[name="rating"]');
        radioButtons.forEach(radio => radio.checked = false);
        
        // Clear review text
        const reviewTextarea = document.getElementById('rating-review');
        if (reviewTextarea) {
            reviewTextarea.value = '';
        }
        
        // Reset star colors
        const starLabels = document.querySelectorAll('.star-btn');
        starLabels.forEach(label => {
            label.classList.remove('text-yellow-400');
            label.classList.add('text-gray-300');
        });
    }
    
    setupStarRating() {
        const starLabels = document.querySelectorAll('.star-btn');
        starLabels.forEach((label, index) => {
            label.addEventListener('click', () => {
                const rating = index + 1;
                
                // Update radio button
                const radio = label.querySelector('input[name="rating"]');
                if (radio) {
                    radio.checked = true;
                }
                
                // Update star colors
                starLabels.forEach((starLabel, starIndex) => {
                    if (starIndex < rating) {
                        starLabel.classList.remove('text-gray-300');
                        starLabel.classList.add('text-yellow-400');
                    } else {
                        starLabel.classList.remove('text-yellow-400');
                        starLabel.classList.add('text-gray-300');
                    }
                });
            });
        });
    }

    async submitRating() {
        if (!this.currentRatingRecipeId) return;

        const rating = document.querySelector('input[name="rating"]:checked')?.value;
        if (!rating) {
            this.utils.showToast('Please select a rating', 'error');
            return;
        }

        const review = document.getElementById('rating-review')?.value || '';

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
                this.utils.showToast('Rating submitted successfully!', 'success');
                closeRatingModal();
                // Refresh the recipe display to show updated rating
                this.displayRecipes();
            } else {
                this.utils.showToast(data.error || 'Failed to submit rating', 'error');
            }
        } catch (error) {
            console.error('Error submitting rating:', error);
            this.utils.showToast('Failed to submit rating', 'error');
        }
    }

    // Utility methods
    validateRecipeData(recipe) {
        return this.utils.validateRecipeData(recipe);
    }

    showToast(message, type = 'info') {
        this.utils.showToast(message, type);
    }
}

    // Export for use
    window.RecipeManager = RecipeManager;
}
