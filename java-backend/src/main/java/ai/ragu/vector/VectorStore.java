package ai.ragu.vector;

import java.util.List;

public interface VectorStore {

    VectorOperationResult upsert(String collectionName, String version, List<VectorDocument> documents);

    List<VectorDocument> search(String collectionName, String version, List<Double> queryVector, int k);

    VectorOperationResult deleteCollection(String collectionName, String version);

    List<String> listCollections();
}

