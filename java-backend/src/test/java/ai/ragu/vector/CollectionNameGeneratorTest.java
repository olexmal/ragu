package ai.ragu.vector;

import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.assertEquals;

class CollectionNameGeneratorTest {

    private final CollectionNameGenerator generator = new CollectionNameGenerator();

    @Test
    void normalizesBaseAndVersion() {
        assertEquals("common-model-docs-v19", generator.generate("Common Model Docs", "19"));
        assertEquals("custom-collection-vbeta", generator.generate("custom collection vBeta", "beta"));
    }
}

