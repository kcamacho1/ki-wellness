/**
 * Add Food Form Component
 * A modular component for adding food entries to the journal
 */
class AddFoodForm {
    constructor(containerId = 'addFoodFormComponent') {
        this.containerId = containerId;
        this.currentStep = 1;
        this.currentNutritionData = null;
        this.currentFoodData = null;
        this.scanner = null;
        
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
        
        // Step 3: Review & Submit
        const backToStep2Btn = this.container.querySelector('#backToStep2Btn');
        const discardBtn = this.container.querySelector('#discardBtn');
        const submitToJournalBtn = this.container.querySelector('#submitToJournalBtn');
        
        if (backToStep2Btn) {
            backToStep2Btn.addEventListener('click', () => this.showStep(2));
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
        const closeScannerBtn = document.getElementById('closeScannerBtn');
        const useBarcodeBtn = document.getElementById('useBarcodeBtn');
        const manualBarcodeBtn = document.getElementById('manualBarcodeBtn');
        
        if (startScannerBtn) {
            startScannerBtn.addEventListener('click', () => this.startBarcodeScanner());
        }
        if (stopScannerBtn) {
            stopScannerBtn.addEventListener('click', () => this.stopBarcodeScanner());
        }
        if (closeScannerBtn) {
            closeScannerBtn.addEventListener('click', () => this.closeBarcodeScanner());
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
        const steps = ['step1ChooseMethod', 'step2FoodInput', 'step3ReviewSubmit'];
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
            case 3: return 'ReviewSubmit';
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
        const scannerModal = document.getElementById('scannerModal');
        if (scannerModal) {
            scannerModal.classList.remove('hidden');
        }
    }
    
    closeBarcodeScanner() {
        this.stopBarcodeScanner();
        const scannerModal = document.getElementById('scannerModal');
        if (scannerModal) {
            scannerModal.classList.add('hidden');
        }
    }
    
    startBarcodeScanner() {
        if (typeof Quagga === 'undefined') {
            this.showError('Barcode scanner library not loaded');
            return;
        }
        
        const startBtn = document.getElementById('startScannerBtn');
        const stopBtn = document.getElementById('stopScannerBtn');
        const status = document.getElementById('scannerStatus');
        
        if (startBtn) startBtn.classList.add('hidden');
        if (stopBtn) stopBtn.classList.remove('hidden');
        if (status) status.textContent = 'Starting camera...';
        
        Quagga.init({
            inputStream: {
                name: "Live",
                type: "LiveStream",
                target: document.querySelector('#scannerVideo'),
                constraints: {
                    width: { min: 640 },
                    height: { min: 480 },
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
                readers: ["ean_reader", "ean_8_reader", "code_128_reader", "code_39_reader", "upc_reader"]
            },
            locate: true
        }, (err) => {
            if (err) {
                console.error('Scanner initialization failed:', err);
                this.showError('Scanner initialization failed. Please try again.');
                return;
            }
            
            if (status) status.textContent = 'Camera ready - scan barcode';
            Quagga.start();
        });
        
        Quagga.onDetected((result) => {
            const barcode = result.codeResult.code;
            this.handleBarcodeDetected(barcode);
        });
        
        this.scanner = Quagga;
    }
    
    stopBarcodeScanner() {
        if (this.scanner) {
            this.scanner.stop();
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
            const response = await fetch('/food-journal/search-barcode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ barcode: barcode })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentFoodData = data.data;
                this.closeBarcodeScanner();
                this.showStep(3);
                this.populateNutritionData(data.data);
            } else {
                this.showError('No food found for this barcode. Please try manual entry.');
            }
        } catch (error) {
            console.error('Error searching barcode:', error);
            this.showError('Error searching barcode. Please try again.');
        }
    }
    
    async handleSearchNutrition() {
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
            return;
        }
        
        try {
            const response = await fetch('/food-journal/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(foodData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentFoodData = { ...foodData, ...data.data };
                this.currentNutritionData = data.data;
                this.showStep(3);
                this.populateNutritionData(this.currentFoodData);
            } else {
                this.showError('No nutritional data found. You can still add the food without nutrition info.');
                // Still proceed to step 3 with basic data
                this.currentFoodData = foodData;
                this.currentNutritionData = null;
                this.showStep(3);
                this.populateNutritionData(this.currentFoodData);
            }
        } catch (error) {
            console.error('Error searching nutrition:', error);
            this.showError('Error searching nutrition. Please try again.');
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
                    element.textContent = this.currentNutritionData[field].toFixed(1);
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
    
    async handleSubmitToJournal() {
        if (!this.currentFoodData) {
            this.showError('No food data to submit');
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
            consumed_at: new Date().toISOString(),
            browser_timezone: Intl.DateTimeFormat().resolvedOptions().timeZone
        };
        
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
                this.showSuccess('Food entry added successfully!');
                this.reset();
                this.close();
                
                // Trigger refresh of food journal if callback exists
                if (window.refreshFoodJournal) {
                    window.refreshFoodJournal();
                }
            } else {
                this.showError('Error adding food entry: ' + (data.message || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error submitting to journal:', error);
            this.showError('Error submitting to journal. Please try again.');
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
        if (this.container) {
            this.container.classList.add('hidden');
        }
        this.closeBarcodeScanner();
    }
    
    showError(message) {
        // Simple error display - can be enhanced with a proper modal
        alert(message);
    }
    
    showSuccess(message) {
        // Simple success display - can be enhanced with a proper modal
        alert(message);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AddFoodForm;
} else {
    window.AddFoodForm = AddFoodForm;
}
