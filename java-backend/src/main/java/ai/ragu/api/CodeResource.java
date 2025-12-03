package ai.ragu.api;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

/**
 * Mirrors POST /extract-code.
 */
@Path("/extract-code")
@Consumes(MediaType.APPLICATION_JSON)
@Produces(MediaType.APPLICATION_JSON)
public class CodeResource extends BaseResource {

    @POST
    public Response extract() {
        return notImplemented("Code extraction");
    }
}

