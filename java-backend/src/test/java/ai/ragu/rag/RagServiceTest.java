package ai.ragu.rag;

import ai.ragu.api.model.QueryRequest;
import ai.ragu.embedding.EmbeddingService;
import ai.ragu.embedding.LangChainEmbeddingService;
import ai.ragu.embedding.cache.InMemoryEmbeddingCache;
import ai.ragu.vector.QdrantVectorService;
import ai.ragu.vector.VectorDocument;
import ai.ragu.vector.VectorStore;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class RagServiceTest {

    private RagService ragService;
    private VectorStore vectorStore;
    private SimpleMeterRegistry meterRegistry;

    @BeforeEach
    void setUp() {
        EmbeddingService embeddingService = new LangChainEmbeddingService(new InMemoryEmbeddingCache());
        vectorStore = new QdrantVectorService();
        meterRegistry = new SimpleMeterRegistry();
        ragService = new RagService(embeddingService, vectorStore, "unit-collection", meterRegistry);

        vectorStore.upsert(
                "unit-collection",
                "v1",
                List.of(new VectorDocument(
                        "seed-doc",
                        List.of(0.1, 0.2, 0.3),
                        Map.of("content", "Seed document content", "metadata", Map.of("source", "seed"))
                ))
        );
    }

    @Test
    void returnsPlaceholderAnswerWhenNoMatches() {
        QueryRequest request = new QueryRequest("What is the plan?", null, "v2", 3, false);
        var response = ragService.handleQuery(request);

        assertTrue(response.answer().contains("What is the plan?"));
    }

    @Test
    void returnsSourceDocumentsWhenIndexed() {
        QueryRequest request = new QueryRequest("Seed question", "unit-collection", "v1", 3, false);
        var response = ragService.handleQuery(request);

        assertEquals("Seed question", response.query());
        assertTrue(response.sources() != null);
    }
}

