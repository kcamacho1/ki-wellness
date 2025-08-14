/**
 * Food Journal Module
 * Handles food journal functionality including data loading, display, and interactions
 */

class FoodJournalManager {
    constructor(options = {}) {
        this.tableId = options.tableId || 'foodJournalTable';
        this.currentDate = new Date();
        this.onEntryAdded = options.onEntryAdded || null;
        this.onEntryDeleted = options.onEntryDeleted || null;
        this.entries = [];
        this.isLoading = false;
    }

    /**
     * Initialize the food journal manager
     */
    async init() {
        this.setupDateNavigation();
        await this.loadEntries();
        this.setupEventListeners();
    }

    /**
     * Setup date navigation controls
     */
    setupDateNavigation() {
        this.updateDateDisplay();
        
        // Previous day button
        const prevDayBtn = document.getElementById('prevDayBtn');
        if (prevDayBtn) {
            prevDayBtn.addEventListener('click', () => this.navigateToPreviousDay());
        }
        
        // Next day button
        const nextDayBtn = document.getElementById('nextDayBtn');
        if (nextDayBtn) {
            nextDayBtn.addEventListener('click', () => this.navigateToNextDay());
        }
        
        // Today button
        const todayBtn = document.getElementById('todayBtn');
        if (todayBtn) {
            todayBtn.addEventListener('click', () => this.navigateToToday());
        }
    }

    /**
     * Navigate to previous day
     */
    navigateToPreviousDay() {
        this.currentDate.setDate(this.currentDate.getDate() - 1);
        this.updateDateDisplay();
        this.loadEntries();
        this.updateDashboardStats();
    }

    /**
     * Navigate to next day
     */
    navigateToNextDay() {
        const tomorrow = new Date(this.currentDate);
        tomorrow.setDate(tomorrow.getDate() + 1);
        
        // Don't allow navigation to future dates
        const today = new Date();
        today.setHours(23, 59, 59, 999);
        
        if (tomorrow <= today) {
            this.currentDate = tomorrow;
            this.updateDateDisplay();
            this.loadEntries();
            this.updateDashboardStats();
        }
    }

    /**
     * Navigate to today
     */
    navigateToToday() {
        this.currentDate = new Date();
        this.updateDateDisplay();
        this.loadEntries();
        this.updateDashboardStats();
    }

    /**
     * Update the date display
     */
    updateDateDisplay() {
        const currentDateElement = document.getElementById('currentDate');
        if (currentDateElement) {
            const today = new Date();
            const isToday = this.currentDate.toDateString() === today.toDateString();
            
            const dateString = this.currentDate.toLocaleDateString('en-US', {
                weekday: 'short',
                month: 'short',
                day: 'numeric'
            });
            
            currentDateElement.textContent = isToday ? `Today (${dateString})` : dateString;
            
            // Update button states
            const nextDayBtn = document.getElementById('nextDayBtn');
            if (nextDayBtn) {
                nextDayBtn.disabled = isToday;
                nextDayBtn.classList.toggle('opacity-50', isToday);
                nextDayBtn.classList.toggle('cursor-not-allowed', isToday);
            }
        }
    }

    /**
     * Load food journal entries for the current date
     */
    async loadEntries() {
        try {
            this.isLoading = true;
            this.showLoadingState();

            const dateString = this.currentDate.toISOString().split('T')[0];
            
            const response = await fetch(`/food-journal/entries?start_date=${dateString}&end_date=${dateString}`);
            const data = await response.json();
            
            if (data.success) {
                this.entries = data.entries || [];
                this.displayEntries();
                this.updateMacronutrientChart();
                this.updateDashboardStats();
            } else {
                console.error('Error loading food journal:', data.error);
                this.showErrorState(data.error);
            }
        } catch (error) {
            console.error('Error loading food journal:', error);
            this.showErrorState('Failed to load food journal entries');
        } finally {
            this.isLoading = false;
        }
    }

    /**
     * Update macronutrient chart with daily totals
     */
    updateMacronutrientChart() {
        const totals = this.calculateDailyTotals();
        
        // Update the macronutrient chart if it exists
        const macrosChart = window.macrosChart;
        if (macrosChart) {
            // Update chart data
            macrosChart.data.datasets[0].data = [
                totals.protein * 4, // Protein calories (4 cal/g)
                totals.carbs * 4,   // Carbs calories (4 cal/g)
                totals.fat * 9      // Fat calories (9 cal/g)
            ];
            macrosChart.update();
        }
        
        // Update the text displays
        const totalCaloriesElement = document.getElementById('totalCalories');
        const proteinAmountElement = document.getElementById('proteinAmount');
        const carbsAmountElement = document.getElementById('carbsAmount');
        const fatAmountElement = document.getElementById('fatAmount');
        
        if (totalCaloriesElement) totalCaloriesElement.textContent = totals.calories;
        if (proteinAmountElement) proteinAmountElement.textContent = `${totals.protein}g`;
        if (carbsAmountElement) carbsAmountElement.textContent = `${totals.carbs}g`;
        if (fatAmountElement) fatAmountElement.textContent = `${totals.fat}g`;
    }

    /**
     * Calculate daily totals from entries
     */
    calculateDailyTotals() {
        return this.entries.reduce((totals, entry) => {
            totals.calories += parseInt(entry.calories) || 0;
            totals.protein += parseFloat(entry.protein) || 0;
            totals.carbs += parseFloat(entry.carbs) || 0;
            totals.fat += parseFloat(entry.fat) || 0;
            return totals;
        }, { calories: 0, protein: 0, carbs: 0, fat: 0 });
    }

    /**
     * Display food journal entries in the table
     */
    displayEntries() {
        const tableBody = document.getElementById(this.tableId);
        if (!tableBody) {
            console.error(`Table body with id '${this.tableId}' not found`);
            return;
        }

        tableBody.innerHTML = '';
        
        if (this.entries.length === 0) {
            this.showEmptyState(tableBody);
            return;
        }
        
        this.entries.forEach(entry => {
            const row = this.createEntryRow(entry);
            tableBody.appendChild(row);
        });
    }

    /**
     * Create a table row for a food entry
     */
    createEntryRow(entry) {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50 transition-colors duration-200';
        row.dataset.entryId = entry.id;
        
        row.innerHTML = `
            <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                ${this.formatTime(entry.consumed_at)}
            </td>
            <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                ${this.getMealTimeDisplay(entry.time_of_day)}
            </td>
            <td class="px-4 py-4 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900">${entry.food_name}</div>
                ${entry.brand ? `<div class="text-sm text-gray-500">${entry.brand}</div>` : ''}
            </td>
            <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                ${entry.serving_size} ${entry.serving_unit}
            </td>
            <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                ${entry.calories || 0}
            </td>
            <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                ${entry.protein || 0}g
            </td>
            <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                ${entry.carbs || 0}g
            </td>
            <td class="px-4 py-4 whitespace-nowrap text-sm text-gray-900">
                ${entry.fat || 0}g
            </td>
            <td class="px-4 py-4 whitespace-nowrap text-right text-sm font-medium">
                <button class="text-red-600 hover:text-red-900 delete-entry-btn" data-entry-id="${entry.id}">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                    </svg>
                </button>
            </td>
        `;

        // Add delete functionality
        const deleteBtn = row.querySelector('.delete-entry-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.deleteEntry(entry.id);
            });
        }

        return row;
    }

    /**
     * Show loading state
     */
    showLoadingState() {
        const tableBody = document.getElementById(this.tableId);
        if (!tableBody) return;

        tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="px-6 py-8 text-center">
                    <div class="flex flex-col items-center space-y-3">
                        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-mint-green"></div>
                        <p class="text-sm text-gray-600">Loading food entries...</p>
                    </div>
                </td>
            </tr>
        `;
    }

    /**
     * Show empty state
     */
    showEmptyState(tableBody) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="9" class="px-6 py-8 text-center text-gray-500">
                <div class="flex flex-col items-center space-y-3">
                    <svg class="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                    <div class="text-center">
                        <p class="text-sm font-medium text-gray-900">No food entries for this date</p>
                        <p class="text-xs text-gray-400 mt-1">Start tracking your nutrition by adding your first meal</p>
                    </div>
                </div>
            </td>
        `;
        tableBody.appendChild(row);
    }

    /**
     * Show error state
     */
    showErrorState(error) {
        const tableBody = document.getElementById(this.tableId);
        if (!tableBody) return;

        tableBody.innerHTML = `
            <tr>
                <td colspan="9" class="px-6 py-8 text-center">
                    <div class="flex flex-col items-center space-y-3">
                        <svg class="w-12 h-12 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                        </svg>
                        <div class="text-center">
                            <p class="text-sm font-medium text-red-900">Failed to load entries</p>
                            <p class="text-xs text-red-600 mt-1">${error}</p>
                            <button class="mt-3 px-4 py-2 bg-mint-green text-white rounded-md hover:bg-forest-green transition-colors duration-200 text-sm" onclick="foodJournalManager.loadEntries()">
                                Try Again
                            </button>
                        </div>
                    </div>
                </td>
            </tr>
        `;
    }

    /**
     * Delete a food entry
     */
    async deleteEntry(entryId) {
        if (!confirm('Are you sure you want to delete this food entry?')) {
            return;
        }

        try {
            const response = await fetch('/food-journal/delete', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ entry_id: entryId })
            });

            const data = await response.json();
            
            if (data.success) {
                // Remove from local entries array
                this.entries = this.entries.filter(entry => entry.id !== entryId);
                
                // Remove from DOM
                const row = document.querySelector(`[data-entry-id="${entryId}"]`);
                if (row) {
                    row.remove();
                }

                // Show empty state if no entries left
                if (this.entries.length === 0) {
                    this.showEmptyState(document.getElementById(this.tableId));
                }

                // Call callback if provided
                if (this.onEntryDeleted) {
                    this.onEntryDeleted(entryId);
                }

                // Show success message
                this.showNotification('Food entry deleted successfully', 'success');
            } else {
                this.showNotification('Failed to delete entry: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Error deleting entry:', error);
            this.showNotification('Error deleting entry. Please try again.', 'error');
        }
    }

    /**
     * Add a new food entry
     */
    async addEntry(entryData) {
        try {
            const response = await fetch('/food-journal/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(entryData)
            });

            const data = await response.json();
            
            if (data.success) {
                // Reload entries to get the new entry
                await this.loadEntries();
                
                // Call callback if provided
                if (this.onEntryAdded) {
                    this.onEntryAdded(data.entry);
                }

                this.showNotification('Food entry added successfully', 'success');
                return true;
            } else {
                this.showNotification('Failed to add entry: ' + (data.error || 'Unknown error'), 'error');
                return false;
            }
        } catch (error) {
            console.error('Error adding entry:', error);
            this.showNotification('Error adding entry. Please try again.', 'error');
            return false;
        }
    }

    /**
     * Update date range and reload entries
     */
    async updateDateRange(startDate, endDate) {
        this.dateRange = { start: startDate, end: endDate };
        await this.loadEntries();
    }

    /**
     * Setup event listeners
     */
    setupEventListeners() {
        // Add any additional event listeners here
        // This can be extended based on specific page requirements
    }

    /**
     * Show notification
     */
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;
        
        const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
        const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
        
        notification.innerHTML = `
            <div class="flex items-center space-x-3">
                <div class="flex-shrink-0">
                    <span class="text-white text-lg">${icon}</span>
                </div>
                <div class="flex-1">
                    <p class="text-white text-sm font-medium">${message}</p>
                </div>
                <button class="text-white hover:text-gray-200" onclick="this.parentElement.parentElement.remove()">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;
        
        notification.classList.add(bgColor);
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }, 5000);
    }

    /**
     * Format time for display in user's timezone
     */
    formatTime(dateString) {
        try {
            const date = new Date(dateString);
            
            // Check if the date is valid
            if (isNaN(date.getTime())) {
                console.warn('Invalid date string:', dateString);
                return 'Invalid time';
            }
            
            // Format time in user's local timezone
            return date.toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit',
                hour12: true 
            });
        } catch (error) {
            console.error('Error formatting time:', error);
            return 'Invalid time';
        }
    }

    /**
     * Get meal time display with icon
     */
    getMealTimeDisplay(mealTime) {
        const mealIcons = {
            'breakfast': '🌅',
            'lunch': '☀️',
            'dinner': '🌙',
            'snacks': '🍎'
        };
        const mealNames = {
            'breakfast': 'Breakfast',
            'lunch': 'Lunch',
            'dinner': 'Dinner',
            'snacks': 'Snacks'
        };
        return `${mealIcons[mealTime] || '🍽️'} ${mealNames[mealTime] || mealTime}`;
    }

    /**
     * Get nutritional summary
     */
    getNutritionalSummary() {
        const summary = {
            totalCalories: 0,
            totalProtein: 0,
            totalCarbs: 0,
            totalFat: 0,
            entryCount: this.entries.length
        };

        this.entries.forEach(entry => {
            summary.totalCalories += entry.calories || 0;
            summary.totalProtein += entry.protein || 0;
            summary.totalCarbs += entry.carbs || 0;
            summary.totalFat += entry.fat || 0;
        });

        return summary;
    }

    /**
     * Update dashboard stats for the current date
     */
    updateDashboardStats() {
        // Call the global loadStatsForDate function if it exists
        if (typeof window.loadStatsForDate === 'function') {
            window.loadStatsForDate(this.currentDate);
        }
    }

    /**
     * Refresh entries
     */
    async refresh() {
        await this.loadEntries();
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FoodJournalManager;
} else {
    window.FoodJournalManager = FoodJournalManager;
}
