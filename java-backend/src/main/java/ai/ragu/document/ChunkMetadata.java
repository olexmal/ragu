package ai.ragu.document;

import java.util.Collections;
import java.util.Map;

/**
 * Metadata describing a specific document chunk.
 */
public record ChunkMetadata(
        String source,
        String version,
        int index,
        Map<String, Object> attributes
) {
    public ChunkMetadata {
        if (attributes == null) {
            attributes = Collections.emptyMap();
        }
    }
}

