package ai.ragu.api;

import io.quarkus.test.junit.QuarkusTest;
import io.restassured.common.mapper.TypeRef;
import io.restassured.http.ContentType;
import io.restassured.response.Response;
import org.junit.jupiter.api.Test;

import java.nio.charset.StandardCharsets;
import java.util.Map;

import static io.restassured.RestAssured.given;
import static org.hamcrest.MatcherAssert.assertThat;
import static org.hamcrest.Matchers.containsString;
import static org.hamcrest.Matchers.equalTo;
import static org.hamcrest.Matchers.greaterThanOrEqualTo;
import static org.hamcrest.Matchers.notNullValue;

@QuarkusTest
class PhaseSevenIntegrationTest {

    private static final TypeRef<Map<String, Object>> MAP_TYPE = new TypeRef<>() {};

    @Test
    void shouldEmbedDocumentViaMultipartUpload() {
        given()
                .multiPart("file", "phase7.txt", "Phase 7 embed flow".getBytes(StandardCharsets.UTF_8))
                .multiPart("collection_name", "phase7-embed")
                .multiPart("version", "v1")
                .multiPart("overwrite", "true")
        .when()
                .post("/embed")
        .then()
                .statusCode(200)
                .body("message", containsString("Embedded"))
                .body("collection_name", equalTo("phase7-embed-v1"))
                .body("mode", equalTo("overwrite"))
                .body("filename", equalTo("phase7.txt"));
    }

    @Test
    void shouldQueryEmbeddedContent() {
        String collection = "phase7-query";
        embedFixture(collection, "v1", "Phase 7 query doc");

        given()
                .contentType(ContentType.JSON)
                .body(Map.of(
                        "query", "What does the phase 7 doc say?",
                        "collection_name", collection,
                        "version", "v1",
                        "k", 2
                ))
        .when()
                .post("/query")
        .then()
                .statusCode(200)
                .body("answer", containsString("Placeholder"))
                .body("sources.size()", greaterThanOrEqualTo(1))
                .body("sources[0].content", containsString("Phase 7 query doc"));
    }

    @Test
    void shouldRunScrapeTaskToCompletion() throws InterruptedException {
        String taskId = given()
                .contentType(ContentType.JSON)
                .body(Map.of(
                        "url", "https://example.com/docs/phase7",
                        "collection_name", "phase7-scrape",
                        "version", "v1"
                ))
        .when()
                .post("/embed-url")
        .then()
                .statusCode(202)
                .body("task_id", notNullValue())
                .extract()
                .path("task_id");

        Map<String, Object> finalStatus = waitForTaskCompletion(taskId);
        assertThat(finalStatus.get("state"), equalTo("SUCCESS"));
        assertThat(((Number) finalStatus.get("progress")).intValue(), equalTo(100));
    }

    private void embedFixture(String collection, String version, String content) {
        given()
                .multiPart("file", collection + ".txt", content.getBytes(StandardCharsets.UTF_8))
                .multiPart("collection_name", collection)
                .multiPart("version", version)
                .multiPart("overwrite", "true")
        .when()
                .post("/embed")
        .then()
                .statusCode(200);
    }

    private Map<String, Object> waitForTaskCompletion(String taskId) throws InterruptedException {
        for (int i = 0; i < 60; i++) {
            Response response = given()
                    .when()
                    .get("/embed-url/status/" + taskId);
            if (response.getStatusCode() == 200) {
                Map<String, Object> status = response.as(MAP_TYPE);
                Object state = status.get("state");
                if ("SUCCESS".equals(state) || "FAILURE".equals(state) || "REVOKED".equals(state)) {
                    return status;
                }
            }
            Thread.sleep(100);
        }
        throw new AssertionError("Task did not complete in time");
    }
}

