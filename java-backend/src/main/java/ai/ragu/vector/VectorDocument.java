package ai.ragu.vector;

import java.util.Collections;
import java.util.List;
import java.util.Map;

/**
 * Represents a stored vector and its payload metadata.
 */
public record VectorDocument(
        String id,
        List<Double> vector,
        Map<String, Object> payload
) {
    public VectorDocument {
        if (vector == null) {
            vector = List.of();
        }
        if (payload == null) {
            payload = Collections.emptyMap();
        }
    }
}

