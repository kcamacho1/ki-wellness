// Ki Wellness Dashboard JavaScript
// ================================

class DashboardManager {
    constructor() {
        this.currentDate = new Date();
        this.selectedFood = null;
        this.stream = null;
        this.macroChart = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.updateDateDisplay();
        this.updateFoodLoggingDate();
        this.initMacroChart();
        this.loadDashboardData();
        this.initTabs();
    }

    setupEventListeners() {
        // Date navigation
        document.getElementById('date-prev').addEventListener('click', () => this.changeDate(-1));
        document.getElementById('date-next').addEventListener('click', () => this.changeDate(1));
        document.getElementById('today-btn').addEventListener('click', () => this.goToToday());

        // Food search
        document.getElementById('search-btn').addEventListener('click', () => this.searchFood());
        document.getElementById('food-search').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.searchFood();
        });

        // Barcode scanner
        document.getElementById('start-barcode-scanner').addEventListener('click', () => this.startBarcodeScanner());
        document.getElementById('stop-barcode-scanner').addEventListener('click', () => this.stopBarcodeScanner());
        document.getElementById('search-barcode').addEventListener('click', () => this.searchBarcode());

        // Manual food entry
        document.getElementById('add-manual').addEventListener('click', () => this.addManualFood());

        // Modal controls
        document.getElementById('close-modal').addEventListener('click', () => this.closeModal());
        document.getElementById('cancel-modal').addEventListener('click', () => this.closeModal());
        document.getElementById('add-to-log').addEventListener('click', () => this.addFoodToLog());

        // Modal input changes
        document.getElementById('modal-amount').addEventListener('input', () => this.updateConversion());
        document.getElementById('modal-unit').addEventListener('change', () => this.updateConversion());
        document.getElementById('modal-quantity').addEventListener('input', () => this.updateConversion());

        // Date selection controls
        document.getElementById('use-current-date').addEventListener('click', () => this.syncWithDashboardDate());
        document.getElementById('modal-use-current-date').addEventListener('click', () => this.syncWithDashboardDate());

        // Date input change listeners
        const manualDateInput = document.getElementById('manual-date');
        const modalDateInput = document.getElementById('modal-date');
        
        if (manualDateInput) {
            manualDateInput.addEventListener('change', () => this.onDateInputChange('manual-date'));
        }
        if (modalDateInput) {
            modalDateInput.addEventListener('change', () => this.onDateInputChange('modal-date'));
        }

        // Edit modal controls
        document.getElementById('close-move-modal').addEventListener('click', () => this.closeMoveModal());
        document.getElementById('cancel-move').addEventListener('click', () => this.closeMoveModal());
        document.getElementById('confirm-move').addEventListener('click', () => this.confirmMoveFood());
        document.getElementById('move-use-current-date').addEventListener('click', () => this.setCurrentDate('move-date'));
    }

    initTabs() {
        const tabs = ['search', 'barcode', 'manual', 'mood-notes'];
        const contents = ['search-content', 'barcode-content', 'manual-content', 'mood-notes-content'];

        tabs.forEach((tab, index) => {
            document.getElementById(`${tab}-tab`).addEventListener('click', () => {
                this.switchTab(tab, contents[index]);
            });
        });


    }

    switchTab(activeTab, activeContent) {
        // Update tab buttons
        ['search-tab', 'barcode-tab', 'manual-tab', 'mood-notes-tab'].forEach(tabId => {
            const tab = document.getElementById(tabId);
            if (tabId === `${activeTab}-tab`) {
                tab.classList.add('text-ki-green-600', 'bg-white', 'shadow-sm', 'border', 'border-gray-200');
                tab.classList.remove('text-gray-500', 'hover:bg-white');
            } else {
                tab.classList.remove('text-ki-green-600', 'bg-white', 'shadow-sm', 'border', 'border-gray-200');
                tab.classList.add('text-gray-500', 'hover:bg-white');
            }
        });

        // Update content
        ['search-content', 'barcode-content', 'manual-content', 'mood-notes-content'].forEach(contentId => {
            const content = document.getElementById(contentId);
            if (contentId === activeContent) {
                content.classList.remove('hidden');
                // Load mood and notes history when the tab is opened
                if (contentId === 'mood-notes-content') {
                    this.loadMoodNotesHistory();
                }
            } else {
                content.classList.add('hidden');
            }
        });

        // If switching to manual tab, sync the date
        if (activeTab === 'manual') {
            this.updateFoodLoggingDate();
        }
    }

    updateDateDisplay() {
        const dateElement = document.getElementById('current-date');
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        dateElement.textContent = this.currentDate.toLocaleDateString('en-US', options);
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
        const container = document.getElementById('food-log');
        
        // Check if the food-log container exists (it was removed from the template)
        if (!container) {
            return;
        }
        
        if (foodLogs.length === 0) {
                    container.innerHTML = `
            <div class="text-center py-8 sm:py-12 text-gray-500">
                <div class="w-12 h-12 sm:w-16 sm:h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3 sm:mb-4">
                    <svg class="w-6 h-6 sm:w-8 sm:h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                    </svg>
                </div>
                <p class="text-base sm:text-lg font-medium text-gray-900 mb-2">No food logged yet today</p>
                <p class="text-xs sm:text-sm text-gray-500">Start by searching for food or adding manually</p>
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

    async searchFood() {
        const query = document.getElementById('food-search').value.trim();
        if (!query) {
            showToast('Please enter a food item to search', 'warning');
            return;
        }

        try {
            showLoading();
            const response = await fetch('/api/search-food', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });

            const data = await response.json();
            
            if (data.success) {
                this.displaySearchResults(data.results);
            } else {
                showToast('Failed to search for food', 'error');
            }
        } catch (error) {
            console.error('Error searching food:', error);
            showToast('Failed to search for food', 'error');
        } finally {
            hideLoading();
        }
    }

    displaySearchResults(results) {
        const container = document.getElementById('search-results');
        
        if (results.length === 0) {
            container.innerHTML = '<p class="text-gray-500 text-center py-4">No food items found</p>';
            container.classList.remove('hidden');
            return;
        }

        container.innerHTML = results.map(food => `
            <div class="food-result" onclick="dashboardManager.selectFood(${JSON.stringify(food).replace(/\"/g, '&quot;')})">
                <div class="food-result-info">
                    <div class="food-result-name">${food.name}</div>
                    <div class="food-result-brand">${food.brand}</div>
                    <div class="flex space-x-2 mt-1 text-xs">
                        <span class="text-red-600">${Math.round(food.protein)}g protein</span>
                        <span class="text-yellow-600">${Math.round(food.carbs)}g carbs</span>
                        <span class="text-green-600">${Math.round(food.fat)}g fat</span>
                        <span class="text-purple-600">${Math.round(food.calories)} cal</span>
                    </div>
                    <div class="mt-1">
                        <span class="px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-medium ${
                            food.source === 'usda' ? 'bg-indigo-50 text-indigo-700' :
                            food.source === 'openfoodfacts' ? 'bg-orange-50 text-orange-700' :
                            food.source === 'common_foods' ? 'bg-gray-100 text-gray-700' :
                            'bg-gray-100 text-gray-600'
                        }">
                            Source: ${
                                food.source === 'usda' ? 'USDA' :
                                food.source === 'openfoodfacts' ? 'Open Food Facts' :
                                food.source === 'common_foods' ? 'Ki Wellness (local)' :
                                'Unknown'
                            }
                        </span>
                    </div>
                </div>
            </div>
        `).join('');

        container.classList.remove('hidden');
    }

    selectFood(food) {
        this.selectedFood = food;
        this.showFoodModal(food);
    }

    showFoodModal(food) {
        this.selectedFood = food;
        document.getElementById('modal-food-name').textContent = food.name;
        
        const infoHtml = `
            <div class="space-y-2">
                <p class="text-sm text-gray-600">Brand: ${food.brand}</p>
                <p class="text-xs">
                    <span class="px-2 py-0.5 rounded-full text-[10px] sm:text-xs font-medium ${
                        food.source === 'usda' ? 'bg-indigo-50 text-indigo-700' :
                        food.source === 'openfoodfacts' ? 'bg-orange-50 text-orange-700' :
                        food.source === 'common_foods' ? 'bg-gray-100 text-gray-700' :
                        'bg-gray-100 text-gray-600'
                    }">
                        Source: ${
                            food.source === 'usda' ? 'USDA' :
                            food.source === 'openfoodfacts' ? 'Open Food Facts' :
                            food.source === 'common_foods' ? 'Ki Wellness (local)' :
                            'Unknown'
                        }
                    </span>
                </p>
                <div class="grid grid-cols-2 gap-2 text-sm">
                    <div class="bg-red-50 p-2 rounded">
                        <span class="text-red-600 font-medium">Protein:</span> ${Math.round(food.protein)}g
                    </div>
                    <div class="bg-yellow-50 p-2 rounded">
                        <span class="text-yellow-600 font-medium">Carbs:</span> ${Math.round(food.carbs)}g
                    </div>
                    <div class="bg-green-50 p-2 rounded">
                        <span class="text-green-600 font-medium">Fat:</span> ${Math.round(food.fat)}g
                    </div>
                    <div class="bg-purple-50 p-2 rounded">
                        <span class="text-purple-600 font-medium">Calories:</span> ${Math.round(food.calories)}
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('modal-food-info').innerHTML = infoHtml;
        
        // Set the modal date to match the current dashboard date
        const modalDateInput = document.getElementById('modal-date');
        if (modalDateInput) {
            modalDateInput.value = this.currentDate.toISOString().split('T')[0];
        }
        
        this.updateConversion();
        document.getElementById('food-modal').classList.remove('hidden');
    }

    closeModal() {
        document.getElementById('food-modal').classList.add('hidden');
        this.selectedFood = null;
    }

    updateConversion() {
        if (!this.selectedFood) return;

        const amount = parseFloat(document.getElementById('modal-amount').value) || 0;
        const unit = document.getElementById('modal-unit').value;
        const quantity = parseFloat(document.getElementById('modal-quantity').value) || 1;

        // Convert to grams (simplified conversion)
        let grams = amount;
        switch (unit) {
            case 'oz': grams = amount * 28.35; break;
            case 'cup': grams = amount * 240; break;
            case 'tbsp': grams = amount * 15; break;
            case 'tsp': grams = amount * 5; break;
            default: grams = amount; // already in grams
        }

        const totalGrams = grams * quantity;
        document.getElementById('total-grams').textContent = `${Math.round(totalGrams)}g`;
    }

    async addFoodToLog() {
        if (!this.selectedFood) return;

        const amount = parseFloat(document.getElementById('modal-amount').value) || 0;
        const unit = document.getElementById('modal-unit').value;
        const quantity = parseFloat(document.getElementById('modal-quantity').value) || 1;

        if (amount <= 0) {
            showToast('Please enter a valid amount', 'warning');
            return;
        }

        // Convert to grams
        let grams = amount;
        switch (unit) {
            case 'oz': grams = amount * 28.35; break;
            case 'cup': grams = amount * 240; break;
            case 'tbsp': grams = amount * 15; break;
            case 'tsp': grams = amount * 5; break;
            default: grams = amount;
        }

        const totalGrams = grams * quantity;
        const multiplier = totalGrams / 100; // Assuming nutrition is per 100g

        const timeOfDay = document.getElementById('modal-time-of-day').value;
        const selectedDate = this.getSelectedDate('modal-date');
        
        const foodData = {
            name: this.selectedFood.name,
            brand: this.selectedFood.brand,
            calories: Math.round(this.selectedFood.calories * multiplier),
            protein: Math.round(this.selectedFood.protein * multiplier),
            carbs: Math.round(this.selectedFood.carbs * multiplier),
            fat: Math.round(this.selectedFood.fat * multiplier),
            fiber: Math.round((this.selectedFood.fiber || 0) * multiplier),
            sugar: Math.round((this.selectedFood.sugar || 0) * multiplier),
            sodium: Math.round((this.selectedFood.sodium || 0) * multiplier),
            serving_size: totalGrams,
            original_amount: amount,
            original_unit: unit,
            quantity: quantity,
            time_of_day: timeOfDay,
            date: selectedDate
        };

        try {
            const response = await fetch('/api/food-log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(foodData)
            });

            const data = await response.json();
            
            if (data.success) {
                showToast('Food added to log successfully!', 'success');
                this.closeModal();
                this.loadDashboardData();
            } else {
                showToast('Failed to add food to log', 'error');
            }
        } catch (error) {
            console.error('Error adding food:', error);
            showToast('Failed to add food to log', 'error');
        }
    }

    async addManualFood() {
        const name = document.getElementById('manual-name').value.trim();
        const brand = document.getElementById('manual-brand').value.trim();
        const calories = parseFloat(document.getElementById('manual-calories').value) || 0;
        const protein = parseFloat(document.getElementById('manual-protein').value) || 0;
        const carbs = parseFloat(document.getElementById('manual-carbs').value) || 0;
        const fat = parseFloat(document.getElementById('manual-fat').value) || 0;
        const amount = parseFloat(document.getElementById('manual-amount').value) || 0;
        const unit = document.getElementById('manual-unit').value;
        const quantity = parseFloat(document.getElementById('manual-quantity').value) || 1;

        if (!name || calories <= 0) {
            showToast('Please enter food name and calories', 'warning');
            return;
        }

        // Convert to grams
        let grams = amount;
        switch (unit) {
            case 'oz': grams = amount * 28.35; break;
            case 'cup': grams = amount * 240; break;
            case 'tbsp': grams = amount * 15; break;
            case 'tsp': grams = amount * 5; break;
            default: grams = amount;
        }

        const totalGrams = grams * quantity;

        const timeOfDay = document.getElementById('manual-time-of-day').value;
        const selectedDate = this.getSelectedDate('manual-date');
        
        const foodData = {
            name: name,
            brand: brand,
            calories: calories,
            protein: protein,
            carbs: carbs,
            fat: fat,
            serving_size: totalGrams,
            original_amount: amount,
            original_unit: unit,
            quantity: quantity,
            time_of_day: timeOfDay,
            date: selectedDate
        };

        try {
            const response = await fetch('/api/food-log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(foodData)
            });

            const data = await response.json();
            
            if (data.success) {
                showToast('Food added to log successfully!', 'success');
                this.clearManualForm();
                this.loadDashboardData();
            } else {
                showToast('Failed to add food to log', 'error');
            }
        } catch (error) {
            console.error('Error adding manual food:', error);
            showToast('Failed to add food to log', 'error');
        }
    }

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

    clearManualForm() {
        document.getElementById('manual-name').value = '';
        document.getElementById('manual-brand').value = '';
        document.getElementById('manual-calories').value = '';
        document.getElementById('manual-protein').value = '';
        document.getElementById('manual-carbs').value = '';
        document.getElementById('manual-fat').value = '';
        document.getElementById('manual-time-of-day').value = 'snack';
        document.getElementById('manual-amount').value = '1';
        document.getElementById('manual-quantity').value = '1';
    }

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

    async startBarcodeScanner() {
        try {
            // First, check if camera permissions are available
            if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                throw new Error('Camera access not supported in this browser');
            }

            // Request camera permissions first
            console.log('Requesting camera permissions...');
            try {
                const permissionStream = await navigator.mediaDevices.getUserMedia({ video: true });
                // Stop this test stream immediately
                permissionStream.getTracks().forEach(track => track.stop());
                console.log('Camera permissions granted');
            } catch (permissionError) {
                console.log('Camera permission request failed:', permissionError);
                throw new Error('Camera access denied. Please allow camera permissions in your browser settings and try again.');
            }

            // Try to get available video devices
            let devices = [];
            let videoDevices = [];
            
            try {
                devices = await navigator.mediaDevices.enumerateDevices();
                videoDevices = devices.filter(device => device.kind === 'videoinput');
                console.log('Available video devices:', videoDevices);
            } catch (enumError) {
                console.log('Could not enumerate devices, trying direct camera access:', enumError);
                // If enumeration fails, we'll try direct camera access
            }

            // Try different camera configurations
            let stream = null;
            const cameraConfigs = [
                { video: { facingMode: 'environment' } },  // Rear camera
                { video: { facingMode: 'user' } },        // Front camera
                { video: true },                          // Any camera
            ];
            
            // Add device-specific configs if we have device info
            if (videoDevices.length > 0) {
                cameraConfigs.push({ video: { deviceId: videoDevices[0].deviceId } });
            }

            for (const config of cameraConfigs) {
                try {
                    console.log('Trying camera config:', config);
                    stream = await navigator.mediaDevices.getUserMedia(config);
                    console.log('Camera access granted with config:', config);
                    break;
                } catch (configError) {
                    console.log('Camera config failed:', config, configError);
                    continue;
                }
            }

            if (!stream) {
                // If we couldn't get any camera, try one more time with basic config
                try {
                    console.log('Trying basic camera access as last resort...');
                    stream = await navigator.mediaDevices.getUserMedia({ video: true });
                    console.log('Basic camera access succeeded');
                } catch (finalError) {
                    console.error('All camera access attempts failed:', finalError);
                    throw new Error('Could not access any camera. Please check camera permissions and ensure no other apps are using the camera.');
                }
            }

            this.stream = stream;
            const video = document.getElementById('barcode-video');
            video.srcObject = this.stream;
            
            // Wait for video to be ready
            await new Promise((resolve) => {
                video.onloadedmetadata = () => {
                    video.play();
                    resolve();
                };
            });
            
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
            
            // Add helpful instructions for camera permissions
            if (error.name === 'NotAllowedError' || error.message.includes('permissions')) {
                errorMessage += '\n\nTo enable camera access:\n' +
                    '• Click the camera icon in your browser\'s address bar\n' +
                    '• Select "Allow" for camera access\n' +
                    '• Refresh the page and try again';
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
        
        // Configure QuaggaJS
        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: video,
                constraints: {
                    width: { min: 640 },
                    height: { min: 480 },
                    facingMode: "environment" // Use rear camera
                },
            },
            locator: {
                patchSize: "medium",
                halfSample: true
            },
            numOfWorkers: 2,
            frequency: 10,
            decoder: {
                readers: [
                    "code_128_reader",
                    "ean_reader",
                    "ean_8_reader",
                    "code_39_reader",
                    "code_39_vin_reader",
                    "codabar_reader",
                    "upc_reader",
                    "upc_e_reader",
                    "i2of5_reader"
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
        
        // Listen for barcode detection
        Quagga.onDetected((result) => {
            const code = result.codeResult.code;
            console.log('Barcode detected:', code);
            
            // Stop scanning and search for the product
            this.stopBarcodeScanner();
            this.searchBarcodeByCode(code);
        });
        
        // Listen for processing
        Quagga.onProcessed((result) => {
            const drawingCanvas = Quagga.canvas.dom.overlay;
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
    
    updateScanningIndicator() {
        // Add a visual indicator that scanning is active
        const video = document.getElementById('barcode-video');
        if (!video.classList.contains('scanning-active')) {
            video.classList.add('scanning-active');
            video.style.border = '3px solid #16a34a';
            video.style.boxShadow = '0 0 20px rgba(22, 163, 74, 0.3)';
        }
    }
    
    async searchBarcodeByCode(barcode) {
        try {
            showLoading();
            const response = await fetch(`/api/product/${barcode}`);
            const data = await response.json();

            if (data.success) {
                this.selectFood(data.product);
                showToast(`Product found: ${data.product.name}`, 'success');
            } else {
                showToast('Product not found in database. Try manual entry.', 'warning');
                // Show manual entry option
                document.getElementById('manual-barcode').value = barcode;
            }
        } catch (error) {
            console.error('Error searching barcode:', error);
            showToast('Failed to search barcode', 'error');
        } finally {
            hideLoading();
        }
    }

    async searchBarcode() {
        const barcode = document.getElementById('manual-barcode').value.trim();
        if (!barcode) {
            showToast('Please enter a barcode', 'warning');
            return;
        }

        try {
            showLoading();
            const response = await fetch(`/api/product/${barcode}`);
            const data = await response.json();

            if (data.success) {
                this.selectFood(data.product);
            } else {
                showToast('Product not found', 'error');
            }
        } catch (error) {
            console.error('Error searching barcode:', error);
            showToast('Failed to search barcode', 'error');
        } finally {
            hideLoading();
        }
    }

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
