// Cache Manager Module
// Handles client-side caching for dashboard data
class CacheManager {
    constructor() {
        this.cache = new Map();
        this.cacheExpiry = new Map();
        this.accessTimes = new Map(); // Track access for LRU
        this.hitCount = new Map(); // Track cache hits
        this.defaultTTL = 5 * 60 * 1000; // 5 minutes
        this.maxCacheSize = 50; // Maximum number of cached items
        
        // Performance monitoring
        this.stats = {
            hits: 0,
            misses: 0,
            evictions: 0
        };
    }

    set(key, data, ttl = this.defaultTTL) {
        // Evict old entries if cache is full
        if (this.cache.size >= this.maxCacheSize) {
            this.evictLRU();
        }
        
        this.cache.set(key, data);
        this.cacheExpiry.set(key, Date.now() + ttl);
        this.accessTimes.set(key, Date.now());
        this.hitCount.set(key, 0);
    }

    get(key) {
        if (!this.cache.has(key)) {
            this.stats.misses++;
            return null;
        }
        
        const expiry = this.cacheExpiry.get(key);
        if (Date.now() > expiry) {
            this.delete(key);
            this.stats.misses++;
            return null;
        }
        
        // Update access tracking
        this.accessTimes.set(key, Date.now());
        this.hitCount.set(key, (this.hitCount.get(key) || 0) + 1);
        this.stats.hits++;
        
        return this.cache.get(key);
    }

    // LRU eviction strategy
    evictLRU() {
        let oldestKey = null;
        let oldestTime = Date.now();
        
        for (const [key, time] of this.accessTimes) {
            if (time < oldestTime) {
                oldestTime = time;
                oldestKey = key;
            }
        }
        
        if (oldestKey) {
            this.delete(oldestKey);
            this.stats.evictions++;
        }
    }

    delete(key) {
        this.cache.delete(key);
        this.cacheExpiry.delete(key);
        this.accessTimes.delete(key);
        this.hitCount.delete(key);
    }

    clear() {
        this.cache.clear();
        this.cacheExpiry.clear();
        this.accessTimes.clear();
        this.hitCount.clear();
        this.stats = { hits: 0, misses: 0, evictions: 0 };
    }

    // Performance monitoring
    getCacheStats() {
        const hitRate = this.stats.hits + this.stats.misses > 0 
            ? (this.stats.hits / (this.stats.hits + this.stats.misses) * 100).toFixed(2)
            : 0;
            
        return {
            ...this.stats,
            hitRate: `${hitRate}%`,
            cacheSize: this.cache.size,
            maxSize: this.maxCacheSize
        };
    }

    // Preload frequently accessed data
    async preload(keys, dataLoader) {
        const promises = keys.map(async (key) => {
            if (!this.cache.has(key)) {
                try {
                    const data = await dataLoader(key);
                    this.set(key, data);
                } catch (error) {
                    console.warn(`Failed to preload ${key}:`, error);
                }
            }
        });
        
        await Promise.all(promises);
    }

    // Generate cache key for dashboard data
    getDashboardKey(date) {
        return `dashboard-${date}`;
    }

    // Generate cache key for mood/notes data
    getMoodNotesKey(date) {
        return `mood-notes-${date}`;
    }

    // Check if we need to refetch data
    shouldRefetch(key) {
        return !this.get(key);
    }
}

// Export for use in other modules
window.CacheManager = CacheManager;
