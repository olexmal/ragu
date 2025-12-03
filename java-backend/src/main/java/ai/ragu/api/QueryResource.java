package ai.ragu.api;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

/**
 * Mirrors /query, /query/multi-version, and /query/compare routes.
 */
@Path("/query")
@Consumes(MediaType.APPLICATION_JSON)
@Produces(MediaType.APPLICATION_JSON)
public class QueryResource extends BaseResource {

    @POST
    public Response query() {
        return notImplemented("Primary RAG query");
    }

    @POST
    @Path("/multi-version")
    public Response multiVersion() {
        return notImplemented("Multi-version query");
    }

    @POST
    @Path("/compare")
    public Response compare() {
        return notImplemented("Version comparison query");
    }
}

