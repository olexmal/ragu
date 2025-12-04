package ai.ragu.api;

import ai.ragu.api.model.MultiVersionQueryRequest;
import ai.ragu.api.model.QueryRequest;
import ai.ragu.api.model.QueryResponse;
import ai.ragu.rag.RagService;
import ai.ragu.security.RequiresAuth;
import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.Map;

/**
 * Mirrors /query, /query/multi-version, and /query/compare routes.
 */
@Path("/query")
@Consumes(MediaType.APPLICATION_JSON)
@Produces(MediaType.APPLICATION_JSON)
@RequiresAuth
public class QueryResource extends BaseResource {

    private final RagService ragService;

    @Inject
    public QueryResource(RagService ragService) {
        this.ragService = ragService;
    }

    @POST
    public Response query(QueryRequest request) {
        QueryResponse response = ragService.handleQuery(request);
        return Response.ok(response).build();
    }

    @POST
    @Path("/multi-version")
    public Response multiVersion(MultiVersionQueryRequest request) {
        if (request.versions() == null || request.versions().isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "versions", "message", "At least one version is required"))
                    .build();
        }

        QueryResponse response = ragService.handleMultiVersionQuery(
                request.query(),
                request.versions(),
                request.k()
        );
        return Response.ok(response).build();
    }

    @POST
    @Path("/compare")
    public Response compare(MultiVersionQueryRequest request) {
        if (request.versions() == null || request.versions().isEmpty()) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(Map.of("error", "versions", "message", "At least one version is required"))
                    .build();
        }

        Map<String, Object> response = ragService.handleCompareQuery(
                request.query(),
                request.versions(),
                request.k()
        );
        return Response.ok(response).build();
    }
}
