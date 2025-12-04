package ai.ragu.rag;

import ai.ragu.api.model.QueryRequest;
import ai.ragu.api.model.QueryResponse;
import ai.ragu.api.model.QueryStats;
import ai.ragu.api.model.SourceDocument;
import ai.ragu.embedding.EmbeddingOptions;
import ai.ragu.embedding.EmbeddingResult;
import ai.ragu.embedding.EmbeddingService;
import ai.ragu.vector.VectorDocument;
import ai.ragu.vector.VectorStore;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;

import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@ApplicationScoped
public class RagService {

    private final EmbeddingService embeddingService;
    private final VectorStore vectorStore;
    private final String defaultCollection;
    private final MeterRegistry meterRegistry;
    private final Timer queryTimer;

    @Inject
    public RagService(EmbeddingService embeddingService,
                      VectorStore vectorStore,
                      @ConfigProperty(name = "ragu.qdrant.collection-base", defaultValue = "common-model-docs") String defaultCollection,
                      MeterRegistry meterRegistry) {
        this.embeddingService = embeddingService;
        this.vectorStore = vectorStore;
        this.defaultCollection = defaultCollection;
        this.meterRegistry = meterRegistry;
        this.queryTimer = meterRegistry.timer("ragu.query.duration");
    }

    public QueryResponse handleQuery(QueryRequest request) {
        Timer.Sample sample = Timer.start(meterRegistry);
        try {
            EmbeddingResult queryEmbedding = embeddingService.embed(request.query(), EmbeddingOptions.defaultOptions());

            String targetCollection = (request.collectionName() == null || request.collectionName().isBlank())
                    ? defaultCollection
                    : request.collectionName();

            List<VectorDocument> hits = vectorStore.search(
                    targetCollection,
                    request.version(),
                    queryEmbedding.vector(),
                    request.k()
            );

            List<SourceDocument> sources = hits.stream()
                    .map(this::toSourceDocument)
                    .toList();

            String answer = hits.isEmpty()
                    ? "No indexed documents yet, but we received your question: \"%s\"".formatted(request.query())
                    : "Placeholder answer synthesized from %d retrieved documents.".formatted(hits.size());

            QueryStats stats = new QueryStats(
                    null,
                    null,
                    null,
                    null,
                    null,
                    null,
                    null,
                    null
            );

            meterRegistry.counter("ragu.query.requests", "result", hits.isEmpty() ? "no_hits" : "hits").increment();
            meterRegistry.summary("ragu.query.sources").record(sources.size());

            return new QueryResponse(
                    answer,
                    request.query(),
                    sources,
                    sources.size(),
                    stats
            );
        } finally {
            sample.stop(queryTimer);
        }
    }

    private SourceDocument toSourceDocument(VectorDocument doc) {
        Object contentObj = doc.payload().getOrDefault("content", "Content unavailable in stub store");
        Object metadataObj = doc.payload().getOrDefault("metadata", Collections.emptyMap());

        Map<String, Object> metadata = metadataObj instanceof Map<?, ?> map
                ? map.entrySet().stream()
                    .filter(entry -> entry.getKey() instanceof String)
                    .collect(Collectors.toMap(
                            entry -> (String) entry.getKey(),
                            Map.Entry::getValue))
                : Collections.emptyMap();

        return new SourceDocument(
                contentObj.toString(),
                metadata
        );
    }
}

