package ai.ragu.document;

/**
 * Represents a chunk of content ready for embedding.
 */
public record DocumentChunk(
        String content,
        ChunkMetadata metadata
) {
}

