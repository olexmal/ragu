package ai.ragu.api.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.quarkus.runtime.annotations.RegisterForReflection;
import jakarta.validation.constraints.NotBlank;

@RegisterForReflection
public record QueryRequest(
        @JsonProperty("query")
        @NotBlank
        String query,
        @JsonProperty("collection_name")
        String collectionName,
        @JsonProperty("version")
        String version,
        @JsonProperty("k")
        Integer k,
        @JsonProperty("simple")
        Boolean simple
) {
    public QueryRequest {
        if (k == null || k < 1) {
            k = 3;
        }
        if (simple == null) {
            simple = Boolean.FALSE;
        }
    }
}

