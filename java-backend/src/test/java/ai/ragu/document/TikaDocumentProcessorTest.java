package ai.ragu.document;

import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class TikaDocumentProcessorTest {

    private final TikaDocumentProcessor processor = new TikaDocumentProcessor();

    @Test
    void splitsContentIntoChunksRespectingOverlap() {
        String content = "Sentence one. Sentence two is here. Sentence three follows. Sentence four wraps things up.";

        DocumentProcessingOptions options = DocumentProcessingOptions.builder()
                .chunkSize(30)
                .chunkOverlap(5)
                .source("unit-test")
                .version("v1")
                .build();

        List<DocumentChunk> chunks = processor.process(content, options);

        assertTrue(chunks.size() > 1, "Expected multiple chunks");
        assertEquals("unit-test", chunks.get(0).metadata().source());
        assertEquals("v1", chunks.get(0).metadata().version());
        assertTrue(chunks.get(0).content().contains("Sentence one"));
    }
}

