package ai.ragu.vector;

public record VectorOperationResult(
        boolean success,
        String message
) {
    public static VectorOperationResult ok(String message) {
        return new VectorOperationResult(true, message);
    }

    public static VectorOperationResult failure(String message) {
        return new VectorOperationResult(false, message);
    }
}

