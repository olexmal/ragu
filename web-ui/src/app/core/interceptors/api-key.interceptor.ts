import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { AuthService } from '../services/auth.service';

export const apiKeyInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const apiKey = authService.getApiKey();

  if (apiKey) {
    const cloned = req.clone({
      setHeaders: {
        'X-API-Key': apiKey
      }
    });
    return next(cloned);
  }

  return next(req);
};

