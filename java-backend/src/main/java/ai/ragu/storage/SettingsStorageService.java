package ai.ragu.storage;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import io.quarkus.redis.datasource.RedisDataSource;
import io.quarkus.redis.datasource.value.ValueCommands;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

/**
 * Redis-backed storage for application settings (system, confluence, llm-providers).
 */
@ApplicationScoped
public class SettingsStorageService {

    private static final String SYSTEM_KEY = "ragu:settings:system";
    private static final String CONFLUENCE_KEY = "ragu:settings:confluence";
    private static final String LLM_PROVIDERS_KEY = "ragu:settings:llm-providers";

    private final ValueCommands<String, String> redis;
    private final ObjectMapper objectMapper;

    @Inject
    public SettingsStorageService(RedisDataSource ds, ObjectMapper objectMapper) {
        this.redis = ds.value(String.class);
        this.objectMapper = objectMapper;
    }

    // ============ System Settings ============

    public Map<String, Object> getSystemSettings() {
        return getJson(SYSTEM_KEY).orElseGet(() -> Map.of("systemName", "RAGU"));
    }

    public void saveSystemSettings(Map<String, Object> settings) {
        saveJson(SYSTEM_KEY, settings);
    }

    // ============ Confluence Settings ============

    public Map<String, Object> getConfluenceSettings() {
        return getJson(CONFLUENCE_KEY).orElseGet(this::defaultConfluenceSettings);
    }

    public void saveConfluenceSettings(Map<String, Object> settings) {
        saveJson(CONFLUENCE_KEY, settings);
    }

    private Map<String, Object> defaultConfluenceSettings() {
        Map<String, Object> defaults = new HashMap<>();
        defaults.put("enabled", false);
        defaults.put("url", "");
        defaults.put("instance_type", "cloud");
        defaults.put("api_token", "");
        defaults.put("username", "");
        defaults.put("password", "");
        defaults.put("page_ids", java.util.List.of());
        defaults.put("auto_sync", false);
        defaults.put("sync_interval", 3600);
        return defaults;
    }

    // ============ LLM Provider Settings ============

    public Map<String, Object> getLLMProviders() {
        return getJson(LLM_PROVIDERS_KEY).orElseGet(this::defaultLLMProviders);
    }

    public void saveLLMProviders(Map<String, Object> providers) {
        saveJson(LLM_PROVIDERS_KEY, providers);
    }

    private Map<String, Object> defaultLLMProviders() {
        Map<String, Object> defaults = new HashMap<>();
        defaults.put("llm_providers", new HashMap<>());
        defaults.put("embedding_providers", new HashMap<>());
        return defaults;
    }

    /**
     * Returns active providers (first enabled one in each category).
     */
    @SuppressWarnings("unchecked")
    public Map<String, Object> getActiveProviders() {
        Map<String, Object> providers = getLLMProviders();
        Map<String, Object> result = new HashMap<>();

        Map<String, Object> llmProviders = (Map<String, Object>) providers.getOrDefault("llm_providers", Map.of());
        Map<String, Object> embeddingProviders = (Map<String, Object>) providers.getOrDefault("embedding_providers", Map.of());

        result.put("llm", findActiveProvider(llmProviders));
        result.put("embedding", findActiveProvider(embeddingProviders));

        return result;
    }

    @SuppressWarnings("unchecked")
    private Map<String, Object> findActiveProvider(Map<String, Object> providers) {
        for (Map.Entry<String, Object> entry : providers.entrySet()) {
            if (entry.getValue() instanceof Map<?, ?> config) {
                Map<String, Object> providerConfig = (Map<String, Object>) config;
                Boolean isActive = (Boolean) providerConfig.getOrDefault("is_active", false);
                if (Boolean.TRUE.equals(isActive)) {
                    return providerConfig;
                }
            }
        }
        return Map.of("provider", "none");
    }

    // ============ Helper Methods ============

    private Optional<Map<String, Object>> getJson(String key) {
        String json = redis.get(key);
        if (json == null || json.isBlank()) {
            return Optional.empty();
        }
        try {
            return Optional.of(objectMapper.readValue(json, new TypeReference<>() {}));
        } catch (JsonProcessingException e) {
            return Optional.empty();
        }
    }

    private void saveJson(String key, Map<String, Object> data) {
        try {
            String json = objectMapper.writeValueAsString(data);
            redis.set(key, json);
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Failed to serialize settings", e);
        }
    }
}

