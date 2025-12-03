package ai.ragu.security;

import jakarta.annotation.Priority;
import jakarta.inject.Inject;
import jakarta.ws.rs.Priorities;
import jakarta.ws.rs.container.ContainerRequestContext;
import jakarta.ws.rs.container.ContainerRequestFilter;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.ext.Provider;

@Provider
@RequiresWriteAuth
@Priority(Priorities.AUTHENTICATION + 1)
public class WriteAuthFilter implements ContainerRequestFilter {

    @Inject
    AuthService authService;

    @Override
    public void filter(ContainerRequestContext requestContext) {
        Response failure = authService.checkAccess(requestContext, true);
        if (failure != null) {
            requestContext.abortWith(failure);
        }
    }
}

