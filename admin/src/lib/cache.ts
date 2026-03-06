/**
 * In-memory cache with TTL support
 * Reduces database queries and improves API response times
 */

interface CacheEntry<T> {
    data: T;
    expiresAt: number;
}

class MemoryCache {
    private cache: Map<string, CacheEntry<any>> = new Map();
    private cleanupInterval: NodeJS.Timeout;

    constructor() {
        // Cleanup expired entries every 5 minutes
        this.cleanupInterval = setInterval(() => {
            this.cleanup();
        }, 5 * 60 * 1000);
    }

    /**
     * Set a value in cache with TTL in seconds
     */
    set<T>(key: string, data: T, ttlSeconds: number = 3600): void {
        const expiresAt = Date.now() + ttlSeconds * 1000;
        this.cache.set(key, { data, expiresAt });
    }

    /**
     * Get a value from cache
     */
    get<T>(key: string): T | null {
        const entry = this.cache.get(key);

        if (!entry) {
            return null;
        }

        if (Date.now() > entry.expiresAt) {
            this.cache.delete(key);
            return null;
        }

        return entry.data as T;
    }

    /**
     * Delete a specific key
     */
    delete(key: string): void {
        this.cache.delete(key);
    }

    /**
     * Clear all cache
     */
    clear(): void {
        this.cache.clear();
    }

    /**
     * Get or set with function
     */
    async getOrSet<T>(
        key: string,
        fetchFn: () => Promise<T>,
        ttlSeconds: number = 3600
    ): Promise<T> {
        const cached = this.get<T>(key);

        if (cached !== null) {
            return cached;
        }

        const data = await fetchFn();
        this.set(key, data, ttlSeconds);
        return data;
    }

    /**
     * Remove expired entries
     */
    private cleanup(): void {
        const now = Date.now();
        const keysToDelete: string[] = [];

        this.cache.forEach((entry, key) => {
            if (now > entry.expiresAt) {
                keysToDelete.push(key);
            }
        });

        keysToDelete.forEach((key) => this.cache.delete(key));

        if (keysToDelete.length > 0) {
            console.log(`Cache cleanup: removed ${keysToDelete.length} expired entries`);
        }
    }

    /**
     * Get cache statistics
     */
    getStats() {
        return {
            size: this.cache.size,
            keys: Array.from(this.cache.keys()),
        };
    }

    /**
     * Destroy cache and cleanup interval
     */
    destroy(): void {
        clearInterval(this.cleanupInterval);
        this.cache.clear();
    }
}

// Export singleton instance
export const cache = new MemoryCache();

// Helper functions for common cache patterns
export const cacheUtils = {
    /**
     * Generate cache key for drama list
     */
    dramaListKey: (page: number, limit: number, category?: string) =>
        `dramas:list:${page}:${limit}:${category || 'all'}`,

    /**
     * Generate cache key for drama detail
     */
    dramaKey: (id: string) => `drama:${id}`,

    /**
     * Generate cache key for recommendations
     */
    recommendationsKey: (userId: string, type: string) =>
        `recommendations:${userId}:${type}`,

    /**
     * Generate cache key for analytics
     */
    analyticsKey: (type: string) => `analytics:${type}`,

    /**
     * Invalidate all cache keys matching a pattern
     */
    invalidatePattern: (pattern: string) => {
        const stats = cache.getStats();
        stats.keys.forEach((key) => {
            if (key.includes(pattern)) {
                cache.delete(key);
            }
        });
    },
};

export default cache;
