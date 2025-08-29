// Dashboard Food Management
// Handles food logging, display, and interactions
class DashboardFood {
    constructor(core) {
        this.core = core;
        this.currentEditingFood = null;
        this.setupEditEventListeners();
    }

    displayFoodLog(foodLogs) {

        const container = document.getElementById('food-log-display');
        
        if (!container) {
            console.error('Food log container not found');
            return;
        }



        if (!foodLogs || foodLogs.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12 text-gray-500">
                    <svg class="mx-auto h-16 w-16 text-gray-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/>
                    </svg>
                    <p class="mt-4 text-lg">No food logged yet today</p>
                    <p class="text-sm text-gray-400">Start tracking your meals!</p>
                </div>
            `;
            return;
        }

        // Group foods by meal type
        const mealGroups = this.groupFoodsByMeal(foodLogs);
        
        let html = '';
        for (const [mealType, foods] of Object.entries(mealGroups)) {
            if (foods.length > 0) {
                html += this.generateMealSection(mealType, foods);
            }
        }

        container.innerHTML = html;
    }

    groupFoodsByMeal(foodLogs) {
        const groups = {
            'Breakfast': [],
            'Lunch': [],
            'Dinner': [],
            'Snack': []
        };

        foodLogs.forEach(food => {
            // Map time_of_day from API to display format
            const timeOfDay = food.time_of_day || 'snack';
            const mealType = timeOfDay.charAt(0).toUpperCase() + timeOfDay.slice(1).toLowerCase();
            
            if (groups[mealType]) {
                groups[mealType].push(food);
            } else {
                groups['Snack'].push(food);
            }
        });

        return groups;
    }

    setupEditEventListeners() {
        // Handle edit button clicks
        document.addEventListener('click', (e) => {
            if (e.target.closest('.edit-food-btn')) {
                const foodId = e.target.closest('.edit-food-btn').dataset.foodId;
                this.openEditModal(foodId);
            }
        });

        // Handle modal close events
        document.addEventListener('click', (e) => {
            if (e.target.matches('#close-edit-food-modal') || e.target.matches('#cancel-edit-food')) {
                this.closeEditModal();
            }
        });

        // Handle save button
        document.addEventListener('click', (e) => {
            if (e.target.matches('#save-edit-food')) {
                this.saveEditedFood();
            }
        });

        // Handle real-time nutrition calculation updates
        document.addEventListener('input', (e) => {
            if (e.target.matches('#edit-food-quantity') || e.target.matches('#edit-food-unit')) {
                this.updateCalculatedNutrition();
            }
        });

        // Handle nutrition updates when user leaves the field
        document.addEventListener('change', (e) => {
            if (e.target.matches('#edit-food-quantity') || e.target.matches('#edit-food-unit')) {
                this.updateCalculatedNutrition();
            }
        });

        // Handle nutrition updates when user clicks out of field (blur)
        document.addEventListener('blur', (e) => {
            if (e.target.matches('#edit-food-quantity') || e.target.matches('#edit-food-unit')) {
                this.updateCalculatedNutrition();
            }
        }, true); // Use capture to ensure we catch the blur event

        // Handle form submission
        document.addEventListener('submit', (e) => {
            if (e.target.matches('#edit-food-form')) {
                e.preventDefault();
                this.saveEditedFood();
            }
        });
    }

    async openEditModal(foodId) {
        try {
            // Check if modal exists
            const modal = document.getElementById('edit-food-modal');
            if (!modal) {
                console.error('Edit modal not found in DOM');
                return;
            }

            // Find the food item in current data
            const allFoodLogs = this.core.currentData?.food_logs || [];
            const foodItem = allFoodLogs.find(food => food.id == foodId);
            
            if (!foodItem) {
                console.error('Food item not found:', foodId);
                return;
            }

            this.currentEditingFood = foodItem;

            // Get modal elements with null checks
            const nameEl = document.getElementById('edit-food-name');
            const brandEl = document.getElementById('edit-food-brand');
            const quantityEl = document.getElementById('edit-food-quantity');
            const unitEl = document.getElementById('edit-food-unit');
            const timeOfDayEl = document.getElementById('edit-food-time-of-day');
            const dateEl = document.getElementById('edit-food-date');

            // Check if all required elements exist
            if (!nameEl || !brandEl || !quantityEl || !unitEl || !timeOfDayEl || !dateEl) {
                console.error('Some modal elements not found');
                return;
            }

            // Populate modal with current values
            nameEl.textContent = foodItem.name;
            brandEl.textContent = foodItem.brand || 'Unknown Brand';
            quantityEl.value = foodItem.quantity || 1;
            unitEl.value = 'g'; // Default to grams
            timeOfDayEl.value = foodItem.time_of_day || 'snack';
            
            // Set date (convert from timestamp if needed)
            const foodDate = foodItem.date || new Date().toISOString().split('T')[0];
            dateEl.value = foodDate;

            // Calculate and display current nutrition
            this.updateCalculatedNutrition();

            // Add specific event listeners for this modal session
            this.attachModalEventListeners(quantityEl, unitEl);

            // Show modal
            modal.classList.remove('hidden');
            document.body.style.overflow = 'hidden';

        } catch (error) {
            console.error('Error opening edit modal:', error);
        }
    }

    closeEditModal() {
        const modal = document.getElementById('edit-food-modal');
        if (modal) {
            modal.classList.add('hidden');
        }
        document.body.style.overflow = '';
        
        // Remove modal-specific event listeners
        this.removeModalEventListeners();
        
        this.currentEditingFood = null;
    }

    attachModalEventListeners(quantityEl, unitEl) {
        // Store references for removal later
        this.modalQuantityHandler = () => {
            this.updateCalculatedNutrition();
        };
        
        this.modalUnitHandler = () => {
            this.updateCalculatedNutrition();
        };

        // Add multiple event types to ensure updates
        quantityEl.addEventListener('input', this.modalQuantityHandler);
        quantityEl.addEventListener('change', this.modalQuantityHandler);
        quantityEl.addEventListener('blur', this.modalQuantityHandler);
        quantityEl.addEventListener('keyup', this.modalQuantityHandler);

        unitEl.addEventListener('input', this.modalUnitHandler);
        unitEl.addEventListener('change', this.modalUnitHandler);
        unitEl.addEventListener('blur', this.modalUnitHandler);
        

    }

    removeModalEventListeners() {
        const quantityEl = document.getElementById('edit-food-quantity');
        const unitEl = document.getElementById('edit-food-unit');

        if (quantityEl && this.modalQuantityHandler) {
            quantityEl.removeEventListener('input', this.modalQuantityHandler);
            quantityEl.removeEventListener('change', this.modalQuantityHandler);
            quantityEl.removeEventListener('blur', this.modalQuantityHandler);
            quantityEl.removeEventListener('keyup', this.modalQuantityHandler);
        }

        if (unitEl && this.modalUnitHandler) {
            unitEl.removeEventListener('input', this.modalUnitHandler);
            unitEl.removeEventListener('change', this.modalUnitHandler);
            unitEl.removeEventListener('blur', this.modalUnitHandler);
        }

        this.modalQuantityHandler = null;
        this.modalUnitHandler = null;
        

    }

    async refreshFoodDisplayAfterEdit() {
        // Force refresh of food display after edit to ensure UI is updated
        try {
            // First try to use current data if available
            if (this.core && this.core.currentData && this.core.currentData.food_logs) {
                this.displayFoodLog(this.core.currentData.food_logs);
            }
            
            // Also trigger a fresh data load to ensure we have the latest
            if (window.dashboardManager && window.dashboardManager.loadDashboardDataOptimized) {
                await window.dashboardManager.loadDashboardDataOptimized();
            }
        } catch (error) {
            console.error('Error refreshing food display after edit:', error);
        }
    }

    updateCalculatedNutrition() {
        if (!this.currentEditingFood) {
            console.warn('No current editing food found');
            return;
        }

        const quantityEl = document.getElementById('edit-food-quantity');
        const unitEl = document.getElementById('edit-food-unit');
        const caloriesEl = document.getElementById('edit-calculated-calories');
        const proteinEl = document.getElementById('edit-calculated-protein');
        const carbsEl = document.getElementById('edit-calculated-carbs');
        const fatEl = document.getElementById('edit-calculated-fat');

        // Check if elements exist
        if (!quantityEl || !unitEl || !caloriesEl || !proteinEl || !carbsEl || !fatEl) {
            console.warn('Some nutrition calculation elements not found');
            return;
        }

        const quantity = parseFloat(quantityEl.value) || 1;
        const unit = unitEl.value;



        // Calculate nutrition based on grams: new_grams / original_serving_size_grams
        const originalServingSizeGrams = this.currentEditingFood.serving_size || 100;
        const newQuantityGrams = unit === 'g' ? quantity : quantity * originalServingSizeGrams;
        const multiplier = newQuantityGrams / originalServingSizeGrams;

        const calories = Math.round((this.currentEditingFood.calories || 0) * multiplier);
        const protein = Math.round((this.currentEditingFood.protein || 0) * multiplier * 10) / 10;
        const carbs = Math.round((this.currentEditingFood.carbs || 0) * multiplier * 10) / 10;
        const fat = Math.round((this.currentEditingFood.fat || 0) * multiplier * 10) / 10;

        // Update display
        caloriesEl.textContent = calories;
        proteinEl.textContent = protein + 'g';
        carbsEl.textContent = carbs + 'g';
        fatEl.textContent = fat + 'g';
    }

    async saveEditedFood() {
        if (!this.currentEditingFood) return;

        try {
            const quantity = parseFloat(document.getElementById('edit-food-quantity').value) || 1;
            const unit = document.getElementById('edit-food-unit').value;
            const timeOfDay = document.getElementById('edit-food-time-of-day').value;
            const date = document.getElementById('edit-food-date').value;

            // Calculate updated nutrition values using the same logic as updateCalculatedNutrition
            const originalServingSizeGrams = this.currentEditingFood.serving_size || 100;
            const newQuantityGrams = unit === 'g' ? quantity : quantity * originalServingSizeGrams;
            const multiplier = newQuantityGrams / originalServingSizeGrams;

            const updatedData = {
                quantity: quantity,
                time_of_day: timeOfDay,
                date: date,
                calories: Math.round((this.currentEditingFood.calories || 0) * multiplier),
                protein: Math.round((this.currentEditingFood.protein || 0) * multiplier * 10) / 10,
                carbs: Math.round((this.currentEditingFood.carbs || 0) * multiplier * 10) / 10,
                fat: Math.round((this.currentEditingFood.fat || 0) * multiplier * 10) / 10,
                serving_size: newQuantityGrams
            };

            // Send update to server
            const response = await fetch(`/api/food-log/${this.currentEditingFood.id}/edit`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'same-origin',
                body: JSON.stringify(updatedData)
            });

            const result = await response.json();

            if (result.success) {
                // Check if the date was changed (normalize dates for comparison)
                const originalDate = this.currentEditingFood.date;
                const newDate = date;
                
                // Normalize both dates to YYYY-MM-DD format for comparison
                let normalizedOriginalDate = originalDate;
                if (originalDate && originalDate.includes('T')) {
                    normalizedOriginalDate = originalDate.split('T')[0];
                } else if (originalDate && originalDate.length > 10) {
                    normalizedOriginalDate = new Date(originalDate).toISOString().split('T')[0];
                }
                
                const dateChanged = normalizedOriginalDate !== newDate;
                

                
                // Close modal first
                this.closeEditModal();
                
                if (dateChanged) {
                    // Food was moved to a different date
                    this.showToast(`Food entry moved to ${newDate}!`, 'success');
                    
                    // Small delay to let the success message show, then navigate
                    setTimeout(() => {
                        // Navigate dashboard to the new date to show the moved item
                        if (window.dashboardManager && window.dashboardManager.selectDate) {
                            window.dashboardManager.selectDate(newDate);
                        } else if (window.dashboardManager && window.dashboardManager.currentDate) {
                            // Fallback: set the current date and refresh
                            window.dashboardManager.currentDate = new Date(newDate);
                            if (window.dashboardManager.loadDashboardDataOptimized) {
                                window.dashboardManager.loadDashboardDataOptimized();
                            }
                        }
                    }, 1000);
                } else {
                    // Same date, just show success and refresh
                    this.showToast('Food entry updated successfully!', 'success');
                    
                    // Refresh dashboard to show updated values
                    if (window.dashboardManager && window.dashboardManager.loadDashboardDataOptimized) {
                        await window.dashboardManager.loadDashboardDataOptimized();
                        
                        // Additional explicit refresh of food display
                        setTimeout(() => {
                            this.refreshFoodDisplayAfterEdit();
                        }, 200);
                    }
                }
            } else {
                this.showToast(result.message || 'Failed to update food entry', 'error');
            }

        } catch (error) {
            console.error('Error saving edited food:', error);
            this.showToast('Network error occurred', 'error');
        }
    }

    showToast(message, type = 'info') {
        // Create toast notification
        const toast = document.createElement('div');
        toast.className = `fixed top-4 right-4 z-50 px-4 py-2 rounded-md text-white ${
            type === 'success' ? 'bg-green-500' : 
            type === 'error' ? 'bg-red-500' : 
            'bg-blue-500'
        }`;
        toast.textContent = message;
        
        document.body.appendChild(toast);
        
        // Remove after 3 seconds
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    generateMealSection(mealType, foods) {
        const mealEmojis = {
            'Breakfast': '🌅',
            'Lunch': '☀️',
            'Dinner': '🌙',
            'Snack': '🍎'
        };

        const totalCalories = foods.reduce((sum, food) => sum + (food.calories || 0), 0);

        const foodItems = foods.map(food => this.generateFoodItem(food)).join('');

        return `
            <div class="mb-6 bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                <div class="bg-gradient-to-r from-ki-green-50 to-green-50 px-6 py-4 border-b border-gray-100">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <span class="text-2xl">${mealEmojis[mealType]}</span>
                            <div>
                                <h3 class="text-lg font-semibold text-gray-900">${mealType}</h3>
                                <p class="text-sm text-gray-600">${foods.length} item${foods.length !== 1 ? 's' : ''}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <p class="text-lg font-bold text-ki-green-600">${Math.round(totalCalories)} cal</p>
                        </div>
                    </div>
                </div>
                <div class="divide-y divide-gray-100">
                    ${foodItems}
                </div>
            </div>
        `;
    }

    generateFoodItem(food) {
        const timeAgo = this.getTimeAgo(new Date(food.timestamp));
        
        return `
            <div class="px-6 py-4 hover:bg-gray-50 transition-colors">
                <div class="flex items-center justify-between">
                    <div class="flex-1 min-w-0">
                        <div class="flex items-center space-x-3">
                            <div class="flex-1">
                                <h4 class="text-base font-medium text-gray-900 truncate">${food.name}</h4>
                                <div class="flex items-center space-x-4 mt-1">
                                    <p class="text-sm text-gray-600">
                                        ${food.quantity || 1} serving${(food.quantity || 1) !== 1 ? 's' : ''} ${food.brand ? `• ${food.brand}` : ''}
                                    </p>
                                    <p class="text-sm text-gray-500">
                                        ${timeAgo}
                                    </p>
                                </div>
                            </div>
                        </div>
                        <div class="flex items-center space-x-4 mt-2 text-xs text-gray-500">
                            <span>🔥 ${Math.round(food.calories || 0)} cal</span>
                            <span>🍞 ${Math.round(food.carbs || 0)}g carbs</span>
                            <span>🥩 ${Math.round(food.protein || 0)}g protein</span>
                            <span>🥑 ${Math.round(food.fat || 0)}g fat</span>
                        </div>
                    </div>
                    <div class="flex items-center space-x-2 ml-4">
                        <button class="edit-food-btn p-2 text-gray-400 hover:text-blue-500 transition-colors" 
                                data-food-id="${food.id}" 
                                title="Edit entry">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                            </svg>
                        </button>
                        <button class="copy-food-btn p-2 text-gray-400 hover:text-ki-green-600 transition-colors" 
                                data-food-id="${food.id}" 
                                title="Copy to today">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"/>
                            </svg>
                        </button>
                        <button class="delete-food-btn p-2 text-gray-400 hover:text-red-500 transition-colors" 
                                data-food-id="${food.id}" 
                                title="Delete entry">
                            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"/>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `;
    }

    getTimeAgo(timestamp) {
        const now = new Date();
        const diffInMs = now - timestamp;
        const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
        const diffInHours = Math.floor(diffInMinutes / 60);

        if (diffInMinutes < 1) return 'Just now';
        if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
        if (diffInHours < 24) return `${diffInHours}h ago`;
        
        return timestamp.toLocaleDateString();
    }

    async showCopyConfirmation(foodId) {
        try {
            const response = await fetch(`/api/food-log/${foodId}`);
            const data = await response.json();
            
            if (data.success) {
                const food = data.food_log;
                const confirmed = confirm(`Copy "${food.food_name}" (${food.amount} ${food.unit}) to today?`);
                
                if (confirmed) {
                    this.confirmCopyFood(foodId);
                }
            }
        } catch (error) {
            console.error('Error fetching food details:', error);
            this.core.ui.showToast('Failed to get food details', 'error');
        }
    }

    async confirmCopyFood(foodId) {
        try {
            const response = await fetch(`/api/food-log/${foodId}/copy`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    date: this.core.currentDate.toISOString().split('T')[0]
                })
            });

            const data = await response.json();
            
            if (data.success) {
                this.core.ui.showToast('Food copied to today!', 'success');
                this.core.debouncedReload();
            } else {
                this.core.ui.showToast('Failed to copy food item', 'error');
            }
        } catch (error) {
            console.error('Error copying food item:', error);
            this.core.ui.showToast('Failed to copy food item', 'error');
        }
    }

    async confirmDeleteFood(foodId) {
        const confirmed = confirm('Are you sure you want to delete this food entry?');
        if (!confirmed) return;

        try {
            const response = await fetch(`/api/food-log/${foodId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                this.core.ui.showToast('Food item removed', 'success');
                this.core.invalidateCacheAndReload();
            } else {
                this.core.ui.showToast('Failed to remove food item', 'error');
            }
        } catch (error) {
            console.error('Error removing food item:', error);
            this.core.ui.showToast('Failed to remove food item', 'error');
        }
    }
}

// Make available globally
window.DashboardFood = DashboardFood;
