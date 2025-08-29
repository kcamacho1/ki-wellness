// Dashboard UI Components
// Handles all UI updates and visual elements
class DashboardUI {
    constructor(core) {
        this.core = core;
        this.macroChart = null;
    }

    showLoading() {
        if (window.showLoading) window.showLoading();
    }

    hideLoading() {
        if (window.hideLoading) window.hideLoading();
    }

    showToast(message, type) {
        if (window.showToast) window.showToast(message, type);
    }

    updateDateDisplay() {
        const options = { 
            weekday: 'short', 
            month: 'short', 
            day: 'numeric', 
            year: 'numeric' 
        };
        
        const formattedDate = this.core.currentDate.toLocaleDateString('en-US', options);
        const dateElement = document.getElementById('current-date');
        if (dateElement) {
            dateElement.textContent = formattedDate;
        }

        // Update date selector input
        const dateSelector = document.getElementById('date-selector');
        if (dateSelector) {
            dateSelector.value = this.core.currentDate.toISOString().split('T')[0];
        }
    }

    updateFoodLoggingDate() {
        const dateStr = this.core.currentDate.toISOString().split('T')[0];
        
        // Update food journal date display
        const foodDateDisplay = document.getElementById('current-date-display');
        if (foodDateDisplay) {
            const options = { 
                weekday: 'long', 
                month: 'long', 
                day: 'numeric', 
                year: 'numeric' 
            };
            foodDateDisplay.textContent = this.core.currentDate.toLocaleDateString('en-US', options);
        }

        // Update modal date inputs
        const modalDateInputs = document.querySelectorAll('.food-log-date');
        modalDateInputs.forEach(input => {
            input.value = dateStr;
        });

        // Sync date selector styling
        this.onDateInputChange('date-selector');
    }

    displayNotes(notes) {
        const notesInput = document.getElementById('daily-notes');
        if (!notesInput) return;
        
        if (notes && notes.length > 0) {
            // Display the most recent note for the day
            const latestNote = notes[notes.length - 1];
            notesInput.value = latestNote.content || '';
        } else {
            notesInput.value = '';
        }
        
        // Update notes history
        this.displayNotesHistory(notes);
    }

    displayNotesHistory(notes) {
        const historyContainer = document.getElementById('notes-history');
        if (!historyContainer) {
            console.error('Notes history container not found');
            return;
        }

        if (!notes || notes.length === 0) {
            historyContainer.innerHTML = `
                <div class="text-center py-6 text-gray-500">
                    <div class="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                        <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                        </svg>
                    </div>
                    <p class="text-sm font-medium text-gray-900 mb-1">No notes for this date</p>
                    <p class="text-xs text-gray-500">Add notes in the Mood & Notes card above</p>
                </div>
            `;
            return;
        }

        const historyHTML = notes.map(note => {
            const time = new Date(note.timestamp).toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
            });
            
            return `
                <div class="p-3 bg-gray-50 rounded-lg">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <p class="text-sm text-gray-900">${note.content || ''}</p>
                            <p class="text-xs text-gray-500 mt-1">${time}</p>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        historyContainer.innerHTML = historyHTML;
    }

    clearNotesInput() {
        const notesInput = document.getElementById('daily-notes');
        if (notesInput && notesInput.value === '') {
            notesInput.value = '';
        }
    }

    updateDateInputStyle(inputElement, isSynced) {
        if (isSynced) {
            inputElement.classList.add('border-green-500', 'bg-green-50');
            inputElement.classList.remove('border-blue-300', 'bg-white');
        } else {
            inputElement.classList.remove('border-green-500', 'bg-green-50');
            inputElement.classList.add('border-blue-300', 'bg-white');
        }
    }

    onDateInputChange(inputId) {
        const inputElement = document.getElementById(inputId);
        const selectedDate = inputElement.value;
        const dashboardDate = this.core.currentDate.toISOString().split('T')[0];
        
        const isSynced = selectedDate === dashboardDate;
        this.updateDateInputStyle(inputElement, isSynced);
        
        if (!isSynced) {
            inputElement.title = `Current date: ${dashboardDate}. Click to sync or change dashboard date.`;
        } else {
            inputElement.title = 'Date is synchronized with dashboard';
        }
    }

    initMacroChart() {
        const ctx = document.getElementById('macro-chart');
        if (!ctx) return;

        this.macroChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Protein', 'Carbs', 'Fat'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: ['#EF4444', '#F59E0B', '#22C55E'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label;
                                const calorieValue = context.raw;
                                
                                // Convert calories back to grams for display
                                let gramValue;
                                if (label === 'Protein' || label === 'Carbs') {
                                    gramValue = Math.round(calorieValue / 4);
                                } else if (label === 'Fat') {
                                    gramValue = Math.round(calorieValue / 9);
                                }
                                
                                return `${label}: ${gramValue}g (${Math.round(calorieValue)} cal)`;
                            }
                        }
                    }
                },
                cutout: '70%'
            }
        });
    }

    updateMacros(totals) {
        // Update total calories display in center of chart
        const totalCaloriesEl = document.getElementById('total-calories-display');
        if (totalCaloriesEl) totalCaloriesEl.textContent = Math.round(totals.calories || 0);
        
        // Update macro breakdown displays
        const carbsEl = document.getElementById('carbs-display');
        const proteinEl = document.getElementById('protein-display');
        const fatEl = document.getElementById('fat-display');
        
        if (carbsEl) carbsEl.textContent = `${Math.round(totals.carbs || 0)}g`;
        if (proteinEl) proteinEl.textContent = `${Math.round(totals.protein || 0)}g`;
        if (fatEl) fatEl.textContent = `${Math.round(totals.fat || 0)}g`;

        // Update chart
        if (this.macroChart) {
            const carbsCal = (totals.carbs || 0) * 4;
            const proteinCal = (totals.protein || 0) * 4;
            const fatCal = (totals.fat || 0) * 9;
            
            this.macroChart.data.datasets[0].data = [proteinCal, carbsCal, fatCal];
            this.macroChart.update('none');
        }
    }

    // Tab management for mood & notes
    switchLogTab(tabName) {
        const foodTab = document.getElementById('food-log-tab');
        const moodNotesTab = document.getElementById('mood-notes-tab');
        const foodContent = document.getElementById('food-log-content');
        const moodNotesContent = document.getElementById('mood-notes-content');
        const actionButtons = document.getElementById('tab-action-buttons');

        // Update tab states
        if (tabName === 'mood-notes') {
            // Activate mood & notes tab
            moodNotesTab.classList.remove('text-gray-500', 'border-transparent');
            moodNotesTab.classList.add('text-ki-green-600', 'border-ki-green-500');
            
            // Deactivate food log tab
            foodTab.classList.remove('text-ki-green-600', 'border-ki-green-500');
            foodTab.classList.add('text-gray-500', 'border-transparent');
            
            // Show/hide content
            foodContent.classList.add('hidden');
            moodNotesContent.classList.remove('hidden');
            
            // Update action buttons
            actionButtons.innerHTML = `
                <button onclick="window.foodJournal.openModal()" 
                        class="bg-ki-green-600 hover:bg-ki-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                    Add Entry
                </button>
            `;
            
            // Load mood and notes history for current date
            this.loadMoodNotesHistory();
        } else {
            // Activate food log tab (default)
            foodTab.classList.remove('text-gray-500', 'border-transparent');
            foodTab.classList.add('text-ki-green-600', 'border-ki-green-500');
            
            // Deactivate mood & notes tab
            moodNotesTab.classList.remove('text-ki-green-600', 'border-ki-green-500');
            moodNotesTab.classList.add('text-gray-500', 'border-transparent');
            
            // Show/hide content
            moodNotesContent.classList.add('hidden');
            foodContent.classList.remove('hidden');
            
            // Update action buttons
            actionButtons.innerHTML = `
                <button onclick="window.foodJournal.openModal()" 
                        class="bg-ki-green-600 hover:bg-ki-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors">
                    Add Food
                </button>
            `;
        }
    }

    async loadMoodNotesHistory() {
        // Refresh dashboard data to ensure mood & notes are up-to-date
        try {
            if (window.dashboardManager && window.dashboardManager.loadDashboardDataOptimized) {
                await window.dashboardManager.loadDashboardDataOptimized();
            }
        } catch (error) {
            console.error('Error refreshing mood & notes data:', error);
        }
    }

    displayMoodHistoryLegacy(moodLogs) {
        const container = document.getElementById('mood-history');
        
        if (moodLogs.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
                    </svg>
                    <p class="mt-2">No mood entries for this date</p>
                    <p class="text-sm text-gray-400">Add your first mood entry below</p>
                </div>
            `;
            return;
        }

        const moodEmojis = {
            1: '😞', 2: '😐', 3: '🙂', 4: '😊', 5: '😄'
        };
        
        const moodTexts = {
            1: 'Terrible', 2: 'Okay', 3: 'Good', 4: 'Great', 5: 'Excellent'
        };

        const entriesHTML = moodLogs.map(mood => {
            const time = new Date(mood.timestamp).toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit' 
            });
            
            return `
                <div class="bg-white rounded-lg p-4 border border-gray-200">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <span class="text-3xl">${moodEmojis[mood.mood_value]}</span>
                            <div>
                                <p class="font-medium text-gray-900">${moodTexts[mood.mood_value]}</p>
                                <p class="text-sm text-gray-500">${time}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        container.innerHTML = entriesHTML;
    }

    displayNotesHistory(notes) {
        const container = document.getElementById('notes-history');
        
        if (notes.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"/>
                    </svg>
                    <p class="mt-2">No notes for this date</p>
                    <p class="text-sm text-gray-400">Add your first note below</p>
                </div>
            `;
            return;
        }

        const entriesHTML = notes.map(note => {
            const time = new Date(note.timestamp).toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit' 
            });
            
            return `
                <div class="bg-white rounded-lg p-4 border border-gray-200">
                    <div class="flex justify-between items-start mb-2">
                        <p class="text-sm text-gray-500">${time}</p>
                    </div>
                    <p class="text-gray-900">${note.content}</p>
                </div>
            `;
        }).join('');

        container.innerHTML = entriesHTML;
    }

    updateMoodNotesTab() {
        // Check if we're on the mood & notes tab and reload if so
        const moodNotesTab = document.getElementById('mood-notes-tab');
        if (moodNotesTab && moodNotesTab.classList.contains('text-ki-green-600')) {
            // Load mood and notes history for current date
            this.loadMoodNotesHistory();
        }
    }
}

// Make available globally
window.DashboardUI = DashboardUI;
