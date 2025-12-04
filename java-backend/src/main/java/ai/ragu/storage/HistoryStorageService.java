package ai.ragu.storage;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.quarkus.redis.datasource.RedisDataSource;
import io.quarkus.redis.datasource.sortedset.ScoredValue;
import io.quarkus.redis.datasource.sortedset.SortedSetCommands;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

/**
 * Redis-backed storage for query history using sorted sets (by timestamp).
 */
@ApplicationScoped
public class HistoryStorageService {

    private static final String HISTORY_KEY = "ragu:history";

    private final SortedSetCommands<String, String> sortedSet;
    private final ObjectMapper objectMapper;

    @Inject
    public HistoryStorageService(RedisDataSource ds, ObjectMapper objectMapper) {
        this.sortedSet = ds.sortedSet(String.class);
        this.objectMapper = objectMapper;
    }

    /**
     * Adds a query entry to history.
     */
    public void addEntry(String query, String answer, int sourceCount, String collectionName) {
        Map<String, Object> entry = Map.of(
                "id", UUID.randomUUID().toString(),
                "query", query,
                "answer", truncate(answer, 500),
                "source_count", sourceCount,
                "collection_name", collectionName != null ? collectionName : "",
                "timestamp", Instant.now().toString()
        );

        try {
            String json = objectMapper.writeValueAsString(entry);
            double score = Instant.now().toEpochMilli();
            sortedSet.zadd(HISTORY_KEY, score, json);

            // Keep only last 1000 entries
            long count = sortedSet.zcard(HISTORY_KEY);
            if (count > 1000) {
                sortedSet.zremrangebyrank(HISTORY_KEY, 0, count - 1001);
            }
        } catch (JsonProcessingException e) {
            // Log and continue - history is non-critical
        }
    }

    /**
     * Lists history entries with pagination.
     */
    public List<Map<String, Object>> list(int limit, int offset) {
        // Get entries in reverse order (newest first)
        List<ScoredValue<String>> entries = sortedSet.zrangeWithScores(HISTORY_KEY, 0, -1);

        // Reverse to get newest first, then paginate
        List<Map<String, Object>> result = new ArrayList<>();
        int start = entries.size() - 1 - offset;
        int end = Math.max(start - limit, -1);

        for (int i = start; i > end && i >= 0; i--) {
            try {
                Map<String, Object> entry = objectMapper.readValue(entries.get(i).value(), new TypeReference<>() {});
                result.add(entry);
            } catch (JsonProcessingException e) {
                // Skip malformed entries
            }
        }

        return result;
    }

    /**
     * Returns total count of history entries.
     */
    public long total() {
        return sortedSet.zcard(HISTORY_KEY);
    }

    /**
     * Searches history entries by query text.
     */
    public List<Map<String, Object>> search(String searchTerm, int limit) {
        if (searchTerm == null || searchTerm.isBlank()) {
            return list(limit, 0);
        }

        String lowerSearch = searchTerm.toLowerCase();
        List<ScoredValue<String>> entries = sortedSet.zrangeWithScores(HISTORY_KEY, 0, -1);

        List<Map<String, Object>> results = new ArrayList<>();
        // Search from newest to oldest
        for (int i = entries.size() - 1; i >= 0 && results.size() < limit; i--) {
            try {
                Map<String, Object> entry = objectMapper.readValue(entries.get(i).value(), new TypeReference<>() {});
                String query = ((String) entry.getOrDefault("query", "")).toLowerCase();
                String answer = ((String) entry.getOrDefault("answer", "")).toLowerCase();

                if (query.contains(lowerSearch) || answer.contains(lowerSearch)) {
                    results.add(entry);
                }
            } catch (JsonProcessingException e) {
                // Skip malformed entries
            }
        }

        return results;
    }

    /**
     * Exports history in the requested format.
     */
    public Object export(String format) {
        List<Map<String, Object>> allEntries = list(1000, 0);

        if ("csv".equalsIgnoreCase(format)) {
            StringBuilder csv = new StringBuilder();
            csv.append("id,query,answer,source_count,collection_name,timestamp\n");

            for (Map<String, Object> entry : allEntries) {
                csv.append(escapeCsv(entry.get("id")))
                        .append(",")
                        .append(escapeCsv(entry.get("query")))
                        .append(",")
                        .append(escapeCsv(entry.get("answer")))
                        .append(",")
                        .append(entry.getOrDefault("source_count", 0))
                        .append(",")
                        .append(escapeCsv(entry.get("collection_name")))
                        .append(",")
                        .append(escapeCsv(entry.get("timestamp")))
                        .append("\n");
            }

            return csv.toString();
        }

        // Default to JSON
        return allEntries;
    }

    private String truncate(String text, int maxLength) {
        if (text == null) return "";
        return text.length() > maxLength ? text.substring(0, maxLength) + "..." : text;
    }

    private String escapeCsv(Object value) {
        if (value == null) return "";
        String str = value.toString();
        if (str.contains(",") || str.contains("\"") || str.contains("\n")) {
            return "\"" + str.replace("\"", "\"\"") + "\"";
        }
        return str;
    }
}

