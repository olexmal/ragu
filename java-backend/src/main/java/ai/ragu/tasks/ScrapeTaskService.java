package ai.ragu.tasks;

import ai.ragu.api.model.EmbedUrlRequest;
import ai.ragu.api.model.TaskEnqueueResponse;
import ai.ragu.api.model.TaskStatusResponse;
import io.smallrye.mutiny.Multi;
import io.smallrye.mutiny.subscription.MultiEmitter;
import jakarta.annotation.PreDestroy;
import jakarta.enterprise.context.ApplicationScoped;
import jakarta.inject.Inject;
import org.eclipse.microprofile.config.inject.ConfigProperty;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import java.util.concurrent.*;

/**
 * In-memory simulation of the future Kafka-backed scrape pipeline.
 * Generates deterministic progress events so the REST/SSE surfaces can be tested today.
 */
@ApplicationScoped
public class ScrapeTaskService {

    private final long stepMillis;
    private final ScheduledExecutorService executor;
    private final ConcurrentMap<String, TaskStatusResponse> statuses = new ConcurrentHashMap<>();
    private final ConcurrentMap<String, ScheduledFuture<?>> futures = new ConcurrentHashMap<>();
    private final ConcurrentMap<String, CopyOnWriteArrayList<MultiEmitter<? super TaskStatusResponse>>> subscribers = new ConcurrentHashMap<>();

    @Inject
    public ScrapeTaskService(
            @ConfigProperty(name = "ragu.scrape.simulation-step-ms", defaultValue = "500") long stepMillis) {
        this(stepMillis, Executors.newScheduledThreadPool(2));
    }

    ScrapeTaskService(long stepMillis, ScheduledExecutorService executor) {
        this.stepMillis = Math.max(100, stepMillis);
        this.executor = executor;
    }

    public TaskEnqueueResponse enqueue(EmbedUrlRequest request) {
        String taskId = UUID.randomUUID().toString();
        TaskStatusResponse initial = new TaskStatusResponse(
                taskId,
                "PENDING",
                "Task queued",
                0,
                request.url(),
                null,
                null
        );
        statuses.put(taskId, initial);
        emit(taskId, initial);

        ScheduledFuture<?> future = executor.scheduleAtFixedRate(new ProgressJob(taskId, request), stepMillis, stepMillis, TimeUnit.MILLISECONDS);
        futures.put(taskId, future);

        return new TaskEnqueueResponse(
                "URL scraping and embedding job queued",
                taskId,
                "/embed-url/status/" + taskId
        );
    }

    public Optional<TaskStatusResponse> getStatus(String taskId) {
        return Optional.ofNullable(statuses.get(taskId));
    }

    public TaskStatusResponse cancel(String taskId) {
        ScheduledFuture<?> future = futures.remove(taskId);
        if (future != null) {
            future.cancel(true);
        }
        TaskStatusResponse cancelled = new TaskStatusResponse(
                taskId,
                "REVOKED",
                "Task cancelled",
                currentProgress(taskId),
                getStatus(taskId).map(TaskStatusResponse::url).orElse(null),
                null,
                "Cancelled by user"
        );
        statuses.put(taskId, cancelled);
        emit(taskId, cancelled);
        return cancelled;
    }

    public Multi<TaskStatusResponse> stream(String taskId) {
        return Multi.createFrom().<TaskStatusResponse>emitter(emitter -> {
            subscribers.compute(taskId, (key, list) -> {
                CopyOnWriteArrayList<MultiEmitter<? super TaskStatusResponse>> emitters = list != null ? list : new CopyOnWriteArrayList<>();
                emitters.add(emitter);
                return emitters;
            });

            emitter.onTermination(() -> subscribers.computeIfPresent(taskId, (key, list) -> {
                list.remove(emitter);
                return list.isEmpty() ? null : list;
            }));

            TaskStatusResponse current = statuses.get(taskId);
            if (current != null) {
                emitter.emit(current);
            }
        });
    }

    @PreDestroy
    void shutdown() {
        futures.values().forEach(f -> f.cancel(true));
        executor.shutdownNow();
    }

    private void emit(String taskId, TaskStatusResponse status) {
        List<MultiEmitter<? super TaskStatusResponse>> emitters = subscribers.get(taskId);
        if (emitters != null) {
            emitters.forEach(emitter -> emitter.emit(status));
        }
    }

    private int currentProgress(String taskId) {
        return getStatus(taskId).map(TaskStatusResponse::progress).orElse(0);
    }

    private boolean isTerminal(String state) {
        return "SUCCESS".equals(state) || "FAILURE".equals(state) || "REVOKED".equals(state);
    }

    private class ProgressJob implements Runnable {
        private final String taskId;
        private final EmbedUrlRequest request;
        private int progress = 0;

        ProgressJob(String taskId, EmbedUrlRequest request) {
            this.taskId = taskId;
            this.request = request;
        }

        @Override
        public void run() {
            TaskStatusResponse current = statuses.get(taskId);
            if (current == null || isTerminal(current.state())) {
                cancelFuture();
                return;
            }

            progress = Math.min(100, progress + 20);
            String state = progress >= 100 ? "SUCCESS" : "PROGRESS";
            String message = switch (state) {
                case "SUCCESS" -> "Scraping completed";
                default -> "Scraping in progress " + progress + "%";
            };

            TaskStatusResponse updated = new TaskStatusResponse(
                    taskId,
                    state,
                    message,
                    progress,
                    request.url(),
                    state.equals("SUCCESS") ? Map.of(
                            "pagesProcessed", 5,
                            "completedAt", Instant.now().toString(),
                            "collection", request.collectionName()
                    ) : null,
                    null
            );
            statuses.put(taskId, updated);
            emit(taskId, updated);

            if (state.equals("SUCCESS")) {
                cancelFuture();
            }
        }

        private void cancelFuture() {
            ScheduledFuture<?> future = futures.remove(taskId);
            if (future != null) {
                future.cancel(false);
            }
        }
    }
}

