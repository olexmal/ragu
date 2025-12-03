package ai.ragu.api.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.quarkus.runtime.annotations.RegisterForReflection;
import jakarta.validation.constraints.NotBlank;

@RegisterForReflection
public record EmbedUrlRequest(
        @JsonProperty("url")
        @NotBlank
        String url,
        @JsonProperty("collection_name")
        String collectionName,
        @JsonProperty("version")
        String version,
        @JsonProperty("overwrite")
        Boolean overwrite,
        @JsonProperty("max_depth")
        Integer maxDepth
) {
    public EmbedUrlRequest {
        if (maxDepth == null || maxDepth < 1) {
            maxDepth = 3;
        }
        if (overwrite == null) {
            overwrite = Boolean.FALSE;
        }
    }
}

