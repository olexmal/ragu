package ai.ragu.vector;

import java.util.List;

public interface VectorStore {

    VectorOperationResult upsert(String collectionName, String version, List<VectorDocument> documents);

    List<VectorDocument> search(String collectionName, String version, List<Double> queryVector, int k);

    VectorOperationResult deleteCollection(String collectionName, String version);

    List<VectorDocument> getCollectionDocuments(String collectionName, String version);

    List<CollectionSummary> listCollections();

    VectorOperationResult deleteDocument(String collectionName, String version, String documentId);

    record CollectionSummary(String name, int count) {}
}

