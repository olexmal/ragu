package ai.ragu.api;

import ai.ragu.api.model.EmbedUrlRequest;
import ai.ragu.api.model.TaskEnqueueResponse;
import ai.ragu.api.model.TaskStatusResponse;
import ai.ragu.tasks.ScrapeTaskService;
import io.smallrye.mutiny.Multi;
import jakarta.inject.Inject;
import jakarta.ws.rs.*;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.jboss.resteasy.reactive.RestStreamElementType;

import java.util.Map;

/**
 * Mirrors the async scraping endpoints: /embed-url*, SSE stream, cancel + status.
 */
@Path("/embed-url")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class EmbedUrlResource extends BaseResource {

    private final ScrapeTaskService taskService;

    @Inject
    public EmbedUrlResource(ScrapeTaskService taskService) {
        this.taskService = taskService;
    }

    @POST
    public Response enqueue(EmbedUrlRequest request) {
        TaskEnqueueResponse response = taskService.enqueue(request);
        return Response.accepted(response).build();
    }

    @GET
    @Path("/status/{taskId}")
    public Response status(@PathParam("taskId") String taskId) {
        return taskService.getStatus(taskId)
                .map(status -> Response.ok(status).build())
                .orElseGet(() -> Response.status(Response.Status.NOT_FOUND)
                        .entity(Map.of("message", "Task not found", "task_id", taskId))
                        .build());
    }

    @POST
    @Path("/cancel/{taskId}")
    public Response cancel(@PathParam("taskId") String taskId) {
        TaskStatusResponse response = taskService.cancel(taskId);
        return Response.accepted(response).build();
    }

    @GET
    @Path("/stream/{taskId}")
    @Produces(MediaType.SERVER_SENT_EVENTS)
    @RestStreamElementType(MediaType.APPLICATION_JSON)
    public Multi<TaskStatusResponse> stream(@PathParam("taskId") String taskId) {
        return taskService.stream(taskId);
    }
}

