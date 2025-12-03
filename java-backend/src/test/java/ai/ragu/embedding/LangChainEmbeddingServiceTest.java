package ai.ragu.embedding;

import ai.ragu.document.ChunkMetadata;
import ai.ragu.document.DocumentChunk;
import ai.ragu.embedding.cache.InMemoryEmbeddingCache;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertSame;

class LangChainEmbeddingServiceTest {

    private final LangChainEmbeddingService service = new LangChainEmbeddingService(new InMemoryEmbeddingCache());

    @Test
    void returnsDeterministicVectorsAndUsesCache() {
        DocumentChunk chunk = new DocumentChunk("Example text for embedding.", new ChunkMetadata("test", "v1", 0, java.util.Map.of()));

        EmbeddingResult first = service.embed(chunk, EmbeddingOptions.defaultOptions());
        EmbeddingResult second = service.embed(chunk, EmbeddingOptions.defaultOptions());

        assertEquals(first.vector(), second.vector(), "Embedding vectors should be deterministic");
        assertSame(first.vector(), second.vector(), "Cache should return the same vector instance");
    }
}

