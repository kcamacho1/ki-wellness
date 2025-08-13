/**
 * Ki Wellness - Profile Module
 * ===========================
 * 
 * Modular JavaScript functions for profile management
 * Reuses existing components and follows established patterns
 * 
 * Author: Ki Wellness Team
 * Version: 2.0
 */

// Profile Management Class
class ProfileManager {
    constructor() {
        this.form = null;
        this.saveButton = null;
        this.saveButtonText = null;
        this.saveButtonLoading = null;
        this.saveStatus = null;
        this.saveMessage = null;
        this.autoSaveTimeout = null;
        this.autoSaveDelay = 2000; // 2 seconds
        this.currentHeightUnit = 'cm'; // Default to centimeters
        this.isToggling = false; // Prevent multiple rapid toggles
        this.heightUnitInitialized = false; // Track if height unit has been initialized
        this.savedHeightCm = null; // Store saved cm value
        this.savedHeightFt = null; // Store saved ft value
        this.isSectionToggling = false; // Prevent multiple rapid section toggles
    }

    /**
     * Initialize the profile manager
     * @param {string} formId - ID of the profile form
     */
    init(formId = 'profileForm') {
        this.form = document.getElementById(formId);
        
        this.saveButton = document.getElementById('saveButton');
        this.saveButtonText = document.getElementById('saveButtonText');
        this.saveButtonLoading = document.getElementById('saveButtonLoading');
        this.saveStatus = document.getElementById('saveStatus');
        this.saveMessage = document.getElementById('saveMessage');

        if (this.form) {
            this.setupEventListeners();
            this.loadProfileData();
        } else {
            console.error(`ProfileManager.init: Form with id '${formId}' not found!`);
        }
    }

    /**
     * Setup event listeners for form interactions
     */
    setupEventListeners() {
        // Form submission
        this.form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.saveProfile(true);
        });

        // Auto-save on input changes (excluding section content to prevent interference)
        const inputs = this.form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            // Skip auto-save for section content inputs to prevent interference with toggles
            const isSectionInput = input.closest('#mindContent, #bodyContent, #spiritContent');
            if (!isSectionInput) {
                input.addEventListener('input', () => {
                    this.scheduleAutoSave();
                });
            }
        });

        // Height field specific listeners
        const heightInput = document.getElementById('height_input');
        const heightUnitToggle = document.getElementById('height_unit_toggle');

        if (heightInput) {
            heightInput.addEventListener('input', () => {
                console.log(`heightInput input event: currentHeightUnit = ${this.currentHeightUnit}`);
                this.updateHeightValue();
                this.scheduleAutoSave();
            });
        }

        if (heightUnitToggle) {
            heightUnitToggle.addEventListener('click', () => {
                console.log(`heightUnitToggle click event: currentHeightUnit = ${this.currentHeightUnit}`);
                this.toggleHeightUnit();
            });
        }

        // Section toggle buttons
        this.setupSectionToggles();
    }

    /**
     * Load profile data from the server
     */
    async loadProfileData() {
        try {
            const response = await fetch('/profile/data');
            const result = await response.json();
            
            if (result.success && result.data) {
                const data = result.data;
                this.populateFormFields(data);
                this.updateAvatarDisplay(data.avatar);
                this.updateUsernameDisplay(data.username);
            }
        } catch (error) {
            console.error('Error loading profile data:', error);
        }
    }

    /**
     * Populate form fields with profile data
     * @param {Object} data - Profile data object
     */
    populateFormFields(data) {
        Object.keys(data).forEach(key => {
            const element = document.getElementById(key);
            if (element) {
                element.value = data[key] || '';
            }
        });

        // Handle weight unit loading
        if (data.weight_unit) {
            const weightUnitSelect = document.getElementById('weight_unit');
            if (weightUnitSelect) {
                weightUnitSelect.value = data.weight_unit;
            }
        }

        // Calculate and set age from date of birth
        if (data.date_of_birth) {
            const dateOfBirthInput = document.getElementById('date_of_birth');
            const ageInput = document.getElementById('age');
            if (dateOfBirthInput && ageInput) {
                dateOfBirthInput.value = data.date_of_birth;
                const calculatedAge = this.calculateAge(data.date_of_birth);
                ageInput.value = calculatedAge;
            }
        }

        // Handle height conversion and population
        if (data.height) {
            this.populateHeightFields(data.height, data.height_ft);
        }
    }

    /**
     * Update avatar display
     * @param {string} avatar - Avatar filename
     */
    updateAvatarDisplay(avatar) {
        if (avatar) {
            const currentAvatar = document.getElementById('currentAvatar');
            const avatarInput = document.getElementById('avatar');
            if (currentAvatar && avatarInput) {
                currentAvatar.src = `/static/public/avatars/${avatar}`;
                avatarInput.value = avatar;
            }
        }
    }

    /**
     * Update username display in header
     * @param {string} username - Username
     */
    updateUsernameDisplay(username) {
        if (username) {
            const profileUsername = document.getElementById('profileUsername');
            if (profileUsername) {
                profileUsername.textContent = `@${username} • Manage your wellness journey with mindful awareness`;
            }
        }
    }

    /**
     * Schedule auto-save with debouncing
     */
    scheduleAutoSave() {
        if (this.autoSaveTimeout) {
            clearTimeout(this.autoSaveTimeout);
        }
        this.autoSaveTimeout = setTimeout(() => {
            this.saveProfile(false);
        }, this.autoSaveDelay);
    }

    /**
     * Save profile data
     * @param {boolean} showLoading - Whether to show loading state
     * @param {string} section - Section name for success message
     */
    async saveProfile(showLoading = true, section = null) {
        if (showLoading) {
            this.showLoadingState(true);
        }

        try {
            const formData = new FormData(this.form);
            const data = {};
            
            for (let [key, value] of formData.entries()) {
                data[key] = value;
            }
            
            // Debug: Log height-related fields
            console.log(`saveProfile: height_input = ${data.height_input}, height = ${data.height}, currentHeightUnit = ${this.currentHeightUnit}`);

            const response = await fetch('/profile/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.success) {
                const sectionMessage = section ? `${section.charAt(0).toUpperCase() + section.slice(1)} section saved successfully!` : 'Profile saved successfully!';
                this.showSaveStatus(sectionMessage, 'success');
            } else {
                this.showSaveStatus(result.message || 'Error saving profile', 'error');
            }
        } catch (error) {
            this.showSaveStatus('Error saving profile', 'error');
            console.error('Error saving profile:', error);
        } finally {
            if (showLoading) {
                this.showLoadingState(false);
            }
        }
    }

    /**
     * Show/hide loading state
     * @param {boolean} show - Whether to show loading state
     */
    showLoadingState(show) {
        if (show) {
            this.saveButtonText.classList.add('hidden');
            this.saveButtonLoading.classList.remove('hidden');
            this.saveButton.disabled = true;
        } else {
            this.saveButtonText.classList.remove('hidden');
            this.saveButtonLoading.classList.add('hidden');
            this.saveButton.disabled = false;
        }
    }

    /**
     * Show save status message
     * @param {string} message - Status message
     * @param {string} type - Message type ('success' or 'error')
     */
    showSaveStatus(message, type) {
        if (this.saveMessage) {
            this.saveMessage.textContent = message;
        }
        if (this.saveStatus) {
            this.saveStatus.className = `mb-4 p-4 rounded-lg ${type === 'success' ? 'bg-green-500/20 border border-green-500/30 text-green-300' : 'bg-red-500/20 border border-red-500/30 text-red-300'}`;
            this.saveStatus.classList.remove('hidden');
            
            // Auto-hide success messages after 3 seconds
            if (type === 'success') {
                setTimeout(() => {
                    this.saveStatus.classList.add('hidden');
                }, 3000);
            }
        }
    }

    /**
     * Calculate age from date of birth
     * @param {string} birthDate - Date of birth in ISO format
     * @returns {number} Calculated age
     */
    calculateAge(birthDate) {
        const today = new Date();
        const birth = new Date(birthDate);
        let age = today.getFullYear() - birth.getFullYear();
        const monthDiff = today.getMonth() - birth.getMonth();
        
        if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
            age--;
        }
        
        return age;
    }

    /**
     * Convert centimeters to feet and inches
     * @param {number} cm - Height in centimeters
     * @returns {Object} Object with feet and inches
     */
    cmToFeetInches(cm) {
        const totalInches = cm / 2.54;
        const feet = Math.floor(totalInches / 12);
        const inches = Math.round(totalInches % 12);
        return { feet, inches };
    }

    /**
     * Convert feet and inches to centimeters
     * @param {number} feet - Height in feet
     * @param {number} inches - Height in inches
     * @returns {number} Height in centimeters
     */
    feetInchesToCm(feet, inches) {
        const totalInches = (feet * 12) + inches;
        return Math.round(totalInches * 2.54);
    }

    /**
     * Convert feet.inches format to feet and inches
     * @param {number} feetDecimal - Height in feet.decimal format (e.g., 5.6 for 5'6")
     * @returns {Object} Object with feet and inches
     */
    feetDecimalToFeetInches(feetDecimal) {
        const feet = Math.floor(feetDecimal);
        const inches = Math.round((feetDecimal - feet) * 10);
        return { feet, inches };
    }

    /**
     * Populate height field with saved values
     * @param {number} heightCm - Height in centimeters
     * @param {number} heightFt - Height in feet (optional)
     */
    populateHeightFields(heightCm, heightFt = null) {
        const heightInput = document.getElementById('height_input');
        const heightHiddenInput = document.getElementById('height');
        const heightUnitToggle = document.getElementById('height_unit_toggle');

        if (heightCm && heightCm > 0) {
            // Store both values
            this.savedHeightCm = heightCm;
            
            // Calculate ft value if not provided
            if (!heightFt) {
                const { feet, inches } = this.cmToFeetInches(heightCm);
                heightFt = feet + (inches / 10);
            }
            this.savedHeightFt = heightFt;
            
            console.log(`populateHeightFields: saved cm=${heightCm}, ft=${heightFt}`);
            
            // Only set the current unit to cm if this is the initial load
            const isInitialLoad = !this.heightUnitInitialized;
            if (isInitialLoad) {
                console.log(`populateHeightFields: initial load, setting currentHeightUnit = cm`);
                this.currentHeightUnit = 'cm';
                this.heightUnitInitialized = true;
            } else {
                console.log(`populateHeightFields: not initial load, keeping currentHeightUnit = ${this.currentHeightUnit}`);
            }
            
            if (heightUnitToggle) {
                heightUnitToggle.textContent = this.currentHeightUnit;
            }
            
            // Populate the input field with the appropriate value based on current unit
            if (heightInput) {
                if (this.currentHeightUnit === 'ft') {
                    heightInput.value = this.savedHeightFt;
                } else {
                    heightInput.value = this.savedHeightCm;
                }
            }
            if (heightHiddenInput) heightHiddenInput.value = heightCm;
            
            console.log(`populateHeightFields: currentHeightUnit = ${this.currentHeightUnit}, displaying ${this.currentHeightUnit === 'ft' ? this.savedHeightFt : this.savedHeightCm}`);
        }
    }

    /**
     * Update height values and save to database
     */
    updateHeightValue() {
        const heightInput = document.getElementById('height_input');
        const heightHiddenInput = document.getElementById('height');

        if (heightInput && heightInput.value) {
            const inputValue = parseFloat(heightInput.value);
            console.log(`updateHeightValue: inputValue = ${inputValue}, currentHeightUnit = ${this.currentHeightUnit}`);
            
            let cmValue = 0;
            let ftValue = 0;
            
            if (this.currentHeightUnit === 'ft') {
                // Convert feet to cm
                const { feet, inches } = this.feetDecimalToFeetInches(inputValue);
                console.log(`updateHeightValue: feet = ${feet}, inches = ${inches}`);
                cmValue = this.feetInchesToCm(feet, inches);
                ftValue = inputValue;
                console.log(`updateHeightValue: cm = ${cmValue}, ft = ${ftValue}`);
            } else {
                // Already in cm
                cmValue = inputValue;
                const { feet, inches } = this.cmToFeetInches(inputValue);
                ftValue = feet + (inches / 10);
                console.log(`updateHeightValue: cm = ${cmValue}, ft = ${ftValue}`);
            }
            
            // Update hidden field with cm value
            if (heightHiddenInput) heightHiddenInput.value = cmValue;
            
            // Save both values to database
            this.saveHeightToDatabase(cmValue, ftValue);
        }
    }

    /**
     * Save height values to database
     */
    async saveHeightToDatabase(cmValue, ftValue) {
        try {
            const data = {
                height: cmValue,
                height_ft: ftValue
            };
            
            console.log(`saveHeightToDatabase: saving cm=${cmValue}, ft=${ftValue}`);
            
            const response = await fetch('/profile/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.success) {
                console.log(`✅ Height saved successfully: cm=${cmValue}, ft=${ftValue}`);
            } else {
                console.error(`❌ Error saving height: ${result.message}`);
            }
        } catch (error) {
            console.error('Error saving height:', error);
        }
    }

    /**
     * Toggle between feet/inches and centimeters
     */
    toggleHeightUnit() {
        const heightInput = document.getElementById('height_input');
        const heightUnitToggle = document.getElementById('height_unit_toggle');

        if (!heightInput || !heightUnitToggle) return;

        // Prevent multiple rapid toggles
        if (this.isToggling) {
            console.log(`toggleHeightUnit: already toggling, skipping`);
            return;
        }
        this.isToggling = true;

        console.log(`toggleHeightUnit: currentHeightUnit = ${this.currentHeightUnit}`);

        if (this.currentHeightUnit === 'cm') {
            // Switch to feet/inches
            console.log(`toggleHeightUnit: switching from cm to ft`);
            this.currentHeightUnit = 'ft';
            heightUnitToggle.textContent = 'ft';
            
            // Display saved ft value
            if (this.savedHeightFt) {
                heightInput.value = this.savedHeightFt;
                console.log(`toggleHeightUnit: displaying saved ft value = ${this.savedHeightFt}`);
            }
            
            heightInput.placeholder = 'Enter height (e.g., 5.6 for 5\'6")';
        } else {
            // Switch to cm
            console.log(`toggleHeightUnit: switching from ft to cm`);
            this.currentHeightUnit = 'cm';
            heightUnitToggle.textContent = 'cm';
            
            // Display saved cm value
            if (this.savedHeightCm) {
                heightInput.value = this.savedHeightCm;
                console.log(`toggleHeightUnit: displaying saved cm value = ${this.savedHeightCm}`);
            }
            
            heightInput.placeholder = 'Enter height in cm';
        }
        
        // Reset toggle flag after a short delay
        setTimeout(() => {
            this.isToggling = false;
        }, 100);
    }

    /**
     * Setup section toggle buttons (Mind, Body, Spirit)
     */
    setupSectionToggles() {
        // Mind section toggle
        const toggleMindBtn = document.getElementById('toggleMindBtn');
        const mindContent = document.getElementById('mindContent');
        const saveMindBtn = document.getElementById('saveMindBtn');

        if (toggleMindBtn && mindContent) {
            // Initialize the data attribute
            mindContent.setAttribute('data-section-hidden', 'true');
            
            // Check if event listener already exists
            if (toggleMindBtn.hasAttribute('data-toggle-listener-added')) {
                return;
            }
            
            toggleMindBtn.setAttribute('data-toggle-listener-added', 'true');
            
            toggleMindBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleSection(mindContent, toggleMindBtn, saveMindBtn, 'mind');
            });
        }

        // Body section toggle
        const toggleBodyBtn = document.getElementById('toggleBodyBtn');
        const bodyContent = document.getElementById('bodyContent');
        const saveBodyBtn = document.getElementById('saveBodyBtn');

        if (toggleBodyBtn && bodyContent) {
            // Initialize the data attribute
            bodyContent.setAttribute('data-section-hidden', 'true');
            toggleBodyBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleSection(bodyContent, toggleBodyBtn, saveBodyBtn, 'body');
            });
        }

        // Spirit section toggle
        const toggleSpiritBtn = document.getElementById('toggleSpiritBtn');
        const spiritContent = document.getElementById('spiritContent');
        const saveSpiritBtn = document.getElementById('saveSpiritBtn');

        if (toggleSpiritBtn && spiritContent) {
            // Initialize the data attribute
            spiritContent.setAttribute('data-section-hidden', 'true');
            toggleSpiritBtn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.toggleSection(spiritContent, toggleSpiritBtn, saveSpiritBtn, 'spirit');
            });
        }

        // Setup save buttons for individual sections
        this.setupSectionSaveButtons();
    }

    /**
     * Toggle section visibility
     * @param {HTMLElement} content - Content element to toggle
     * @param {HTMLElement} toggleBtn - Toggle button element
     * @param {HTMLElement} saveBtn - Save button element
     * @param {string} sectionName - Name of the section
     */
    toggleSection(content, toggleBtn, saveBtn, sectionName) {
        // Prevent multiple rapid toggles
        if (this.isSectionToggling) {
            return;
        }
        this.isSectionToggling = true;
        
        // Use a custom data attribute to track state instead of relying on 'hidden' class
        const isCurrentlyHidden = content.getAttribute('data-section-hidden') === 'true';
        
        if (isCurrentlyHidden) {
            // Show content
            content.setAttribute('data-section-hidden', 'false');
            content.style.display = 'block';
            content.style.visibility = 'visible';
            content.style.opacity = '1';
            content.classList.remove('hidden');
            
            // Rotate arrow
            const arrow = toggleBtn.querySelector('svg');
            if (arrow) {
                arrow.style.transform = 'rotate(180deg)';
            }
            
            // Show save button
            if (saveBtn) {
                saveBtn.classList.remove('hidden');
            }
            
            // Force a reflow to ensure the content is visible
            setTimeout(() => {
                this.isSectionToggling = false;
            }, 200);
        } else {
            // Hide content
            content.setAttribute('data-section-hidden', 'true');
            content.style.display = 'none';
            content.classList.add('hidden');
            
            // Rotate arrow back
            const arrow = toggleBtn.querySelector('svg');
            if (arrow) {
                arrow.style.transform = 'rotate(0deg)';
            }
            
            // Hide save button
            if (saveBtn) {
                saveBtn.classList.add('hidden');
            }
            
            this.isSectionToggling = false;
        }
    }

    /**
     * Setup save buttons for individual sections
     */
    setupSectionSaveButtons() {
        // Mind section save button
        const saveMindBtn = document.getElementById('saveMindBtn');
        if (saveMindBtn) {
            saveMindBtn.addEventListener('click', () => {
                this.saveSection('mind');
            });
        }

        // Body section save button
        const saveBodyBtn = document.getElementById('saveBodyBtn');
        if (saveBodyBtn) {
            saveBodyBtn.addEventListener('click', () => {
                this.saveSection('body');
            });
        }

        // Spirit section save button
        const saveSpiritBtn = document.getElementById('saveSpiritBtn');
        if (saveSpiritBtn) {
            saveSpiritBtn.addEventListener('click', () => {
                this.saveSection('spirit');
            });
        }
    }

    /**
     * Save specific section data
     * @param {string} sectionName - Name of the section to save
     */
    async saveSection(sectionName) {
        console.log(`💾 Saving ${sectionName} section...`);
        
        // Get all form data
        const formData = new FormData(this.form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }

        try {
            const response = await fetch('/profile/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();
            
            if (result.success) {
                this.showSaveStatus(`${sectionName.charAt(0).toUpperCase() + sectionName.slice(1)} section saved successfully!`, 'success');
                console.log(`✅ ${sectionName} section saved successfully`);
            } else {
                this.showSaveStatus(result.message || `Error saving ${sectionName} section`, 'error');
                console.error(`❌ Error saving ${sectionName} section:`, result.message);
            }
        } catch (error) {
            this.showSaveStatus(`Error saving ${sectionName} section`, 'error');
            console.error(`Error saving ${sectionName} section:`, error);
        }
    }
}

// Password Management Class - Uses existing modal component
class PasswordManager {
    constructor() {
        this.currentPasswordField = null;
        this.newPasswordField = null;
        this.confirmPasswordField = null;
    }

    /**
     * Initialize password manager
     */
    init() {
        this.currentPasswordField = document.getElementById('currentPassword');
        this.newPasswordField = document.getElementById('newPassword');
        this.confirmPasswordField = document.getElementById('confirmPassword');
    }

    /**
     * Open password change modal
     */
    openPasswordModal() {
        // Create and show password modal
        this.showPasswordModal();
        
        // Focus on first field
        setTimeout(() => {
            if (this.currentPasswordField) {
                this.currentPasswordField.focus();
            }
        }, 100);
    }

    /**
     * Show password change modal
     */
    showPasswordModal() {
        // Create modal if it doesn't exist
        if (!document.getElementById('passwordModal')) {
            this.createPasswordModal();
        }
        
        // Show the password modal
        const modal = document.getElementById('passwordModal');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        
        // Reset form
        this.resetPasswordForm();
    }
    
    /**
     * Create password modal HTML
     */
    createPasswordModal() {
        const modalHTML = `
            <div id="passwordModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 hidden flex items-center justify-center">
                <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4 transform transition-all">
                    <!-- Modal Header -->
                    <div class="flex items-center justify-between p-6 border-b border-gray-200">
                        <h3 class="text-lg font-semibold text-gray-900">Change Password</h3>
                        <button onclick="passwordManager.closePasswordModal()" class="text-gray-400 hover:text-gray-600 transition-colors">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                    
                    <!-- Modal Body -->
                    <div class="p-6">
                        <div class="space-y-4">
                            <div>
                                <label for="currentPassword" class="block text-sm font-medium text-gray-700">Current Password:</label>
                                <div class="relative">
                                    <input type="password" id="currentPassword" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mint-green focus:border-transparent">
                                    <button type="button" id="currentPasswordToggle" onclick="passwordManager.togglePasswordVisibility('currentPassword')" class="absolute right-3 top-1/2 transform -translate-y-1/2">🙈</button>
                                </div>
                            </div>
                            <div>
                                <label for="newPassword" class="block text-sm font-medium text-gray-700">New Password:</label>
                                <div class="relative">
                                    <input type="password" id="newPassword" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mint-green focus:border-transparent">
                                    <button type="button" id="newPasswordToggle" onclick="passwordManager.togglePasswordVisibility('newPassword')" class="absolute right-3 top-1/2 transform -translate-y-1/2">🙈</button>
                                </div>
                            </div>
                            <div>
                                <label for="confirmPassword" class="block text-sm font-medium text-gray-700">Confirm New Password:</label>
                                <div class="relative">
                                    <input type="password" id="confirmPassword" class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-mint-green focus:border-transparent">
                                    <button type="button" id="confirmPasswordToggle" onclick="passwordManager.togglePasswordVisibility('confirmPassword')" class="absolute right-3 top-1/2 transform -translate-y-1/2">🙈</button>
                                </div>
                            </div>
                            <div id="passwordStatus" class="hidden text-sm font-medium"></div>
                            <div class="flex space-x-3">
                                <button onclick="passwordManager.changePassword()" class="flex-1 bg-mint-green text-white px-4 py-2 rounded-lg hover:bg-green-600">
                                    Change Password
                                </button>
                                <button onclick="passwordManager.closePasswordModal()" class="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400">
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Add event listeners
        this.setupPasswordModalEvents();
    }
    
    /**
     * Setup password modal event listeners
     */
    setupPasswordModalEvents() {
        const modal = document.getElementById('passwordModal');
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closePasswordModal();
            }
        });
        
        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                this.closePasswordModal();
            }
        });
    }
    
    /**
     * Close password modal
     */
    closePasswordModal() {
        const modal = document.getElementById('passwordModal');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
        this.resetPasswordForm();
    }

    /**
     * Reset password form
     */
    resetPasswordForm() {
        // Get fields directly from DOM
        const currentPasswordField = document.getElementById('currentPassword');
        const newPasswordField = document.getElementById('newPassword');
        const confirmPasswordField = document.getElementById('confirmPassword');
        
        if (currentPasswordField) currentPasswordField.value = '';
        if (newPasswordField) newPasswordField.value = '';
        if (confirmPasswordField) confirmPasswordField.value = '';
        
        // Reset password visibility
        this.togglePasswordVisibility('currentPassword');
        this.togglePasswordVisibility('newPassword');
        this.togglePasswordVisibility('confirmPassword');
        
        // Hide status message
        const statusElement = document.getElementById('passwordStatus');
        if (statusElement) {
            statusElement.classList.add('hidden');
        }
    }

    /**
     * Toggle password visibility
     * @param {string} fieldId - Password field ID
     */
    togglePasswordVisibility(fieldId) {
        const field = document.getElementById(fieldId);
        const toggleBtn = document.getElementById(`${fieldId}Toggle`);
        
        if (field && toggleBtn) {
            if (field.type === 'password') {
                field.type = 'text';
                toggleBtn.innerHTML = '👁️';
            } else {
                field.type = 'password';
                toggleBtn.innerHTML = '🙈';
            }
        }
    }

    /**
     * Validate password strength
     * @param {string} password - Password to validate
     * @returns {Object} Validation result
     */
    validatePassword(password) {
        const minLength = 8;
        const hasUpperCase = /[A-Z]/.test(password);
        const hasLowerCase = /[a-z]/.test(password);
        const hasNumbers = /\d/.test(password);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);
        
        const isValid = password.length >= minLength && hasUpperCase && hasLowerCase && hasNumbers && hasSpecialChar;
        
        return {
            isValid,
            minLength: password.length >= minLength,
            hasUpperCase,
            hasLowerCase,
            hasNumbers,
            hasSpecialChar
        };
    }

    /**
     * Change user password
     */
    async changePassword() {
        // Get field values directly from DOM since they're created dynamically
        const currentPasswordField = document.getElementById('currentPassword');
        const newPasswordField = document.getElementById('newPassword');
        const confirmPasswordField = document.getElementById('confirmPassword');
        
        if (!currentPasswordField || !newPasswordField || !confirmPasswordField) {
            this.showPasswordStatus('Password fields not found', 'error');
            return;
        }
        
        const currentPassword = currentPasswordField.value;
        const newPassword = newPasswordField.value;
        const confirmPassword = confirmPasswordField.value;

        // Validation
        if (!currentPassword || !newPassword || !confirmPassword) {
            this.showPasswordStatus('All fields are required', 'error');
            return;
        }

        if (newPassword !== confirmPassword) {
            this.showPasswordStatus('New passwords do not match', 'error');
            return;
        }

        const validation = this.validatePassword(newPassword);
        if (!validation.isValid) {
            this.showPasswordStatus('Password does not meet requirements', 'error');
            return;
        }

        try {
            const response = await fetch('/profile/change-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            });

            const result = await response.json();
            
            if (result.success) {
                showSuccess('Password changed successfully!');
                setTimeout(() => {
                    this.closePasswordModal();
                }, 1500);
            } else {
                this.showPasswordStatus(result.error || 'Failed to change password', 'error');
            }
        } catch (error) {
            this.showPasswordStatus('Error changing password', 'error');
            console.error('Error changing password:', error);
        }
    }

    /**
     * Show password status message
     * @param {string} message - Status message
     * @param {string} type - Message type
     */
    showPasswordStatus(message, type) {
        const statusElement = document.getElementById('passwordStatus');
        if (statusElement) {
            statusElement.textContent = message;
            statusElement.className = `text-sm font-medium ${type === 'success' ? 'text-green-600' : 'text-red-600'}`;
            statusElement.classList.remove('hidden');
        }
    }
}

// Avatar Management Class - Uses existing modal component
class AvatarManager {
    constructor() {
        this.selectedAvatar = null;
        this.avatarOptions = [
            'default-avatar.png', 'girl1.png', 'girl2.png', 'girl3.png', 'girl4.png', 'girl5.png',
            'man1.png', 'man2.png', 'man3.png', 'man4.png', 'man5.png'
        ];
    }

    /**
     * Initialize avatar manager
     */
    init() {
        this.selectedAvatar = 'default-avatar.png';
    }

    /**
     * Open avatar selection modal
     */
    openAvatarModal() {
        const currentAvatar = document.getElementById('currentAvatar');
        if (currentAvatar) {
            const currentSrc = currentAvatar.src;
            this.selectedAvatar = currentSrc.split('/').pop();
        }

        // Create and show avatar modal
        this.showAvatarModal();
    }

    /**
     * Show avatar selection modal
     */
    showAvatarModal() {
        // Create modal if it doesn't exist
        if (!document.getElementById('avatarModal')) {
            this.createAvatarModal();
        }
        
        // Show the avatar modal
        const modal = document.getElementById('avatarModal');
        modal.classList.remove('hidden');
        modal.classList.add('flex');
        
        // Update selection indicators
        this.updateAvatarSelectionIndicators();
    }
    
    /**
     * Create avatar modal HTML
     */
    createAvatarModal() {
        const modalHTML = `
            <div id="avatarModal" class="fixed inset-0 bg-black bg-opacity-50 z-50 hidden flex items-center justify-center">
                <div class="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 transform transition-all">
                    <!-- Modal Header -->
                    <div class="flex items-center justify-between p-6 border-b border-gray-200">
                        <h3 class="text-lg font-semibold text-gray-900">Select Avatar</h3>
                        <button onclick="avatarManager.closeAvatarModal()" class="text-gray-400 hover:text-gray-600 transition-colors">
                            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                            </svg>
                        </button>
                    </div>
                    
                    <!-- Modal Body -->
                    <div class="p-6">
                        <div class="space-y-4">
                            <div class="grid grid-cols-5 gap-2 max-h-64 overflow-y-auto" id="avatarGrid">
                                <!-- Avatar options will be populated here -->
                            </div>
                            <div class="flex space-x-3">
                                <button onclick="avatarManager.confirmAvatarSelection()" class="flex-1 bg-mint-green text-white px-4 py-2 rounded-lg hover:bg-green-600">
                                    Confirm Selection
                                </button>
                                <button onclick="avatarManager.closeAvatarModal()" class="flex-1 bg-gray-300 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-400">
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHTML);
        
        // Add event listeners
        this.setupAvatarModalEvents();
        
        // Populate avatar grid
        this.populateAvatarGrid();
    }
    
    /**
     * Setup avatar modal event listeners
     */
    setupAvatarModalEvents() {
        const modal = document.getElementById('avatarModal');
        
        // Close modal when clicking outside
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                this.closeAvatarModal();
            }
        });
        
        // Close modal with Escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
                this.closeAvatarModal();
            }
        });
    }
    
    /**
     * Populate avatar grid
     */
    populateAvatarGrid() {
        const avatarGrid = document.getElementById('avatarGrid');
        if (!avatarGrid) return;
        
        const avatarHTML = this.avatarOptions.map(avatar => `
            <div class="avatar-option cursor-pointer p-2 rounded-lg hover:bg-gray-100 transition-colors flex items-center justify-center ${this.selectedAvatar === avatar ? 'bg-mint-green bg-opacity-20' : ''}" 
                 onclick="avatarManager.handleAvatarSelectionInModal('${avatar}')">
                <img src="/static/public/avatars/${avatar}" 
                     alt="Avatar ${avatar}" 
                     class="w-16 h-16 rounded-full border-2 border-gray-200">
            </div>
        `).join('');
        
        avatarGrid.innerHTML = avatarHTML;
    }
    
    /**
     * Close avatar modal
     */
    closeAvatarModal() {
        const modal = document.getElementById('avatarModal');
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
    
    /**
     * Update avatar selection indicators
     */
    updateAvatarSelectionIndicators() {
        const avatarOptions = document.querySelectorAll('.avatar-option');
        avatarOptions.forEach(option => {
            const img = option.querySelector('img');
            if (img && img.src.includes(this.selectedAvatar)) {
                option.classList.add('bg-mint-green', 'bg-opacity-20');
            } else {
                option.classList.remove('bg-mint-green', 'bg-opacity-20');
            }
        });
    }

    /**
     * Handle avatar selection in modal
     * @param {string} selectedAvatar - Selected avatar filename
     */
    handleAvatarSelectionInModal(selectedAvatar) {
        this.selectedAvatar = selectedAvatar;
        
        // Update selection indicators
        const avatarOptions = document.querySelectorAll('.avatar-option');
        avatarOptions.forEach(option => {
            const img = option.querySelector('img');
            if (img && img.src.includes(selectedAvatar)) {
                option.classList.add('ring-2', 'ring-mint-green');
            } else {
                option.classList.remove('ring-2', 'ring-mint-green');
            }
        });
    }

    /**
     * Confirm avatar selection
     */
    async confirmAvatarSelection() {
        try {
            const response = await fetch('/profile/save', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    avatar: this.selectedAvatar
                })
            });

            const result = await response.json();
            
            if (result.success) {
                // Update avatar display
                const currentAvatar = document.getElementById('currentAvatar');
                const avatarInput = document.getElementById('avatar');
                
                if (currentAvatar) {
                    currentAvatar.src = `/static/public/avatars/${this.selectedAvatar}`;
                }
                if (avatarInput) {
                    avatarInput.value = this.selectedAvatar;
                }
                
                showSuccess('Avatar updated successfully!');
                this.closeAvatarModal();
            } else {
                showError('Failed to save avatar: ' + (result.error || 'Unknown error'));
            }
        } catch (error) {
            showError('Error saving avatar');
            console.error('Error saving avatar:', error);
        }
    }
}

// Session management is handled by existing Flask session configuration
// No need for custom session manager as Flask handles this automatically

// Export classes for global use
window.ProfileManager = ProfileManager;
window.PasswordManager = PasswordManager;
window.AvatarManager = AvatarManager;

// Initialize managers when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize profile manager if profile form exists
    if (document.getElementById('profileForm')) {
        window.profileManager = new ProfileManager();
        window.profileManager.init();
    }

    // Initialize password manager
    window.passwordManager = new PasswordManager();
    window.passwordManager.init();

    // Initialize avatar manager
    window.avatarManager = new AvatarManager();
    window.avatarManager.init();
});

// Global utility functions for backward compatibility
window.openPasswordModal = function() {
    if (window.passwordManager) {
        window.passwordManager.openPasswordModal();
    }
};

window.togglePasswordVisibility = function(fieldId) {
    if (window.passwordManager) {
        window.passwordManager.togglePasswordVisibility(fieldId);
    }
};

window.changePassword = function() {
    if (window.passwordManager) {
        window.passwordManager.changePassword();
    }
};

window.closePasswordModal = function() {
    if (window.passwordManager) {
        window.passwordManager.closePasswordModal();
    }
};

window.openAvatarModal = function() {
    if (window.avatarManager) {
        window.avatarManager.openAvatarModal();
    }
};

window.closeAvatarModal = function() {
    if (window.avatarManager) {
        window.avatarManager.closeAvatarModal();
    }
};

window.handleAvatarSelectionInModal = function(selectedAvatar) {
    if (window.avatarManager) {
        window.avatarManager.handleAvatarSelectionInModal(selectedAvatar);
    }
};

window.confirmAvatarSelection = function() {
    if (window.avatarManager) {
        window.avatarManager.confirmAvatarSelection();
    }
};
