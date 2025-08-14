/**
 * Add Food Form Component
 * A modular component for adding food entries to the journal
 */
class AddFoodForm {
    constructor(containerId = 'addFoodFormComponent', targetDate = null) {
        this.containerId = containerId;
        this.currentStep = 1;
        this.currentNutritionData = null;
        this.currentFoodData = null;
        this.scanner = null;
        this.targetDate = targetDate || new Date(); // Default to current date
        
        this.init();
    }
    
    init() {
        this.container = document.getElementById(this.containerId);
        if (!this.container) {
            console.error(`AddFoodForm: Container with ID '${this.containerId}' not found`);
            return;
        }
        
        this.setupEventListeners();
        this.showStep(1);
    }
    
    setupEventListeners() {
        // Step 1: Choose Method
        const scanBarcodeBtn = this.container.querySelector('#scanBarcodeBtn');
        const manualEntryBtn = this.container.querySelector('#manualEntryBtn');
        const closeAddFoodForm = this.container.querySelector('#closeAddFoodForm');
        
        if (scanBarcodeBtn) {
            scanBarcodeBtn.addEventListener('click', () => this.handleScanBarcode());
        }
        if (manualEntryBtn) {
            manualEntryBtn.addEventListener('click', () => this.handleManualEntry());
        }
        if (closeAddFoodForm) {
            closeAddFoodForm.addEventListener('click', () => this.close());
        }
        
        // Step 2: Food Input
        const backToStep1Btn = this.container.querySelector('#backToStep1Btn');
        const searchNutritionBtn = this.container.querySelector('#searchNutritionBtn');
        
        if (backToStep1Btn) {
            backToStep1Btn.addEventListener('click', () => this.showStep(1));
        }
        if (searchNutritionBtn) {
            searchNutritionBtn.addEventListener('click', () => this.handleSearchNutrition());
        }
        
        // Step 3: Food Selection
        const backToStep2FromSelectionBtn = this.container.querySelector('#backToStep2FromSelectionBtn');
        if (backToStep2FromSelectionBtn) {
            backToStep2FromSelectionBtn.addEventListener('click', () => this.showStep(2));
        }
        
        // Step 4: Review & Submit
        const backToStep2Btn = this.container.querySelector('#backToStep2Btn');
        const discardBtn = this.container.querySelector('#discardBtn');
        const submitToJournalBtn = this.container.querySelector('#submitToJournalBtn');
        
        if (backToStep2Btn) {
            backToStep2Btn.addEventListener('click', () => this.showStep(3));
        }
        if (discardBtn) {
            discardBtn.addEventListener('click', () => this.discard());
        }
        if (submitToJournalBtn) {
            submitToJournalBtn.addEventListener('click', () => this.handleSubmitToJournal());
        }
        
        // Barcode Scanner
        this.setupBarcodeScannerListeners();
    }
    
    setupBarcodeScannerListeners() {
        const startScannerBtn = document.getElementById('startScannerBtn');
        const stopScannerBtn = document.getElementById('stopScannerBtn');
        const useBarcodeBtn = document.getElementById('useBarcodeBtn');
        const manualBarcodeBtn = document.getElementById('manualBarcodeBtn');
        
        if (startScannerBtn) {
            startScannerBtn.addEventListener('click', () => this.startBarcodeScanner());
        }
        if (stopScannerBtn) {
            stopScannerBtn.addEventListener('click', () => this.stopBarcodeScanner());
        }
        if (useBarcodeBtn) {
            useBarcodeBtn.addEventListener('click', () => this.useScannedBarcode());
        }
        if (manualBarcodeBtn) {
            manualBarcodeBtn.addEventListener('click', () => this.handleManualBarcode());
        }
    }
    
    showStep(step) {
        this.currentStep = step;
        
        // Hide all steps
        const steps = ['step1ChooseMethod', 'step2FoodInput', 'step3FoodSelection', 'step4ReviewSubmit'];
        steps.forEach(stepId => {
            const stepElement = this.container.querySelector(`#${stepId}`);
            if (stepElement) {
                stepElement.classList.add('hidden');
            }
        });
        
        // Show current step
        const currentStepElement = this.container.querySelector(`#step${step}${this.getStepName(step)}`);
        if (currentStepElement) {
            currentStepElement.classList.remove('hidden');
        }
    }
    
    getStepName(step) {
        switch (step) {
            case 1: return 'ChooseMethod';
            case 2: return 'FoodInput';
            case 3: return 'FoodSelection';
            case 4: return 'ReviewSubmit';
            default: return 'ChooseMethod';
        }
    }
    
    handleScanBarcode() {
        this.showStep(2);
        this.showBarcodeSection();
        this.openBarcodeScanner();
    }
    
    handleManualEntry() {
        this.showStep(2);
        this.showManualEntrySection();
    }
    
    showBarcodeSection() {
        const barcodeSection = this.container.querySelector('#barcodeSection');
        const manualEntrySection = this.container.querySelector('#manualEntrySection');
        
        if (barcodeSection) barcodeSection.classList.remove('hidden');
        if (manualEntrySection) manualEntrySection.classList.add('hidden');
    }
    
    showManualEntrySection() {
        const barcodeSection = this.container.querySelector('#barcodeSection');
        const manualEntrySection = this.container.querySelector('#manualEntrySection');
        
        if (barcodeSection) barcodeSection.classList.add('hidden');
        if (manualEntrySection) manualEntrySection.classList.remove('hidden');
    }
    
    openBarcodeScanner() {
        // The barcode scanner is now integrated into the main form
        // No need to open a separate modal
        console.log('Barcode scanner section is already visible');
    }
    
    closeBarcodeScanner() {
        this.stopBarcodeScanner();
        // The barcode scanner is integrated, so we don't need to hide a separate modal
        console.log('Barcode scanner stopped');
    }
    
    startBarcodeScanner() {
        console.log('Starting barcode scanner...');
        
        if (typeof Quagga === 'undefined') {
            console.error('Quagga library not loaded');
            this.showError('Barcode scanner library not loaded. Please refresh the page and try again.');
            return;
        }
        
        const startBtn = document.getElementById('startScannerBtn');
        const stopBtn = document.getElementById('stopScannerBtn');
        const status = document.getElementById('scannerStatus');
        const videoContainer = document.querySelector('#scannerVideo');
        
        if (startBtn) startBtn.classList.add('hidden');
        if (stopBtn) stopBtn.classList.remove('hidden');
        if (status) status.textContent = 'Starting camera...';
        
        // Check if we have camera access
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            this.showError('Camera access not available. Please use a modern browser with camera support.');
            this.stopBarcodeScanner();
            return;
        }
        
        // Test camera access first
        navigator.mediaDevices.getUserMedia({ video: true })
            .then(stream => {
                console.log('Camera access granted');
                stream.getTracks().forEach(track => track.stop()); // Stop test stream
                
                // Initialize Quagga
                Quagga.init({
                    inputStream: {
                        name: "Live",
                        type: "LiveStream",
                        target: videoContainer,
                        constraints: {
                            width: { min: 320, ideal: 640, max: 1280 },
                            height: { min: 240, ideal: 480, max: 720 },
                            facingMode: "environment"
                        }
                    },
                    locator: {
                        patchSize: "medium",
                        halfSample: true
                    },
                    numOfWorkers: 2,
                    frequency: 10,
                    decoder: {
                        readers: ["ean_reader", "ean_8_reader", "code_128_reader", "code_39_reader", "upc_reader", "upc_e_reader"]
                    },
                    locate: true
                }, (err) => {
                    if (err) {
                        console.error('Scanner initialization failed:', err);
                        this.showError('Scanner initialization failed: ' + err.message);
                        this.stopBarcodeScanner();
                        return;
                    }
                    
                    console.log('Scanner initialized successfully');
                    if (status) status.textContent = 'Camera ready - scan barcode';
                    Quagga.start();
                });
                
                // Set up detection handler
                Quagga.onDetected((result) => {
                    console.log('Barcode detected:', result);
                    const barcode = result.codeResult.code;
                    this.handleBarcodeDetected(barcode);
                });
                
                // Set up error handler
                Quagga.onProcessed((result) => {
                    if (result) {
                        console.log('Processing barcode...');
                    }
                });
                
                this.scanner = Quagga;
            })
            .catch(err => {
                console.error('Camera access denied:', err);
                this.showError('Camera access denied. Please allow camera access and try again.');
                this.stopBarcodeScanner();
            });
    }
    
    stopBarcodeScanner() {
        console.log('Stopping barcode scanner...');
        
        if (this.scanner) {
            try {
                this.scanner.stop();
                console.log('Scanner stopped successfully');
            } catch (error) {
                console.error('Error stopping scanner:', error);
            }
            this.scanner = null;
        }
        
        const startBtn = document.getElementById('startScannerBtn');
        const stopBtn = document.getElementById('stopScannerBtn');
        const status = document.getElementById('scannerStatus');
        
        if (startBtn) startBtn.classList.remove('hidden');
        if (stopBtn) stopBtn.classList.add('hidden');
        if (status) status.textContent = 'Scanner stopped';
    }
    
    handleBarcodeDetected(barcode) {
        const barcodeValue = document.getElementById('barcodeValue');
        const scannedBarcode = document.getElementById('scannedBarcode');
        
        if (barcodeValue) barcodeValue.textContent = barcode;
        if (scannedBarcode) scannedBarcode.classList.remove('hidden');
        
        this.stopBarcodeScanner();
    }
    
    useScannedBarcode() {
        const barcodeValue = document.getElementById('barcodeValue');
        if (barcodeValue && barcodeValue.textContent) {
            this.searchBarcode(barcodeValue.textContent);
        }
    }
    
    handleManualBarcode() {
        const manualBarcode = document.getElementById('manualBarcode');
        if (manualBarcode && manualBarcode.value.trim()) {
            this.searchBarcode(manualBarcode.value.trim());
        } else {
            this.showError('Please enter a barcode');
        }
    }
    
    async searchBarcode(barcode) {
        try {
            const response = await fetch('/food-journal/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin', // Include session cookies
                body: JSON.stringify({ barcode: barcode })
            });
            
            // Check if response is a redirect (authentication issue)
            if (response.redirected || response.status === 302) {
                console.log('Authentication required, redirecting to login...');
                window.location.href = '/login';
                return;
            }
            
            // Check if response is not JSON (server error)
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Server returned non-JSON response:', response.status, response.statusText);
                this.showError('Server error. Please try again or contact support.');
                return;
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Check if we have multiple results to choose from
                if (data.multiple_results && data.results && data.results.length > 1) {
                    this.showFoodSelection(data.results, { food_name: 'Barcode Product', serving_size: 100, serving_unit: 'g' });
                } else if (data.data) {
                    // Single result, proceed directly to review
                    this.currentFoodData = data.data;
                    this.closeBarcodeScanner();
                    this.showStep(4);
                    this.populateNutritionData(data.data);
                } else if (data.results && data.results.length === 1) {
                    // Single result in results array
                    this.currentFoodData = data.results[0];
                    this.closeBarcodeScanner();
                    this.showStep(4);
                    this.populateNutritionData(data.results[0]);
                } else {
                    this.showError('No food found for this barcode. Please try manual entry.');
                }
            } else {
                if (data.suggest_manual && data.barcode) {
                    // For barcode searches that fail, suggest manual entry
                    this.showError(`${data.error} You can add it manually below.`);
                    // Pre-fill the barcode field for manual entry
                    const barcodeInput = document.getElementById('manualBarcode');
                    if (barcodeInput) {
                        barcodeInput.value = data.barcode;
                    }
                    // Switch to manual entry mode
                    this.showStep(2);
                } else {
                    this.showError('No food found for this barcode. Please try manual entry.');
                }
            }
        } catch (error) {
            console.error('Error searching barcode:', error);
            this.showError('Error searching barcode. Please try again.');
        }
    }
    
    async handleSearchNutrition() {
        // Show loading state
        this.showSearchLoading(true);
        
        let foodData = null;
        
        // Check if we're in manual entry mode
        const manualFoodName = this.container.querySelector('#manualFoodName');
        const manualServingSize = this.container.querySelector('#manualServingSize');
        const manualServingUnit = this.container.querySelector('#manualServingUnit');
        
        if (manualFoodName && manualServingSize && manualServingUnit) {
            const foodName = manualFoodName.value.trim();
            const servingSize = manualServingSize.value;
            const servingUnit = manualServingUnit.value;
            
            if (!foodName || !servingSize || !servingUnit) {
                this.showError('Please fill in all required fields');
                this.showSearchLoading(false);
                return;
            }
            
            foodData = {
                food_name: foodName,
                serving_size: servingSize,
                serving_unit: servingUnit
            };
        }
        
        if (!foodData) {
            this.showError('No food data available');
            this.showSearchLoading(false);
            return;
        }
        
        try {
            const response = await fetch('/food-journal/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin', // Include session cookies
                body: JSON.stringify(foodData)
            });
            
            // Check if response is a redirect (authentication issue)
            if (response.redirected || response.status === 302) {
                console.log('Authentication required, redirecting to login...');
                window.location.href = '/login';
                return;
            }
            
            // Check if response is not JSON (server error)
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Server returned non-JSON response:', response.status, response.statusText);
                this.showError('Server error. Please try again or contact support.');
                return;
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Check if we have multiple results to choose from
                if (data.multiple_results && data.results && data.results.length > 1) {
                    this.showFoodSelection(data.results, foodData);
                } else if (data.data) {
                    // Single result, proceed directly to review
                    this.currentFoodData = { ...foodData, ...data.data };
                    this.currentNutritionData = data.data;
                    this.showStep(4);
                    this.populateNutritionData(this.currentFoodData);
                } else if (data.results && data.results.length === 1) {
                    // Single result in results array
                    this.currentFoodData = { ...foodData, ...data.results[0] };
                    this.currentNutritionData = data.results[0];
                    this.showStep(4);
                    this.populateNutritionData(this.currentFoodData);
                } else {
                    this.showError('No nutritional data found. You can still add the food without nutrition info.');
                    // Still proceed to step 4 with basic data
                    this.currentFoodData = foodData;
                    this.currentNutritionData = null;
                    this.showStep(4);
                    this.populateNutritionData(this.currentFoodData);
                }
            } else {
                // Check if we have spelling suggestions
                if (data.spelling_suggestions && data.spelling_suggestions.length > 0) {
                    this.showSpellingSuggestions(data.spelling_suggestions, foodData);
                } else {
                    this.showError('No nutritional data found. You can still add the food without nutrition info.');
                    // Still proceed to step 4 with basic data
                    this.currentFoodData = foodData;
                    this.currentNutritionData = null;
                    this.showStep(4);
                    this.populateNutritionData(this.currentFoodData);
                }
            }
        } catch (error) {
            console.error('Error searching nutrition:', error);
            this.showError('Error searching nutrition. Please try again.');
        } finally {
            // Hide loading state
            this.showSearchLoading(false);
        }
    }
    
    populateNutritionData(foodData) {
        // Populate food summary
        const foodSummary = this.container.querySelector('#foodSummary');
        if (foodSummary) {
            foodSummary.innerHTML = `
                <div><strong>Food:</strong> ${foodData.food_name}</div>
                <div><strong>Serving:</strong> ${foodData.serving_size} ${foodData.serving_unit}</div>
            `;
        }
        
        // Populate nutrition values
        if (this.currentNutritionData) {
            const nutritionFields = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium'];
            nutritionFields.forEach(field => {
                const element = this.container.querySelector(`#${field}`);
                if (element && this.currentNutritionData[field] !== undefined) {
                    const value = this.currentNutritionData[field];
                    // Check if value is a number and convert to string with 1 decimal place
                    if (typeof value === 'number' && !isNaN(value)) {
                        element.textContent = value.toFixed(1);
                    } else if (value !== null && value !== undefined) {
                        // If it's a string or other type, just convert to string
                        element.textContent = String(value);
                    } else {
                        element.textContent = '-';
                    }
                }
            });
            
            // Show data source
            const dataSource = this.container.querySelector('#dataSource');
            if (dataSource && this.currentNutritionData.source) {
                dataSource.textContent = `Source: ${this.currentNutritionData.source}`;
            }
        } else {
            // Clear nutrition values if no data
            const nutritionFields = ['calories', 'protein', 'carbs', 'fat', 'fiber', 'sugar', 'sodium'];
            nutritionFields.forEach(field => {
                const element = this.container.querySelector(`#${field}`);
                if (element) {
                    element.textContent = '-';
                }
            });
            
            const dataSource = this.container.querySelector('#dataSource');
            if (dataSource) {
                dataSource.textContent = 'No data available';
            }
        }
    }
    
    showFoodSelection(results, baseFoodData) {
        this.showStep(3);
        
        const container = this.container.querySelector('#foodOptionsContainer');
        if (!container) {
            console.error('❌ Food options container not found');
            return;
        }
        
        container.innerHTML = '';
        
        // Limit to top 20 results for better UX
        const limitedResults = results.slice(0, 20);
        
        // Check if any results have spelling corrections
        const spellingCorrections = new Set();
        results.forEach(result => {
            if (result.search_query && result.search_query !== baseFoodData.food_name) {
                spellingCorrections.add(result.search_query);
            }
        });
        
        // Add result count message with spelling correction info
        const resultCountDiv = document.createElement('div');
        resultCountDiv.className = 'text-center mb-4 p-2 bg-blue-50 border border-blue-200 rounded-lg';
        
        let message = `Found ${results.length} results${results.length > 20 ? ` (showing top 20)` : ''}`;
        if (spellingCorrections.size > 0) {
            message += `<br><span class="text-xs text-green-600">✨ Found results using spelling variations: ${Array.from(spellingCorrections).join(', ')}</span>`;
        }
        
        resultCountDiv.innerHTML = `<p class="text-sm text-blue-800">${message}</p>`;
        container.appendChild(resultCountDiv);
        
        limitedResults.forEach((result, index) => {
            const optionDiv = document.createElement('div');
            optionDiv.className = 'p-3 sm:p-4 border border-gray-200 rounded-lg hover:border-forest-green hover:bg-mint-green/5 cursor-pointer transition-all duration-200';
            optionDiv.innerHTML = `
                <div class="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-2 sm:gap-0">
                    <div class="flex-1 min-w-0">
                        <h5 class="font-medium text-forest-green mb-1 text-sm sm:text-base truncate">${result.food_name}</h5>
                        ${result.brand ? `<p class="text-xs sm:text-sm text-sage-green mb-2 truncate">${result.brand}</p>` : ''}
                        <div class="grid grid-cols-2 sm:grid-cols-3 gap-1 sm:gap-2 text-xs">
                            <div><span class="font-medium">Calories:</span> ${result.calories || '-'}</div>
                            <div><span class="font-medium">Protein:</span> ${result.protein || '-'}g</div>
                            <div class="sm:col-span-1"><span class="font-medium">Fat:</span> ${result.fat || '-'}g</div>
                        </div>
                        <p class="text-xs text-gray-500 mt-1">Source: ${result.source || 'Unknown'}</p>
                    </div>
                    <button class="w-full sm:w-auto px-3 sm:px-4 py-2 bg-forest-green text-white rounded-md hover:bg-forest-green/90 focus:outline-none focus:ring-2 focus:ring-forest-green focus:ring-offset-2 transition-colors duration-200 text-sm font-medium">
                        Select
                    </button>
                </div>
            `;
            
            // Add click handler
            optionDiv.addEventListener('click', () => {
                this.selectFoodOption(result, baseFoodData);
            });
            
            container.appendChild(optionDiv);
        });
    }
    
    selectFoodOption(selectedResult, baseFoodData) {
        // Convert nutritional data based on user's serving size
        const userServingSize = baseFoodData.serving_size;
        const userServingUnit = baseFoodData.serving_unit;
        
        // Create the food data with user's serving size
        this.currentFoodData = {
            ...baseFoodData,
            food_name: selectedResult.food_name,
            brand: selectedResult.brand || ''
        };
        
        // Convert nutritional data if we have serving size info
        if (userServingSize && userServingUnit) {
            // For now, we'll use the selected result directly
            // The backend should have already converted it
            this.currentNutritionData = selectedResult;
        } else {
            this.currentNutritionData = selectedResult;
        }
        
        // Proceed to review step
        this.showStep(4);
        this.populateNutritionData(this.currentFoodData);
    }
    
    async handleSubmitToJournal() {
        // Show loading state
        this.showSubmitLoading(true);
        
        if (!this.currentFoodData) {
            this.showError('No food data to submit');
            this.showSubmitLoading(false);
            return;
        }
        
        const mealTime = this.container.querySelector('#mealTime')?.value || '';
        const mood = this.container.querySelector('#mood')?.value || '';
        const notes = this.container.querySelector('#notes')?.value || '';
        
        const entryData = {
            food_name: this.currentFoodData.food_name,
            brand: this.currentNutritionData?.brand || '',
            serving_size: this.currentFoodData.serving_size,
            serving_unit: this.currentFoodData.serving_unit,
            calories: this.currentNutritionData?.calories || null,
            protein: this.currentNutritionData?.protein || null,
            carbs: this.currentNutritionData?.carbs || null,
            fat: this.currentNutritionData?.fat || null,
            fiber: this.currentNutritionData?.fiber || null,
            sugar: this.currentNutritionData?.sugar || null,
            sodium: this.currentNutritionData?.sodium || null,
            time_of_day: mealTime,
            water_amount: 0,
            water_unit: 'ml',
            mood: mood,
            notes: notes,
            consumed_at: this.targetDate.toISOString(),
            browser_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        };
        
        try {
            const response = await fetch('/food-journal/add', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'same-origin', // Include session cookies
                body: JSON.stringify(entryData)
            });
            
            // Check if response is a redirect (authentication issue)
            if (response.redirected || response.status === 302) {
                console.log('Authentication required, redirecting to login...');
                window.location.href = '/login';
                return;
            }
            
            // Check if response is not JSON (server error)
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Server returned non-JSON response:', response.status, response.statusText);
                this.showError('Server error. Please try again or contact support.');
                return;
            }
            
            const data = await response.json();
            
            if (data.success) {
                this.showSuccess('Food entry added successfully!');
                this.reset();
                this.close();
                
                // Refresh the page to update dashboard with new data
                window.location.reload();
            } else {
                this.showError('Error adding food entry: ' + (data.message || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error submitting to journal:', error);
            this.showError('Error submitting to journal. Please try again.');
        } finally {
            // Hide loading state
            this.showSubmitLoading(false);
        }
    }
    
    discard() {
        this.reset();
        this.close();
    }
    
    reset() {
        this.currentStep = 1;
        this.currentNutritionData = null;
        this.currentFoodData = null;
        
        // Reset form fields
        const inputs = this.container.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            if (input.type === 'number') {
                input.value = '';
            } else if (input.type === 'text' || input.type === 'textarea') {
                input.value = '';
            } else if (input.tagName === 'SELECT') {
                input.selectedIndex = 0;
            }
        });
        
        this.showStep(1);
    }
    
    show() {
        if (this.container) {
            this.container.classList.remove('hidden');
        }
    }
    
    close() {
        // Close the modal
        const addFoodModal = document.getElementById('addFoodModal');
        if (addFoodModal) {
            addFoodModal.classList.add('hidden');
            document.body.style.overflow = ''; // Restore scrolling
        }
        this.closeBarcodeScanner();
        
        // Reset form to initial state
        this.reset();
    }
    
    showSearchLoading(show) {
        const button = this.container.querySelector('#searchNutritionBtn');
        const text = this.container.querySelector('#searchNutritionText');
        const spinner = this.container.querySelector('#searchNutritionSpinner');
        
        if (button && text && spinner) {
            if (show) {
                button.disabled = true;
                text.textContent = 'Searching...';
                spinner.classList.remove('hidden');
            } else {
                button.disabled = false;
                text.textContent = 'Search Nutrition →';
                spinner.classList.add('hidden');
            }
        }
    }
    
    showSubmitLoading(show) {
        const button = this.container.querySelector('#submitToJournalBtn');
        const text = this.container.querySelector('#submitToJournalText');
        const spinner = this.container.querySelector('#submitToJournalSpinner');
        
        if (button && text && spinner) {
            if (show) {
                button.disabled = true;
                text.textContent = 'Adding...';
                spinner.classList.remove('hidden');
            } else {
                button.disabled = false;
                text.textContent = 'Add to Journal';
                spinner.classList.add('hidden');
            }
        }
    }
    
    showError(message) {
        // Create a notification element
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 transform translate-x-full transition-transform duration-300';
        notification.innerHTML = `
            <div class="flex items-center space-x-2">
                <span>❌</span>
                <span>${message}</span>
            </div>
        `;
        
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

    showSpellingSuggestions(suggestions, baseFoodData) {
        this.showStep(3);
        
        const container = this.container.querySelector('#foodOptionsContainer');
        if (!container) {
            console.error('❌ Food options container not found');
            return;
        }
        
        container.innerHTML = '';
        
        // Add spelling suggestions message
        const suggestionsDiv = document.createElement('div');
        suggestionsDiv.className = 'text-center mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg';
        suggestionsDiv.innerHTML = `
            <p class="text-sm text-yellow-800 mb-2">
                <strong>No exact match found for "${baseFoodData.food_name}"</strong>
            </p>
            <p class="text-xs text-yellow-700 mb-3">
                Did you mean one of these?
            </p>
        `;
        container.appendChild(suggestionsDiv);
        
        // Create suggestion buttons
        suggestions.forEach(suggestion => {
            const suggestionDiv = document.createElement('div');
            suggestionDiv.className = 'mb-2';
            
            const button = document.createElement('button');
            button.type = 'button';
            button.className = 'w-full p-3 text-left border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors duration-200';
            button.innerHTML = `
                <div class="font-medium text-gray-900">${suggestion}</div>
                <div class="text-xs text-gray-500">Click to search for this instead</div>
            `;
            
            button.addEventListener('click', () => {
                // Update the search input and search again
                const searchInput = this.container.querySelector('#foodName');
                if (searchInput) {
                    searchInput.value = suggestion;
                }
                this.handleSearchNutrition();
            });
            
            suggestionDiv.appendChild(button);
            container.appendChild(suggestionDiv);
        });
        
        // Add option to continue with original search
        const continueDiv = document.createElement('div');
        continueDiv.className = 'mt-4 p-3 border border-gray-200 rounded-lg';
        
        const continueButton = document.createElement('button');
        continueButton.type = 'button';
        continueButton.className = 'w-full p-3 text-left text-gray-600 hover:bg-gray-50 transition-colors duration-200';
        continueButton.innerHTML = `
            <div class="font-medium">Continue with "${baseFoodData.food_name}"</div>
            <div class="text-xs text-gray-500">Add without nutritional data</div>
        `;
        
        continueButton.addEventListener('click', () => {
            this.currentFoodData = baseFoodData;
            this.currentNutritionData = null;
            this.showStep(4);
            this.populateNutritionData(this.currentFoodData);
        });
        
        continueDiv.appendChild(continueButton);
        container.appendChild(continueDiv);
    }
    
    showSuccess(message) {
        // Create a notification element
        const notification = document.createElement('div');
        notification.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 transform translate-x-full transition-transform duration-300';
        notification.innerHTML = `
            <div class="flex items-center space-x-2">
                <span>✅</span>
                <span>${message}</span>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }, 3000);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AddFoodForm;
} else {
    window.AddFoodForm = AddFoodForm;
}
