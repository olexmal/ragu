package ai.ragu.security;

import jakarta.annotation.Priority;
import jakarta.inject.Inject;
import jakarta.ws.rs.Priorities;
import jakarta.ws.rs.container.ContainerRequestContext;
import jakarta.ws.rs.container.ContainerRequestFilter;
import jakarta.ws.rs.core.Response;
import jakarta.ws.rs.ext.Provider;

@Provider
@RequiresAuth
@Priority(Priorities.AUTHENTICATION)
public class ReadAuthFilter implements ContainerRequestFilter {

    @Inject
    AuthService authService;

    @Override
    public void filter(ContainerRequestContext requestContext) {
        Response failure = authService.checkAccess(requestContext, false);
        if (failure != null) {
            requestContext.abortWith(failure);
        }
    }
}

