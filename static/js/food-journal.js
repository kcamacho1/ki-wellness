/**
 * FoodJournal - A modular class for managing food journal functionality
 * Handles food search, barcode scanning, manual entry, and logging
 * Version: 2.0.2 - Fixed null reference errors and enhanced Quagga error handling
 */
class FoodJournal {
    constructor() {
        this.currentTab = 'search';
        this.modal = null;
        this.currentDate = new Date().toISOString().split('T')[0];
        this.searchCache = new Map();
        this.barcodeScanner = null;
        this.stream = null; // Add stream property for camera management
        
        this.init();
    }
    
    /**
     * Initialize the food journal
     */
    init() {
        this.bindEvents();
        this.setupModal();
    }
    
    /**
     * Bind event listeners
     */
    bindEvents() {
        // Modal open/close events
        window.openFoodJournalModal = () => this.openModal();
        window.closeFoodJournalModal = () => this.closeModal();
        
        // Tab switching
        document.addEventListener('click', (e) => {
            if (e.target.matches('#modal-search-tab')) this.switchTab('search');
            if (e.target.matches('#modal-barcode-tab')) this.switchTab('barcode');
            if (e.target.matches('#modal-manual-tab')) this.switchTab('manual');
        });
        
        // Search functionality
        document.addEventListener('click', (e) => {
            if (e.target.matches('#modal-search-btn')) this.performSearch();
        });
        
        document.addEventListener('keypress', (e) => {
            if (e.target.matches('#modal-food-search') && e.key === 'Enter') {
                this.performSearch();
            }
        });
        
        // Barcode scanner
        document.addEventListener('click', (e) => {
            if (e.target.matches('#modal-start-barcode-scanner')) this.startBarcodeScanner();
            if (e.target.matches('#modal-stop-barcode-scanner')) this.stopBarcodeScanner();
            if (e.target.matches('#modal-search-barcode')) this.searchBarcode();
        });
        
        // Manual entry
        document.addEventListener('click', (e) => {
            if (e.target.matches('#modal-add-manual')) this.addManualEntry();
        });
        
        // Close modal on backdrop click
        document.addEventListener('click', (e) => {
            if (e.target.matches('#food-journal-modal')) this.closeModal();
        });
        
        // Escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isModalOpen()) this.closeModal();
        });
    }
    
    /**
     * Setup modal elements
     */
    setupModal() {
        this.modal = document.getElementById('food-journal-modal');
        if (!this.modal) {
            console.error('Food journal modal not found');
            return;
        }
        
        // Add CSS classes for styling
        this.modal.classList.add('food-journal-modal');
        
        // Set current date as default
        const dateInputs = this.modal.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => input.value = this.currentDate);
    }
    
    /**
     * Open the food journal modal
     */
    openModal() {
        if (!this.modal) return;
        
        this.modal.classList.remove('hidden');
        this.modal.classList.add('show');
        document.body.style.overflow = 'hidden';
        
        // Focus on search input
        setTimeout(() => {
            const searchInput = document.getElementById('modal-food-search');
            if (searchInput) searchInput.focus();
        }, 100);
        
        this.logActivity('Food journal modal opened');
    }
    
    /**
     * Close the food journal modal
     */
    closeModal() {
        if (!this.modal) return;
        
        // Stop barcode scanner immediately to prevent any lingering processes
        this.stopBarcodeScanner();
        
        this.modal.classList.add('hide');
        
        setTimeout(() => {
            this.modal.classList.add('hidden');
            this.modal.classList.remove('show', 'hide');
            document.body.style.overflow = '';
            
            // Clear search fields when modal closes
            this.clearSearchFields();
        }, 300);
        
        this.logActivity('Food journal modal closed');
    }
    
    /**
     * Check if modal is currently open
     */
    isModalOpen() {
        return this.modal && !this.modal.classList.contains('hidden');
    }
    
    /**
     * Switch between tabs (search, barcode, manual)
     */
    switchTab(tabName) {
        this.currentTab = tabName;
        
        // Update tab buttons
        const tabs = ['search', 'barcode', 'manual'];
        tabs.forEach(tab => {
            const tabBtn = document.getElementById(`modal-${tab}-tab`);
            const tabContent = document.getElementById(`modal-${tab}-content`);
            
            if (tabBtn && tabContent) {
                if (tab === tabName) {
                    tabBtn.classList.add('text-ki-green-600', 'bg-white', 'shadow-sm', 'border', 'border-gray-200');
                    tabBtn.classList.remove('text-gray-500', 'hover:text-gray-700', 'hover:bg-white');
                    tabContent.classList.remove('hidden');
                } else {
                    tabBtn.classList.remove('text-ki-green-600', 'bg-white', 'shadow-sm', 'border', 'border-gray-200');
                    tabBtn.classList.add('text-gray-500', 'hover:text-gray-700', 'hover:bg-white');
                    tabContent.classList.add('hidden');
                }
            }
        });
        
        // Focus appropriate input
        this.focusTabInput(tabName);
        
        this.logActivity(`Switched to ${tabName} tab`);
    }
    
    /**
     * Focus the main input for the current tab
     */
    focusTabInput(tabName) {
        setTimeout(() => {
            let inputElement;
            switch (tabName) {
                case 'search':
                    inputElement = document.getElementById('modal-food-search');
                    break;
                case 'barcode':
                    inputElement = document.getElementById('modal-manual-barcode');
                    break;
                case 'manual':
                    inputElement = document.getElementById('modal-manual-name');
                    break;
            }
            if (inputElement) inputElement.focus();
        }, 100);
    }
    
    /**
     * Perform food search using the API
     */
    async performSearch() {
        const searchInput = document.getElementById('modal-food-search');
        const resultsContainer = document.getElementById('modal-search-results');
        
        if (!searchInput || !resultsContainer) return;
        
        const query = searchInput.value.trim();
        if (!query) {
            this.showToast('Please enter a food item to search', 'warning');
            return;
        }
        
        // Check cache first
        if (this.searchCache.has(query)) {
            this.displaySearchResults(this.searchCache.get(query), resultsContainer);
            return;
        }
        
        try {
            this.showLoading(resultsContainer);
            
            const response = await fetch('/api/search-food', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ query })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.searchCache.set(query, data.results);
                this.displaySearchResults(data.results, resultsContainer);
                this.logActivity(`Food search performed: ${query}`);
            } else {
                this.showError(resultsContainer, 'Failed to search for food');
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showError(resultsContainer, 'Network error occurred');
        }
    }
    
    /**
     * Display search results in the UI
     */
    displaySearchResults(results, container) {
        if (!results || results.length === 0) {
            container.innerHTML = `
                <div class="text-center py-8 text-gray-500">
                    <svg class="w-12 h-12 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
                    </svg>
                    <p>No food items found</p>
                    <p class="text-xs">Try a different search term or add it to the database</p>
                </div>
                ${this.createAddProductButton()}
            `;
            return;
        }
        
        const resultsHTML = results.map(item => `
            <div class="food-search-result p-4 cursor-pointer hover:bg-gray-50 border rounded-lg transition-colors"
                 onclick="foodJournal.selectFoodItem(${JSON.stringify(item).replace(/"/g, '&quot;')})">
                <div class="flex justify-between items-start">
                    <div class="flex-1">
                        <h4 class="font-medium text-gray-900">${this.escapeHtml(item.name || 'Unknown')}</h4>
                        ${item.brand ? `<p class="text-sm text-gray-600">${this.escapeHtml(item.brand)}</p>` : ''}
                        <div class="flex flex-wrap gap-2 mt-2">
                            ${item.calories ? `<span class="nutrition-badge calories">${item.calories} cal</span>` : ''}
                            ${item.protein ? `<span class="nutrition-badge protein">${item.protein}g protein</span>` : ''}
                            ${item.carbs ? `<span class="nutrition-badge carbs">${item.carbs}g carbs</span>` : ''}
                            ${item.fat ? `<span class="nutrition-badge fat">${item.fat}g fat</span>` : ''}
                        </div>
                    </div>
                    <svg class="w-5 h-5 text-gray-400 ml-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                    </svg>
                </div>
            </div>
        `).join('');
        
        // Add the "Add Product" option at the bottom
        container.innerHTML = resultsHTML + this.createAddProductButton();
    }
    
    /**
     * Handle food item selection from search results
     */
    selectFoodItem(foodItem) {
        // Store selected food item data
        this.selectedFood = foodItem;
        
        // Show the food selection modal instead of directly adding to log
        this.showFoodSelectionModal(foodItem);
        
        this.logActivity(`Food item selected: ${foodItem.name}`);
    }
    
    /**
     * Show food selection modal for serving size and meal type
     */
    showFoodSelectionModal(foodItem) {
        const modal = document.getElementById('food-selection-modal');
        if (!modal) {
            console.error('Food selection modal not found');
            return;
        }
        
        // Populate food information
        document.getElementById('selected-food-name').textContent = foodItem.name || 'Unknown';
        document.getElementById('selected-food-brand').textContent = foodItem.brand || 'Unknown Brand';
        document.getElementById('selected-food-calories').textContent = Math.round(foodItem.calories || 0);
        document.getElementById('selected-food-protein').textContent = Math.round(foodItem.protein || 0);
        document.getElementById('selected-food-carbs').textContent = Math.round(foodItem.carbs || 0);
        document.getElementById('selected-food-fat').textContent = Math.round(foodItem.fat || 0);
        
        // Set default serving size and meal type based on current time
        const currentHour = new Date().getHours();
        let defaultMealType = 'snack';
        if (currentHour >= 6 && currentHour < 11) {
            defaultMealType = 'breakfast';
        } else if (currentHour >= 11 && currentHour < 15) {
            defaultMealType = 'lunch';
        } else if (currentHour >= 15 && currentHour < 21) {
            defaultMealType = 'dinner';
        }
        
        document.getElementById('food-selection-meal-type').value = defaultMealType;
        document.getElementById('food-selection-amount').value = '1';
        document.getElementById('food-selection-unit').value = 'serving';
        
        // Show modal
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        // Set up event listeners for this modal
        this.setupFoodSelectionModalEvents();
        
        // Calculate initial nutrition values after a small delay to ensure DOM is ready
        setTimeout(() => {
            this.updateFoodSelectionNutrition();
        }, 100);
        
        this.logActivity(`Food selection modal opened for: ${foodItem.name}`);
    }
    
    /**
     * Setup event listeners for food selection modal
     */
    setupFoodSelectionModalEvents() {
        // Remove any existing listeners to prevent duplicates
        this.removeFoodSelectionModalEvents();
        
        // Close modal events
        this.foodSelectionCloseHandler = () => this.closeFoodSelectionModal();
        this.foodSelectionCancelHandler = () => this.closeFoodSelectionModal();
        this.foodSelectionConfirmHandler = () => this.confirmFoodSelection();
        this.foodSelectionEscapeHandler = (e) => {
            if (e.key === 'Escape') this.closeFoodSelectionModal();
        };
        
        // Add event listeners
        const closeBtn = document.getElementById('close-food-selection-modal');
        const cancelBtn = document.getElementById('cancel-add-food');
        const confirmBtn = document.getElementById('confirm-add-food');
        
        if (closeBtn) closeBtn.addEventListener('click', this.foodSelectionCloseHandler);
        if (cancelBtn) cancelBtn.addEventListener('click', this.foodSelectionCancelHandler);
        if (confirmBtn) confirmBtn.addEventListener('click', this.foodSelectionConfirmHandler);
        document.addEventListener('keydown', this.foodSelectionEscapeHandler);
        
        // Close modal on backdrop click
        const modal = document.getElementById('food-selection-modal');
        if (modal) {
            this.foodSelectionBackdropHandler = (e) => {
                if (e.target === modal) this.closeFoodSelectionModal();
            };
            modal.addEventListener('click', this.foodSelectionBackdropHandler);
        }
        
        // Real-time nutrition calculation
        this.foodSelectionNutritionHandler = () => this.updateFoodSelectionNutrition();
        
        const amountInput = document.getElementById('food-selection-amount');
        const unitSelect = document.getElementById('food-selection-unit');
        
        if (amountInput) {
            amountInput.addEventListener('input', this.foodSelectionNutritionHandler);
            amountInput.addEventListener('change', this.foodSelectionNutritionHandler);
            amountInput.addEventListener('blur', this.foodSelectionNutritionHandler);
            amountInput.addEventListener('keyup', this.foodSelectionNutritionHandler);
        }
        
        if (unitSelect) {
            unitSelect.addEventListener('change', this.foodSelectionNutritionHandler);
        }
    }
    
    /**
     * Remove event listeners for food selection modal
     */
    removeFoodSelectionModalEvents() {
        const closeBtn = document.getElementById('close-food-selection-modal');
        const cancelBtn = document.getElementById('cancel-add-food');
        const confirmBtn = document.getElementById('confirm-add-food');
        const modal = document.getElementById('food-selection-modal');
        
        if (closeBtn && this.foodSelectionCloseHandler) {
            closeBtn.removeEventListener('click', this.foodSelectionCloseHandler);
        }
        if (cancelBtn && this.foodSelectionCancelHandler) {
            cancelBtn.removeEventListener('click', this.foodSelectionCancelHandler);
        }
        if (confirmBtn && this.foodSelectionConfirmHandler) {
            confirmBtn.removeEventListener('click', this.foodSelectionConfirmHandler);
        }
        if (this.foodSelectionEscapeHandler) {
            document.removeEventListener('keydown', this.foodSelectionEscapeHandler);
        }
        if (modal && this.foodSelectionBackdropHandler) {
            modal.removeEventListener('click', this.foodSelectionBackdropHandler);
        }
        
        // Remove nutrition calculation event listeners
        const amountInput = document.getElementById('food-selection-amount');
        const unitSelect = document.getElementById('food-selection-unit');
        
        if (amountInput && this.foodSelectionNutritionHandler) {
            amountInput.removeEventListener('input', this.foodSelectionNutritionHandler);
            amountInput.removeEventListener('change', this.foodSelectionNutritionHandler);
            amountInput.removeEventListener('blur', this.foodSelectionNutritionHandler);
            amountInput.removeEventListener('keyup', this.foodSelectionNutritionHandler);
        }
        
        if (unitSelect && this.foodSelectionNutritionHandler) {
            unitSelect.removeEventListener('change', this.foodSelectionNutritionHandler);
        }
    }
    
    /**
     * Update nutrition display in food selection modal based on serving size
     */
    updateFoodSelectionNutrition() {
        try {
            if (!this.selectedFood) {
                console.warn('updateFoodSelectionNutrition called but no selectedFood available');
                return;
            }
            
            const amountInput = document.getElementById('food-selection-amount');
            const unitSelect = document.getElementById('food-selection-unit');
            
            if (!amountInput || !unitSelect) {
                console.warn('updateFoodSelectionNutrition called but input elements not found');
                return;
            }
            
            const amount = parseFloat(amountInput.value) || 1;
            const unit = unitSelect.value || 'serving';
            
            // Validate selectedFood has required properties
            if (typeof this.selectedFood !== 'object' || this.selectedFood === null) {
                console.error('selectedFood is not a valid object:', this.selectedFood);
                return;
            }
            
            // Calculate nutrition based on the same logic as confirmFoodSelection
            const baseServingSize = this.selectedFood.serving_size || 100;
            const actualAmount = unit === 'g' ? amount : amount * baseServingSize;
            const multiplier = actualAmount / baseServingSize;
            
            // Calculate scaled nutrition values
            const scaledCalories = Math.round((this.selectedFood.calories || 0) * multiplier);
            const scaledProtein = Math.round((this.selectedFood.protein || 0) * multiplier * 10) / 10;
            const scaledCarbs = Math.round((this.selectedFood.carbs || 0) * multiplier * 10) / 10;
            const scaledFat = Math.round((this.selectedFood.fat || 0) * multiplier * 10) / 10;
            
            // Update the displayed nutrition values
            const caloriesEl = document.getElementById('selected-food-calories');
            const proteinEl = document.getElementById('selected-food-protein');
            const carbsEl = document.getElementById('selected-food-carbs');
            const fatEl = document.getElementById('selected-food-fat');
            
            if (caloriesEl) caloriesEl.textContent = scaledCalories;
            if (proteinEl) proteinEl.textContent = scaledProtein + 'g';
            if (carbsEl) carbsEl.textContent = scaledCarbs + 'g';
            if (fatEl) fatEl.textContent = scaledFat + 'g';
        } catch (error) {
            console.error('Error updating food selection nutrition:', error);
        }
    }

    /**
     * Close food selection modal
     */
    closeFoodSelectionModal() {
        const modal = document.getElementById('food-selection-modal');
        if (!modal) return;
        
        modal.classList.add('hidden');
        document.body.style.overflow = '';
        
        // Remove event listeners
        this.removeFoodSelectionModalEvents();
        
        // Clear selected food reference to prevent memory leaks and null reference errors
        this.selectedFood = null;
        
        this.logActivity('Food selection modal closed');
    }
    
    /**
     * Confirm food selection and add to log
     */
    async confirmFoodSelection() {
        console.log('🔧 confirmFoodSelection called, selectedFood:', this.selectedFood);
        
        if (!this.selectedFood) {
            console.error('❌ No selectedFood available in confirmFoodSelection');
            this.showToast('No food item selected', 'error');
            return;
        }
        
        // Store reference to selected food before operations
        const selectedFood = this.selectedFood;
        const foodName = selectedFood?.name || 'Unknown Food';
        
        console.log('✅ Using selectedFood:', selectedFood, 'foodName:', foodName);
        
        // Get form values
        const amount = parseFloat(document.getElementById('food-selection-amount')?.value) || 1;
        const unit = document.getElementById('food-selection-unit')?.value || 'serving';
        const mealType = document.getElementById('food-selection-meal-type')?.value || 'snack';
        
        // Validate inputs
        if (amount <= 0) {
            this.showToast('Please enter a valid amount', 'warning');
            return;
        }
        
        // Calculate nutrition values based on serving size
        // Base nutrition values are typically per 100g, so we need to scale properly
        const baseServingSize = selectedFood.serving_size || 100; // Default to 100g if not specified
        const actualAmount = unit === 'g' ? amount : amount * baseServingSize; // Convert to grams if needed
        const multiplier = actualAmount / baseServingSize; // Calculate the proper ratio
        

        
        const adjustedFoodItem = {
            ...selectedFood,
            calories: Math.round((selectedFood.calories || 0) * multiplier),
            protein: Math.round((selectedFood.protein || 0) * multiplier * 10) / 10, // 1 decimal place
            carbs: Math.round((selectedFood.carbs || 0) * multiplier * 10) / 10,
            fat: Math.round((selectedFood.fat || 0) * multiplier * 10) / 10,
            serving_size: actualAmount,
            serving_unit: 'g'
        };
        

        
        // Add to log with selected parameters
        await this.addFoodToLog(adjustedFoodItem, mealType);
        
        // Log before closing modal (while selectedFood is still available)
        this.logActivity(`Food confirmed and added: ${foodName} (${amount} ${unit}, ${mealType})`);
        
        // Close the food selection modal (this clears selectedFood)
        this.closeFoodSelectionModal();
    }
    
    /**
     * Start barcode scanner with mobile optimization
     */
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
            
            const video = document.getElementById('modal-barcode-video');
            const scannerContainer = document.getElementById('modal-barcode-scanner-container');
            
            if (!video || !scannerContainer) {
                throw new Error('Video element not found');
            }
            
            video.srcObject = this.stream;
            
            // Wait for video to be ready
            await new Promise((resolve) => {
                video.onloadedmetadata = () => {
                    video.play();
                    resolve();
                };
            });
            
            // Show scanner UI
            scannerContainer.classList.remove('hidden');
            
            // Start barcode detection
            this.startBarcodeDetection();
            
            this.showToast('Camera started - point at barcode to scan', 'success');
            this.logActivity('Barcode scanner started');
            
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
            
            this.showToast(errorMessage, 'error');
        }
    }

    /**
     * Start barcode detection using QuaggaJS
     */
    startBarcodeDetection() {
        if (!this.stream) return;
        
        const video = document.getElementById('modal-barcode-video');
        
        // Check if QuaggaJS is available
        if (typeof Quagga === 'undefined') {
            console.warn('QuaggaJS not loaded, falling back to basic camera');
            this.updateScanningIndicator();
            this.showToast('Barcode scanning not available. Use manual entry.', 'warning');
            return;
        }
        
        // Configure QuaggaJS with mobile-optimized settings and error protection
        try {
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
                numOfWorkers: Math.min(navigator.hardwareConcurrency || 2, 4), // Limit workers to prevent issues
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
                locate: true,
                // Add debug settings to help isolate issues
                debug: {
                    drawBoundingBox: false,
                    showFrequency: false,
                    drawScanline: false,
                    showPattern: false
                }
            }, (err) => {
                if (err) {
                    console.error('Quagga initialization failed:', err);
                    this.showToast('Failed to initialize barcode scanner', 'error');
                    return;
                }
                
                console.log('Quagga initialized successfully');
                
                try {
                    Quagga.start();
                    // Add visual scanning indicator
                    this.updateScanningIndicator();
                } catch (startError) {
                    console.error('Quagga start failed:', startError);
                    this.showToast('Failed to start barcode scanner', 'error');
                }
            });
        } catch (initError) {
            console.error('Quagga init setup failed:', initError);
            this.showToast('Barcode scanner initialization error', 'error');
        }
        
        // Listen for barcode detection with improved error handling
        Quagga.onDetected((result) => {
            try {
                // Validate result structure
                if (!result || !result.codeResult) {
                    console.warn('Invalid detection result structure:', result);
                    return;
                }
                
                const code = result.codeResult.code;
                const format = result.codeResult.format || 'unknown';
                
                if (!code) {
                    console.warn('No barcode code detected in result');
                    return;
                }
                
                console.log('Barcode detected:', code, 'Format:', format);
                
                // Validate barcode format and length
                if (this.isValidBarcode(code, format)) {
                    // Stop scanning and search for the product
                    this.stopBarcodeScanner();
                    this.searchBarcodeByCode(code);
                } else {
                    console.log('Invalid barcode format, continuing scan...');
                }
            } catch (error) {
                console.error('Error processing barcode detection:', error);
            }
        });
        
        // Listen for processing with improved visual feedback
        Quagga.onProcessed((result) => {
            try {
                const drawingCanvas = Quagga.canvas?.dom?.overlay;
                if (!drawingCanvas) return;
                
                const drawingCtx = drawingCanvas.getContext('2d');
                if (!drawingCtx) return;
                
                if (result && typeof result === 'object') {
                    if (result.boxes && Array.isArray(result.boxes)) {
                        drawingCtx.clearRect(0, 0, parseInt(drawingCanvas.getAttribute("width")), parseInt(drawingCanvas.getAttribute("height")));
                        result.boxes.filter((box) => box && box !== result.box).forEach((box) => {
                            if (box && typeof box === 'object') {
                                Quagga.ImageDebug.drawPath(box, { x: 0, y: 1 }, drawingCtx, { color: "green", lineWidth: 2 });
                            }
                        });
                    }
                    
                    if (result.box && typeof result.box === 'object') {
                        Quagga.ImageDebug.drawPath(result.box, { x: 0, y: 1 }, drawingCtx, { color: "blue", lineWidth: 2 });
                    }
                    
                    if (result.codeResult && result.codeResult.code && result.line && typeof result.line === 'object') {
                        Quagga.ImageDebug.drawPath(result.line, { x: 'x', y: 'y' }, drawingCtx, { color: 'red', lineWidth: 3 });
                    }
                }
            } catch (error) {
                console.warn('Error in Quagga onProcessed callback:', error);
            }
        });
    }
    
    /**
     * Validate barcode format and length
     */
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
    
    /**
     * Update scanning visual indicator
     */
    updateScanningIndicator() {
        // Add a visual indicator that scanning is active
        const video = document.getElementById('modal-barcode-video');
        if (video && !video.classList.contains('scanning-active')) {
            video.classList.add('scanning-active');
            video.style.border = '3px solid #16a34a';
            video.style.boxShadow = '0 0 20px rgba(22, 163, 74, 0.3)';
        }
    }
    
    /**
     * Search for food by detected barcode
     */
    async searchBarcodeByCode(barcode) {
        const resultsContainer = document.getElementById('modal-barcode-results');
        
        if (!resultsContainer) return;
        
        try {
            this.showLoading(resultsContainer);
            this.showToast(`Searching for barcode: ${barcode}`, 'info');
            
            const response = await fetch('/api/search-food-barcode', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ barcode })
            });
            
            const data = await response.json();
            
            if (data.success && data.result) {
                this.displaySearchResults([data.result], resultsContainer);
                this.showToast('Product found! Click to add to your log.', 'success');
                this.logActivity(`Barcode search successful: ${barcode}`);
            } else {
                this.showBarcodeNotFound(resultsContainer, barcode);
                this.showToast('Product not found. You can add it to the database!', 'warning');
            }
        } catch (error) {
            console.error('Barcode search error:', error);
            this.showError(resultsContainer, 'Network error occurred');
            this.showToast('Search failed. Check your connection.', 'error');
        }
    }
    
    /**
     * Stop barcode scanner
     */
    stopBarcodeScanner() {
        try {
            // Stop QuaggaJS safely
            if (typeof Quagga !== 'undefined') {
                console.log('🛑 Stopping Quagga scanner');
                Quagga.stop();
                
                // Clear any remaining event listeners
                Quagga.offDetected();
                Quagga.offProcessed();
            }
        } catch (quaggaError) {
            console.warn('Error stopping Quagga:', quaggaError);
        }
        
        try {
            // Stop camera stream
            if (this.stream) {
                this.stream.getTracks().forEach(track => {
                    try {
                        track.stop();
                    } catch (trackError) {
                        console.warn('Error stopping camera track:', trackError);
                    }
                });
                this.stream = null;
            }
        } catch (streamError) {
            console.warn('Error stopping camera stream:', streamError);
        }
        
        // Reset video styling
        const video = document.getElementById('modal-barcode-video');
        if (video) {
            video.classList.remove('scanning-active');
            video.style.border = '';
            video.style.boxShadow = '';
            video.srcObject = null;
        }
        
        // Hide scanner UI
        const scannerContainer = document.getElementById('modal-barcode-scanner-container');
        if (scannerContainer) {
            scannerContainer.classList.add('hidden');
        }
        
        this.logActivity('Barcode scanner stopped');
    }
    
    /**
     * Search food by barcode (manual entry)
     */
    async searchBarcode() {
        const barcodeInput = document.getElementById('modal-manual-barcode');
        const resultsContainer = document.getElementById('modal-barcode-results');
        
        if (!barcodeInput || !resultsContainer) return;
        
        const barcode = barcodeInput.value.trim();
        if (!barcode) {
            this.showToast('Please enter a barcode', 'warning');
            return;
        }
        
        await this.searchBarcodeByCode(barcode);
    }
    
    /**
     * Add manual entry to food log
     */
    async addManualEntry() {
        const form = {
            name: document.getElementById('modal-manual-name')?.value?.trim(),
            brand: document.getElementById('modal-manual-brand')?.value?.trim(),
            calories: parseFloat(document.getElementById('modal-manual-calories')?.value) || 0,
            protein: parseFloat(document.getElementById('modal-manual-protein')?.value) || 0,
            carbs: parseFloat(document.getElementById('modal-manual-carbs')?.value) || 0,
            fat: parseFloat(document.getElementById('modal-manual-fat')?.value) || 0,
            timeOfDay: document.getElementById('modal-manual-time-of-day')?.value || 'snack',
            amount: parseFloat(document.getElementById('modal-manual-amount')?.value) || 1,
            unit: document.getElementById('modal-manual-unit')?.value || 'g'
        };
        
        // Validation
        if (!form.name) {
            this.showToast('Please enter a food name', 'warning');
            return;
        }
        
        if (form.calories <= 0) {
            this.showToast('Please enter calories', 'warning');
            return;
        }
        
        // Create food item object
        const foodItem = {
            name: form.name,
            brand: form.brand,
            calories: form.calories,
            protein: form.protein,
            carbs: form.carbs,
            fat: form.fat,
            serving_size: form.amount,
            serving_unit: form.unit
        };
        
        await this.addFoodToLog(foodItem, form.timeOfDay);
        
        // Clear form
        this.clearManualForm();
        
        this.logActivity(`Manual food entry added: ${form.name}`);
    }
    
    /**
     * Add food item to the log
     */
    async addFoodToLog(foodItem, timeOfDay = 'snack', date = null) {
        // Use dashboard's selected date if available, otherwise fall back to journal's date
        let logDate = date;
        if (!logDate && window.dashboardManager && window.dashboardManager.currentDate) {
            logDate = window.dashboardManager.currentDate.toISOString().split('T')[0];
        } else if (!logDate) {
            logDate = this.currentDate;
        }
        
        try {
            const response = await fetch('/api/food-log', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: foodItem.name,
                    brand: foodItem.brand || '',
                    calories: foodItem.calories || 0,
                    protein: foodItem.protein || 0,
                    carbs: foodItem.carbs || 0,
                    fat: foodItem.fat || 0,
                    serving_size: foodItem.serving_size || 100,
                    original_amount: foodItem.serving_size || 100,
                    original_unit: foodItem.serving_unit || 'g',
                    quantity: 1,
                    time_of_day: timeOfDay,
                    date: logDate
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Food added to log successfully!', 'success');
                this.refreshFoodLog();
                
                // Clear search fields before closing modal
                this.clearSearchFields();
                this.closeModal();
            } else {
                this.showToast(data.message || 'Failed to add food to log', 'error');
            }
        } catch (error) {
            console.error('Add food error:', error);
            this.showToast('Network error occurred', 'error');
        }
    }
    
    /**
     * Refresh the food log display
     */
    async refreshFoodLog() {
        // Trigger dashboard refresh if available - use optimized version for better performance
        if (window.dashboardManager) {
            if (typeof window.dashboardManager.loadDashboardDataOptimized === 'function') {
                await window.dashboardManager.loadDashboardDataOptimized();
            } else if (typeof window.dashboardManager.loadDashboardData === 'function') {
                await window.dashboardManager.loadDashboardData();
            }
        }
        
        // Macro chart and all dashboard components are updated as part of loadDashboardData()
    }
    
    /**
     * Clear manual entry form
     */
    clearManualForm() {
        const inputs = [
            'modal-manual-name', 'modal-manual-brand', 'modal-manual-calories',
            'modal-manual-protein', 'modal-manual-carbs', 'modal-manual-fat',
            'modal-manual-amount'
        ];
        
        inputs.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.value = '';
        });
        
        // Reset to default values
        const amountInput = document.getElementById('modal-manual-amount');
        if (amountInput) amountInput.value = '1';
    }
    
    /**
     * Clear search fields in the food journal
     */
    clearSearchFields() {
        // Clear the main search input
        const searchInput = document.getElementById('modal-food-search');
        if (searchInput) {
            searchInput.value = '';
        }
        
        // Clear barcode input (correct ID)
        const barcodeInput = document.getElementById('modal-manual-barcode');
        if (barcodeInput) {
            barcodeInput.value = '';
        }
        
        // Clear search results
        const resultsContainer = document.getElementById('modal-search-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = '';
        }
        
        // Clear barcode results (find correct container)
        const barcodeResultsContainer = document.getElementById('modal-barcode-results');
        if (barcodeResultsContainer) {
            barcodeResultsContainer.innerHTML = '';
        }
        
        // Reset selected food
        this.selectedFood = null;
        
        // Log for debugging
        console.log('🧹 Search fields cleared');
    }

    /**
     * Show loading state
     */
    showLoading(container) {
        container.innerHTML = `
            <div class="flex items-center justify-center py-8">
                <div class="loading-spinner"></div>
                <span class="ml-3 text-gray-600">Searching...</span>
            </div>
        `;
    }
    
    /**
     * Show error message
     */
    showError(container, message) {
        container.innerHTML = `
            <div class="text-center py-8 text-red-500">
                <svg class="w-12 h-12 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                </svg>
                <p>${message}</p>
            </div>
        `;
    }
    
    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        // Use existing toast system if available
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            // Fallback alert
            alert(message);
        }
    }
    
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Log activity for debugging/analytics
     */
    logActivity(activity) {
        console.log(`[FoodJournal] ${activity}`);
    }
    
    /**
     * Update current date
     */
    setCurrentDate(date) {
        this.currentDate = date;
        
        // Update date inputs in modal
        const dateInputs = this.modal?.querySelectorAll('input[type="date"]');
        dateInputs?.forEach(input => input.value = date);
    }
    
    /**
     * Get current statistics
     */
    getStats() {
        return {
            searchCacheSize: this.searchCache.size,
            currentTab: this.currentTab,
            isModalOpen: this.isModalOpen(),
            currentDate: this.currentDate
        };
    }

    /**
     * Create "Add Product to Database" button HTML
     */
    createAddProductButton() {
        return `
            <div class="mt-4 p-3 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50">
                <div class="text-center">
                    <div class="inline-flex items-center justify-center w-10 h-10 bg-ki-green-100 rounded-full mb-2">
                        <svg class="w-5 h-5 text-ki-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path>
                        </svg>
                    </div>
                    <h4 class="text-sm font-medium text-gray-900 mb-1">Can't find your product?</h4>
                    <p class="text-xs text-gray-600 mb-3">Help the community by adding it to the database</p>
                    <button onclick="foodJournal.showAddProductModal()" 
                            class="bg-ki-green-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-ki-green-700 transition-colors touch-manipulation">
                        Add to Database
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Show barcode not found with add product option
     */
    showBarcodeNotFound(container, barcode) {
        container.innerHTML = `
            <div class="text-center py-6">
                <div class="inline-flex items-center justify-center w-12 h-12 bg-yellow-100 rounded-full mb-3">
                    <svg class="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.732-.833-2.464 0L4.35 16.5c-.77.833.192 2.5 1.732 2.5z"></path>
                    </svg>
                </div>
                <h3 class="text-base font-medium text-gray-900 mb-2">Product Not Found</h3>
                <p class="text-sm text-gray-600 mb-3">Barcode: <code class="bg-gray-100 px-2 py-1 rounded text-xs">${this.escapeHtml(barcode)}</code></p>
                <p class="text-xs text-gray-500 mb-4">Not in database yet - help add it!</p>
                
                <button onclick="foodJournal.showAddProductModal('${this.escapeHtml(barcode)}')" 
                        class="bg-ki-green-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-ki-green-700 transition-colors touch-manipulation">
                    Add to Database
                </button>
            </div>
        `;
    }

    /**
     * Show the add product modal
     */
    showAddProductModal(barcode = '') {
        const modal = document.getElementById('add-product-modal');
        const barcodeInput = document.getElementById('product-barcode');
        
        if (barcode) {
            barcodeInput.value = barcode;
        }
        
        // Clear the form
        document.getElementById('add-product-form').reset();
        if (barcode) {
            barcodeInput.value = barcode; // Restore barcode after reset
        }
        
        modal.classList.remove('hidden');
        
        // Setup event listeners if not already done
        this.setupAddProductModalEvents();
    }

    /**
     * Setup event listeners for add product modal
     */
    setupAddProductModalEvents() {
        // Prevent duplicate event listeners
        if (this.addProductEventsSetup) return;
        this.addProductEventsSetup = true;

        const modal = document.getElementById('add-product-modal');
        const closeBtn = document.getElementById('close-add-product-modal');
        const cancelBtn = document.getElementById('cancel-add-product');
        const submitBtn = document.getElementById('submit-add-product');

        closeBtn.addEventListener('click', () => this.closeAddProductModal());
        cancelBtn.addEventListener('click', () => this.closeAddProductModal());
        submitBtn.addEventListener('click', () => this.submitProductToDatabase());

        // Close on backdrop click
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeAddProductModal();
            }
        });

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                this.closeAddProductModal();
            }
        });
    }

    /**
     * Close the add product modal
     */
    closeAddProductModal() {
        const modal = document.getElementById('add-product-modal');
        modal.classList.add('hidden');
    }

    /**
     * Submit product data to Open Food Facts database
     */
    async submitProductToDatabase() {
        const form = document.getElementById('add-product-form');
        const formData = new FormData(form);
        
        // Get image files
        const imageFiles = document.getElementById('product-images').files;
        
        // Basic validation
        const productName = formData.get('product_name');
        if (!productName || !productName.trim()) {
            this.showToast('Product name is required', 'error');
            return;
        }

        try {
            // Show loading state
            const submitBtn = document.getElementById('submit-add-product');
            const originalText = submitBtn.textContent;
            submitBtn.disabled = true;
            submitBtn.textContent = 'Submitting...';

            // Create FormData for API submission
            const apiFormData = new FormData();
            
            // Add all form fields
            for (let [key, value] of formData.entries()) {
                if (value && value.trim()) {
                    apiFormData.append(key, value);
                }
            }
            
            // Add images
            for (let i = 0; i < imageFiles.length; i++) {
                apiFormData.append('images', imageFiles[i]);
            }

            const response = await fetch('/api/add-product-to-off', {
                method: 'POST',
                body: apiFormData
            });

            const data = await response.json();

            if (data.success) {
                this.showToast('Product successfully added to Open Food Facts! Thank you!', 'success');
                this.closeAddProductModal();
                
                // If this was from a barcode search, try searching again
                const barcode = formData.get('barcode');
                if (barcode) {
                    setTimeout(() => {
                        this.searchBarcodeByCode(barcode);
                    }, 2000); // Wait 2 seconds for the database to update
                }
            } else {
                this.showToast(`Failed to add product: ${data.message || 'Unknown error'}`, 'error');
            }

        } catch (error) {
            console.error('Error adding product:', error);
            this.showToast('Network error. Please try again.', 'error');
        } finally {
            // Restore button state
            const submitBtn = document.getElementById('submit-add-product');
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    }
}

// Initialize food journal when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.foodJournal = new FoodJournal();
});