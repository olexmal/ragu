import { Injectable } from '@angular/core';
import { HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

@Injectable({
  providedIn: 'root'
})
export class HistoryService extends ApiService {
  getHistory(limit: number = 50, offset: number = 0): Observable<any> {
    const params = new HttpParams()
      .set('limit', limit.toString())
      .set('offset', offset.toString());
    return this.get('/history', params);
  }

  searchHistory(query: string, limit: number = 20): Observable<any> {
    const params = new HttpParams()
      .set('q', query)
      .set('limit', limit.toString());
    return this.get('/history/search', params);
  }

  exportHistory(format: 'json' | 'csv' = 'json'): Observable<any> {
    const params = new HttpParams().set('format', format);
    return this.get('/history/export', params);
  }

  getFavorites(): Observable<any> {
    return this.get('/favorites');
  }

  addFavorite(query: string): Observable<any> {
    return this.post('/favorites', { query });
  }

  removeFavorite(query: string): Observable<any> {
    return this.delete(`/favorites?query=${encodeURIComponent(query)}`);
  }
}

