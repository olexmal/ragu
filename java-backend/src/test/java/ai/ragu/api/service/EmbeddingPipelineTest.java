package ai.ragu.api.service;

import ai.ragu.api.model.EmbedResponse;
import ai.ragu.document.DocumentProcessor;
import ai.ragu.document.DocumentProcessingOptions;
import ai.ragu.document.DocumentChunk;
import ai.ragu.embedding.EmbeddingOptions;
import ai.ragu.embedding.EmbeddingService;
import ai.ragu.vector.CollectionNameGenerator;
import ai.ragu.vector.VectorDocument;
import ai.ragu.vector.VectorOperationResult;
import ai.ragu.vector.VectorStore;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.nio.file.Path;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertTrue;

class EmbeddingPipelineTest {

    private EmbeddingPipeline pipeline;

    @BeforeEach
    void setUp() {
        DocumentProcessor processor = new DocumentProcessor() {
            @Override
            public List<DocumentChunk> process(Path path, DocumentProcessingOptions options) {
                return List.of(new DocumentChunk("content", new ai.ragu.document.ChunkMetadata(options.source(), options.version(), 0, java.util.Map.of())));
            }

            @Override
            public List<DocumentChunk> process(String content, DocumentProcessingOptions options) {
                return List.of(new DocumentChunk(content, new ai.ragu.document.ChunkMetadata(options.source(), options.version(), 0, java.util.Map.of())));
            }
        };

        EmbeddingService embeddingService = new EmbeddingService() {
            @Override
            public ai.ragu.embedding.EmbeddingResult embed(DocumentChunk chunk, EmbeddingOptions options) {
                return new ai.ragu.embedding.EmbeddingResult(List.of(0.1, 0.2), chunk.metadata(), "stub", "stub");
            }

            @Override
            public ai.ragu.embedding.EmbeddingResult embed(String text, EmbeddingOptions options) {
                return new ai.ragu.embedding.EmbeddingResult(List.of(0.1, 0.2), new ai.ragu.document.ChunkMetadata("adhoc", null, 0, java.util.Map.of()), "stub", "stub");
            }
        };

        VectorStore store = new VectorStore() {
            @Override
            public VectorOperationResult upsert(String collectionName, String version, List<VectorDocument> documents) {
                return VectorOperationResult.ok("ok");
            }

            @Override
            public List<VectorDocument> search(String collectionName, String version, List<Double> queryVector, int k) {
                return List.of();
            }

            @Override
            public VectorOperationResult deleteCollection(String collectionName, String version) {
                return VectorOperationResult.ok("deleted");
            }

            @Override
            public List<VectorDocument> getCollectionDocuments(String collectionName, String version) {
                return List.of();
            }

            @Override
            public List<CollectionSummary> listCollections() {
                return List.of();
            }

            @Override
            public VectorOperationResult deleteDocument(String collectionName, String version, String documentId) {
                return VectorOperationResult.ok("deleted");
            }
        };

        pipeline = new EmbeddingPipeline(processor, embeddingService, store, new CollectionNameGenerator(), "unit");
    }

    @Test
    void embedsContent() {
        EmbedResponse response = pipeline.embedContent("Hello world", "unit.txt", "unit", "v1", false);
        assertTrue(response.message().contains("Embedded"));
    }
}

