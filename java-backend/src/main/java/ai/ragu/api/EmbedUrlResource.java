package ai.ragu.api;

import ai.ragu.api.model.EmbedUrlRequest;
import ai.ragu.api.model.TaskEnqueueResponse;
import ai.ragu.api.model.TaskStatusResponse;
import io.smallrye.mutiny.Multi;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.jboss.resteasy.reactive.RestStreamElementType;

import java.time.Instant;

/**
 * Mirrors the async scraping endpoints: /embed-url*, SSE stream, cancel + status.
 */
@Path("/embed-url")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class EmbedUrlResource extends BaseResource {

    private static final String PLACEHOLDER_TASK_ID = "pending-task-id";

    @POST
    public Response enqueue(EmbedUrlRequest request) {
        TaskEnqueueResponse response = new TaskEnqueueResponse(
                "URL scraping and embedding job queued",
                PLACEHOLDER_TASK_ID,
                "/embed-url/status/" + PLACEHOLDER_TASK_ID
        );
        return Response.accepted(response).build();
    }

    @GET
    @Path("/status/{taskId}")
    public Response status(@PathParam("taskId") String taskId) {
        TaskStatusResponse response = new TaskStatusResponse(
                taskId,
                "PENDING",
                "Kafka-backed scrape pipeline not wired yet",
                0,
                null,
                null,
                null
        );
        return Response.ok(response).build();
    }

    @POST
    @Path("/cancel/{taskId}")
    public Response cancel(@PathParam("taskId") String taskId) {
        TaskStatusResponse response = new TaskStatusResponse(
                taskId,
                "REVOKED",
                "Task cancellation placeholder until Kafka wiring is completed",
                0,
                null,
                null,
                null
        );
        return Response.accepted(response).build();
    }

    @GET
    @Path("/stream/{taskId}")
    @Produces(MediaType.SERVER_SENT_EVENTS)
    @RestStreamElementType(MediaType.APPLICATION_JSON)
    public Multi<TaskStatusResponse> stream(@PathParam("taskId") String taskId) {
        return Multi.createFrom().item(() -> new TaskStatusResponse(
                taskId,
                "PENDING",
                "SSE stream placeholder until Kafka progress events are connected",
                0,
                null,
                Instant.now().toString(),
                null
        ));
    }
}

