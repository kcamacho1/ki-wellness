// Dashboard Event Handlers
// Manages all event listeners and user interactions
class DashboardEvents {
    constructor(core) {
        this.core = core;
    }

    setupEventListeners() {
        // Date navigation
        document.getElementById('date-prev')?.addEventListener('click', () => this.core.changeDate(-1));
        document.getElementById('date-next')?.addEventListener('click', () => this.core.changeDate(1));

        // Date selector
        document.getElementById('date-selector')?.addEventListener('change', (e) => {
            this.core.selectDate(e.target.value);
        });



        // Date input styling
        document.getElementById('date-selector')?.addEventListener('input', () => {
            this.core.ui.onDateInputChange('date-selector');
        });

        // Meal buttons
        document.querySelectorAll('.meal-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleMealButtonClick(e));
        });

        // Copy food buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.copy-food-btn') || e.target.closest('.copy-food-btn')) {
                const button = e.target.matches('.copy-food-btn') ? e.target : e.target.closest('.copy-food-btn');
                const foodId = button.getAttribute('data-food-id');
                if (foodId) {
                    this.core.food.showCopyConfirmation(foodId);
                }
            }
        });

        // Delete food buttons
        document.addEventListener('click', (e) => {
            if (e.target.matches('.delete-food-btn') || e.target.closest('.delete-food-btn')) {
                const button = e.target.matches('.delete-food-btn') ? e.target : e.target.closest('.delete-food-btn');
                const foodId = button.getAttribute('data-food-id');
                if (foodId) {
                    this.core.food.confirmDeleteFood(foodId);
                }
            }
        });

        // Tab switching for mood & notes
        document.getElementById('food-log-tab')?.addEventListener('click', () => {
            this.core.ui.switchLogTab('food-log');
        });
        
        document.getElementById('mood-notes-tab')?.addEventListener('click', () => {
            this.core.ui.switchLogTab('mood-notes');
        });

        // Notes submission
        document.getElementById('save-notes-btn')?.addEventListener('click', () => {
            this.handleSaveNotes();
        });

        // Mood buttons
        document.querySelectorAll('.mood-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleMoodButtonClick(e));
        });

        // Water logging
        document.getElementById('log-water-btn')?.addEventListener('click', () => {
            this.core.water.logWater();
        });

        // Quick water buttons
        document.querySelectorAll('.quick-water-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const amount = parseInt(e.target.getAttribute('data-amount'));
                if (amount) {
                    this.core.water.addQuickWater(amount);
                }
            });
        });
    }

    handleMealButtonClick(e) {
        const mealType = e.target.getAttribute('data-meal');
        if (mealType && window.foodJournal) {
            window.foodJournal.openModal();
            // Set the meal type in the food journal
            setTimeout(() => {
                const mealSelect = document.getElementById('food-meal-type');
                if (mealSelect) {
                    mealSelect.value = mealType;
                }
            }, 100);
        }
    }

    handleMoodButtonClick(e) {
        const moodText = e.target.getAttribute('data-mood');
        if (moodText) {
            this.core.mood.setMood(e.target.getAttribute('data-emoji'), moodText, e.target);
        }
    }

    async handleSaveNotes() {
        const notesInput = document.getElementById('daily-notes');
        const notesContent = notesInput?.value?.trim();
        
        if (!notesContent) {
            this.core.ui.showToast('Please enter some notes first', 'warning');
            return;
        }

        try {
            const date = this.core.currentDate.toISOString().split('T')[0];
            const response = await fetch('/api/save-notes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ content: notesContent, date })
            });

            const data = await response.json();
            
            if (data.success) {
                this.core.ui.showToast('Notes saved!', 'success');
                notesInput.value = ''; // Clear the input
                this.core.debouncedReload();
            } else {
                this.core.ui.showToast('Failed to save notes', 'error');
            }
        } catch (error) {
            console.error('Error saving notes:', error);
            this.core.ui.showToast('Failed to save notes', 'error');
        }
    }
}

// Make available globally
window.DashboardEvents = DashboardEvents;
