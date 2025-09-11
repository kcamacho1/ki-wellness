/**
 * Recipe Search Module
 * Handles search functionality, filtering, and ingredient-based search
 */

// Prevent duplicate loading
if (typeof window.RecipeSearch !== 'undefined') {
    // Already loaded, skip silently
} else {
    class RecipeSearch {
    constructor(recipeManager) {
        this.recipeManager = recipeManager;
    }

    showSearchLoading() {
        this.recipeManager.isSearching = true;
        
        // Update unified search button
        const unifiedSearchButton = document.getElementById('unified-search-button');
        const unifiedSearchButtonText = document.getElementById('unified-search-button-text');
        const unifiedSearchButtonSpinner = document.getElementById('unified-search-button-spinner');
        
        if (unifiedSearchButton && unifiedSearchButtonText && unifiedSearchButtonSpinner) {
            unifiedSearchButton.disabled = true;
            unifiedSearchButtonText.classList.add('hidden');
            unifiedSearchButtonSpinner.classList.remove('hidden');
        }
        
        // Update original search button for backward compatibility
        const searchButton = document.getElementById('search-button');
        const searchButtonText = document.getElementById('search-button-text');
        const searchButtonSpinner = document.getElementById('search-button-spinner');
        
        if (searchButton && searchButtonText && searchButtonSpinner) {
            searchButton.disabled = true;
            searchButtonText.classList.add('hidden');
            searchButtonSpinner.classList.remove('hidden');
        }
    }

    hideSearchLoading() {
        this.recipeManager.isSearching = false;
        
        // Update unified search button
        const unifiedSearchButton = document.getElementById('unified-search-button');
        const unifiedSearchButtonText = document.getElementById('unified-search-button-text');
        const unifiedSearchButtonSpinner = document.getElementById('unified-search-button-spinner');
        
        if (unifiedSearchButton && unifiedSearchButtonText && unifiedSearchButtonSpinner) {
            unifiedSearchButton.disabled = false;
            unifiedSearchButtonText.classList.remove('hidden');
            unifiedSearchButtonSpinner.classList.add('hidden');
        }
        
        // Update original search button for backward compatibility
        const searchButton = document.getElementById('search-button');
        const searchButtonText = document.getElementById('search-button-text');
        const searchButtonSpinner = document.getElementById('search-button-spinner');
        
        if (searchButton && searchButtonText && searchButtonSpinner) {
            searchButton.disabled = false;
            searchButtonText.classList.remove('hidden');
            searchButtonSpinner.classList.add('hidden');
        }
    }

    async searchRecipes() {
        if (this.recipeManager.isSearching) return;
        
        // Try unified search input first, fallback to original
        const unifiedInput = document.getElementById('unified-search-input');
        const originalInput = document.getElementById('recipe-search');
        const query = (unifiedInput ? unifiedInput.value : originalInput.value).trim();
        
        if (!query) {
            this.recipeManager.showToast('Please enter a search term', 'error');
            return;
        }

        this.showSearchLoading();
        const searchStartTime = performance.now();

        try {
            const response = await fetch(`/api/recipes/search?q=${encodeURIComponent(query)}&include_public=true`, {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            const data = await response.json();
            
            if (data.success) {
                // Validate recipe data and filter out invalid entries
                this.recipeManager.recipes = data.recipes.filter(recipe => this.recipeManager.validateRecipeData(recipe));
                
                this.recipeManager.currentPage = 1;
                this.recipeManager.totalPages = data.total_pages || 1;
                this.recipeManager.displayRecipes();
                
                // Calculate search time
                const searchTime = Math.round(performance.now() - searchStartTime);
                
                const totalFound = data.total_found || this.recipeManager.recipes.length;
                this.recipeManager.showToast(`Found ${totalFound} recipes matching "${query}" in ${searchTime}ms`, 'success');
                
                // Search completed successfully
                this.recipeManager.isSearching = false;
            } else {
                this.recipeManager.showToast(data.error || 'Search failed', 'error');
            }
        } catch (error) {
            console.error('Error searching recipes:', error);
            this.recipeManager.showToast('Search failed', 'error');
        } finally {
            this.hideSearchLoading();
        }
    }

    async searchByIngredients() {
        if (this.recipeManager.isSearching) return;
        
        const ingredientsList = document.getElementById('ingredients-list');
        const ingredients = Array.from(ingredientsList.children).map(span => {
            // Get the text content before the button (first text node)
            const textNode = span.childNodes[0];
            return textNode ? textNode.textContent.trim() : '';
        }).filter(ingredient => ingredient.length > 0);
        
        console.log('Ingredients extracted:', ingredients);
        
        if (ingredients.length < 3) {
            this.recipeManager.showToast('Please add at least 3 ingredients', 'error');
            return;
        }

        this.showSearchLoading();
        const searchStartTime = performance.now();

        try {
            const response = await fetch('/api/recipes/search-by-ingredients', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.recipeManager.getCSRFToken()
                },
                body: JSON.stringify({ 
                    ingredients,
                    include_public: true,
                    min_ingredients: 3
                })
            });

            const data = await response.json();
            console.log('Ingredient search response:', data);
            
            if (data.success) {
                // Validate recipe data and filter out invalid entries
                this.recipeManager.recipes = data.recipes.filter(recipe => this.recipeManager.validateRecipeData(recipe));
                
                this.recipeManager.currentPage = 1;
                this.recipeManager.totalPages = data.total_pages || 1;
                this.recipeManager.displayRecipes();
                
                // Calculate search time
                const searchTime = Math.round(performance.now() - searchStartTime);
                
                const totalFound = data.total_found || this.recipeManager.recipes.length;
                this.recipeManager.showToast(`Found ${totalFound} recipes with your ingredients in ${searchTime}ms`, 'success');
                
                // Search completed successfully
                this.recipeManager.isSearching = false;
            } else {
                this.recipeManager.showToast(data.error || 'Ingredient search failed', 'error');
            }
        } catch (error) {
            console.error('Error searching by ingredients:', error);
            this.recipeManager.showToast('Ingredient search failed', 'error');
        } finally {
            this.hideSearchLoading();
        }
    }

    async filterByCategory(category) {
        this.recipeManager.currentCategory = category;
        this.recipeManager.currentPage = 1;
        
        // Update active category button
        document.querySelectorAll('.category-btn').forEach(btn => {
            btn.classList.remove('bg-ki-green-600', 'text-white');
            btn.classList.add('bg-gray-100', 'text-gray-700');
        });
        
        const activeBtn = document.querySelector(`[onclick*="${category}"]`);
        if (activeBtn) {
            activeBtn.classList.remove('bg-gray-100', 'text-gray-700');
            activeBtn.classList.add('bg-ki-green-600', 'text-white');
        }
        
        this.recipeManager.displayRecipes();
    }

    async clearSearch() {
        // Clear unified search input
        const unifiedInput = document.getElementById('unified-search-input');
        if (unifiedInput) {
            unifiedInput.value = '';
        }
        
        // Clear original search inputs for backward compatibility
        const originalInput = document.getElementById('recipe-search');
        if (originalInput) {
            originalInput.value = '';
        }
        
        document.getElementById('ingredients-list').innerHTML = '';
        this.recipeManager.isSearching = false; // Reset search state
        this.hideSearchLoading(); // Ensure loading state is hidden
        this.recipeManager.showPlaceholderContent(); // Show placeholder instead of loading recipes
        this.recipeManager.showToast('Search cleared', 'info');
    }

    addIngredient(ingredient) {
        const ingredientsList = document.getElementById('ingredients-list');
        const li = document.createElement('li');
        li.className = 'inline-flex items-center px-3 py-1 rounded-full text-sm bg-ki-green-100 text-ki-green-800 mr-2 mb-2';
        li.innerHTML = `
            ${ingredient}
            <button onclick="this.parentElement.remove()" class="ml-2 text-ki-green-600 hover:text-ki-green-800">
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        `;
        ingredientsList.appendChild(li);
    }

    handleIngredientKeyPress(event) {
        if (event.key === 'Enter') {
            event.preventDefault();
            const input = event.target;
            const ingredient = input.value.trim();
            
            if (ingredient) {
                this.addIngredient(ingredient);
                input.value = '';
            }
        }
    }
}

    // Export for use in other modules
    window.RecipeSearch = RecipeSearch;
}
