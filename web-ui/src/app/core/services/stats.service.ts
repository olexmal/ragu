import { Injectable } from '@angular/core';
import { HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';

@Injectable({
  providedIn: 'root'
})
export class StatsService extends ApiService {
  getStats(days: number = 7): Observable<any> {
    const params = new HttpParams().set('days', days.toString());
    return this.get('/stats', params);
  }

  clearCache(): Observable<any> {
    return this.post('/cache/clear', {});
  }
}

