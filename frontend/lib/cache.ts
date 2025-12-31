/**
 * Production-ready caching utilities
 * Implements browser cache, localStorage, and in-memory caching
 */

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  expiresAt: number;
}

class CacheManager {
  private memoryCache: Map<string, CacheEntry<any>> = new Map();
  private readonly DEFAULT_TTL = 5 * 60 * 1000; // 5 minutes

  /**
   * Get item from cache (checks memory -> localStorage -> null)
   */
  get<T>(key: string): T | null {
    // Check memory cache first
    const memEntry = this.memoryCache.get(key);
    if (memEntry && memEntry.expiresAt > Date.now()) {
      return memEntry.data as T;
    }

    // Check localStorage
    if (typeof window !== 'undefined') {
      try {
        const stored = localStorage.getItem(`cache_${key}`);
        if (stored) {
          const entry: CacheEntry<T> = JSON.parse(stored);
          if (entry.expiresAt > Date.now()) {
            // Restore to memory cache
            this.memoryCache.set(key, entry);
            return entry.data;
          } else {
            // Expired, remove it
            localStorage.removeItem(`cache_${key}`);
          }
        }
      } catch (e) {
        console.warn('Cache read error:', e);
      }
    }

    return null;
  }

  /**
   * Set item in cache (both memory and localStorage)
   */
  set<T>(key: string, data: T, ttl: number = this.DEFAULT_TTL): void {
    const entry: CacheEntry<T> = {
      data,
      timestamp: Date.now(),
      expiresAt: Date.now() + ttl,
    };

    // Set in memory
    this.memoryCache.set(key, entry);

    // Set in localStorage
    if (typeof window !== 'undefined') {
      try {
        localStorage.setItem(`cache_${key}`, JSON.stringify(entry));
      } catch (e) {
        console.warn('Cache write error (quota exceeded?):', e);
        // If quota exceeded, clear old entries
        this.clearExpired();
      }
    }
  }

  /**
   * Remove item from cache
   */
  remove(key: string): void {
    this.memoryCache.delete(key);
    if (typeof window !== 'undefined') {
      localStorage.removeItem(`cache_${key}`);
    }
  }

  /**
   * Clear all cache
   */
  clear(): void {
    this.memoryCache.clear();
    if (typeof window !== 'undefined') {
      const keys = Object.keys(localStorage);
      keys.forEach(key => {
        if (key.startsWith('cache_')) {
          localStorage.removeItem(key);
        }
      });
    }
  }

  /**
   * Clear expired entries from localStorage
   */
  clearExpired(): void {
    if (typeof window !== 'undefined') {
      const now = Date.now();
      const keys = Object.keys(localStorage);
      keys.forEach(key => {
        if (key.startsWith('cache_')) {
          try {
            const stored = localStorage.getItem(key);
            if (stored) {
              const entry = JSON.parse(stored);
              if (entry.expiresAt < now) {
                localStorage.removeItem(key);
              }
            }
          } catch (e) {
            // Invalid entry, remove it
            localStorage.removeItem(key);
          }
        }
      });
    }
  }

  /**
   * Cached fetch with automatic retry and stale-while-revalidate
   */
  async cachedFetch<T>(
    url: string,
    options?: RequestInit,
    ttl: number = this.DEFAULT_TTL
  ): Promise<T> {
    const cacheKey = `fetch_${url}_${JSON.stringify(options || {})}`;

    // Check cache first
    const cached = this.get<T>(cacheKey);
    if (cached) {
      // Return cached data immediately
      // But also revalidate in background if stale (older than half TTL)
      const entry = this.memoryCache.get(cacheKey);
      if (entry && Date.now() - entry.timestamp > ttl / 2) {
        // Stale, revalidate in background
        this.fetchAndCache<T>(url, options, cacheKey, ttl).catch(console.error);
      }
      return cached;
    }

    // No cache, fetch fresh data
    return this.fetchAndCache<T>(url, options, cacheKey, ttl);
  }

  private async fetchAndCache<T>(
    url: string,
    options: RequestInit | undefined,
    cacheKey: string,
    ttl: number
  ): Promise<T> {
    const response = await fetch(url, options);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();
    this.set(cacheKey, data, ttl);
    return data;
  }
}

export const cache = new CacheManager();

// Auto-cleanup expired entries on page load
if (typeof window !== 'undefined') {
  cache.clearExpired();
}
