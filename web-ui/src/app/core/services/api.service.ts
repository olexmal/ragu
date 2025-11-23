import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, retry } from 'rxjs/operators';
import { environment } from '../../../environments/environment';

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = environment.apiUrl;

  constructor(private http: HttpClient) {}

  protected get<T>(endpoint: string, params?: HttpParams): Observable<T> {
    return this.http.get<T>(`${this.apiUrl}${endpoint}`, { 
      params,
      withCredentials: true // Send cookies with requests
    })
      .pipe(
        retry(2),
        catchError(this.handleError)
      );
  }

  protected post<T>(endpoint: string, body: any, options?: { headers?: HttpHeaders }): Observable<T> {
    const isLoginRequest = endpoint.includes('/auth/login');
    
    return this.http.post<T>(`${this.apiUrl}${endpoint}`, body, {
      ...options,
      withCredentials: true // Send cookies with requests
    })
      .pipe(
        // Don't retry login requests - we want to show errors immediately
        retry(isLoginRequest ? 0 : 2),
        catchError(this.handleError)
      );
  }

  protected delete<T>(endpoint: string): Observable<T> {
    return this.http.delete<T>(`${this.apiUrl}${endpoint}`, {
      withCredentials: true // Send cookies with requests
    })
      .pipe(
        retry(2),
        catchError(this.handleError)
      );
  }

  protected postFormData<T>(endpoint: string, formData: FormData, headers?: HttpHeaders): Observable<T> {
    return this.http.post<T>(`${this.apiUrl}${endpoint}`, formData, { headers })
      .pipe(
        catchError(this.handleError)
      );
  }

  healthCheck(): Observable<any> {
    return this.get('/health');
  }

  private handleError = (error: any): Observable<never> => {
    let errorMessage = 'An unknown error occurred';
    
    if (error.error instanceof ErrorEvent) {
      errorMessage = `Error: ${error.error.message}`;
    } else {
      errorMessage = `Error Code: ${error.status}\nMessage: ${error.message}`;
      if (error.error?.error) {
        errorMessage = error.error.error;
      } else if (error.error?.message) {
        errorMessage = error.error.message;
      }
    }
    
    console.error(errorMessage);
    // Preserve the original error structure so components can access error.error
    return throwError(() => error);
  };
}

