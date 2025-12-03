package ai.ragu.security;

import jakarta.enterprise.context.ApplicationScoped;

import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@ApplicationScoped
public class RateLimiterService {

    private static final class FixedWindow {
        private long windowStart;
        private int count;

        private FixedWindow(long windowStart) {
            this.windowStart = windowStart;
        }
    }

    private final Map<String, FixedWindow> windows = new ConcurrentHashMap<>();

    public boolean allow(String key, RateLimitProfile profile) {
        long now = Instant.now().getEpochSecond();
        FixedWindow window = windows.computeIfAbsent(windowKey(key, profile), k -> new FixedWindow(now));
        synchronized (window) {
            if (now - window.windowStart >= profile.windowSeconds()) {
                window.windowStart = now;
                window.count = 0;
            }
            if (window.count >= profile.limit()) {
                return false;
            }
            window.count++;
            return true;
        }
    }

    private String windowKey(String key, RateLimitProfile profile) {
        return key + ":" + profile.windowSeconds() + ":" + profile.limit();
    }
}

