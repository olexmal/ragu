package ai.ragu.api.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.quarkus.runtime.annotations.RegisterForReflection;

import java.util.Collections;
import java.util.Map;

@RegisterForReflection
@JsonInclude(JsonInclude.Include.NON_NULL)
public record SourceDocument(
        @JsonProperty("content")
        String content,
        @JsonProperty("metadata")
        Map<String, Object> metadata
) {
    public SourceDocument {
        if (metadata == null) {
            metadata = Collections.emptyMap();
        }
    }
}

