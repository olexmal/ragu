package ai.ragu.storage;

import io.quarkus.redis.datasource.RedisDataSource;
import io.quarkus.redis.datasource.keys.KeyCommands;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import java.util.List;

/**
 * Service for managing application cache in Redis.
 */
@ApplicationScoped
public class CacheService {

    private static final String CACHE_PREFIX = "ragu:cache:*";
    private static final String EMBEDDING_CACHE_PREFIX = "ragu:embedding:*";

    private final KeyCommands<String> keyCommands;

    @Inject
    public CacheService(RedisDataSource ds) {
        this.keyCommands = ds.key();
    }

    /**
     * Clears all cache entries and returns the count of cleared keys.
     */
    public long clear() {
        long cleared = 0;

        // Clear main cache keys
        cleared += clearPattern(CACHE_PREFIX);

        // Clear embedding cache keys
        cleared += clearPattern(EMBEDDING_CACHE_PREFIX);

        return cleared;
    }

    /**
     * Clears a specific cache pattern.
     */
    public long clearPattern(String pattern) {
        List<String> keys = keyCommands.keys(pattern);
        if (keys.isEmpty()) {
            return 0;
        }

        long deleted = 0;
        for (String key : keys) {
            if (keyCommands.del(key) > 0) {
                deleted++;
            }
        }
        return deleted;
    }

    /**
     * Returns approximate count of cached entries.
     */
    public long getCacheSize() {
        List<String> cacheKeys = keyCommands.keys(CACHE_PREFIX);
        List<String> embeddingKeys = keyCommands.keys(EMBEDDING_CACHE_PREFIX);
        return cacheKeys.size() + embeddingKeys.size();
    }
}

