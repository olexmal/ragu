package ai.ragu.api;

import ai.ragu.storage.HistoryStorageService;
import jakarta.inject.Inject;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.List;
import java.util.Map;

/**
 * Mirrors /history*, including search and export with Redis-backed storage.
 */
@Path("/history")
@Produces(MediaType.APPLICATION_JSON)
public class HistoryResource extends BaseResource {

    @Inject
    HistoryStorageService historyStorage;

    @GET
    public Response history(@QueryParam("limit") Integer limit, @QueryParam("offset") Integer offset) {
        int effectiveLimit = limit == null || limit < 1 ? 50 : Math.min(limit, 200);
        int effectiveOffset = offset == null || offset < 0 ? 0 : offset;

        List<Map<String, Object>> entries = historyStorage.list(effectiveLimit, effectiveOffset);
        long total = historyStorage.total();

        return Response.ok(Map.of(
                "history", entries,
                "total", total,
                "limit", effectiveLimit,
                "offset", effectiveOffset
        )).build();
    }

    @GET
    @Path("/search")
    public Response search(@QueryParam("q") String query, @QueryParam("limit") Integer limit) {
        int effectiveLimit = limit == null || limit < 1 ? 20 : Math.min(limit, 100);

        List<Map<String, Object>> results = historyStorage.search(query, effectiveLimit);

        return Response.ok(Map.of(
                "results", results,
                "total", results.size(),
                "query", query != null ? query : ""
        )).build();
    }

    @GET
    @Path("/export")
    public Response export(@QueryParam("format") String format) {
        Object exported = historyStorage.export(format);

        if ("csv".equalsIgnoreCase(format)) {
            return Response.ok(exported)
                    .type("text/csv")
                    .header("Content-Disposition", "attachment; filename=query-history.csv")
                    .build();
        }

        return Response.ok(Map.of("history", exported)).build();
    }
}
