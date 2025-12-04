package ai.ragu.api;

import ai.ragu.storage.SettingsStorageService;
import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.DefaultValue;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;

import java.util.List;
import java.util.Map;

/**
 * Mirrors /settings/* endpoints with Redis-backed persistence.
 */
@Path("/settings")
@Produces(MediaType.APPLICATION_JSON)
@Consumes(MediaType.APPLICATION_JSON)
public class SettingsResource extends BaseResource {

    @Inject
    SettingsStorageService settingsStorage;

    @GET
    @Path("/confluence")
    public Response getConfluence() {
        return Response.ok(settingsStorage.getConfluenceSettings()).build();
    }

    @POST
    @Path("/confluence")
    public Response saveConfluence(Map<String, Object> settings) {
        settingsStorage.saveConfluenceSettings(settings);
        return Response.ok(Map.of("success", true, "message", "Confluence settings saved")).build();
    }

    @GET
    @Path("/system")
    public Response getSystem() {
        return Response.ok(settingsStorage.getSystemSettings()).build();
    }

    @POST
    @Path("/system")
    public Response saveSystem(Map<String, Object> settings) {
        settingsStorage.saveSystemSettings(settings);
        return Response.ok(Map.of("success", true, "message", "System settings saved")).build();
    }

    @GET
    @Path("/llm-providers")
    public Response getProviders() {
        return Response.ok(settingsStorage.getLLMProviders()).build();
    }

    @POST
    @Path("/llm-providers")
    public Response saveProviders(Map<String, Object> providers) {
        settingsStorage.saveLLMProviders(providers);
        return Response.ok(Map.of("success", true, "message", "LLM provider settings saved")).build();
    }

    @GET
    @Path("/llm-providers/active")
    public Response getActiveProviders() {
        return Response.ok(settingsStorage.getActiveProviders()).build();
    }

    @GET
    @Path("/llm-providers/models")
    public Response listModels(@QueryParam("provider_type") String providerType,
                               @QueryParam("category") @DefaultValue("llm") String category,
                               @QueryParam("api_key") String apiKey) {
        // Return static model lists per provider type
        List<Map<String, Object>> models = switch (providerType) {
            case "ollama" -> List.of(
                    modelEntry("llama2", "Llama 2", 4096),
                    modelEntry("mistral", "Mistral 7B", 8192),
                    modelEntry("codellama", "Code Llama", 16384),
                    modelEntry("nomic-embed-text", "Nomic Embed Text", 8192)
            );
            case "openai" -> List.of(
                    modelEntry("gpt-4", "GPT-4", 8192),
                    modelEntry("gpt-4-turbo", "GPT-4 Turbo", 128000),
                    modelEntry("gpt-3.5-turbo", "GPT-3.5 Turbo", 16385),
                    modelEntry("text-embedding-3-small", "Text Embedding 3 Small", 8191),
                    modelEntry("text-embedding-3-large", "Text Embedding 3 Large", 8191)
            );
            case "openrouter" -> List.of(
                    modelEntry("openai/gpt-4-turbo", "GPT-4 Turbo (OpenRouter)", 128000),
                    modelEntry("anthropic/claude-3-opus", "Claude 3 Opus", 200000),
                    modelEntry("anthropic/claude-3-sonnet", "Claude 3 Sonnet", 200000),
                    modelEntry("meta-llama/llama-3-70b-instruct", "Llama 3 70B", 8192),
                    modelEntry("openai/text-embedding-3-small", "Text Embedding 3 Small", 8191)
            );
            case "anthropic" -> List.of(
                    modelEntry("claude-3-opus-20240229", "Claude 3 Opus", 200000),
                    modelEntry("claude-3-sonnet-20240229", "Claude 3 Sonnet", 200000),
                    modelEntry("claude-3-haiku-20240307", "Claude 3 Haiku", 200000)
            );
            case "azure-openai" -> List.of(
                    modelEntry("gpt-4", "GPT-4 (Azure)", 8192),
                    modelEntry("gpt-35-turbo", "GPT-3.5 Turbo (Azure)", 16385),
                    modelEntry("text-embedding-ada-002", "Ada Embedding (Azure)", 8191)
            );
            case "google" -> List.of(
                    modelEntry("gemini-pro", "Gemini Pro", 30720),
                    modelEntry("gemini-1.5-pro", "Gemini 1.5 Pro", 1000000),
                    modelEntry("text-embedding-004", "Text Embedding 004", 2048)
            );
            case null, default -> List.of();
        };

        return Response.ok(Map.of("models", models)).build();
    }

    @POST
    @Path("/llm-providers/test")
    public Response testProviders(Map<String, Object> request) {
        String type = (String) request.getOrDefault("type", "");
        @SuppressWarnings("unchecked")
        Map<String, Object> config = (Map<String, Object>) request.getOrDefault("config", Map.of());

        // Stub: validate required fields exist
        boolean hasApiKey = config.containsKey("api_key") && config.get("api_key") != null;
        boolean isOllama = "ollama".equals(type);

        if (isOllama || hasApiKey) {
            return Response.ok(Map.of(
                    "success", true,
                    "message", "Connection successful (stub validation)",
                    "test_response", "Provider configuration appears valid"
            )).build();
        }

        return Response.ok(Map.of(
                "success", false,
                "message", "API key is required for " + type
        )).build();
    }

    private Map<String, Object> modelEntry(String id, String name, int contextLength) {
        return Map.of(
                "id", id,
                "name", name,
                "context_length", contextLength
        );
    }
}
