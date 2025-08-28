// Ki Wellness Dashboard JavaScript
// ================================

class DashboardManager {
    constructor() {
        this.currentDate = new Date();
        this.selectedFood = null;
        this.stream = null;
        this.macroChart = null;
        this.quickWaterAmount = 8; // Default to 8 oz
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateDateDisplay();
        this.updateFoodLoggingDate();
        this.initMacroChart();
        this.loadDashboardData();
        this.loadWaterSettings();
        // Note: initTabs() removed - tab functionality moved to food-journal.js
    }

    setupEventListeners() {
        // Date navigation
        document.getElementById('date-prev').addEventListener('click', () => this.changeDate(-1));
        document.getElementById('date-next').addEventListener('click', () => this.changeDate(1));
        document.getElementById('today-btn').addEventListener('click', () => this.goToToday());
        document.getElementById('date-selector').addEventListener('change', (e) => this.selectDate(e.target.value));

        // Note: Food journal functionality moved to food-journal.js
        // Modal controls (with null checks)
        const cancelModal = document.getElementById('cancel-modal');
        const addToLog = document.getElementById('add-to-log');
        
        if (cancelModal) cancelModal.addEventListener('click', () => this.closeModal());
        // Note: addToLog functionality moved to food-journal.js

        // Modal input changes (with null checks)
        const modalAmount = document.getElementById('modal-amount');
        const modalUnit = document.getElementById('modal-unit');
        const modalQuantity = document.getElementById('modal-quantity');
        
        if (modalAmount) modalAmount.addEventListener('input', () => this.updateConversion());
        if (modalUnit) modalUnit.addEventListener('change', () => this.updateConversion());
        if (modalQuantity) modalQuantity.addEventListener('input', () => this.updateConversion());

        // Date selection controls (with null checks)
        const modalUseDateBtn = document.getElementById('modal-use-current-date');
        if (modalUseDateBtn) {
            modalUseDateBtn.addEventListener('click', () => this.syncWithDashboardDate());
        }

        // Date input change listeners (with null checks)
        const modalDateInput = document.getElementById('modal-date');
        
        if (modalDateInput) {
            modalDateInput.addEventListener('change', () => this.onDateInputChange('modal-date'));
        }

        // Edit modal controls
        document.getElementById('close-move-modal').addEventListener('click', () => this.closeMoveModal());
        document.getElementById('cancel-move').addEventListener('click', () => this.closeMoveModal());
        document.getElementById('confirm-move').addEventListener('click', () => this.confirmMoveFood());
        document.getElementById('move-use-current-date').addEventListener('click', () => this.setCurrentDate('move-date'));

        // Copy modal controls
        document.getElementById('close-copy-modal').addEventListener('click', () => this.closeCopyModal());
        document.getElementById('cancel-copy').addEventListener('click', () => this.closeCopyModal());
        document.getElementById('confirm-copy').addEventListener('click', () => this.confirmCopyFood());
        document.getElementById('copy-use-current-date').addEventListener('click', () => this.setCurrentDate('copy-date'));

        // Water settings modal controls
        document.getElementById('close-water-settings-modal').addEventListener('click', () => closeWaterSettingsModal());
        document.getElementById('cancel-water-settings').addEventListener('click', () => closeWaterSettingsModal());
        document.getElementById('save-water-settings').addEventListener('click', () => saveWaterSettings());
        
        // Log tab controls
        document.getElementById('food-log-tab').addEventListener('click', () => this.switchLogTab('food'));
        document.getElementById('mood-notes-tab').addEventListener('click', () => this.switchLogTab('mood-notes'));
    }

    initTabs() {
        // Note: Tab functionality moved to food-journal.js
        // This method is kept for compatibility but no longer needed
    }

    switchTab(activeTab, activeContent) {
        // Note: Tab functionality moved to food-journal.js
        // This method is kept for compatibility but adds null checks for safety
        
        // Update tab buttons (with null checks)
        ['search-tab', 'barcode-tab', 'manual-tab', 'mood-notes-tab'].forEach(tabId => {
            const tab = document.getElementById(tabId);
            if (tab) {
                if (tabId === `${activeTab}-tab`) {
                    tab.classList.add('text-ki-green-600', 'bg-white', 'shadow-sm', 'border', 'border-gray-200');
                    tab.classList.remove('text-gray-500', 'hover:bg-white');
                } else {
                    tab.classList.remove('text-ki-green-600', 'bg-white', 'shadow-sm', 'border', 'border-gray-200');
                    tab.classList.add('text-gray-500', 'hover:bg-white');
                }
            }
        });

        // Update content (with null checks)
        ['search-content', 'barcode-content', 'manual-content', 'mood-notes-content'].forEach(contentId => {
            const content = document.getElementById(contentId);
            if (content) {
                if (contentId === activeContent) {
                    content.classList.remove('hidden');
                    // Load mood and notes history when the tab is opened
                    if (contentId === 'mood-notes-content') {
                        this.loadMoodNotesHistory();
                    }
                } else {
                    content.classList.add('hidden');
                }
            }
        });

        // If switching to manual tab, sync the date
        if (activeTab === 'manual') {
            this.updateFoodLoggingDate();
        }
    }

    updateDateDisplay() {
        // Update the main date display in the header
        const dateElement = document.getElementById('current-date');
        if (dateElement) {
            const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
            dateElement.textContent = this.currentDate.toLocaleDateString('en-US', options);
        }
        
        // Update the date navigation display
        const dateDisplayElement = document.getElementById('current-date-display');
        if (dateDisplayElement) {
            const options = { weekday: 'long', month: 'long', day: 'numeric' };
            dateDisplayElement.textContent = this.currentDate.toLocaleDateString('en-US', options);
        }
        
        // Update the date selector input
        const dateSelector = document.getElementById('date-selector');
        if (dateSelector) {
            dateSelector.value = this.currentDate.toISOString().split('T')[0];
        }
    }

    changeDate(days) {
        this.currentDate.setDate(this.currentDate.getDate() + days);
        this.updateDateDisplay();
        this.clearNotesInput(); // Clear notes input when changing dates
        this.loadDashboardData();
        this.updateFoodLoggingDate();
        this.updateMoodNotesTab();
    }

    goToToday() {
        this.currentDate = new Date();
        this.updateDateDisplay();
        this.clearNotesInput(); // Clear notes input when going to today
        this.loadDashboardData();
        this.updateFoodLoggingDate();
        this.updateMoodNotesTab();
    }

    selectDate(dateString) {
        if (!dateString) return;
        
        const selectedDate = new Date(dateString);
        if (isNaN(selectedDate.getTime())) {
            showToast('Invalid date selected', 'error');
            return;
        }
        
        this.currentDate = selectedDate;
        this.updateDateDisplay();
        this.clearNotesInput(); // Clear notes input when changing dates
        this.loadDashboardData();
        this.updateFoodLoggingDate();
        this.updateMoodNotesTab();
        
        // Show a toast with the selected date
        const dateStr = selectedDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
        showToast(`Navigated to ${dateStr}`, 'success');
    }

    clearNotesInput() {
        const notesInput = document.getElementById('daily-notes');
        if (notesInput) {
            notesInput.value = '';
        }
    }

    setCurrentDate(inputId) {
        const today = new Date().toISOString().split('T')[0];
        document.getElementById(inputId).value = today;
    }

    getSelectedDate(inputId) {
        const dateInput = document.getElementById(inputId);
        return dateInput.value || this.currentDate.toISOString().split('T')[0];
    }

    updateFoodLoggingDate() {
        const currentDateStr = this.currentDate.toISOString().split('T')[0];
        
        // Update both date inputs
        const manualDateInput = document.getElementById('manual-date');
        const modalDateInput = document.getElementById('modal-date');
        
        if (manualDateInput) {
            manualDateInput.value = currentDateStr;
            this.updateDateInputStyle(manualDateInput, true);
        }
        if (modalDateInput) {
            modalDateInput.value = currentDateStr;
            this.updateDateInputStyle(modalDateInput, true);
        }
    }

    updateMoodNotesTab() {
        // Check if the mood & notes tab is currently active
        const moodNotesContent = document.getElementById('mood-notes-content');
        if (moodNotesContent && !moodNotesContent.classList.contains('hidden')) {
            this.loadMoodNotesHistory();
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
        const dashboardDate = this.currentDate.toISOString().split('T')[0];
        
        // Check if the selected date matches the dashboard date
        const isSynced = selectedDate === dashboardDate;
        this.updateDateInputStyle(inputElement, isSynced);
        
        if (!isSynced) {
            const selectedDateObj = new Date(selectedDate);
            const dateStr = selectedDateObj.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
            showToast(`Food will be added to ${dateStr}`, 'info');
        }
    }

    syncWithDashboardDate() {
        const currentDateStr = this.currentDate.toISOString().split('T')[0];
        
        // Update both date inputs to match dashboard date
        const manualDateInput = document.getElementById('manual-date');
        const modalDateInput = document.getElementById('modal-date');
        
        if (manualDateInput) {
            manualDateInput.value = currentDateStr;
        }
        if (modalDateInput) {
            modalDateInput.value = currentDateStr;
        }
        
        showToast(`Date set to ${this.currentDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}`, 'info');
    }

    async loadDashboardData() {
        try {
            showLoading();
            const dateStr = this.currentDate.toISOString().split('T')[0];
            const response = await fetch(`/api/dashboard-data?date=${dateStr}`);
            const data = await response.json();

            if (data.success) {
                this.updateDashboard(data.data);
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            showToast('Failed to load dashboard data', 'error');
        } finally {
            hideLoading();
        }
    }

    updateDashboard(data) {
        // Update water display
        this.updateWaterDisplay(data.water_logs);
        
        // Update macronutrients
        this.updateMacros(data.totals);
        
        // Update mood
        this.updateMoodDisplay(data.mood_logs);
        
        // Keep notes input field empty for new entries
        // Don't auto-populate with previous notes - let users enter fresh content
        const notesInput = document.getElementById('daily-notes');
        if (notesInput && notesInput.value === '') {
            // Only clear if it's already empty (don't overwrite user's current input)
            notesInput.value = '';
        }
        
        // Update food log
        this.displayFoodLog(data.food_logs);
    }

    updateWaterDisplay(waterLogs) {
        const totalWater = waterLogs.reduce((sum, log) => sum + log.amount, 0);
        const goal = 64; // 64 oz daily goal
        const percentage = Math.min((totalWater / goal) * 100, 100);

        document.getElementById('water-display').textContent = `${Math.round(totalWater)} oz`;
        document.getElementById('water-progress').style.width = `${percentage}%`;
    }

    initMacroChart() {
        const ctx = document.getElementById('macro-chart');
        if (!ctx) return;
        
        // Simple center text plugin
        const centerTextPlugin = {
            id: 'centerText',
            beforeDraw: function(chart) {
                const { ctx, width, height } = chart;
                ctx.restore();
                
                const text = chart.data.datasets[0].centerText || '0';
                const fontSize = Math.min(width, height) / 8;
                
                ctx.font = `bold ${fontSize}px Quicksand`;
                ctx.textAlign = 'center';
                ctx.textBaseline = 'middle';
                ctx.fillStyle = '#374151';
                ctx.fillText(text, width / 2, height / 2);
                
                ctx.save();
            }
        };
        
        this.macroChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Protein', 'Carbs', 'Fat'],
                datasets: [{
                    data: [0, 0, 0],
                    centerText: '0',
                    backgroundColor: [
                        '#ef4444', // red-500
                        '#eab308', // yellow-500
                        '#22c55e'  // green-500
                    ],
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
                                const label = context.label || '';
                                const value = context.parsed || 0;
                                return `${label}: ${Math.round(value)}g`;
                            }
                        }
                    }
                },
                cutout: '70%'
            },
            plugins: [centerTextPlugin]
        });
    }

    updateMacros(totals) {
        document.getElementById('protein-display').textContent = `${Math.round(totals.protein)}g`;
        document.getElementById('carbs-display').textContent = `${Math.round(totals.carbs)}g`;
        document.getElementById('fat-display').textContent = `${Math.round(totals.fat)}g`;
        
        // Update pie chart
        if (this.macroChart) {
            const protein = totals.protein || 0;
            const carbs = totals.carbs || 0;
            const fat = totals.fat || 0;
            const calories = totals.calories || 0;
            
            // Update center text with total calories
            this.macroChart.data.datasets[0].centerText = Math.round(calories).toString();
            
            // If no macros, show empty chart
            if (protein === 0 && carbs === 0 && fat === 0) {
                this.macroChart.data.datasets[0].data = [1, 1, 1];
                this.macroChart.data.datasets[0].backgroundColor = ['#e5e7eb', '#e5e7eb', '#e5e7eb'];
            } else {
                this.macroChart.data.datasets[0].data = [protein, carbs, fat];
                this.macroChart.data.datasets[0].backgroundColor = [
                    '#ef4444', // red-500
                    '#eab308', // yellow-500
                    '#22c55e'  // green-500
                ];
            }
            this.macroChart.update();
        }
    }

    updateMoodDisplay(moodLogs) {
        if (moodLogs.length > 0) {
            const latestMood = moodLogs[moodLogs.length - 1].mood;
            const moodEmojis = ['😢', '😐', '🙂', '😀', '😊'];
            const moodTexts = ['Terrible', 'Okay', 'Good', 'Great', 'Excellent'];
            
            const moodEmojiElement = document.getElementById('current-mood');
            const moodTextElement = document.getElementById('mood-text');
            
            if (moodEmojiElement) {
                moodEmojiElement.textContent = moodEmojis[latestMood - 1];
            }
            if (moodTextElement) {
                moodTextElement.textContent = moodTexts[latestMood - 1];
            }
        }
    }

    displayFoodLog(foodLogs) {
        const container = document.getElementById('food-log-display');
        
        console.log('displayFoodLog called with:', foodLogs);
        console.log('Container found:', !!container);
        
        if (!container) {
            console.error('food-log-display container not found!');
            return;
        }
        
        if (foodLogs.length === 0) {
            // Use the default empty state that's already in the template
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4m0 0L7 13m0 0l-2.5 5M7 13l2.5 5m6-5v6a2 2 0 01-2 2H9a2 2 0 01-2-2v-6m6 0V9a2 2 0 00-2-2H9a2 2 0 00-2 2v4.01"></path>
                    </svg>
                    <p>No food entries for today</p>
                    <p class="text-xs">Click "Add Food" or click the macronutrients chart to start logging</p>
                </div>
            `;
            return;
        }

        container.innerHTML = foodLogs.map(log => `
            <div class="food-log-item bg-gray-50 rounded-xl p-3 sm:p-4 border border-gray-100">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <div class="flex items-center gap-2 mb-1">
                            <h4 class="font-semibold text-gray-900 text-base sm:text-lg">${log.name}</h4>
                            <span class="px-2 py-1 text-xs font-medium rounded-full capitalize ${this.getTimeOfDayBadgeClass(log.time_of_day || 'snack')}">${log.time_of_day || 'snack'}</span>
                        </div>
                        <p class="text-xs sm:text-sm text-gray-500 mb-2 sm:mb-3">${log.brand || 'Unknown Brand'}</p>
                        <div class="flex flex-wrap gap-2 sm:gap-4 mb-2">
                            <span class="text-red-600 font-medium text-xs sm:text-sm">${Math.round(log.protein)}g protein</span>
                            <span class="text-yellow-600 font-medium text-xs sm:text-sm">${Math.round(log.carbs)}g carbs</span>
                            <span class="text-green-600 font-medium text-xs sm:text-sm">${Math.round(log.fat)}g fat</span>
                            <span class="text-purple-600 font-medium text-xs sm:text-sm">${Math.round(log.calories)} cal</span>
                        </div>
                        <p class="text-xs text-gray-400">
                            Serving: ${log.original_amount} ${log.original_unit} × ${log.quantity} = ${Math.round(log.serving_size)}g
                        </p>
                    </div>
                    <div class="flex items-center space-x-1">
                        <button onclick="dashboardManager.copyFoodItem(${log.id})" class="text-gray-400 hover:text-green-500 p-1 sm:p-2 hover:bg-green-50 rounded-lg transition-colors" title="Copy to another date">
                            <svg class="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
                            </svg>
                        </button>
                        <button onclick="dashboardManager.editFoodItem(${log.id}, '${log.name}', '${log.date}', '${log.time_of_day || 'snack'}')" class="text-gray-400 hover:text-blue-500 p-1 sm:p-2 hover:bg-blue-50 rounded-lg transition-colors" title="Edit food item">
                            <svg class="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
                            </svg>
                        </button>
                        <button onclick="dashboardManager.removeFoodItem(${log.id})" class="text-gray-400 hover:text-red-500 p-1 sm:p-2 hover:bg-red-50 rounded-lg transition-colors" title="Delete">
                            <svg class="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                            </svg>
                        </button>
                    </div>
                </div>
            </div>
        `).join('');
    }

    // Note: searchFood() removed - functionality moved to food-journal.js

    // Note: displaySearchResults() removed - functionality moved to food-journal.js

    // Note: selectFood() removed - functionality moved to food-journal.js

    // Note: showFoodModal() removed - functionality moved to food-journal.js

    // Note: closeModal() removed - functionality moved to food-journal.js

    // Note: updateConversion() removed - functionality moved to food-journal.js

    // Note: addFoodToLog() removed - functionality moved to food-journal.js

    // Note: addManualFood() removed - functionality moved to food-journal.js

    getTimeOfDayBadgeClass(timeOfDay) {
        switch (timeOfDay.toLowerCase()) {
            case 'breakfast':
                return 'bg-orange-100 text-orange-700';
            case 'lunch':
                return 'bg-green-100 text-green-700';
            case 'dinner':
                return 'bg-purple-100 text-purple-700';
            case 'snack':
            default:
                return 'bg-blue-100 text-blue-700';
        }
    }

    // Note: clearManualForm() removed - functionality moved to food-journal.js

    getTimeOfDayBadgeClass(timeOfDay) {
        switch (timeOfDay.toLowerCase()) {
            case 'breakfast':
                return 'bg-orange-100 text-orange-700';
            case 'lunch':
                return 'bg-green-100 text-green-700';
            case 'dinner':
                return 'bg-purple-100 text-purple-700';
            case 'snack':
            default:
                return 'bg-blue-100 text-blue-700';
        }
    }

    switchLogTab(tabName) {
        // Update tab buttons
        const tabs = document.querySelectorAll('.log-tab');
        tabs.forEach(tab => {
            tab.classList.remove('active', 'text-ki-green-600', 'bg-white', 'shadow-sm', 'border', 'border-gray-200');
            tab.classList.add('text-gray-500', 'hover:text-gray-700', 'hover:bg-white');
        });

        // Update content visibility
        const contents = document.querySelectorAll('.tab-content');
        contents.forEach(content => content.classList.add('hidden'));

        // Update action buttons
        const addFoodBtn = document.getElementById('add-food-btn');
        const addMoodNoteBtn = document.getElementById('add-mood-note-btn');

        if (tabName === 'food') {
            // Activate food log tab
            const foodTab = document.getElementById('food-log-tab');
            foodTab.classList.add('active', 'text-ki-green-600', 'bg-white', 'shadow-sm', 'border', 'border-gray-200');
            foodTab.classList.remove('text-gray-500', 'hover:text-gray-700', 'hover:bg-white');
            
            // Show food content
            document.getElementById('food-log-content').classList.remove('hidden');
            
            // Show food action button
            addFoodBtn.classList.remove('hidden');
            addMoodNoteBtn.classList.add('hidden');
        } else if (tabName === 'mood-notes') {
            // Activate mood & notes tab
            const moodTab = document.getElementById('mood-notes-tab');
            moodTab.classList.add('active', 'text-purple-600', 'bg-white', 'shadow-sm', 'border', 'border-gray-200');
            moodTab.classList.remove('text-gray-500', 'hover:text-gray-700', 'hover:bg-white');
            
            // Show mood & notes content
            document.getElementById('mood-notes-content').classList.remove('hidden');
            
            // Show mood & notes action button
            addMoodNoteBtn.classList.remove('hidden');
            addFoodBtn.classList.add('hidden');
            
            // Load mood and notes history for current date
            this.loadMoodNotesHistory();
        }
    }

    async loadMoodNotesHistory() {
        const dateStr = this.currentDate.toISOString().split('T')[0];
        
        try {
            const response = await fetch(`/api/dashboard-data?date=${dateStr}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayMoodHistory(data.mood_logs);
                this.displayNotesHistory(data.notes);
            }
        } catch (error) {
            console.error('Error loading mood and notes history:', error);
        }
    }

    displayMoodHistory(moodLogs) {
        const container = document.getElementById('mood-history');
        
        if (moodLogs.length === 0) {
            container.innerHTML = `
                <div class="text-center py-6 text-gray-500">
                    <div class="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                        <svg class="w-6 h-6 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.828 14.828a4 4 0 01-5.656 0M9 10h1.586a1 1 0 01.707.293L12 11l.707-.707A1 1 0 0113.414 10H15M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                    </div>
                    <p class="text-sm font-medium text-gray-900 mb-1">No mood entries for this date</p>
                    <p class="text-xs text-gray-500">Add your first mood entry above</p>
                </div>
            `;
            return;
        }

        const moodEmojis = ['😢', '😕', '😐', '😊', '😄'];
        const moodTexts = ['Very Sad', 'Sad', 'Neutral', 'Happy', 'Very Happy'];

        container.innerHTML = moodLogs.map(log => {
            const timestamp = new Date(log.timestamp).toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit', 
                hour12: true 
            });
            const moodEmoji = moodEmojis[log.rating - 1];
            const moodText = moodTexts[log.rating - 1];

            return `
                <div class="bg-purple-50 border border-purple-200 rounded-lg p-3">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <span class="text-2xl">${moodEmoji}</span>
                            <div>
                                <p class="font-medium text-gray-900">${moodText}</p>
                                <p class="text-xs text-gray-500">${timestamp}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    displayNotesHistory(notes) {
        const container = document.getElementById('notes-history');
        
        if (notes.length === 0) {
            container.innerHTML = `
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

        container.innerHTML = notes.map(note => {
            const timestamp = new Date(note.timestamp).toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit', 
                hour12: true 
            });

            return `
                <div class="bg-indigo-50 border border-indigo-200 rounded-lg p-3">
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <p class="text-gray-900 text-sm mb-1">${note.content}</p>
                            <p class="text-xs text-gray-500">${timestamp}</p>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    async startBarcodeScanner() {
        try {
            // Check if camera permissions are available
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Camera access not supported in this browser');
            }

            // Check if we're on a mobile device
            const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
            
            // Mobile-optimized camera constraints
            const constraints = {
                video: {
                    facingMode: 'environment', // Use rear camera on mobile
                    width: { ideal: isMobile ? 1280 : 1920, min: 640 },
                    height: { ideal: isMobile ? 720 : 1080, min: 480 },
                    aspectRatio: { ideal: 16/9 }
                }
            };

            // On mobile, ensure we don't have multiple camera requests
            if (this.stream) {
                this.stopBarcodeScanner();
                // Small delay to ensure previous stream is fully closed
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            console.log('Requesting camera access...');
            this.stream = await navigator.mediaDevices.getUserMedia(constraints);
            
            const video = document.getElementById('barcode-video');
            video.srcObject = this.stream;
            
            // Wait for video to be ready
            await new Promise((resolve) => {
                video.onloadedmetadata = () => {
                    video.play();
                    resolve();
                };
            });
            
            // Show scanner UI
            document.getElementById('barcode-scanner-container').classList.remove('hidden');
            document.getElementById('start-barcode-scanner').classList.add('hidden');
            
            // Start barcode detection
            this.startBarcodeDetection();
            
            showToast('Camera started successfully', 'success');
            
        } catch (error) {
            console.error('Error starting barcode scanner:', error);
            
            let errorMessage = 'Failed to start camera';
            if (error.name === 'NotFoundError') {
                errorMessage = 'No camera found. Please check if your device has a camera.';
            } else if (error.name === 'NotAllowedError') {
                errorMessage = 'Camera access denied. Please allow camera permissions and try again.';
            } else if (error.name === 'NotReadableError') {
                errorMessage = 'Camera is in use by another application. Please close other camera apps.';
            } else if (error.message) {
                errorMessage = error.message;
            }
            
            showToast(errorMessage, 'error');
        }
    }

    stopBarcodeScanner() {
        // Stop QuaggaJS
        if (typeof Quagga !== 'undefined') {
            Quagga.stop();
        }
        
        // Stop camera stream
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        // Reset video styling
        const video = document.getElementById('barcode-video');
        video.classList.remove('scanning-active');
        video.style.border = '';
        video.style.boxShadow = '';
        
        // Hide scanner UI
        document.getElementById('barcode-scanner-container').classList.add('hidden');
        document.getElementById('start-barcode-scanner').classList.remove('hidden');
        
        showToast('Scanner stopped', 'info');
    }

    startBarcodeDetection() {
        if (!this.stream) return;
        
        const video = document.getElementById('barcode-video');
        
        // Check if QuaggaJS is available
        if (typeof Quagga === 'undefined') {
            console.warn('QuaggaJS not loaded, falling back to basic camera');
            this.updateScanningIndicator();
            showToast('Barcode scanning not available. Use manual entry.', 'warning');
            return;
        }
        
        // Configure QuaggaJS with mobile-optimized settings
        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: video,
                constraints: {
                    width: { min: 640, ideal: 1280 },
                    height: { min: 480, ideal: 720 },
                    facingMode: "environment", // Use rear camera
                    aspectRatio: { min: 1, max: 2 }
                },
            },
            locator: {
                patchSize: "medium",
                halfSample: true
            },
            numOfWorkers: navigator.hardwareConcurrency || 2, // Use available CPU cores
            frequency: 10,
            decoder: {
                readers: [
                    "ean_reader",        // Most common for food products
                    "ean_8_reader",      // Shorter EAN codes
                    "upc_reader",        // Universal Product Code
                    "upc_e_reader",      // UPC-E format
                    "code_128_reader",   // Code 128
                    "code_39_reader",    // Code 39
                    "code_39_vin_reader", // Code 39 VIN
                    "codabar_reader",    // Codabar
                    "i2of5_reader"       // Interleaved 2 of 5
                ]
            },
            locate: true
        }, (err) => {
            if (err) {
                console.error('Quagga initialization failed:', err);
                showToast('Failed to initialize barcode scanner', 'error');
                return;
            }
            
            console.log('Quagga initialized successfully');
            Quagga.start();
            
            // Add visual scanning indicator
            this.updateScanningIndicator();
        });
        
        // Listen for barcode detection with improved error handling
        Quagga.onDetected((result) => {
            const code = result.codeResult.code;
            const format = result.codeResult.format;
            console.log('Barcode detected:', code, 'Format:', format);
            
            // Validate barcode format and length
            if (this.isValidBarcode(code, format)) {
                // Stop scanning and search for the product
                this.stopBarcodeScanner();
                // Note: Barcode search moved to food-journal.js
                console.log('Barcode found but search moved to food journal:', code);
            } else {
                console.log('Invalid barcode format, continuing scan...');
            }
        });
        
        // Listen for processing with improved visual feedback
        Quagga.onProcessed((result) => {
            const drawingCanvas = Quagga.canvas.dom.overlay;
            if (!drawingCanvas) return;
            
            const drawingCtx = drawingCanvas.getContext('2d');
            
            if (result) {
                if (result.boxes) {
                    drawingCtx.clearRect(0, 0, parseInt(drawingCanvas.getAttribute("width")), parseInt(drawingCanvas.getAttribute("height")));
                    result.boxes.filter((box) => box !== result.box).forEach((box) => {
                        Quagga.ImageDebug.drawPath(box, { x: 0, y: 1 }, drawingCtx, { color: "green", lineWidth: 2 });
                    });
                }
                
                if (result.box) {
                    Quagga.ImageDebug.drawPath(result.box, { x: 0, y: 1 }, drawingCtx, { color: "blue", lineWidth: 2 });
                }
                
                if (result.codeResult && result.codeResult.code) {
                    Quagga.ImageDebug.drawPath(result.line, { x: 'x', y: 'y' }, drawingCtx, { color: 'red', lineWidth: 3 });
                }
            }
        });
    }
    
    isValidBarcode(code, format) {
        if (!code || code.length < 8) return false;
        
        // Common barcode formats and their expected lengths
        const formatLengths = {
            'ean_13': 13,
            'ean_8': 8,
            'upc_a': 12,
            'upc_e': 8,
            'code_128': { min: 8, max: 50 },
            'code_39': { min: 8, max: 50 }
        };
        
        // Check if format matches expected length
        if (formatLengths[format]) {
            const expected = formatLengths[format];
            if (typeof expected === 'number') {
                return code.length === expected;
            } else {
                return code.length >= expected.min && code.length <= expected.max;
            }
        }
        
        // Default validation for unknown formats
        return code.length >= 8 && code.length <= 50;
    }
    
    updateScanningIndicator() {
        // Add a visual indicator that scanning is active
        const video = document.getElementById('barcode-video');
        if (!video.classList.contains('scanning-active')) {
            video.classList.add('scanning-active');
            video.style.border = '3px solid #16a34a';
            video.style.boxShadow = '0 0 20px rgba(22, 163, 74, 0.3)';
        }
    }
    
    // Note: searchBarcodeByCode() removed - functionality moved to food-journal.js

    // Note: searchBarcode() removed - functionality moved to food-journal.js

    async removeFoodItem(foodId) {
        if (!confirm('Are you sure you want to remove this food item?')) return;

        try {
            const response = await fetch(`/api/food-log/${foodId}`, {
                method: 'DELETE'
            });

            const data = await response.json();
            
            if (data.success) {
                showToast('Food item removed', 'success');
                this.loadDashboardData();
            } else {
                showToast('Failed to remove food item', 'error');
            }
        } catch (error) {
            console.error('Error removing food item:', error);
            showToast('Failed to remove food item', 'error');
        }
    }

    editFoodItem(foodId, foodName, currentDate, currentTimeOfDay) {
        this.movingFoodId = foodId;
        this.movingFoodName = foodName;
        this.movingFoodCurrentDate = currentDate;
        this.movingFoodCurrentTimeOfDay = currentTimeOfDay;
        
        // Set the edit modal content
        document.getElementById('move-food-name').textContent = foodName;
        
        // Show current date info
        const currentDateObj = new Date(currentDate);
        const currentDateStr = currentDateObj.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
        
        // Set the move date to the current dashboard date by default
        const moveDateInput = document.getElementById('move-date');
        moveDateInput.value = this.currentDate.toISOString().split('T')[0];
        
        // Set the time of day to the current value
        const moveTimeOfDayInput = document.getElementById('move-time-of-day');
        moveTimeOfDayInput.value = currentTimeOfDay;
        
        // Show the edit modal
        document.getElementById('move-food-modal').classList.remove('hidden');
        
        // Show a toast with current info
        showToast(`Currently logged for ${currentDateStr} as ${currentTimeOfDay}`, 'info');
    }

    closeMoveModal() {
        document.getElementById('move-food-modal').classList.add('hidden');
        this.movingFoodId = null;
        this.movingFoodName = null;
        this.movingFoodCurrentDate = null;
    }

    async confirmMoveFood() {
        if (!this.movingFoodId) return;

        const newDate = document.getElementById('move-date').value;
        const newTimeOfDay = document.getElementById('move-time-of-day').value;
        
        if (!newDate) {
            showToast('Please select a date', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/food-log/${this.movingFoodId}/edit`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    date: newDate,
                    time_of_day: newTimeOfDay
                })
            });

            const data = await response.json();
            
            if (data.success) {
                const newDateObj = new Date(newDate);
                const dateStr = newDateObj.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
                showToast(`Food updated: ${dateStr} as ${newTimeOfDay}`, 'success');
                this.closeMoveModal();
                this.loadDashboardData();
            } else {
                showToast(data.message || 'Failed to update food item', 'error');
            }
        } catch (error) {
            console.error('Error updating food item:', error);
            showToast('Failed to update food item', 'error');
        }
    }

    copyFoodItem(foodId) {
        this.copyingFoodId = foodId;
        
        // Get the food item details from the DOM
        const foodItem = document.querySelector(`[onclick*="copyFoodItem(${foodId})"]`).closest('.food-log-item');
        const foodName = foodItem.querySelector('h4').textContent;
        
        this.copyingFoodName = foodName;
        
        // Set the copy modal content
        document.getElementById('copy-food-name').textContent = foodName;
        
        // Set the copy date to the current dashboard date by default
        const copyDateInput = document.getElementById('copy-date');
        copyDateInput.value = this.currentDate.toISOString().split('T')[0];
        
        // Set the time of day to snack by default
        const copyTimeOfDayInput = document.getElementById('copy-time-of-day');
        copyTimeOfDayInput.value = 'snack';
        
        // Show the copy modal
        document.getElementById('copy-food-modal').classList.remove('hidden');
    }

    closeCopyModal() {
        document.getElementById('copy-food-modal').classList.add('hidden');
        this.copyingFoodId = null;
        this.copyingFoodName = null;
    }

    async confirmCopyFood() {
        if (!this.copyingFoodId) return;

        const targetDate = document.getElementById('copy-date').value;
        const targetTimeOfDay = document.getElementById('copy-time-of-day').value;
        
        if (!targetDate) {
            showToast('Please select a target date', 'warning');
            return;
        }

        try {
            const response = await fetch(`/api/food-log/${this.copyingFoodId}/copy`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    target_date: targetDate,
                    time_of_day: targetTimeOfDay
                })
            });

            const data = await response.json();
            
            if (data.success) {
                const targetDateObj = new Date(targetDate);
                const dateStr = targetDateObj.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });
                showToast(`Food copied to ${dateStr} as ${targetTimeOfDay}`, 'success');
                this.closeCopyModal();
                this.loadDashboardData();
            } else {
                showToast(data.message || 'Failed to copy food item', 'error');
            }
        } catch (error) {
            console.error('Error copying food item:', error);
            showToast('Failed to copy food item', 'error');
        }
    }

    async loadMoodNotesHistory() {
        const selectedDate = this.currentDate.toISOString().split('T')[0];
        
        // Update the date display
        const dateDisplay = document.getElementById('mood-notes-date-display');
        if (dateDisplay) {
            const dateObj = new Date(selectedDate);
            const formattedDate = dateObj.toLocaleDateString('en-US', { 
                weekday: 'long', 
                month: 'long', 
                day: 'numeric',
                year: 'numeric'
            });
            dateDisplay.textContent = formattedDate;
        }
        
        try {
            const response = await fetch(`/api/mood-notes-history?date=${selectedDate}`);
            const data = await response.json();
            
            if (data.success) {
                this.displayMoodHistory(data.mood_logs || []);
                this.displayNotesHistory(data.notes || []);
            } else {
                console.error('Failed to load mood and notes history:', data.message);
            }
        } catch (error) {
            console.error('Error loading mood and notes history:', error);
        }
    }

    displayMoodHistory(moodLogs) {
        const container = document.getElementById('mood-history');
        
        if (moodLogs.length === 0) {
            container.innerHTML = `
                <div class="text-center py-6 text-gray-500">
                    <div class="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                        <svg class="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                        </svg>
                    </div>
                    <p class="text-sm font-medium text-gray-900 mb-1">No mood entries for this date</p>
                    <p class="text-xs text-gray-500">Log your mood in the Mood & Notes card above</p>
                </div>
            `;
            return;
        }

        container.innerHTML = moodLogs.map(log => {
            const moodEmojis = ['😢', '😕', '😐', '😊', '😄'];
            const moodTexts = ['Terrible', 'Bad', 'Okay', 'Good', 'Excellent'];
            const moodEmoji = moodEmojis[log.mood - 1];
            const moodText = moodTexts[log.mood - 1];
            const timestamp = new Date(log.timestamp).toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit',
                hour12: true 
            });

            return `
                <div class="bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-3">
                            <span class="text-2xl">${moodEmoji}</span>
                            <div>
                                <p class="font-medium text-gray-900">${moodText}</p>
                                <p class="text-xs text-gray-500">${timestamp}</p>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }

    displayNotesHistory(notes) {
        const container = document.getElementById('notes-history');
        
        if (notes.length === 0) {
            container.innerHTML = `
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

        container.innerHTML = notes.map(note => {
            const timestamp = new Date(note.timestamp).toLocaleTimeString('en-US', { 
                hour: 'numeric', 
                minute: '2-digit',
                hour12: true 
            });
            const content = typeof note.content === 'string' ? note.content : (note.content || '');

            return `
                <div class="bg-gray-50 rounded-lg p-3 border border-gray-100">
                    <div class="mb-2">
                        <p class="text-xs text-gray-500">${timestamp}</p>
                    </div>
                    <p class="text-sm text-gray-700 whitespace-pre-wrap">${content}</p>
                </div>
            `;
        }).join('');
    }

    // Water settings methods
    loadWaterSettings() {
        const savedAmount = localStorage.getItem('quickWaterAmount');
        if (savedAmount) {
            this.quickWaterAmount = parseInt(savedAmount);
        }
        this.updateQuickAddDisplay();
    }

    getQuickWaterAmount() {
        return this.quickWaterAmount;
    }

    setQuickWaterAmount(amount) {
        this.quickWaterAmount = amount;
        localStorage.setItem('quickWaterAmount', amount.toString());
        this.updateQuickAddDisplay();
    }

    updateQuickAddDisplay() {
        const displayElement = document.getElementById('quick-add-amount');
        if (displayElement) {
            displayElement.textContent = `${this.quickWaterAmount} oz`;
        }
    }
}

// Global functions for onclick handlers
function addWater(cups) {
    const amount = cups; // 1 cup = 8 oz
    const date = dashboardManager.currentDate.toISOString().split('T')[0];
    
    fetch('/api/water-log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount, date })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Water intake logged!', 'success');
            dashboardManager.loadDashboardData();
        } else {
            showToast('Failed to log water intake', 'error');
        }
    })
    .catch(error => {
        console.error('Error logging water:', error);
        showToast('Failed to log water intake', 'error');
    });
}

// Water quick add functionality
function addQuickWater() {
    const amount = dashboardManager.getQuickWaterAmount();
    const date = dashboardManager.currentDate.toISOString().split('T')[0];
    
    fetch('/api/water-log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ amount: amount, date: date })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(`Added ${amount} oz of water!`, 'success');
            dashboardManager.loadDashboardData();
        } else {
            showToast('Failed to log water intake', 'error');
        }
    })
    .catch(error => {
        console.error('Error logging water:', error);
        showToast('Failed to log water intake', 'error');
    });
}

// Water settings functions
function openWaterSettingsModal() {
    const modal = document.getElementById('water-settings-modal');
    const amountInput = document.getElementById('water-quick-amount');
    
    // Load current amount
    amountInput.value = dashboardManager.getQuickWaterAmount();
    
    modal.classList.remove('hidden');
}

function closeWaterSettingsModal() {
    document.getElementById('water-settings-modal').classList.add('hidden');
}

function setWaterAmount(amount) {
    document.getElementById('water-quick-amount').value = amount;
}

function saveWaterSettings() {
    const amount = parseInt(document.getElementById('water-quick-amount').value);
    
    if (isNaN(amount) || amount < 1 || amount > 64) {
        showToast('Please enter a valid amount between 1 and 64 oz', 'warning');
        return;
    }
    
    dashboardManager.setQuickWaterAmount(amount);
    closeWaterSettingsModal();
    showToast(`Quick add amount set to ${amount} oz`, 'success');
}

function setMood(emoji, moodText) {
    // Update the visual display
    document.getElementById('current-mood').textContent = emoji;
    document.getElementById('mood-text').textContent = moodText;
    
    // Map mood text to numeric value (1-5 scale)
    const moodMap = {
        'Terrible': 1,
        'Okay': 2,
        'Good': 3,
        'Great': 4,
        'Excellent': 5
    };
    
    const moodValue = moodMap[moodText];
    if (moodValue) {
        // Log the mood to the server
        logMood(moodValue);
        
        // Add visual feedback to the selected button
        const moodButtons = document.querySelectorAll('.mood-btn');
        moodButtons.forEach(btn => {
            btn.classList.remove('bg-ki-green-100', 'border-ki-green-300');
            btn.classList.add('hover:bg-gray-100');
        });
        
        // Highlight the selected button
        event.target.closest('.mood-btn').classList.add('bg-ki-green-100', 'border-ki-green-300');
        event.target.closest('.mood-btn').classList.remove('hover:bg-gray-100');
    }
}

function logMood(mood) {
    const date = dashboardManager.currentDate.toISOString().split('T')[0];
    
    fetch('/api/mood-log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mood, date })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Mood logged!', 'success');
            dashboardManager.loadDashboardData();
        } else {
            showToast('Failed to log mood', 'error');
        }
    })
    .catch(error => {
        console.error('Error logging mood:', error);
        showToast('Failed to log mood', 'error');
    });
}

function saveNotes() {
    const content = document.getElementById('daily-notes').value.trim();
    const date = dashboardManager.currentDate.toISOString().split('T')[0];
    
    // Validate content
    if (!content) {
        showToast('Please enter some notes before saving', 'warning');
        return;
    }
    
    // Show loading state
    const saveButton = document.querySelector('button[onclick="saveNotes()"]');
    const originalText = saveButton.textContent;
    saveButton.textContent = 'Saving...';
    saveButton.disabled = true;
    
    fetch('/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, date })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Notes saved successfully!', 'success');
            // Clear the input field after successful save
            document.getElementById('daily-notes').value = '';
            // Refresh the dashboard to show the new note
            dashboardManager.loadDashboardData();
            // Update mood & notes history if the tab is active
            if (document.getElementById('mood-notes-content').classList.contains('active')) {
                dashboardManager.loadMoodNotesHistory();
            }
        } else {
            showToast(data.error || 'Failed to save notes', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving notes:', error);
        showToast('Failed to save notes. Please try again.', 'error');
    })
    .finally(() => {
        // Reset button state
        saveButton.textContent = originalText;
        saveButton.disabled = false;
    });
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});
