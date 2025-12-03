package ai.ragu.api;

import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.Map;

/**
 * Mirrors /auth/login, /auth/logout, /auth/status.
 */
@Path("/auth")
@Consumes(MediaType.APPLICATION_JSON)
@Produces(MediaType.APPLICATION_JSON)
public class AuthResource extends BaseResource {

    @POST
    @Path("/login")
    public Response login() {
        return notImplemented("Username/password authentication");
    }

    @POST
    @Path("/logout")
    public Response logout() {
        return notImplemented("Session logout");
    }

    @GET
    @Path("/status")
    public Response status() {
        return Response.ok(
                Map.of(
                        "enabled", true,
                        "mode", "pending-java-port",
                        "message", "Auth configuration will be mirrored from Python settings"
                )
        ).build();
    }
}

