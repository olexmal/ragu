package ai.ragu.vector;

import java.text.Normalizer;

/**
 * Mirrors the Python generate_collection_name helper so both stacks stay in sync.
 */
public class CollectionNameGenerator {

    public String generate(String baseName, String version) {
        String sanitizedBase = sanitize(baseName == null || baseName.isBlank() ? "collection" : baseName);
        if (version == null || version.isBlank()) {
            return sanitizedBase;
        }

        String sanitizedVersion = sanitize(version);
        if (!sanitizedVersion.toLowerCase().startsWith("v")) {
            sanitizedVersion = "v" + sanitizedVersion;
        }

        if (sanitizedBase.toLowerCase().endsWith("-" + sanitizedVersion.toLowerCase())
                || sanitizedBase.toLowerCase().endsWith("_" + sanitizedVersion.toLowerCase())) {
            sanitizedBase = sanitizedBase.substring(0, sanitizedBase.length() - (sanitizedVersion.length() + 1));
        } else if (sanitizedBase.toLowerCase().endsWith(sanitizedVersion.toLowerCase())) {
            sanitizedBase = sanitizedBase.substring(0, sanitizedBase.length() - sanitizedVersion.length());
        }

        return sanitizedBase + "-" + sanitizedVersion;
    }

    private String sanitize(String value) {
        String normalized = Normalizer.normalize(value, Normalizer.Form.NFKD)
                .replaceAll("[^a-zA-Z0-9]+", "-")
                .replaceAll("-{2,}", "-")
                .replaceAll("^-+", "")
                .replaceAll("-+$", "");
        if (normalized.isBlank()) {
            normalized = "collection";
        }
        return normalized.toLowerCase();
    }
}

