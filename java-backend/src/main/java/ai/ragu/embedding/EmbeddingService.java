package ai.ragu.embedding;

import ai.ragu.document.DocumentChunk;

/**
 * Contract for turning chunks into vector embeddings.
 */
public interface EmbeddingService {

    EmbeddingResult embed(DocumentChunk chunk, EmbeddingOptions options);

    EmbeddingResult embed(String text, EmbeddingOptions options);
}

