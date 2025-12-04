package ai.ragu.security;

import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import jakarta.ws.rs.container.ContainerRequestContext;
import jakarta.ws.rs.core.Cookie;
import jakarta.ws.rs.core.HttpHeaders;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@ApplicationScoped
public class AuthService {

    private final boolean enabled;
    private final String username;
    private final String password;
    private final String apiKey;
    private final String sessionCookieName;
    private final RateLimitProfile readProfile;
    private final RateLimitProfile writeProfile;
    private final RateLimiterService rateLimiterService;
    private final SessionService sessionService;

    @Inject
    public AuthService(
            @ConfigProperty(name = "ragu.auth.enabled", defaultValue = "false") boolean enabled,
            @ConfigProperty(name = "ragu.auth.username", defaultValue = "admin") String username,
            @ConfigProperty(name = "ragu.auth.password", defaultValue = "changeme") String password,
            @ConfigProperty(name = "ragu.auth.api-key", defaultValue = "unset") String apiKey,
            @ConfigProperty(name = "ragu.auth.session-cookie-name", defaultValue = "RAGU_SESSION") String sessionCookieName,
            @ConfigProperty(name = "ragu.rate-limit.read.per-minute", defaultValue = "60") int readLimit,
            @ConfigProperty(name = "ragu.rate-limit.write.per-minute", defaultValue = "30") int writeLimit,
            RateLimiterService rateLimiterService,
            SessionService sessionService
    ) {
        this.enabled = enabled;
        this.username = username;
        this.password = password;
        this.apiKey = "unset".equalsIgnoreCase(apiKey) ? "" : apiKey;
        this.sessionCookieName = sessionCookieName;
        this.readProfile = new RateLimitProfile(readLimit, 60);
        this.writeProfile = new RateLimitProfile(writeLimit, 60);
        this.rateLimiterService = rateLimiterService;
        this.sessionService = sessionService;
    }

    public Response checkAccess(ContainerRequestContext context, boolean writeAccess) {
        if (enabled && !authenticate(context, writeAccess)) {
            return Response.status(Response.Status.UNAUTHORIZED)
                    .entity(Map.of("message", "Authentication required"))
                    .type(MediaType.APPLICATION_JSON_TYPE)
                    .build();
        }

        RateLimitProfile profile = writeAccess ? writeProfile : readProfile;
        String key = rateLimitKey(context);
        if (!rateLimiterService.allow(key, profile)) {
            return Response.status(Response.Status.TOO_MANY_REQUESTS)
                    .entity(Map.of("message", "Rate limit exceeded", "retry_after", profile.windowSeconds()))
                    .type(MediaType.APPLICATION_JSON_TYPE)
                    .build();
        }
        return null;
    }

    public boolean verifyCredentials(String providedUser, String providedPassword) {
        if (!enabled) {
            return true;
        }
        return username.equals(providedUser) && password.equals(providedPassword);
    }

    /**
     * Creates a new session for the given username.
     * @return the session ID to be set as a cookie
     */
    public String createSession(String username) {
        return sessionService.createSession(username);
    }

    /**
     * Invalidates a session by ID.
     */
    public void invalidateSession(String sessionId) {
        sessionService.invalidateSession(sessionId);
    }

    /**
     * Returns status info including whether the current session is authenticated.
     */
    public Map<String, Object> status(String sessionId) {
        Map<String, Object> result = new HashMap<>();
        result.put("enabled", enabled);
        result.put("apiKeyConfigured", !apiKey.isBlank());

        if (!enabled) {
            // Auth disabled - always authenticated
            result.put("authenticated", true);
            result.put("username", "");
        } else {
            Optional<String> sessionUser = sessionService.validateSession(sessionId);
            result.put("authenticated", sessionUser.isPresent());
            result.put("username", sessionUser.orElse(""));
        }
        return result;
    }

    /**
     * Legacy status method for backward compatibility.
     */
    public Map<String, Object> status() {
        return status(null);
    }

    public String getSessionCookieName() {
        return sessionCookieName;
    }

    public boolean isEnabled() {
        return enabled;
    }

    private boolean authenticate(ContainerRequestContext context, boolean writeAccess) {
        if (!credentialsConfigured()) {
            return true;
        }

        // Check session cookie first
        Cookie sessionCookie = context.getCookies().get(sessionCookieName);
        if (sessionCookie != null) {
            Optional<String> sessionUser = sessionService.validateSession(sessionCookie.getValue());
            if (sessionUser.isPresent()) {
                return true;
            }
        }

        // Check API key
        if (apiKeyConfigured()) {
            String providedKey = Optional.ofNullable(context.getHeaderString("X-API-Key"))
                    .orElse(context.getHeaderString("X-Api-Key"));
            if (providedKey != null && providedKey.equals(apiKey)) {
                return true;
            }
        }

        // Check Basic auth
        String authHeader = context.getHeaderString(HttpHeaders.AUTHORIZATION);
        if (authHeader != null && authHeader.startsWith("Basic ")) {
            Optional<BasicCredentials> creds = parseBasic(authHeader.substring("Basic ".length()));
            return creds.filter(c -> c.username().equals(username) && c.password().equals(password)).isPresent();
        }

        return !writeAccess; // allow read-only calls if write protection only
    }

    private boolean credentialsConfigured() {
        return enabled && (!username.isBlank() && !password.isBlank() || apiKeyConfigured());
    }

    private boolean apiKeyConfigured() {
        return apiKey != null && !apiKey.isBlank();
    }

    private Optional<BasicCredentials> parseBasic(String encoded) {
        try {
            String decoded = new String(Base64.getDecoder().decode(encoded), StandardCharsets.UTF_8);
            int separator = decoded.indexOf(':');
            if (separator <= 0) {
                return Optional.empty();
            }
            return Optional.of(new BasicCredentials(decoded.substring(0, separator), decoded.substring(separator + 1)));
        } catch (IllegalArgumentException e) {
            return Optional.empty();
        }
    }

    private String rateLimitKey(ContainerRequestContext context) {
        String forwarded = context.getHeaderString("X-Forwarded-For");
        if (forwarded != null && !forwarded.isBlank()) {
            return forwarded.split(",")[0].trim();
        }
        List<String> remote = context.getHeaders().get("X-Real-IP");
        if (remote != null && !remote.isEmpty()) {
            return remote.get(0);
        }
        return Optional.ofNullable(context.getHeaderString("X-API-Key")).orElse("anonymous");
    }

    private record BasicCredentials(String username, String password) { }
}
