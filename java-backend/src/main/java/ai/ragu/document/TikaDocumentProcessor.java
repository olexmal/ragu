package ai.ragu.document;

import jakarta.enterprise.context.ApplicationScoped;
import org.apache.tika.metadata.Metadata;
import org.apache.tika.metadata.TikaCoreProperties;
import org.apache.tika.parser.AutoDetectParser;
import org.apache.tika.parser.ParseContext;
import org.apache.tika.sax.BodyContentHandler;
import org.xml.sax.ContentHandler;
import org.xml.sax.SAXException;

import java.io.IOException;
import java.io.InputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.text.BreakIterator;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * Apache Tika based implementation that normalizes documents ahead of embedding.
 */
@ApplicationScoped
public class TikaDocumentProcessor implements DocumentProcessor {

    private final AutoDetectParser parser = new AutoDetectParser();

    @Override
    public List<DocumentChunk> process(Path path, DocumentProcessingOptions options) {
        try (InputStream inputStream = Files.newInputStream(path)) {
            ContentHandler handler = new BodyContentHandler(-1);
            Metadata metadata = new Metadata();
            metadata.set(TikaCoreProperties.RESOURCE_NAME_KEY, path.getFileName().toString());

            parser.parse(inputStream, handler, metadata, new ParseContext());

            DocumentProcessingOptions finalOptions = DocumentProcessingOptions.builder()
                    .chunkSize(options.chunkSize())
                    .chunkOverlap(options.chunkOverlap())
                    .source(options.source() != null ? options.source() : path.toString())
                    .version(options.version())
                    .build();

            return process(handler.toString(), finalOptions);
        } catch (IOException | SAXException e) {
            throw new DocumentProcessingException("Failed to parse document: " + path, e);
        } catch (Exception e) {
            throw new DocumentProcessingException("Unexpected error parsing document: " + path, e);
        }
    }

    @Override
    public List<DocumentChunk> process(String content, DocumentProcessingOptions options) {
        List<String> sentences = splitIntoSentences(content);
        List<DocumentChunk> chunks = new ArrayList<>();

        StringBuilder currentChunk = new StringBuilder();
        int chunkIndex = 0;

        for (String sentence : sentences) {
            if (currentChunk.length() + sentence.length() > options.chunkSize()) {
                String chunkContent = currentChunk.toString().trim();
                if (!chunkContent.isEmpty()) {
                    chunks.add(buildChunk(chunkIndex++, chunkContent, options));
                }
                currentChunk = new StringBuilder();
                if (options.chunkOverlap() > 0 && !chunks.isEmpty()) {
                    String previousChunk = chunks.get(chunks.size() - 1).content();
                    int overlapStart = Math.max(0, previousChunk.length() - options.chunkOverlap());
                    currentChunk.append(previousChunk.substring(overlapStart)).append(" ");
                }
            }
            currentChunk.append(sentence).append(" ");
        }

        if (!currentChunk.isEmpty()) {
            chunks.add(buildChunk(chunkIndex, currentChunk.toString().trim(), options));
        }

        return chunks;
    }

    private List<String> splitIntoSentences(String content) {
        List<String> sentences = new ArrayList<>();
        BreakIterator iterator = BreakIterator.getSentenceInstance(Locale.ENGLISH);
        iterator.setText(content);

        int start = iterator.first();
        for (int end = iterator.next(); end != BreakIterator.DONE; start = end, end = iterator.next()) {
            String sentence = content.substring(start, end).trim();
            if (!sentence.isEmpty()) {
                sentences.add(sentence);
            }
        }
        return sentences.isEmpty() ? List.of(content) : sentences;
    }

    private DocumentChunk buildChunk(int index, String content, DocumentProcessingOptions options) {
        ChunkMetadata metadata = new ChunkMetadata(
                options.source(),
                options.version(),
                index,
                options.metadata()
        );
        return new DocumentChunk(content, metadata);
    }
}

