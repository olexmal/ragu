package ai.ragu.api;

import ai.ragu.api.model.QueryRequest;
import ai.ragu.api.model.QueryResponse;
import ai.ragu.api.model.QueryStats;
import ai.ragu.api.model.SourceDocument;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.List;

/**
 * Mirrors /query, /query/multi-version, and /query/compare routes.
 */
@Path("/query")
@Consumes(MediaType.APPLICATION_JSON)
@Produces(MediaType.APPLICATION_JSON)
public class QueryResource extends BaseResource {

    @POST
    public Response query(QueryRequest request) {
        QueryResponse response = new QueryResponse(
                "Answer placeholder until LangChain4j pipeline is connected",
                request.query(),
                List.of(new SourceDocument("No documents retrieved (stub)", null)),
                1,
                new QueryStats(0d, 0d, null, null, null, null, null, null)
        );
        return Response.ok(response).build();
    }

    @POST
    @Path("/multi-version")
    public Response multiVersion(QueryRequest request) {
        return notImplemented("Multi-version query");
    }

    @POST
    @Path("/compare")
    public Response compare(QueryRequest request) {
        return notImplemented("Version comparison query");
    }
}

