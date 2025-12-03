package ai.ragu.embedding.cache;

import ai.ragu.embedding.EmbeddingResult;
import jakarta.enterprise.context.ApplicationScoped;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Simple in-memory cache used until Redis integration is wired.
 */
@ApplicationScoped
public class InMemoryEmbeddingCache implements EmbeddingCache {

    private static final Duration DEFAULT_TTL = Duration.ofMinutes(15);

    private record CacheEntry(EmbeddingResult result, Instant expiresAt) {}

    private final Map<String, CacheEntry> store = new ConcurrentHashMap<>();

    @Override
    public Optional<EmbeddingResult> get(String key) {
        CacheEntry entry = store.get(key);
        if (entry == null) {
            return Optional.empty();
        }
        if (Instant.now().isAfter(entry.expiresAt)) {
            store.remove(key);
            return Optional.empty();
        }
        return Optional.of(entry.result);
    }

    @Override
    public void put(String key, EmbeddingResult result) {
        store.put(key, new CacheEntry(result, Instant.now().plus(DEFAULT_TTL)));
    }
}

