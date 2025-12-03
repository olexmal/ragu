package ai.ragu.document;

/**
 * Custom exception thrown when document processing fails.
 */
public class DocumentProcessingException extends RuntimeException {
    public DocumentProcessingException(String message, Throwable cause) {
        super(message, cause);
    }
}

