package ai.ragu.api;

import ai.ragu.storage.FavoritesStorageService;
import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.List;
import java.util.Map;

/**
 * Mirrors GET/POST/DELETE /favorites with Redis-backed storage.
 */
@Path("/favorites")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class FavoritesResource extends BaseResource {

    @Inject
    FavoritesStorageService favoritesStorage;

    @GET
    public Response list() {
        List<String> favorites = favoritesStorage.list();
        return Response.ok(Map.of(
                "favorites", favorites,
                "total", favorites.size()
        )).build();
    }

    @POST
    public Response add(Map<String, String> payload) {
        String query = payload.get("query");
        if (query == null || query.isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("success", false, "message", "Query is required"))
                    .build();
        }

        boolean added = favoritesStorage.add(query);
        return Response.ok(Map.of(
                "success", true,
                "message", added ? "Added to favorites" : "Already in favorites",
                "query", query
        )).build();
    }

    @DELETE
    public Response remove(@QueryParam("query") String query) {
        if (query == null || query.isBlank()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("success", false, "message", "Query parameter is required"))
                    .build();
        }

        boolean removed = favoritesStorage.remove(query);
        return Response.ok(Map.of(
                "success", removed,
                "message", removed ? "Removed from favorites" : "Not found in favorites",
                "query", query
        )).build();
    }
}
