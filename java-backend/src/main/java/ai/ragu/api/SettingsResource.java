package ai.ragu.api;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.DefaultValue;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.Map;

/**
 * Mirrors /settings/* endpoints.
 */
@Path("/settings")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class SettingsResource extends BaseResource {

    @GET
    @Path("/confluence")
    public Response getConfluence() {
        return Response.ok(
                Map.of(
                        "url", "",
                        "instance_type", "cloud",
                        "message", "Confluence settings pending migration"
                )
        ).build();
    }

    @POST
    @Path("/confluence")
    public Response saveConfluence() {
        return notImplemented("Confluence settings persistence");
    }

    @GET
    @Path("/system")
    public Response getSystem() {
        return Response.ok(Map.of("systemName", "RAGU")).build();
    }

    @POST
    @Path("/system")
    public Response saveSystem() {
        return notImplemented("System settings persistence");
    }

    @GET
    @Path("/llm-providers")
    public Response getProviders() {
        return Response.ok(Map.of("llm_providers", Map.of(), "embedding_providers", Map.of())).build();
    }

    @POST
    @Path("/llm-providers")
    public Response saveProviders() {
        return notImplemented("LLM provider persistence");
    }

    @GET
    @Path("/llm-providers/active")
    public Response getActiveProviders() {
        return Response.ok(
                Map.of(
                        "llm", Map.of("provider", "pending"),
                        "embedding", Map.of("provider", "pending")
                )
        ).build();
    }

    @GET
    @Path("/llm-providers/models")
    public Response listModels(@QueryParam("provider_type") String providerType,
                               @QueryParam("category") @DefaultValue("llm") String category,
                               @QueryParam("api_key") String apiKey) {
        return notImplemented("Provider model listing");
    }

    @POST
    @Path("/llm-providers/test")
    public Response testProviders() {
        return notImplemented("Provider connection testing");
    }
}

