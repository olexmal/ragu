package ai.ragu.api.model;

import com.fasterxml.jackson.annotation.JsonProperty;
import io.quarkus.runtime.annotations.RegisterForReflection;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;

import java.util.List;

@RegisterForReflection
public record MultiVersionQueryRequest(
        @JsonProperty("query")
        @NotBlank
        String query,
        @JsonProperty("versions")
        @NotEmpty
        List<String> versions,
        @JsonProperty("k")
        Integer k
) {
    public MultiVersionQueryRequest {
        if (k == null || k < 1) {
            k = 3;
        }
    }
}

