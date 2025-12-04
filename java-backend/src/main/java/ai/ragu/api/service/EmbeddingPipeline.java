package ai.ragu.api.service;

import ai.ragu.api.model.EmbedResponse;
import ai.ragu.document.DocumentChunk;
import ai.ragu.document.DocumentProcessingOptions;
import ai.ragu.document.DocumentProcessor;
import ai.ragu.embedding.EmbeddingOptions;
import ai.ragu.embedding.EmbeddingResult;
import ai.ragu.embedding.EmbeddingService;
import ai.ragu.vector.CollectionNameGenerator;
import ai.ragu.vector.VectorDocument;
import ai.ragu.vector.VectorStore;
import ai.ragu.vector.VectorOperationResult;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;

@ApplicationScoped
public class EmbeddingPipeline {

    private final DocumentProcessor documentProcessor;
    private final EmbeddingService embeddingService;
    private final VectorStore vectorStore;
    private final CollectionNameGenerator nameGenerator;
    private final String defaultCollectionBase;
    private final MeterRegistry meterRegistry;
    private final Timer embeddingTimer;

    @Inject
    public EmbeddingPipeline(DocumentProcessor documentProcessor,
                             EmbeddingService embeddingService,
                             VectorStore vectorStore,
                             CollectionNameGenerator nameGenerator,
                             MeterRegistry meterRegistry,
                             @ConfigProperty(name = "ragu.qdrant.collection-base", defaultValue = "common-model-docs")
                             String defaultCollectionBase) {
        this.documentProcessor = documentProcessor;
        this.embeddingService = embeddingService;
        this.vectorStore = vectorStore;
        this.nameGenerator = nameGenerator;
        this.defaultCollectionBase = defaultCollectionBase;
        this.meterRegistry = meterRegistry;
        this.embeddingTimer = meterRegistry.timer("ragu.embedding.duration");
    }

    public EmbedResponse embedFile(Path path, String originalFilename, String collectionName, String version, boolean overwrite) {
        DocumentProcessingOptions options = DocumentProcessingOptions.builder()
                .source(originalFilename)
                .version(version)
                .build();

        List<DocumentChunk> chunks = documentProcessor.process(path, options);
        return runEmbedding(chunks, originalFilename, collectionName, version, overwrite);
    }

    public EmbedResponse embedContent(String content, String source, String collectionName, String version, boolean overwrite) {
        DocumentProcessingOptions options = DocumentProcessingOptions.builder()
                .source(source)
                .version(version)
                .build();
        List<DocumentChunk> chunks = documentProcessor.process(content, options);
        return runEmbedding(chunks, source, collectionName, version, overwrite);
    }

    private EmbedResponse runEmbedding(List<DocumentChunk> chunks,
                                       String source,
                                       String collectionName,
                                       String version,
                                       boolean overwrite) {
        Timer.Sample sample = Timer.start(meterRegistry);
        try {
            if (chunks.isEmpty()) {
                meterRegistry.counter("ragu.embedding.requests", "result", "empty").increment();
                return new EmbedResponse(
                        "No content detected",
                        version,
                        resolvedCollection(collectionName, version),
                        "noop",
                        source
                );
            }

            if (overwrite) {
                vectorStore.deleteCollection(collectionNameOrDefault(collectionName), version);
            }

            List<VectorDocument> documents = new ArrayList<>();
            for (int i = 0; i < chunks.size(); i++) {
                DocumentChunk chunk = chunks.get(i);
                EmbeddingResult result = embeddingService.embed(chunk, EmbeddingOptions.defaultOptions());
                Map<String, Object> payload = new HashMap<>();
                payload.put("content", chunk.content());
                payload.put("metadata", chunk.metadata());
                payload.put("embedding_provider", result.provider());
                payload.put("embedding_model", result.model());
                documents.add(new VectorDocument(
                        UUID.randomUUID().toString(),
                        result.vector(),
                        payload
                ));
            }

            VectorOperationResult upsertResult = vectorStore.upsert(collectionNameOrDefault(collectionName), version, documents);
            meterRegistry.summary("ragu.embedding.chunks").record(chunks.size());
            meterRegistry.counter("ragu.embedding.requests", "result", upsertResult.success() ? "success" : "warning").increment();

            return new EmbedResponse(
                    upsertResult.success()
                            ? "Embedded %d chunks".formatted(chunks.size())
                            : "Embedding completed with warnings: %s".formatted(upsertResult.message()),
                    version,
                    resolvedCollection(collectionName, version),
                    overwrite ? "overwrite" : "incremental",
                    source
            );
        } catch (RuntimeException e) {
            meterRegistry.counter("ragu.embedding.requests", "result", "failure").increment();
            throw e;
        } finally {
            sample.stop(embeddingTimer);
        }
    }

    private String collectionNameOrDefault(String collectionName) {
        return (collectionName == null || collectionName.isBlank())
                ? defaultCollectionBase
                : collectionName;
    }

    private String resolvedCollection(String collectionName, String version) {
        return nameGenerator.generate(collectionNameOrDefault(collectionName), version);
    }

    public EmbedResponse embedTempFile(byte[] data, String originalFilename, String collectionName, String version, boolean overwrite) throws IOException {
        Path temp = Files.createTempFile("embed-upload-", ".tmp");
        try {
            Files.write(temp, data);
            return embedFile(temp, originalFilename, collectionName, version, overwrite);
        } finally {
            Files.deleteIfExists(temp);
        }
    }
}

