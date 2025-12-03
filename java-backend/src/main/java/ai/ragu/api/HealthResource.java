package ai.ragu.api;

import jakarta.ws.rs.GET;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import java.util.Map;

@Path("/health")
@Produces(MediaType.APPLICATION_JSON)
public class HealthResource {

    @ConfigProperty(name = "ragu.service.name", defaultValue = "RAGU Java Backend")
    String serviceName;

    @ConfigProperty(name = "ragu.dependencies.redis", defaultValue = "redis://localhost:6379")
    String redisEndpoint;

    @ConfigProperty(name = "ragu.dependencies.kafka", defaultValue = "localhost:9092")
    String kafkaBootstrap;

    @ConfigProperty(name = "ragu.dependencies.qdrant", defaultValue = "http://localhost:6333")
    String qdrantUrl;

    @GET
    public Response health() {
        Map<String, Object> payload = Map.of(
                "service", serviceName,
                "status", "initializing",
                "llmProvider", "pending",
                "dependencies", Map.of(
                        "redis", redisEndpoint,
                        "kafka", kafkaBootstrap,
                        "qdrant", qdrantUrl
                )
        );
        return Response.ok(payload).build();
    }
}
