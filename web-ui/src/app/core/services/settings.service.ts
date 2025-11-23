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
    return this.get<any>('/settings/confluence').pipe(
      map((response: any) => ({
        enabled: response.enabled || false,
        url: response.url || '',
        instanceType: response.instance_type || 'cloud',
        apiToken: response.api_token || '',
        username: response.username || '',
        password: response.password || '',
        pageIds: response.page_ids || [],
        autoSync: response.auto_sync || false,
        syncInterval: response.sync_interval || 3600
      }))
    );
  }

  saveConfluenceSettings(settings: ConfluenceSettings): Observable<any> {
    // Convert camelCase to snake_case for backend
    const backendSettings = {
      enabled: settings.enabled,
      url: settings.url,
      instance_type: settings.instanceType,
      api_token: settings.apiToken,
      username: settings.username || '',
      password: settings.password || '',
      page_ids: settings.pageIds,
      auto_sync: settings.autoSync,
      sync_interval: settings.syncInterval
    };
    return this.post('/settings/confluence', backendSettings);
  }

  testConfluenceConnection(settings: Partial<ConfluenceSettings>): Observable<ConfluenceTestResult> {
    // Convert camelCase to snake_case for backend
    const backendSettings: any = {};
    if (settings.url) backendSettings.url = settings.url;
    if (settings.instanceType) backendSettings.instance_type = settings.instanceType;
    if (settings.apiToken) backendSettings.api_token = settings.apiToken;
    if (settings.username) backendSettings.username = settings.username;
    if (settings.password) backendSettings.password = settings.password;
    return this.post<ConfluenceTestResult>('/confluence/test', backendSettings);
  }

  fetchConfluencePages(request: ConfluenceFetchRequest): Observable<ConfluenceFetchResponse> {
    return this.post<ConfluenceFetchResponse>('/confluence/fetch', request);
  }

  getSystemSettings(): Observable<SystemSettings> {
    return this.get<{systemName: string}>('/settings/system').pipe(
      map((response: {systemName: string}) => ({ systemName: response.systemName }))
    );
  }

  saveSystemSettings(settings: SystemSettings): Observable<any> {
    return this.post('/settings/system', { system_name: settings.systemName });
  }
}

