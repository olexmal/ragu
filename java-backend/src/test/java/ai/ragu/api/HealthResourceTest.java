package ai.ragu.api;

import io.quarkus.test.junit.QuarkusTest;
import org.junit.jupiter.api.Test;

import static io.restassured.RestAssured.given;
import static org.hamcrest.CoreMatchers.equalTo;

@QuarkusTest
class HealthResourceTest {
    @Test
    void testHelloEndpoint() {
        given()
          .when().get("/health")
          .then()
             .statusCode(200)
             .body("status", equalTo("initializing"))
             .body("service", equalTo("RAGU Java Backend"))
             .body("llmProvider", equalTo("pending"))
             .body("dependencies.redis", equalTo("redis://localhost:6379/0"))
             .body("dependencies.kafka", equalTo("localhost:9092"))
             .body("dependencies.qdrant", equalTo("http://localhost:6333"));
    }

}