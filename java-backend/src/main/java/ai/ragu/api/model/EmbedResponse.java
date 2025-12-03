package ai.ragu.api.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.quarkus.runtime.annotations.RegisterForReflection;

@RegisterForReflection
@JsonInclude(JsonInclude.Include.NON_NULL)
public record EmbedResponse(
        @JsonProperty("message")
        String message,
        @JsonProperty("version")
        String version,
        @JsonProperty("collection_name")
        String collectionName,
        @JsonProperty("mode")
        String mode,
        @JsonProperty("filename")
        String filename
) {
}

