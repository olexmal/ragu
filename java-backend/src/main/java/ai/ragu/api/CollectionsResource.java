package ai.ragu.api;

import ai.ragu.vector.VectorDocument;
import ai.ragu.vector.VectorStore;
import jakarta.inject.Inject;
import jakarta.ws.rs.DELETE;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.PathParam;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Mirrors the /collections routes.
 */
@Path("/collections")
@Produces(MediaType.APPLICATION_JSON)
public class CollectionsResource extends BaseResource {

    private final VectorStore vectorStore;

    @Inject
    public CollectionsResource(VectorStore vectorStore) {
        this.vectorStore = vectorStore;
    }

    @GET
    public Response listCollections() {
        List<VectorStore.CollectionSummary> summaries = vectorStore.listCollections();
        return Response.ok(
                Map.of(
                        "collections", summaries,
                        "total", summaries.size()
                )
        ).build();
    }

    @GET
    @Path("/{name}")
    public Response getCollection(@PathParam("name") String name) {
        return resolveCollectionName(name)
                .map(collection -> {
                    int count = vectorStore.getCollectionDocuments(collection, null).size();
                    return Response.ok(Map.of(
                            "name", collection,
                            "count", count
                    )).build();
                })
                .orElseGet(() -> Response.status(Response.Status.NOT_FOUND)
                        .entity(Map.of("message", "Collection not found", "collection", name))
                        .build());
    }

    @DELETE
    @Path("/{name}")
    public Response deleteCollection(@PathParam("name") String name) {
        return resolveCollectionName(name)
                .map(collection -> {
                    vectorStore.deleteCollection(collection, null);
                    return Response.ok(Map.of("message", "Deleted collection " + collection)).build();
                })
                .orElseGet(() -> Response.status(Response.Status.NOT_FOUND)
                        .entity(Map.of("message", "Collection not found", "collection", name))
                        .build());
    }

    @GET
    @Path("/{name}/documents")
    public Response listDocuments(@PathParam("name") String name) {
        return resolveCollectionName(name)
                .map(collection -> {
                    List<VectorDocument> docs = vectorStore.getCollectionDocuments(collection, null);
                    return Response.ok(Map.of(
                            "collection", collection,
                            "documents", docs,
                            "total", docs.size()
                    )).build();
                })
                .orElseGet(() -> Response.status(Response.Status.NOT_FOUND)
                        .entity(Map.of("message", "Collection not found", "collection", name))
                        .build());
    }

    @DELETE
    @Path("/{name}/documents/{docId}")
    public Response deleteDocument(@PathParam("name") String name, @PathParam("docId") String docId) {
        return resolveCollectionName(name)
                .map(collection -> {
                    var result = vectorStore.deleteDocument(collection, null, docId);
                    int status = result.success() ? Response.Status.OK.getStatusCode() : Response.Status.NOT_FOUND.getStatusCode();
                    return Response.status(status).entity(Map.of(
                            "message", result.message(),
                            "collection", collection,
                            "document", docId
                    )).build();
                })
                .orElseGet(() -> Response.status(Response.Status.NOT_FOUND)
                        .entity(Map.of("message", "Collection not found", "collection", name))
                        .build());
    }

    private Optional<String> resolveCollectionName(String identifier) {
        String lowered = identifier.toLowerCase();
        return vectorStore.listCollections().stream()
                .map(VectorStore.CollectionSummary::name)
                .filter(name -> name.equalsIgnoreCase(identifier) || name.endsWith(lowered))
                .findFirst();
    }
}

