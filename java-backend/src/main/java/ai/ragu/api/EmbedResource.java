package ai.ragu.api;

import ai.ragu.api.model.EmbedResponse;
import ai.ragu.api.service.EmbeddingPipeline;
import ai.ragu.security.RequiresWriteAuth;
import jakarta.inject.Inject;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.POST;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import org.jboss.resteasy.reactive.RestForm;
import org.jboss.resteasy.reactive.multipart.FileUpload;

/**
 * Mirrors POST /embed from the Python API.
 */
@Path("/embed")
@Consumes(MediaType.MULTIPART_FORM_DATA)
@Produces(MediaType.APPLICATION_JSON)
@RequiresWriteAuth
public class EmbedResource extends BaseResource {

    private final EmbeddingPipeline embeddingPipeline;

    @Inject
    public EmbedResource(EmbeddingPipeline embeddingPipeline) {
        this.embeddingPipeline = embeddingPipeline;
    }

    @POST
    public Response embedFile(@RestForm FileUpload file,
                              @RestForm("collection_name") String collectionName,
                              @RestForm("version") String version,
                              @RestForm("overwrite") String overwriteRaw) {
        if (file == null || file.uploadedFile() == null) {
            return Response.status(Response.Status.BAD_REQUEST)
                    .entity(java.util.Map.of("error", "file", "message", "No file was uploaded"))
                    .build();
        }

        boolean overwrite = overwriteRaw != null && overwriteRaw.equalsIgnoreCase("true");
        try {
            EmbedResponse response = embeddingPipeline.embedFile(
                    file.uploadedFile(),
                    file.fileName(),
                    collectionName,
                    version,
                    overwrite
            );
            return Response.ok(response).build();
        } catch (Exception e) {
            return Response.serverError()
                    .entity(java.util.Map.of("error", "Embedding failed", "message", e.getMessage()))
                    .build();
        }
    }
}

