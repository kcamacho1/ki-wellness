// Ki Wellness Dashboard JavaScript - Optimized Modular Version
// ============================================================

class DashboardManager extends DashboardCore {
    constructor() {
        super();
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    
    
    // Add a small delay to ensure the page is fully loaded and session is established
    setTimeout(() => {
        // Safe modular initialization - load modules but without aggressive API calls
        try {
            // Check if modules are available
            if (window.DashboardCore && window.APIClient && window.CacheManager) {
                // Initialize but with error handling for auth issues
                try {
                    window.dashboardManager = new DashboardManager();
            
                } catch (error) {
                console.error('Dashboard initialization failed:', error);
                // Fallback to simple version
                console.log('⚠️ Falling back to simple dashboard');
                window.dashboardManager = {
                    currentDate: new Date(),
                    async loadDashboardData() {
                        console.log('Simple dashboard - data loading skipped due to auth issues');
                    }
                };
            }
        } else {
            // Fallback to simple dashboard
            console.log('⚠️ Modules not loaded, using simple dashboard');
            window.dashboardManager = {
                currentDate: new Date(),
                async loadDashboardData() {
                    try {
                        const dateStr = this.currentDate.toISOString().split('T')[0];
                        const response = await fetch(`/api/dashboard-data?date=${dateStr}`, {
                            credentials: 'same-origin' // Include cookies for authentication
                        });
                        
                        if (!response.ok) {
                            console.warn('Dashboard API failed');
                            return;
                        }
                        
                        const data = await response.json();
                        if (data.success) {
                            console.log('✅ Dashboard data loaded successfully');
                        }
                    } catch (error) {
                        console.warn('Dashboard loading failed:', error.message);
                    }
                }
            };
            
            window.dashboardManager.loadDashboardData();
        }
        
        // Add debug helper
        window.getCacheStats = () => {
            if (window.dashboardManager?.apiClient?.cache) {
                return window.dashboardManager.apiClient.cache.getCacheStats();
            }
            return 'Cache not available';
        };
        
    } catch (error) {
        console.error('Dashboard initialization failed:', error);
    }
    }, 250); // 250ms delay to ensure session is established
});

// Legacy functions for backward compatibility
function saveNote() {
    if (window.dashboardManager) {
        window.dashboardManager.events.handleSaveNotes();
    }
}

// Export for testing/debugging
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DashboardManager;
}
