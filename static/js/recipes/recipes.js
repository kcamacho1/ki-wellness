/**
 * Ki Wellness Recipes - Modular Architecture
 * Main entry point that loads all recipe modules
 */

// Prevent duplicate loading of the main script
if (window.recipesInitialized) {
    // Silently skip duplicate initialization
    console.log('Recipes already initialized, skipping duplicate');
} else {
    window.recipesInitialized = true;

// Wrap everything in an IIFE to avoid global scope conflicts
(function() {
    'use strict';
    
    // Load all modules
    const moduleScripts = [
        '/static/js/recipes/modules/recipe-utils.js',
        '/static/js/recipes/modules/recipe-form.js',
        '/static/js/recipes/modules/recipe-display.js',
        '/static/js/recipes/modules/recipe-search.js',
        '/static/js/recipes/modules/recipe-manager.js'
    ];

    // Load modules sequentially
    async function loadModules() {
        for (const script of moduleScripts) {
            // Check if module is already loaded
            const moduleName = script.split('/').pop().replace('.js', '');
            const className = moduleName.split('-').map(word => 
                word.charAt(0).toUpperCase() + word.slice(1)
            ).join('');
            
            if (window[className]) {
                // Module already loaded, skip silently
                continue;
            }
            
            await new Promise((resolve, reject) => {
                const scriptElement = document.createElement('script');
                scriptElement.src = script;
                scriptElement.onload = resolve;
                scriptElement.onerror = reject;
                document.head.appendChild(scriptElement);
            });
        }
    }

    // Initialize the application
    async function initializeRecipes() {
        try {
            await loadModules();
            
            // Initialize the main RecipeManager
            new RecipeManager();
            
            console.log('✅ Recipe modules loaded successfully');
            } catch (error) {
            console.error('❌ Error loading recipe modules:', error);
            // Fallback: show error message to user
            if (typeof showToast === 'function') {
                showToast('Failed to load recipe functionality. Please refresh the page.', 'error');
            }
        }
    }

    // Global functions for backward compatibility
    window.addIngredientRow = function() {
        if (window.recipeManager && window.recipeManager.form) {
            window.recipeManager.form.addIngredientRow();
        }
    };

    window.removeImage = function() {
        if (window.recipeManager && window.recipeManager.form) {
            window.recipeManager.form.removeImage();
        }
    };

    window.closeCreateModal = function() {
        document.getElementById('create-recipe-modal').classList.add('hidden');
    };

    window.closeRatingModal = function() {
        document.getElementById('rating-modal').classList.add('hidden');
    };

    window.closeRecipeDetailModal = function() {
        document.getElementById('recipe-detail-modal').classList.add('hidden');
    };

    window.submitRating = function() {
        if (window.recipeManager) {
            window.recipeManager.submitRating();
        }
    };

    window.switchSearchTab = function(tabName) {
        // Hide all tab contents
        document.querySelectorAll('.search-tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        
        // Remove active state from all tabs
        document.querySelectorAll('.search-tab').forEach(tab => {
            tab.classList.remove('active', 'border-ki-green-500', 'text-ki-green-600');
            tab.classList.add('border-transparent', 'text-gray-500');
        });
        
        // Show selected tab content
        const selectedTab = document.getElementById(`tab-content-${tabName}`);
        const selectedTabButton = document.getElementById(`tab-${tabName}`);
        
        if (selectedTab) {
            selectedTab.classList.remove('hidden');
        }
        
        if (selectedTabButton) {
            selectedTabButton.classList.remove('border-transparent', 'text-gray-500');
            selectedTabButton.classList.add('active', 'border-ki-green-500', 'text-ki-green-600');
        }
    };

    // Star rating functions
    window.updateStarDisplay = function(rating) {
    document.querySelectorAll('.star-btn').forEach((btn, index) => {
        if (index < rating) {
            btn.classList.remove('text-gray-300');
            btn.classList.add('text-yellow-400');
        } else {
            btn.classList.remove('text-yellow-400');
            btn.classList.add('text-gray-300');
        }
    });
    };

// Add star rating event listeners
document.addEventListener('DOMContentLoaded', function() {
        document.querySelectorAll('.star-btn').forEach((btn, index) => {
        btn.addEventListener('click', function() {
                window.updateStarDisplay(index + 1);
                // Set the hidden input value
                const ratingInput = document.querySelector('input[name="rating"]');
                if (ratingInput) {
                    ratingInput.value = index + 1;
                }
        });
    });
});

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeRecipes);
    } else {
        initializeRecipes();
    }

})(); // End of IIFE

} // End of duplicate loading protection
