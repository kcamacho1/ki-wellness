class DailyLogManager {
    constructor() {
        this.currentDate = new Date();
        this.init();
    }

    init() {
        this.updateDateDisplay();
        this.loadDailyLog();
        this.setupEventListeners();
    }

    setupEventListeners() {
        document.getElementById('date-prev').addEventListener('click', () => this.changeDate(-1));
        document.getElementById('date-next').addEventListener('click', () => this.changeDate(1));
        document.getElementById('today-btn').addEventListener('click', () => this.goToToday());
    }

    changeDate(days) {
        this.currentDate.setDate(this.currentDate.getDate() + days);
        this.updateDateDisplay();
        this.loadDailyLog();
    }

    goToToday() {
        this.currentDate = new Date();
        this.updateDateDisplay();
        this.loadDailyLog();
    }

    updateDateDisplay() {
        const options = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        };
        const dateString = this.currentDate.toLocaleDateString('en-US', options);
        document.getElementById('current-date-display').textContent = dateString;
    }

    async loadDailyLog() {
        try {
            const dateStr = this.currentDate.toISOString().split('T')[0];
            const response = await fetch(`/api/dashboard-data?date=${dateStr}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayMoodHistory(data.data.mood_logs);
                this.displayNotesHistory(data.data.notes);
                this.displayFoodSummary(data.data.food_logs, data.data.totals);
            }
        } catch (error) {
            console.error('Error loading daily log:', error);
        }
    }

    displayMoodHistory(moodLogs) {
        const container = document.getElementById('mood-history');
        const noMood = document.getElementById('no-mood');
        
        if (moodLogs.length === 0) {
            container.innerHTML = '';
            noMood.style.display = 'block';
            return;
        }

        noMood.style.display = 'none';
        
        const moodEmojis = ['😢', '😕', '😐', '😊', '😄'];
        const moodTexts = ['Terrible', 'Bad', 'Okay', 'Good', 'Excellent'];
        
        container.innerHTML = moodLogs.map(log => {
            const moodIndex = log.mood - 1;
            const emoji = moodEmojis[moodIndex] || '😊';
            const text = moodTexts[moodIndex] || 'Good';
            const time = new Date(log.timestamp).toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit' 
            });
            
            return `
                <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <div class="text-3xl">${emoji}</div>
                            <div>
                                <div class="font-medium text-gray-900">${text}</div>
                                <div class="text-sm text-gray-500">${time}</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    displayNotesHistory(notes) {
        const container = document.getElementById('notes-history');
        const noNotes = document.getElementById('no-notes');
        
        if (!notes || notes.trim() === '') {
            container.innerHTML = '';
            noNotes.style.display = 'block';
            return;
        }

        noNotes.style.display = 'none';
        
        container.innerHTML = `
            <div class="bg-gray-50 rounded-xl p-4 border border-gray-100">
                <div class="prose max-w-none">
                    <p class="text-gray-700 whitespace-pre-wrap">${notes}</p>
                </div>
            </div>
        `;
    }

    displayFoodSummary(foodLogs, totals) {
        const container = document.getElementById('food-summary');
        const noFood = document.getElementById('no-food');
        
        if (foodLogs.length === 0) {
            container.innerHTML = '';
            noFood.style.display = 'block';
            return;
        }

        noFood.style.display = 'none';
        
        // Group food by time of day
        const groupedFood = this.groupFoodByTimeOfDay(foodLogs);
        
        container.innerHTML = `
            <div class="col-span-full mb-6">
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="bg-red-50 rounded-xl p-4 border border-red-100">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-red-600">${Math.round(totals.calories)}</div>
                            <div class="text-sm text-red-600">Calories</div>
                        </div>
                    </div>
                    <div class="bg-yellow-50 rounded-xl p-4 border border-yellow-100">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-yellow-600">${Math.round(totals.protein)}g</div>
                            <div class="text-sm text-yellow-600">Protein</div>
                        </div>
                    </div>
                    <div class="bg-green-50 rounded-xl p-4 border border-green-100">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-green-600">${Math.round(totals.carbs)}g</div>
                            <div class="text-sm text-green-600">Carbs</div>
                        </div>
                    </div>
                    <div class="bg-purple-50 rounded-xl p-4 border border-purple-100">
                        <div class="text-center">
                            <div class="text-2xl font-bold text-purple-600">${Math.round(totals.fat)}g</div>
                            <div class="text-sm text-purple-600">Fat</div>
                        </div>
                    </div>
                </div>
            </div>
            ${Object.entries(groupedFood).map(([timeOfDay, foods]) => `
                <div class="col-span-full">
                    <h4 class="font-semibold text-gray-900 mb-3 capitalize">${timeOfDay}</h4>
                    <div class="space-y-2">
                        ${foods.map(food => `
                            <div class="bg-gray-50 rounded-lg p-3 border border-gray-100">
                                <div class="flex justify-between items-center">
                                    <div>
                                        <div class="font-medium text-gray-900">${food.name}</div>
                                        <div class="text-sm text-gray-500">${food.brand || 'Unknown Brand'}</div>
                                    </div>
                                    <div class="text-right">
                                        <div class="font-medium text-gray-900">${Math.round(food.calories)} cal</div>
                                        <div class="text-xs text-gray-500">${food.original_amount} ${food.original_unit} × ${food.quantity}</div>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            `).join('')}
        `;
    }

    groupFoodByTimeOfDay(foodLogs) {
        const grouped = {};
        foodLogs.forEach(food => {
            const timeOfDay = food.time_of_day || 'snack';
            if (!grouped[timeOfDay]) {
                grouped[timeOfDay] = [];
            }
            grouped[timeOfDay].push(food);
        });
        return grouped;
    }
}

// Initialize the daily log manager when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new DailyLogManager();
});
