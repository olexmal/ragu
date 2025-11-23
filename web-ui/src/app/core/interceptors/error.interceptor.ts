import { HttpInterceptorFn, HttpErrorResponse } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { Router } from '@angular/router';

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);

  return next(req).pipe(
    catchError((error: HttpErrorResponse) => {
      // Don't redirect on 401 if we're already on the login page
      // This allows the login component to handle login errors
      const isLoginRequest = req.url.includes('/auth/login');
      
      if (error.status === 401 && !isLoginRequest) {
        // Unauthorized - redirect to login (but not for login requests themselves)
        router.navigate(['/login']);
      }

      // Preserve the original error structure so components can access error.error.message
      // Only create a new error if we need to transform it
      console.error('HTTP Error:', error);
      return throwError(() => error);
    })
  );
};

