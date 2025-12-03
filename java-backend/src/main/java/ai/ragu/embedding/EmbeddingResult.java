package ai.ragu.embedding;

import ai.ragu.document.ChunkMetadata;

import java.util.List;

/**
 * Result of an embedding call.
 */
public record EmbeddingResult(
        List<Double> vector,
        ChunkMetadata metadata,
        String provider,
        String model
) {
}

