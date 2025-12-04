package ai.ragu.security;

import io.quarkus.redis.datasource.RedisDataSource;
import io.quarkus.redis.datasource.value.ValueCommands;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import java.time.Duration;
import java.util.Optional;
import java.util.UUID;

/**
 * Redis-backed session management for cookie-based authentication.
 */
@ApplicationScoped
public class SessionService {

    private static final String SESSION_PREFIX = "ragu:session:";

    private final ValueCommands<String, String> redis;
    private final Duration sessionTtl;

    @Inject
    public SessionService(RedisDataSource ds,
                          @ConfigProperty(name = "ragu.auth.session-ttl-minutes", defaultValue = "1440") int ttlMinutes) {
        this.redis = ds.value(String.class);
        this.sessionTtl = Duration.ofMinutes(ttlMinutes);
    }

    /**
     * Creates a new session for the given username and returns the session ID.
     */
    public String createSession(String username) {
        String sessionId = UUID.randomUUID().toString();
        redis.setex(SESSION_PREFIX + sessionId, sessionTtl.toSeconds(), username);
        return sessionId;
    }

    /**
     * Validates a session and returns the associated username if valid.
     */
    public Optional<String> validateSession(String sessionId) {
        if (sessionId == null || sessionId.isBlank()) {
            return Optional.empty();
        }
        String username = redis.get(SESSION_PREFIX + sessionId);
        if (username != null) {
            // Refresh TTL on each valid access
            redis.setex(SESSION_PREFIX + sessionId, sessionTtl.toSeconds(), username);
            return Optional.of(username);
        }
        return Optional.empty();
    }

    /**
     * Invalidates a session.
     */
    public void invalidateSession(String sessionId) {
        if (sessionId != null && !sessionId.isBlank()) {
            redis.getdel(SESSION_PREFIX + sessionId);
        }
    }
}

