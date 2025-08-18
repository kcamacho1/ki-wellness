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
    }

    initTabs() {
        const tabs = ['search', 'barcode', 'manual'];
        const contents = ['search-content', 'barcode-content', 'manual-content'];

        tabs.forEach((tab, index) => {
            document.getElementById(`${tab}-tab`).addEventListener('click', () => {
                this.switchTab(tab, contents[index]);
            });
        });
    }

    switchTab(activeTab, activeContent) {
        // Update tab buttons
        ['search-tab', 'barcode-tab', 'manual-tab'].forEach(tabId => {
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
        ['search-content', 'barcode-content', 'manual-content'].forEach(contentId => {
            const content = document.getElementById(contentId);
            if (contentId === activeContent) {
                content.classList.remove('hidden');
            } else {
                content.classList.add('hidden');
            }
        });
    }

    updateDateDisplay() {
        const dateElement = document.getElementById('current-date');
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        dateElement.textContent = this.currentDate.toLocaleDateString('en-US', options);
    }

    changeDate(days) {
        this.currentDate.setDate(this.currentDate.getDate() + days);
        this.updateDateDisplay();
        this.loadDashboardData();
    }

    goToToday() {
        this.currentDate = new Date();
        this.updateDateDisplay();
        this.loadDashboardData();
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
        
        // Update notes
        document.getElementById('daily-notes').value = data.notes || '';
        
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
            const moodEmojis = ['😢', '😕', '😐', '😊', '😄'];
            const moodTexts = ['Terrible', 'Bad', 'Okay', 'Good', 'Excellent'];
            
            document.getElementById('current-mood-emoji').textContent = moodEmojis[latestMood - 1];
            document.getElementById('current-mood-text').textContent = moodTexts[latestMood - 1];
        }
    }

    displayFoodLog(foodLogs) {
        const container = document.getElementById('food-log');
        
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
                    <button onclick="dashboardManager.removeFoodItem(${log.id})" class="text-gray-400 hover:text-red-500 ml-2 sm:ml-4 p-1 sm:p-2 hover:bg-red-50 rounded-lg transition-colors">
                        <svg class="w-4 h-4 sm:w-5 sm:h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path>
                        </svg>
                    </button>
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
            <div class="food-result" onclick="dashboardManager.selectFood(${JSON.stringify(food).replace(/"/g, '&quot;')})">
                <div class="food-result-info">
                    <div class="food-result-name">${food.name}</div>
                    <div class="food-result-brand">${food.brand}</div>
                    <div class="flex space-x-2 mt-1 text-xs">
                        <span class="text-red-600">${Math.round(food.protein)}g protein</span>
                        <span class="text-yellow-600">${Math.round(food.carbs)}g carbs</span>
                        <span class="text-green-600">${Math.round(food.fat)}g fat</span>
                        <span class="text-purple-600">${Math.round(food.calories)} cal</span>
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
        document.getElementById('modal-food-name').textContent = food.name;
        
        const infoHtml = `
            <div class="space-y-2">
                <p class="text-sm text-gray-600">Brand: ${food.brand}</p>
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
            date: this.currentDate.toISOString().split('T')[0]
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
            date: this.currentDate.toISOString().split('T')[0]
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
            this.stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
            const video = document.getElementById('barcode-video');
            video.srcObject = this.stream;
            video.play();
            
            document.getElementById('barcode-scanner-container').classList.remove('hidden');
            document.getElementById('start-barcode-scanner').classList.add('hidden');
            
            // Start barcode detection (simplified - would need a proper barcode library)
            this.startBarcodeDetection();
        } catch (error) {
            console.error('Error starting barcode scanner:', error);
            showToast('Failed to start camera', 'error');
        }
    }

    stopBarcodeScanner() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
            this.stream = null;
        }
        
        document.getElementById('barcode-scanner-container').classList.add('hidden');
        document.getElementById('start-barcode-scanner').classList.remove('hidden');
    }

    startBarcodeDetection() {
        // This is a placeholder - would need a proper barcode detection library
        // For now, we'll just show a message
        showToast('Barcode detection is a placeholder feature', 'info');
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
    const content = document.getElementById('daily-notes').value;
    const date = dashboardManager.currentDate.toISOString().split('T')[0];
    
    fetch('/api/notes', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content, date })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast('Notes saved!', 'success');
        } else {
            showToast('Failed to save notes', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving notes:', error);
        showToast('Failed to save notes', 'error');
    });
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});
