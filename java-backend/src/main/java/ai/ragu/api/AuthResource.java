package ai.ragu.api;

import ai.ragu.security.AuthService;
import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.CookieParam;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.NewCookie;
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
            String sessionId = authService.createSession(username);
            NewCookie sessionCookie = new NewCookie.Builder(authService.getSessionCookieName())
                    .value(sessionId)
                    .path("/")
                    .httpOnly(true)
                    .sameSite(NewCookie.SameSite.LAX)
                    .maxAge(24 * 60 * 60) // 24 hours
                    .build();

            return Response.ok(Map.of(
                    "success", true,
                    "message", "Login successful",
                    "username", username
            )).cookie(sessionCookie).build();
        }

        return Response.status(Response.Status.UNAUTHORIZED)
                .entity(Map.of(
                        "success", false,
                        "message", "Invalid credentials"
                ))
                .build();
    }

    @POST
    @Path("/logout")
    public Response logout(@CookieParam("RAGU_SESSION") String sessionId) {
        if (sessionId != null && !sessionId.isBlank()) {
            authService.invalidateSession(sessionId);
        }

        // Clear the cookie
        NewCookie expiredCookie = new NewCookie.Builder(authService.getSessionCookieName())
                .value("")
                .path("/")
                .httpOnly(true)
                .maxAge(0) // Expire immediately
                .build();

        return Response.ok(Map.of(
                "success", true,
                "message", "Logout successful"
        )).cookie(expiredCookie).build();
    }

    @GET
    @Path("/status")
    public Response status(@CookieParam("RAGU_SESSION") String sessionId) {
        return Response.ok(authService.status(sessionId)).build();
    }
}
