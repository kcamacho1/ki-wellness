// Dashboard Components Module
// Modular components for different dashboard sections
class DashboardComponents {
    constructor(apiClient) {
        this.api = apiClient;
        this.components = {
            water: new WaterComponent(apiClient),
            macros: new MacrosComponent(apiClient),
            mood: new MoodComponent(apiClient),
            foodLog: new FoodLogComponent(apiClient),
            moodNotes: new MoodNotesComponent(apiClient)
        };
    }

    async loadComponent(componentName, date, options = {}) {
        const component = this.components[componentName];
        if (!component) {
            console.warn(`Component ${componentName} not found`);
            return;
        }

        return component.load(date, options);
    }

    async loadAll(date, options = {}) {
        const { priority = 'all' } = options;
        
        if (priority === 'critical') {
            // Load only critical components first (above the fold)
            await Promise.all([
                this.loadComponent('water', date),
                this.loadComponent('macros', date)
            ]);
        } else if (priority === 'remaining') {
            // Lazy load remaining components (below the fold)
            await this.lazyLoadComponents(['mood', 'foodLog'], date);
        } else {
            // Load all components at once (fallback)
            await Promise.all([
                this.loadComponent('water', date),
                this.loadComponent('macros', date),
                this.loadComponent('mood', date),
                this.loadComponent('foodLog', date)
            ]);
        }
    }

    // Lazy loading with intersection observer for performance
    async lazyLoadComponents(componentNames, date) {
        for (const componentName of componentNames) {
            // Check if component is visible before loading
            const componentElement = this.getComponentElement(componentName);
            if (componentElement && this.isElementVisible(componentElement)) {
                await this.loadComponent(componentName, date);
            } else {
                // Load with a small delay to not block main thread
                setTimeout(() => this.loadComponent(componentName, date), 50);
            }
        }
    }

    getComponentElement(componentName) {
        const elementMap = {
            'mood': document.querySelector('.mood-display'),
            'foodLog': document.getElementById('food-log-container'),
            'water': document.getElementById('water-display'),
            'macros': document.getElementById('macroChart')
        };
        return elementMap[componentName];
    }

    isElementVisible(element) {
        if (!element) return false;
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }

    invalidateComponent(componentName, date) {
        const component = this.components[componentName];
        if (component && component.invalidate) {
            component.invalidate(date);
        }
    }
}

// Base Component Class
class BaseComponent {
    constructor(apiClient) {
        this.api = apiClient;
        this.isLoading = false;
        this.lastLoadedDate = null;
    }

    async load(date, options = {}) {
        if (this.isLoading && this.lastLoadedDate === date) {
            return; // Prevent duplicate loads
        }

        this.isLoading = true;
        try {
            await this.loadData(date, options);
            this.lastLoadedDate = date;
        } catch (error) {
            console.error(`Error loading ${this.constructor.name}:`, error);
        } finally {
            this.isLoading = false;
        }
    }

    // Override in subclasses
    async loadData(date, options) {
        throw new Error('loadData must be implemented by subclass');
    }

    invalidate(date) {
        // Clear component-specific cache
        this.api.invalidateCache(this.getCachePattern(date));
    }

    getCachePattern(date) {
        return date; // Default pattern
    }
}

// Water Component
class WaterComponent extends BaseComponent {
    async loadData(date, options) {
        const data = await this.api.getDashboardData(date, options);
        if (data && data.success) {
            this.updateDisplay(data.data.water_logs);
        } else if (data && data.error === 'Authentication required') {
            console.warn('Authentication required for water data');
            return; // Don't throw error, just skip
        }
    }

    updateDisplay(waterLogs) {
        const totalWater = waterLogs.reduce((sum, log) => sum + log.amount, 0);
        const goal = 64;
        const percentage = Math.min((totalWater / goal) * 100, 100);

        const display = document.getElementById('water-display');
        const progress = document.getElementById('water-progress');
        
        if (display) display.textContent = `${Math.round(totalWater)} oz`;
        if (progress) progress.style.width = `${percentage}%`;
    }
}

// Macros Component  
class MacrosComponent extends BaseComponent {
    async loadData(date, options) {
        const data = await this.api.getDashboardData(date, options);
        if (data && data.success) {
            this.updateDisplay(data.data.totals);
        } else if (data && data.error === 'Authentication required') {
            console.warn('Authentication required for macros data');
            return; // Don't throw error, just skip
        }
    }

    updateDisplay(totals) {
        // Update macro chart and values
        if (window.dashboardManager && window.dashboardManager.updateMacros) {
            window.dashboardManager.updateMacros(totals);
        }
    }
}

// Mood Component
class MoodComponent extends BaseComponent {
    async loadData(date, options) {
        const data = await this.api.getDashboardData(date, options);
        if (data && data.success) {
            this.updateDisplay(data.data.mood_logs);
        } else if (data && data.error === 'Authentication required') {
            console.warn('Authentication required for mood data');
            return; // Don't throw error, just skip
        }
    }

    updateDisplay(moodLogs) {
        if (window.dashboardManager && window.dashboardManager.updateMoodDisplay) {
            window.dashboardManager.updateMoodDisplay(moodLogs);
        }
    }
}

// Food Log Component
class FoodLogComponent extends BaseComponent {
    async loadData(date, options) {
        const data = await this.api.getDashboardData(date, options);
        if (data && data.success) {
            this.updateDisplay(data.data.food_logs);
        } else if (data && data.error === 'Authentication required') {
            console.warn('Authentication required for food data');
            return; // Don't throw error, just skip
        }
    }

    updateDisplay(foodLogs) {
        if (window.dashboardManager && window.dashboardManager.displayFoodLog) {
            window.dashboardManager.displayFoodLog(foodLogs);
        }
    }
}

// Mood & Notes Component (for tab)
class MoodNotesComponent extends BaseComponent {
    async loadData(date, options) {
        const data = await this.api.getMoodNotesHistory(date, options);
        if (data && data.success) {
            this.updateDisplay(data.data);
        } else if (data && data.error === 'Authentication required') {
            console.warn('Authentication required for mood/notes data');
            return; // Don't throw error, just skip
        }
    }

    updateDisplay(data) {
        if (window.dashboardManager) {
            if (window.dashboardManager.displayMoodHistory) {
                window.dashboardManager.displayMoodHistory(data.mood_logs);
            }
            if (window.dashboardManager.displayNotesHistory) {
                window.dashboardManager.displayNotesHistory(data.notes);
            }
        }
    }
}

// Export for use in main dashboard
window.DashboardComponents = DashboardComponents;
