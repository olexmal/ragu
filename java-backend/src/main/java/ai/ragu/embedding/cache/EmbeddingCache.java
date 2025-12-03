package ai.ragu.embedding.cache;

import ai.ragu.embedding.EmbeddingResult;

import java.util.Optional;

/**
 * Abstraction over the caching layer (Redis in production, in-memory in dev/tests).
 */
public interface EmbeddingCache {
    Optional<EmbeddingResult> get(String key);
    void put(String key, EmbeddingResult result);
}

