package ai.ragu.api;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

/**
 * Mirrors POST /embed-batch from the Python API.
 */
@Path("/embed-batch")
@Consumes(MediaType.APPLICATION_FORM_URLENCODED)
@Produces(MediaType.APPLICATION_JSON)
public class EmbedBatchResource extends BaseResource {

    @POST
    public Response embedDirectory() {
        return notImplemented("Batch embedding");
    }
}

