package ai.ragu.api;

import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

/**
 * Mirrors POST /cache/clear.
 */
@Path("/cache")
@Produces(MediaType.APPLICATION_JSON)
public class CacheResource extends BaseResource {

    @POST
    @Path("/clear")
    public Response clear() {
        return notImplemented("Cache clearing");
    }
}

