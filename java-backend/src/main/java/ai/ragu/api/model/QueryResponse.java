package ai.ragu.api.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.quarkus.runtime.annotations.RegisterForReflection;

import java.util.Collections;
import java.util.List;

@RegisterForReflection
@JsonInclude(JsonInclude.Include.NON_NULL)
public record QueryResponse(
        @JsonProperty("answer")
        String answer,
        @JsonProperty("query")
        String query,
        @JsonProperty("sources")
        List<SourceDocument> sources,
        @JsonProperty("source_count")
        int sourceCount,
        @JsonProperty("stats")
        QueryStats stats
) {
    public QueryResponse {
        if (sources == null) {
            sources = Collections.emptyList();
        }
        if (sourceCount < 0) {
            sourceCount = sources.size();
        }
    }
}

