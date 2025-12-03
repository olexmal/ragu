package ai.ragu.api;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.List;
import java.util.Map;

/**
 * Mirrors /history*, including search and export.
 */
@Path("/history")
@Produces(MediaType.APPLICATION_JSON)
public class HistoryResource extends BaseResource {

    @GET
    public Response history(@QueryParam("limit") Integer limit, @QueryParam("offset") Integer offset) {
        return Response.ok(
                Map.of(
                        "history", List.of(),
                        "total", 0,
                        "limit", limit == null ? 50 : limit,
                        "offset", offset == null ? 0 : offset,
                        "message", "Query history storage not wired yet"
                )
        ).build();
    }

    @GET
    @Path("/search")
    public Response search(@QueryParam("q") String query, @QueryParam("limit") Integer limit) {
        return notImplemented("History search");
    }

    @GET
    @Path("/export")
    public Response export(@QueryParam("format") String format) {
        return notImplemented("History export");
    }
}

