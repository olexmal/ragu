import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of, throwError } from 'rxjs';
import { tap, catchError, map } from 'rxjs/operators';
import { ApiService } from './api.service';

@Injectable({
  providedIn: 'root'
})
export class AuthService extends ApiService {
  private readonly REMEMBER_ME_KEY = 'rag_remember_me';

  // Signals for reactive state
  isAuthenticated = signal<boolean>(false);
  authEnabled = signal<boolean>(false);

  constructor(http: HttpClient) {
    super(http);
    this.loadStoredApiKey();
    this.checkAuthStatus();
  }

  login(username: string, password: string, rememberMe: boolean = false): Observable<boolean> {
    // If auth is disabled, automatically authenticate
    if (!this.authEnabled()) {
      this.isAuthenticated.set(true);
      return of(true);
    }

    // Make login request to backend
    return this.post<{ success: boolean; message: string; username: string }>('/auth/login', {
      username,
      password
    }).pipe(
      map((response: { success: boolean; message: string; username: string }) => {
        console.log('Login response:', response);
        if (response && response.success === true) {
          // Store username if remember me is checked
          if (rememberMe) {
            localStorage.setItem('rag_username', username);
            localStorage.setItem(this.REMEMBER_ME_KEY, 'true');
          } else {
            sessionStorage.setItem('rag_username', username);
          }
          this.isAuthenticated.set(true);
          return true;
        }
        // If response doesn't have success=true, treat as failure
        this.isAuthenticated.set(false);
        throw new Error(response?.message || 'Login failed');
      }),
      catchError((error: any) => {
        console.error('Login catchError:', error);
        this.isAuthenticated.set(false);
        // Preserve the original error so the component can access error.error.message
        return throwError(() => error);
      })
    );
  }

  logout(): Observable<boolean> {
    return this.post<{ success: boolean; message: string }>('/auth/logout', {}).pipe(
      map(() => {
        localStorage.removeItem('rag_username');
        sessionStorage.removeItem('rag_username');
        localStorage.removeItem(this.REMEMBER_ME_KEY);
        this.isAuthenticated.set(false);
        return true;
      }),
      catchError((error: any) => {
        // Even if logout fails on server, clear local state
        localStorage.removeItem('rag_username');
        sessionStorage.removeItem('rag_username');
        localStorage.removeItem(this.REMEMBER_ME_KEY);
        this.isAuthenticated.set(false);
        return of(true); // Return success anyway
      })
    );
  }


  getAuthStatus(): Observable<any> {
    return this.get('/auth/status');
  }

  private checkAuthStatus(): void {
    this.getAuthStatus().pipe(
      tap((status: any) => {
        this.authEnabled.set(status.enabled === true);
        
        // Check if user is authenticated from session
        if (status.authenticated === true) {
          this.isAuthenticated.set(true);
        } else if (!status.enabled) {
          // If auth is disabled, automatically authenticate
          this.isAuthenticated.set(true);
        } else {
          this.isAuthenticated.set(false);
        }
      }),
      catchError(() => {
        // If auth status endpoint fails, assume auth is disabled
        this.authEnabled.set(false);
        this.isAuthenticated.set(true);
        return of(null);
      })
    ).subscribe();
  }

  private loadStoredApiKey(): void {
    // Check if user was previously logged in (session-based, so just check auth status)
    // The session cookie will be sent automatically by the browser
    this.checkAuthStatus();
  }
}
