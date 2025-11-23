import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { tap, catchError } from 'rxjs/operators';
import { ApiService } from './api.service';

@Injectable({
  providedIn: 'root'
})
export class AuthService extends ApiService {
  private readonly API_KEY_STORAGE_KEY = 'rag_api_key';
  private readonly REMEMBER_ME_KEY = 'rag_remember_me';

  // Signals for reactive state
  isAuthenticated = signal<boolean>(false);
  apiKey = signal<string | null>(null);
  authEnabled = signal<boolean>(false);

  constructor(http: HttpClient) {
    super(http);
    this.loadStoredApiKey();
    this.checkAuthStatus();
  }

  login(apiKey: string, rememberMe: boolean = false): Observable<boolean> {
    // If auth is disabled, allow empty API key
    if (!this.authEnabled() && !apiKey.trim()) {
      this.isAuthenticated.set(true);
      return of(true);
    }

    // If auth is enabled, API key is required
    if (this.authEnabled() && !apiKey.trim()) {
      return new Observable<boolean>(observer => {
        observer.error(new Error('API key is required when authentication is enabled'));
      });
    }

    // Store API key if provided
    if (apiKey.trim()) {
      if (rememberMe) {
        localStorage.setItem(this.API_KEY_STORAGE_KEY, apiKey);
        localStorage.setItem(this.REMEMBER_ME_KEY, 'true');
      } else {
        sessionStorage.setItem(this.API_KEY_STORAGE_KEY, apiKey);
      }
      this.apiKey.set(apiKey);
    }

    this.isAuthenticated.set(true);
    
    return of(true);
  }

  logout(): void {
    localStorage.removeItem(this.API_KEY_STORAGE_KEY);
    sessionStorage.removeItem(this.API_KEY_STORAGE_KEY);
    localStorage.removeItem(this.REMEMBER_ME_KEY);
    this.apiKey.set(null);
    this.isAuthenticated.set(false);
  }

  getApiKey(): string | null {
    return this.apiKey();
  }

  getAuthStatus(): Observable<any> {
    return this.get('/auth/status');
  }

  private checkAuthStatus(): void {
    this.getAuthStatus().pipe(
      tap((status: any) => {
        this.authEnabled.set(status.enabled === true);
        
        // If auth is disabled, automatically authenticate
        if (!status.enabled) {
          this.isAuthenticated.set(true);
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
    const storedKey = localStorage.getItem(this.API_KEY_STORAGE_KEY) || 
                     sessionStorage.getItem(this.API_KEY_STORAGE_KEY);
    
    if (storedKey) {
      this.apiKey.set(storedKey);
      this.isAuthenticated.set(true);
    }
  }
}
