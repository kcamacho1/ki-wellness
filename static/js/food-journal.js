/**
 * FoodJournal - A modular class for managing food journal functionality
 * Handles food search, barcode scanning, manual entry, and logging
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
        
        this.modal.classList.add('hide');
        
        setTimeout(() => {
            this.modal.classList.add('hidden');
            this.modal.classList.remove('show', 'hide');
            document.body.style.overflow = '';
            this.stopBarcodeScanner();
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
                    <p class="text-xs">Try a different search term</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = results.map(item => `
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
        
        this.logActivity('Food selection modal closed');
    }
    
    /**
     * Confirm food selection and add to log
     */
    async confirmFoodSelection() {
        if (!this.selectedFood) {
            this.showToast('No food item selected', 'error');
            return;
        }
        
        // Get form values
        const amount = parseFloat(document.getElementById('food-selection-amount').value) || 1;
        const unit = document.getElementById('food-selection-unit').value || 'serving';
        const mealType = document.getElementById('food-selection-meal-type').value || 'snack';
        
        // Validate inputs
        if (amount <= 0) {
            this.showToast('Please enter a valid amount', 'warning');
            return;
        }
        
        // Calculate nutrition values based on serving size
        const multiplier = amount; // For now, treat amount as direct multiplier
        
        const adjustedFoodItem = {
            ...this.selectedFood,
            calories: (this.selectedFood.calories || 0) * multiplier,
            protein: (this.selectedFood.protein || 0) * multiplier,
            carbs: (this.selectedFood.carbs || 0) * multiplier,
            fat: (this.selectedFood.fat || 0) * multiplier,
            serving_size: (this.selectedFood.serving_size || 100) * multiplier,
            serving_unit: unit
        };
        
        // Add to log with selected parameters
        await this.addFoodToLog(adjustedFoodItem, mealType);
        
        // Close the food selection modal
        this.closeFoodSelectionModal();
        
        this.logActivity(`Food confirmed and added: ${this.selectedFood.name} (${amount} ${unit}, ${mealType})`);
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
                this.showToast('Failed to initialize barcode scanner', 'error');
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
                this.searchBarcodeByCode(code);
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
                this.showError(resultsContainer, 'Food not found for this barcode');
                this.showToast('Product not found. Try manual entry.', 'warning');
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
        const logDate = date || this.currentDate;
        
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
        // Trigger dashboard refresh if available
        if (window.dashboardManager && typeof window.dashboardManager.loadDashboardData === 'function') {
            await window.dashboardManager.loadDashboardData();
        }
        
        // Macro chart is updated as part of loadDashboardData()
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
}

// Initialize food journal when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.foodJournal = new FoodJournal();
});