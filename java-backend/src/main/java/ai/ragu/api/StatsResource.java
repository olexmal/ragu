package ai.ragu.api;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.Map;

/**
 * Mirrors GET /stats.
 */
@Path("/stats")
@Produces(MediaType.APPLICATION_JSON)
public class StatsResource {

    @GET
    public Response stats() {
        return Response.ok(
                Map.of(
                        "query_stats", Map.of(),
                        "embedding_stats", Map.of(),
                        "cache_stats", Map.of(),
                        "message", "Metrics pipeline will be connected in a later phase"
                )
        ).build();
    }
}

