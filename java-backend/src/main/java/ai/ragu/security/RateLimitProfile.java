package ai.ragu.security;

public record RateLimitProfile(int limit, int windowSeconds) {
}

