package ai.ragu.api;

import ai.ragu.security.AuthService;
import jakarta.inject.Inject;
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

    @Inject
    AuthService authService;

    @POST
    @Path("/login")
    public Response login(Map<String, String> payload) {
        String username = payload.getOrDefault("username", "");
        String password = payload.getOrDefault("password", "");
        if (authService.verifyCredentials(username, password)) {
            return Response.ok(Map.of("message", "Login successful")).build();
        }
        return Response.status(Response.Status.UNAUTHORIZED)
                .entity(Map.of("message", "Invalid credentials"))
                .build();
    }

    @POST
    @Path("/logout")
    public Response logout() {
        return Response.ok(Map.of("message", "Logout successful")).build();
    }

    @GET
    @Path("/status")
    public Response status() {
        return Response.ok(authService.status()).build();
    }
}

