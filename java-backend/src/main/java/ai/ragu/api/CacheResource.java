package ai.ragu.api;

import ai.ragu.storage.CacheService;
import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.Map;

/**
 * Mirrors cache management endpoints with Redis-backed clearing.
 */
@Path("/cache")
@Produces(MediaType.APPLICATION_JSON)
public class CacheResource extends BaseResource {

    @Inject
    CacheService cacheService;

    @POST
    @Path("/clear")
    public Response clear() {
        long cleared = cacheService.clear();
        return Response.ok(Map.of(
                "success", true,
                "message", "Cache cleared successfully",
                "cleared", cleared
        )).build();
    }

    @GET
    @Path("/stats")
    public Response stats() {
        long size = cacheService.getCacheSize();
        return Response.ok(Map.of(
                "cache_size", size,
                "message", "Cache statistics"
        )).build();
    }
}
