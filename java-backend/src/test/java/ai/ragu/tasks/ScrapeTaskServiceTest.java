package ai.ragu.tasks;

import ai.ragu.api.model.EmbedUrlRequest;
import ai.ragu.api.model.TaskEnqueueResponse;
import ai.ragu.api.model.TaskStatusResponse;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import io.micrometer.core.instrument.simple.SimpleMeterRegistry;

import java.util.Optional;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;

import static org.junit.jupiter.api.Assertions.*;

class ScrapeTaskServiceTest {

    private final ScheduledExecutorService executor = Executors.newSingleThreadScheduledExecutor();
    private final SimpleMeterRegistry meterRegistry = new SimpleMeterRegistry();
    private final ScrapeTaskService service = new ScrapeTaskService(50, executor, meterRegistry);

    @AfterEach
    void tearDown() {
        service.shutdown();
        meterRegistry.close();
    }

    @Test
    void progressesTaskToSuccess() throws InterruptedException {
        EmbedUrlRequest request = new EmbedUrlRequest("https://example.com", "docs", "v1", false, 2);
        TaskEnqueueResponse response = service.enqueue(request);

        TaskStatusResponse finalStatus = awaitState(response.taskId(), "SUCCESS");
        assertEquals("SUCCESS", finalStatus.state());
        assertEquals(100, finalStatus.progress());
    }

    @Test
    void allowsCancellation() throws InterruptedException {
        EmbedUrlRequest request = new EmbedUrlRequest("https://example.com", "docs", "v1", false, 2);
        TaskEnqueueResponse response = service.enqueue(request);

        Thread.sleep(60);
        TaskStatusResponse cancelled = service.cancel(response.taskId());
        assertEquals("REVOKED", cancelled.state());
    }

    private TaskStatusResponse awaitState(String taskId, String state) throws InterruptedException {
        for (int i = 0; i < 200; i++) {
            Optional<TaskStatusResponse> status = service.getStatus(taskId);
            if (status.isPresent() && state.equals(status.get().state())) {
                return status.get();
            }
            Thread.sleep(20);
        }
        fail("Timed out waiting for state " + state);
        return null;
    }
}

