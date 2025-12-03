package ai.ragu.api;

import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.List;
import java.util.Map;

/**
 * Mirrors the /collections routes.
 */
@Path("/collections")
@Produces(MediaType.APPLICATION_JSON)
public class CollectionsResource extends BaseResource {

    @GET
    public Response listCollections() {
        return Response.ok(
                Map.of(
                        "collections", List.of(),
                        "total", 0,
                        "message", "Qdrant collections not yet synchronized"
                )
        ).build();
    }

    @GET
    @Path("/{version}")
    public Response getCollection(@PathParam("version") String version) {
        return notImplemented("Collection lookup for " + version);
    }

    @DELETE
    @Path("/{version}")
    public Response deleteCollection(@PathParam("version") String version) {
        return notImplemented("Collection deletion for " + version);
    }

    @GET
    @Path("/{version}/documents")
    public Response listDocuments(@PathParam("version") String version) {
        return notImplemented("Collection documents listing for " + version);
    }

    @DELETE
    @Path("/{version}/documents/{docId}")
    public Response deleteDocument(@PathParam("version") String version, @PathParam("docId") String docId) {
        return notImplemented("Document deletion for " + docId);
    }
}

