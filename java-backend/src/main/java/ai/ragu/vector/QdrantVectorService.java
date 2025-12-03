package ai.ragu.vector;

import jakarta.enterprise.context.ApplicationScoped;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * Placeholder Qdrant adapter backed by in-memory storage to keep the API surface stable.
 */
@ApplicationScoped
public class QdrantVectorService implements VectorStore {

    private final Map<String, List<VectorDocument>> collections = new ConcurrentHashMap<>();
    private final CollectionNameGenerator nameGenerator = new CollectionNameGenerator();

    @Override
    public VectorOperationResult upsert(String collectionName, String version, List<VectorDocument> documents) {
        if (documents == null || documents.isEmpty()) {
            return VectorOperationResult.failure("No documents provided");
        }
        String normalized = nameGenerator.generate(collectionName, version);
        collections.computeIfAbsent(normalized, key -> new ArrayList<>()).addAll(documents);
        return VectorOperationResult.ok("Upserted %d vectors into %s".formatted(documents.size(), normalized));
    }

    @Override
    public List<VectorDocument> search(String collectionName, String version, List<Double> queryVector, int k) {
        String normalized = nameGenerator.generate(collectionName, version);
        List<VectorDocument> docs = collections.getOrDefault(normalized, List.of());
        if (queryVector == null || queryVector.isEmpty()) {
            return docs.stream().limit(k).toList();
        }

        return docs.stream()
                .sorted(Comparator.comparingDouble(doc -> -similarity(doc.vector(), queryVector)))
                .limit(Math.max(1, k))
                .toList();
    }

    @Override
    public VectorOperationResult deleteCollection(String collectionName, String version) {
        String normalized = nameGenerator.generate(collectionName, version);
        collections.remove(normalized);
        return VectorOperationResult.ok("Removed collection " + normalized);
    }

    @Override
    public List<String> listCollections() {
        return new ArrayList<>(collections.keySet());
    }

    private double similarity(List<Double> a, List<Double> b) {
        if (a == null || b == null || a.isEmpty() || b.isEmpty()) {
            return 0d;
        }
        int size = Math.min(a.size(), b.size());
        double dot = 0;
        double normA = 0;
        double normB = 0;
        for (int i = 0; i < size; i++) {
            double va = a.get(i);
            double vb = b.get(i);
            dot += va * vb;
            normA += va * va;
            normB += vb * vb;
        }
        if (normA == 0 || normB == 0) {
            return 0d;
        }
        return dot / (Math.sqrt(normA) * Math.sqrt(normB));
    }
}

