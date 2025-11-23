import { Injectable, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, of } from 'rxjs';
import { tap } from 'rxjs/operators';
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

  constructor(http: HttpClient) {
    super(http);
    this.loadStoredApiKey();
  }

  login(apiKey: string, rememberMe: boolean = false): Observable<boolean> {
    // Store API key
    if (rememberMe) {
      localStorage.setItem(this.API_KEY_STORAGE_KEY, apiKey);
      localStorage.setItem(this.REMEMBER_ME_KEY, 'true');
    } else {
      sessionStorage.setItem(this.API_KEY_STORAGE_KEY, apiKey);
    }

    this.apiKey.set(apiKey);
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

  private loadStoredApiKey(): void {
    const storedKey = localStorage.getItem(this.API_KEY_STORAGE_KEY) || 
                     sessionStorage.getItem(this.API_KEY_STORAGE_KEY);
    
    if (storedKey) {
      this.apiKey.set(storedKey);
      this.isAuthenticated.set(true);
    }
  }
}
