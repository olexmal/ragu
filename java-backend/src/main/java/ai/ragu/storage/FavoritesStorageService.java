package ai.ragu.storage;

import io.quarkus.redis.datasource.RedisDataSource;
import io.quarkus.redis.datasource.set.SetCommands;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import java.util.List;
import java.util.Set;

/**
 * Redis-backed storage for favorite queries using a set.
 */
@ApplicationScoped
public class FavoritesStorageService {

    private static final String FAVORITES_KEY = "ragu:favorites";

    private final SetCommands<String, String> setCommands;

    @Inject
    public FavoritesStorageService(RedisDataSource ds) {
        this.setCommands = ds.set(String.class);
    }

    /**
     * Adds a query to favorites.
     */
    public boolean add(String query) {
        if (query == null || query.isBlank()) {
            return false;
        }
        return setCommands.sadd(FAVORITES_KEY, query) > 0;
    }

    /**
     * Removes a query from favorites.
     */
    public boolean remove(String query) {
        if (query == null || query.isBlank()) {
            return false;
        }
        return setCommands.srem(FAVORITES_KEY, query) > 0;
    }

    /**
     * Lists all favorite queries.
     */
    public List<String> list() {
        Set<String> favorites = setCommands.smembers(FAVORITES_KEY);
        return favorites.stream().sorted().toList();
    }

    /**
     * Checks if a query is in favorites.
     */
    public boolean contains(String query) {
        if (query == null || query.isBlank()) {
            return false;
        }
        return setCommands.sismember(FAVORITES_KEY, query);
    }
}

