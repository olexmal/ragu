package ai.ragu.api;

import jakarta.ws.rs.core.Response;

import java.util.HashMap;
import java.util.Map;

/**
 * Common helpers for resources that still need full implementations.
 */
abstract class BaseResource {

    protected Response notImplemented(String feature) {
        Map<String, Object> payload = new HashMap<>();
        payload.put("status", "pending");
        payload.put("feature", feature);
        payload.put("message", feature + " is not implemented yet");
        return Response.status(Response.Status.NOT_IMPLEMENTED)
                .entity(payload)
                .build();
    }
}

