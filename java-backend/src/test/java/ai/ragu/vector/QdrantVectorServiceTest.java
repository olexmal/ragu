package ai.ragu.vector;

import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class QdrantVectorServiceTest {

    private final QdrantVectorService service = new QdrantVectorService();

    @Test
    void upsertAndSearchReturnsStoredDocuments() {
        VectorDocument doc = new VectorDocument(
                "doc-1",
                List.of(0.1, 0.2, 0.3),
                Map.of("content", "stub content", "metadata", Map.of("source", "unit"))
        );

        service.upsert("docs", "1.0", List.of(doc));
        List<VectorDocument> results = service.search("docs", "1.0", List.of(0.1, 0.2, 0.3), 1);

        assertEquals(1, results.size());
        assertEquals("doc-1", results.get(0).id());
        assertTrue(service.listCollections().stream().anyMatch(summary -> summary.name().equals("docs-v1-0")));
        assertEquals(1, service.getCollectionDocuments("docs", "1.0").size());
    }
}

