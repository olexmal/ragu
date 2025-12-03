package ai.ragu.document;

import java.nio.file.Path;
import java.util.List;

/**
 * Contract for converting a document into embedding-ready chunks.
 */
public interface DocumentProcessor {

    /**
     * Process a file located on disk.
     */
    List<DocumentChunk> process(Path path, DocumentProcessingOptions options);

    /**
     * Process raw text content (useful for HTML strings, Confluence exports, etc.).
     */
    List<DocumentChunk> process(String content, DocumentProcessingOptions options);
}

