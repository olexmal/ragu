package ai.ragu.api.model;

import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonProperty;
import io.quarkus.runtime.annotations.RegisterForReflection;

@RegisterForReflection
@JsonInclude(JsonInclude.Include.NON_NULL)
public record TaskStatusResponse(
        @JsonProperty("task_id")
        String taskId,
        @JsonProperty("state")
        String state,
        @JsonProperty("status")
        String status,
        @JsonProperty("progress")
        Integer progress,
        @JsonProperty("url")
        String url,
        @JsonProperty("result")
        Object result,
        @JsonProperty("error")
        String error
) {
    public TaskStatusResponse {
        if (progress != null && progress < 0) {
            progress = 0;
        }
    }
}

