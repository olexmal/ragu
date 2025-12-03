package ai.ragu.api.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.quarkus.runtime.annotations.RegisterForReflection;

@RegisterForReflection
@JsonInclude(JsonInclude.Include.NON_NULL)
public record QueryStats(
        @JsonProperty("request_total_time")
        Double requestTotalTime,
        @JsonProperty("request_overhead_time")
        Double requestOverheadTime,
        @JsonProperty("cache_lookup_time")
        Double cacheLookupTime,
        @JsonProperty("llm_init_time")
        Double llmInitTime,
        @JsonProperty("vector_db_init_time")
        Double vectorDbInitTime,
        @JsonProperty("multi_query_generation_time")
        Double multiQueryGenerationTime,
        @JsonProperty("document_retrieval_time")
        Double documentRetrievalTime,
        @JsonProperty("answer_generation_time")
        Double answerGenerationTime
) {
}

