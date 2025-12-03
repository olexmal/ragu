package ai.ragu.api;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

/**
 * Mirrors GET/POST/DELETE /favorites.
 */
@Path("/favorites")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class FavoritesResource extends BaseResource {

    @GET
    public Response list() {
        return notImplemented("Favorites listing");
    }

    @POST
    public Response add() {
        return notImplemented("Favorites creation");
    }

    @DELETE
    public Response remove() {
        return notImplemented("Favorites removal");
    }
}

