package ai.ragu.embedding;

import ai.ragu.document.ChunkMetadata;
import ai.ragu.document.DocumentChunk;
import ai.ragu.embedding.cache.EmbeddingCache;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.ArrayList;
import java.util.Base64;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Placeholder implementation that simulates embeddings while the LangChain4j + DJL wiring is in progress.
 * The deterministic hash-based vector keeps downstream components testable without external dependencies.
 */
@ApplicationScoped
public class LangChainEmbeddingService implements EmbeddingService {

    private final EmbeddingCache cache;

    @Inject
    public LangChainEmbeddingService(EmbeddingCache cache) {
        this.cache = cache;
    }

    @Override
    public EmbeddingResult embed(DocumentChunk chunk, EmbeddingOptions options) {
        return embed(chunk.content(), chunk.metadata(), options);
    }

    @Override
    public EmbeddingResult embed(String text, EmbeddingOptions options) {
        ChunkMetadata metadata = new ChunkMetadata("adhoc", null, 0, Map.of("source", "adhoc"));
        return embed(text, metadata, options);
    }

    private EmbeddingResult embed(String text, ChunkMetadata metadata, EmbeddingOptions options) {
        EmbeddingOptions localOptions = options != null ? options : EmbeddingOptions.defaultOptions();
        String cacheKey = buildCacheKey(text, localOptions);

        if (localOptions.cacheEnabled()) {
            return cache.get(cacheKey)
                    .orElseGet(() -> {
                        EmbeddingResult generated = generateEmbedding(text, metadata, localOptions);
                        cache.put(cacheKey, generated);
                        return generated;
                    });
        }
        return generateEmbedding(text, metadata, localOptions);
    }

    private EmbeddingResult generateEmbedding(String text, ChunkMetadata metadata, EmbeddingOptions options) {
        List<Double> vector = hashToVector(text, options.dimensions());
        return new EmbeddingResult(vector, metadata, options.provider(), options.model());
    }

    private List<Double> hashToVector(String text, int dimensions) {
        byte[] hash = sha256(text);
        List<Double> vector = new ArrayList<>(dimensions);
        for (int i = 0; i < dimensions; i++) {
            int hashIndex = (i % hash.length);
            double value = ((hash[hashIndex] & 0xFF) / 255.0) * 2 - 1; // Normalize to [-1, 1]
            vector.add(value);
        }
        return vector;
    }

    private byte[] sha256(String input) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            return digest.digest(input.getBytes(StandardCharsets.UTF_8));
        } catch (NoSuchAlgorithmException e) {
            throw new IllegalStateException("SHA-256 not available", e);
        }
    }

    private String buildCacheKey(String text, EmbeddingOptions options) {
        String normalized = text.trim().toLowerCase(Locale.ROOT);
        String rawKey = options.provider() + ":" + options.model() + ":" + normalized;
        return Base64.getUrlEncoder().withoutPadding().encodeToString(rawKey.getBytes(StandardCharsets.UTF_8));
    }

}

