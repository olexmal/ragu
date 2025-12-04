package ai.ragu.rag;

import ai.ragu.api.model.QueryRequest;
import ai.ragu.api.model.QueryResponse;
import ai.ragu.api.model.QueryStats;
import ai.ragu.api.model.SourceDocument;
import ai.ragu.embedding.EmbeddingOptions;
import ai.ragu.embedding.EmbeddingResult;
import ai.ragu.embedding.EmbeddingService;
import ai.ragu.storage.HistoryStorageService;
import ai.ragu.vector.VectorDocument;
import ai.ragu.vector.VectorStore;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;
import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;

import java.util.*;
import java.util.stream.Collectors;

@ApplicationScoped
public class RagService {

    private final EmbeddingService embeddingService;
    private final VectorStore vectorStore;
    private final HistoryStorageService historyStorage;
    private final String defaultCollection;
    private final MeterRegistry meterRegistry;
    private final Timer queryTimer;

    @Inject
    public RagService(EmbeddingService embeddingService,
                      VectorStore vectorStore,
                      HistoryStorageService historyStorage,
                      @ConfigProperty(name = "ragu.qdrant.collection-base", defaultValue = "common-model-docs") String defaultCollection,
                      MeterRegistry meterRegistry) {
        this.embeddingService = embeddingService;
        this.vectorStore = vectorStore;
        this.historyStorage = historyStorage;
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

            // Record to history
            historyStorage.addEntry(request.query(), answer, sources.size(), targetCollection);

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

    /**
     * Handles multi-version query: runs the same query against multiple collections
     * and merges results by relevance score.
     */
    public QueryResponse handleMultiVersionQuery(String query, List<String> versions, int k) {
        Timer.Sample sample = Timer.start(meterRegistry);
        try {
            EmbeddingResult queryEmbedding = embeddingService.embed(query, EmbeddingOptions.defaultOptions());

            List<VectorDocument> allHits = new ArrayList<>();

            for (String version : versions) {
                List<VectorDocument> hits = vectorStore.search(
                        defaultCollection,
                        version,
                        queryEmbedding.vector(),
                        k
                );
                allHits.addAll(hits);
            }

            // Sort by score (assuming higher is better) and take top k
            List<VectorDocument> topHits = allHits.stream()
                    .sorted((a, b) -> Double.compare(
                            getScore(b.payload()),
                            getScore(a.payload())
                    ))
                    .limit(k)
                    .toList();

            List<SourceDocument> sources = topHits.stream()
                    .map(this::toSourceDocument)
                    .toList();

            String answer = topHits.isEmpty()
                    ? "No documents found across versions: %s".formatted(String.join(", ", versions))
                    : "Merged results from %d versions with %d total sources.".formatted(versions.size(), sources.size());

            meterRegistry.counter("ragu.query.requests", "type", "multi-version").increment();

            // Record to history
            historyStorage.addEntry(query, answer, sources.size(), "multi:" + String.join(",", versions));

            return new QueryResponse(
                    answer,
                    query,
                    sources,
                    sources.size(),
                    new QueryStats(null, null, null, null, null, null, null, null)
            );
        } finally {
            sample.stop(queryTimer);
        }
    }

    /**
     * Handles version comparison: runs query against each version separately
     * and returns grouped results.
     */
    public Map<String, Object> handleCompareQuery(String query, List<String> versions, int k) {
        Timer.Sample sample = Timer.start(meterRegistry);
        try {
            EmbeddingResult queryEmbedding = embeddingService.embed(query, EmbeddingOptions.defaultOptions());

            Map<String, List<SourceDocument>> resultsByVersion = new LinkedHashMap<>();

            for (String version : versions) {
                List<VectorDocument> hits = vectorStore.search(
                        defaultCollection,
                        version,
                        queryEmbedding.vector(),
                        k
                );

                List<SourceDocument> sources = hits.stream()
                        .map(this::toSourceDocument)
                        .toList();

                resultsByVersion.put(version, sources);
            }

            int totalSources = resultsByVersion.values().stream()
                    .mapToInt(List::size)
                    .sum();

            meterRegistry.counter("ragu.query.requests", "type", "compare").increment();

            // Record to history
            historyStorage.addEntry(query, "Comparison across " + versions.size() + " versions", totalSources, "compare:" + String.join(",", versions));

            return Map.of(
                    "query", query,
                    "versions", versions,
                    "results_by_version", resultsByVersion,
                    "total_sources", totalSources
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

    private double getScore(Map<String, Object> payload) {
        Object score = payload.get("score");
        if (score instanceof Number) {
            return ((Number) score).doubleValue();
        }
        return 0.0;
    }
}
