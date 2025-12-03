package ai.ragu.document;

import java.util.Collections;
import java.util.HashMap;
import java.util.Map;

/**
 * Builder-style options that control how documents are chunked.
 */
public class DocumentProcessingOptions {
    public static final int DEFAULT_CHUNK_SIZE = 1000;
    public static final int DEFAULT_CHUNK_OVERLAP = 200;

    private final int chunkSize;
    private final int chunkOverlap;
    private final String source;
    private final String version;
    private final Map<String, Object> metadata;

    private DocumentProcessingOptions(Builder builder) {
        this.chunkSize = builder.chunkSize;
        this.chunkOverlap = builder.chunkOverlap;
        this.source = builder.source;
        this.version = builder.version;
        this.metadata = Collections.unmodifiableMap(new HashMap<>(builder.metadata));
    }

    public int chunkSize() {
        return chunkSize;
    }

    public int chunkOverlap() {
        return chunkOverlap;
    }

    public String source() {
        return source;
    }

    public String version() {
        return version;
    }

    public Map<String, Object> metadata() {
        return metadata;
    }

    public static Builder builder() {
        return new Builder();
    }

    public static DocumentProcessingOptions defaults() {
        return builder().build();
    }

    public static final class Builder {
        private int chunkSize = DEFAULT_CHUNK_SIZE;
        private int chunkOverlap = DEFAULT_CHUNK_OVERLAP;
        private String source = "unknown";
        private String version;
        private final Map<String, Object> metadata = new HashMap<>();

        public Builder chunkSize(int chunkSize) {
            if (chunkSize <= 0) {
                throw new IllegalArgumentException("chunkSize must be positive");
            }
            this.chunkSize = chunkSize;
            return this;
        }

        public Builder chunkOverlap(int chunkOverlap) {
            if (chunkOverlap < 0) {
                throw new IllegalArgumentException("chunkOverlap cannot be negative");
            }
            this.chunkOverlap = chunkOverlap;
            return this;
        }

        public Builder source(String source) {
            if (source != null && !source.isBlank()) {
                this.source = source;
            }
            return this;
        }

        public Builder version(String version) {
            this.version = version;
            return this;
        }

        public Builder putMetadata(String key, Object value) {
            if (key != null && value != null) {
                metadata.put(key, value);
            }
            return this;
        }

        public DocumentProcessingOptions build() {
            if (chunkOverlap >= chunkSize) {
                throw new IllegalArgumentException("chunkOverlap must be smaller than chunkSize");
            }
            return new DocumentProcessingOptions(this);
        }
    }
}

