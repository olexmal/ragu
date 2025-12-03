package ai.ragu.api;

import io.smallrye.mutiny.Multi;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.jboss.resteasy.reactive.RestStreamElementType;

import java.time.Instant;
import java.util.Map;

/**
 * Mirrors the async scraping endpoints: /embed-url*, SSE stream, cancel + status.
 */
@Path("/embed-url")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class EmbedUrlResource extends BaseResource {

    @POST
    public Response enqueue(Map<String, Object> request) {
        return notImplemented("URL scraping and embedding");
    }

    @GET
    @Path("/status/{taskId}")
    public Response status(@PathParam("taskId") String taskId) {
        return Response.ok(
                Map.of(
                        "taskId", taskId,
                        "state", "PENDING",
                        "message", "Kafka-backed scrape pipeline not wired yet"
                )
        ).build();
    }

    @POST
    @Path("/cancel/{taskId}")
    public Response cancel(@PathParam("taskId") String taskId) {
        return notImplemented("URL embedding cancellation");
    }

    @GET
    @Path("/stream/{taskId}")
    @Produces(MediaType.SERVER_SENT_EVENTS)
    @RestStreamElementType(MediaType.APPLICATION_JSON)
    public Multi<Map<String, Object>> stream(@PathParam("taskId") String taskId) {
        return Multi.createFrom().item(() -> Map.of(
                "taskId", taskId,
                "state", "PENDING",
                "progress", 0,
                "timestamp", Instant.now().toString(),
                "message", "SSE stream placeholder until Kafka progress events are connected"
        ));
    }
}

