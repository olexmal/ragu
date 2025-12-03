package ai.ragu.embedding;

/**
 * Options controlling embedding generation.
 */
public record EmbeddingOptions(
        String provider,
        String model,
        boolean cacheEnabled,
        int dimensions
) {
    public EmbeddingOptions {
        if (dimensions <= 0) {
            dimensions = 512;
        }
    }

    public static EmbeddingOptions defaultOptions() {
        return new EmbeddingOptions("local", "hash-embedding", true, 512);
    }
}

