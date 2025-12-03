package ai.ragu.api;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

/**
 * Mirrors POST /embed from the Python API.
 */
@Path("/embed")
@Consumes(MediaType.MULTIPART_FORM_DATA)
@Produces(MediaType.APPLICATION_JSON)
public class EmbedResource extends BaseResource {

    @POST
    public Response embedFile() {
        return notImplemented("File embedding");
    }
}

