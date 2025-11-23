import { HttpInterceptorFn } from '@angular/common/http';

/**
 * API Key interceptor - no longer needed for session-based authentication.
 * Sessions are handled automatically by the browser with withCredentials: true.
 * This interceptor is kept for backward compatibility but does nothing.
 */
export const apiKeyInterceptor: HttpInterceptorFn = (req, next) => {
  // Session-based authentication - no API key needed
  // Cookies are sent automatically by the browser
  return next(req);
};

