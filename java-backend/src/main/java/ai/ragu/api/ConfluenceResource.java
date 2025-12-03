package ai.ragu.api;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

/**
 * Mirrors /confluence/test|fetch|import endpoints.
 */
@Path("/confluence")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class ConfluenceResource extends BaseResource {

    @POST
    @Path("/test")
    public Response test() {
        return notImplemented("Confluence connection test");
    }

    @POST
    @Path("/fetch")
    public Response fetch() {
        return notImplemented("Confluence bulk fetch");
    }

    @POST
    @Path("/import")
    public Response importPage() {
        return notImplemented("Confluence page import");
    }
}

