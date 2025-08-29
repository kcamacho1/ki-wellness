// API Client Module
// Centralized API handling with caching and batching
class APIClient {
    constructor() {
        this.cache = new CacheManager();
        this.pendingRequests = new Map();
    }

    // Deduplicate identical API calls
    async get(url, options = {}) {
        // Check cache first
        const cacheKey = this.getCacheKey(url, options);
        const cached = this.cache.get(cacheKey);
        if (cached && !options.bypassCache) {
            return cached;
        }

        // Check if request is already pending
        if (this.pendingRequests.has(url)) {
            return this.pendingRequests.get(url);
        }

        // Make the request
        const requestPromise = this.makeRequest(url, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'same-origin', // Include cookies for authentication
            ...options
        });

        this.pendingRequests.set(url, requestPromise);

        try {
            const result = await requestPromise;
            
            // Cache successful responses
            if (result && result.success) {
                this.cache.set(cacheKey, result, options.cacheTTL);
            }
            
            return result;
        } finally {
            this.pendingRequests.delete(url);
        }
    }

    async post(url, data, options = {}) {
        return this.makeRequest(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data),
            credentials: 'same-origin', // Include cookies for authentication
            ...options
        });
    }

    async makeRequest(url, options) {

        
        try {
            const response = await fetch(url, options);
            

            
            // Check if response is HTML (authentication redirect)
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('text/html')) {
                console.warn(`Authentication required for ${url} - likely HTML redirect`);

                // Don't automatically redirect - let the app handle it gracefully
                return { success: false, error: 'Authentication required' };
            }
            
            // Handle non-200 responses
            if (!response.ok) {
                console.error(`HTTP ${response.status} for ${url}`);
                return { success: false, error: `HTTP ${response.status}` };
            }
            
            const data = await response.json();
            return data;
        } catch (error) {
            console.error(`API Error for ${url}:`, error);
            
            // Check if error is JSON parsing error (likely HTML response)
            if (error.message && error.message.includes('Unexpected token')) {
                console.warn(`Received HTML instead of JSON for ${url} - likely authentication issue`);
                return { success: false, error: 'Authentication required' };
            }
            
            throw error;
        }
    }

    getCacheKey(url, options) {
        return `${url}-${JSON.stringify(options.params || {})}`;
    }

    // Batch multiple API calls
    async batchGet(requests) {
        const promises = requests.map(({ url, options }) => 
            this.get(url, options).catch(error => ({ error, url }))
        );
        return Promise.all(promises);
    }

    // Dashboard-specific methods with enhanced optimization
    async getDashboardData(date, options = {}) {
        return this.get(`/api/dashboard-data?date=${date}`, {
            cacheTTL: 2 * 60 * 1000, // 2 minutes for dashboard data
            ...options
        });
    }

    async getMoodNotesHistory(date, options = {}) {
        // Reuse dashboard data since mood/notes are included
        return this.getDashboardData(date, {
            cacheTTL: 5 * 60 * 1000, // 5 minutes for mood/notes
            ...options
        });
    }

    // Batch load all dashboard data at once (most efficient)
    async loadAllDashboardData(date) {
        const requests = [
            { url: `/api/dashboard-data?date=${date}`, options: { cacheTTL: 2 * 60 * 1000 } }
        ];
        
        const results = await this.batchGet(requests);
        return results[0]; // Return the single dashboard data result
    }

    // Clear cache when data is updated
    invalidateCache(pattern) {
        if (pattern) {
            // Clear specific pattern
            for (const key of this.cache.cache.keys()) {
                if (key.includes(pattern)) {
                    this.cache.delete(key);
                }
            }
        } else {
            // Clear all cache
            this.cache.clear();
        }
    }
}

// Export for use in other modules
window.APIClient = APIClient;
