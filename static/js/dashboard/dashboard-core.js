// Dashboard Core Manager
// Essential dashboard functionality and coordination
class DashboardCore {
    constructor() {
        this.currentDate = new Date();
        this.isInitialLoad = true;
        
        // Initialize optimization modules
        this.apiClient = new APIClient();
        this.components = new DashboardComponents(this.apiClient);
        
        // Initialize UI modules
        this.ui = new DashboardUI(this);
        this.events = new DashboardEvents(this);
        this.food = new DashboardFood(this);
        this.water = new DashboardWater(this);
        this.mood = new DashboardMood(this);
        
        this.init();
    }

    init() {
        this.events.setupEventListeners();
        this.ui.updateDateDisplay();
        this.ui.updateFoodLoggingDate();
        this.ui.initMacroChart();
        this.loadDashboardDataOptimized();
        this.water.loadWaterSettings();
    }

    async loadDashboardDataOptimized() {
        try {
            this.ui.showLoading();
            const dateStr = this.currentDate.toISOString().split('T')[0];
            
            // Check if this is the initial load
            if (this.isInitialLoad) {
        
                
                // Load only critical components first (safer approach)
                try {
                    const data = await this.apiClient.getDashboardData(dateStr);
                    if (data && data.success) {
                        this.updateDashboard(data.data);
                        this.isInitialLoad = false;
                        
                        // Load remaining UI enhancements after core data is displayed
                        setTimeout(() => {
                            this.enhanceDashboardUI();
                        }, 200);
                    } else if (data && data.error === 'Authentication required') {
                        console.warn('🔐 Authentication required - dashboard will show empty state');
                        this.ui.showToast('Please refresh the page and log in again', 'warning');
                        return; // Don't try fallback if auth is the issue
                    } else {
                        // Fallback to original method
                        await this.loadDashboardData();
                    }
                } catch (apiError) {
                    console.warn('Optimized loading failed, using fallback:', apiError.message);
                    // Don't try fallback if it's an auth error
                    if (apiError.message && apiError.message.includes('Authentication')) {
                        console.warn('🔐 Authentication error - skipping data load');
                        this.ui.showToast('Authentication issue detected', 'warning');
                        return;
                    }
                    await this.loadDashboardData();
                }
            } else {
                // Subsequent loads - use cache-first approach
                const cached = this.apiClient.cache.get(this.apiClient.cache.getDashboardKey(dateStr));
                if (cached && cached.data) {
                    console.log('📦 Loading from cache');
                    this.updateDashboard(cached.data);
                } else {
                    console.log('🔄 Fetching fresh dashboard data');
                    await this.loadDashboardData();
                }
            }
            
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.ui.showToast('Failed to load dashboard data', 'error');
        } finally {
            this.ui.hideLoading();
        }
    }

    // Enhanced UI loading for non-critical features
    enhanceDashboardUI() {
        try {
    
            // Initialize advanced features that don't affect core functionality
            if (this.ui.updateMoodNotesTab) {
                this.ui.updateMoodNotesTab();
            }
        } catch (error) {
            console.warn('UI enhancement failed (non-critical):', error);
        }
    }

    // Keep the original method for backward compatibility and direct calls
    async loadDashboardData() {
        try {
            this.ui.showLoading();
            const dateStr = this.currentDate.toISOString().split('T')[0];
            const data = await this.apiClient.getDashboardData(dateStr);

            if (data && data.success) {
                this.updateDashboard(data.data);
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.ui.showToast('Failed to load dashboard data', 'error');
        } finally {
            this.ui.hideLoading();
        }
    }

    updateDashboard(data) {
        // Store current data for access by components (e.g., edit functionality)
        this.currentData = data;
        
        // Update water display
        this.water.updateDisplay(data.water_logs);
        
        // Update macronutrients
        this.ui.updateMacros(data.totals);
        
        // Update mood
        this.mood.updateDisplay(data.mood_logs);
        
        // Update notes display
        this.ui.displayNotes(data.notes);
        
        // Update food log
        this.food.displayFoodLog(data.food_logs);
    }

    // Date management
    changeDate(days) {
        this.currentDate.setDate(this.currentDate.getDate() + days);
        this.ui.updateDateDisplay();
        this.ui.clearNotesInput();
        this.loadDashboardDataOptimized();
        this.ui.updateFoodLoggingDate();
        this.ui.updateMoodNotesTab();
    }

    goToToday() {
        this.currentDate = new Date();
        this.ui.updateDateDisplay();
        this.ui.clearNotesInput();
        this.loadDashboardDataOptimized();
        this.ui.updateFoodLoggingDate();
        this.ui.updateMoodNotesTab();
    }

    selectDate(dateString) {
        if (!dateString) return;
        
        // Parse date without timezone issues by using the date string directly
        const dateParts = dateString.split('-');
        const selectedDate = new Date(parseInt(dateParts[0]), parseInt(dateParts[1]) - 1, parseInt(dateParts[2]));
        
        if (selectedDate.getTime() !== this.currentDate.getTime()) {
            this.currentDate = selectedDate;
            this.ui.updateDateDisplay();
            this.ui.clearNotesInput();
            this.loadDashboardDataOptimized();
            this.ui.updateFoodLoggingDate();
            this.ui.updateMoodNotesTab();
        }
        
        this.ui.showToast(`Date set to ${this.currentDate.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' })}`, 'info');
    }

    // Cache invalidation and reload helper
    invalidateCacheAndReload() {
        const dateStr = this.currentDate.toISOString().split('T')[0];
        this.apiClient.invalidateCache(dateStr);
        this.loadDashboardDataOptimized();
    }

    // Debounced reload to prevent rapid successive calls
    debouncedReload = this.debounce(() => {
        this.invalidateCacheAndReload();
    }, 300);

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Make available globally
window.DashboardCore = DashboardCore;
