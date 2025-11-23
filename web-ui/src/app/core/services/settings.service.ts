import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ApiService } from './api.service';
import { ConfluenceSettings, ConfluenceTestResult, ConfluenceFetchRequest, ConfluenceFetchResponse, SystemSettings } from '../models/settings.models';

@Injectable({
  providedIn: 'root'
})
export class SettingsService extends ApiService {
  getConfluenceSettings(): Observable<ConfluenceSettings> {
    return this.get<ConfluenceSettings>('/settings/confluence');
  }

  saveConfluenceSettings(settings: ConfluenceSettings): Observable<any> {
    return this.post('/settings/confluence', settings);
  }

  testConfluenceConnection(settings: Partial<ConfluenceSettings>): Observable<ConfluenceTestResult> {
    return this.post<ConfluenceTestResult>('/confluence/test', settings);
  }

  fetchConfluencePages(request: ConfluenceFetchRequest): Observable<ConfluenceFetchResponse> {
    return this.post<ConfluenceFetchResponse>('/confluence/fetch', request);
  }

  getSystemSettings(): Observable<SystemSettings> {
    return this.get<{systemName: string}>('/settings/system').pipe(
      map((response) => ({ systemName: response.systemName }))
    );
  }

  saveSystemSettings(settings: SystemSettings): Observable<any> {
    return this.post('/settings/system', { system_name: settings.systemName });
  }
}

