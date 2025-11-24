import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { ApiService } from './api.service';
import { ConfluenceSettings, ConfluenceTestResult, ConfluenceFetchRequest, ConfluenceFetchResponse, SystemSettings, LLMProvidersSettings, LLMProviderConfig, LLMProviderTestResult } from '../models/settings.models';

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

  getLLMProviders(): Observable<LLMProvidersSettings> {
    return this.get<any>('/settings/llm-providers').pipe(
      map((response: any) => {
        // Convert snake_case to camelCase for nested provider configs
        const convertProviderConfig = (config: any): LLMProviderConfig => {
          if (!config || typeof config !== 'object') return config as LLMProviderConfig;
          return {
            enabled: config.enabled ?? false,
            isActive: config.is_active ?? false,
            type: config.type,
            model: config.model,
            apiKey: config.api_key,
            baseUrl: config.base_url,
            temperature: config.temperature,
            httpReferer: config.http_referer,
            appName: config.app_name,
            azureEndpoint: config.azure_endpoint,
            deploymentName: config.deployment_name,
            apiVersion: config.api_version,
            // Preserve any other fields
            ...Object.keys(config).reduce((acc, key) => {
              if (!['enabled', 'is_active', 'type', 'model', 'api_key', 'base_url', 'temperature', 
                     'http_referer', 'app_name', 'azure_endpoint', 'deployment_name', 'api_version'].includes(key)) {
                acc[key] = config[key];
              }
              return acc;
            }, {} as any)
          };
        };

        const convertProviders = (providers: any): { [key: string]: LLMProviderConfig } => {
          if (!providers || typeof providers !== 'object') return {};
          const result: { [key: string]: LLMProviderConfig } = {};
          Object.keys(providers).forEach(key => {
            result[key] = convertProviderConfig(providers[key]);
          });
          return result;
        };

        return {
          llmProviders: convertProviders(response.llm_providers),
          embeddingProviders: convertProviders(response.embedding_providers)
        };
      })
    );
  }

  saveLLMProviders(settings: LLMProvidersSettings): Observable<any> {
    // Convert camelCase to snake_case for nested provider configs
    const convertProviderConfig = (config: LLMProviderConfig): any => {
      if (!config || typeof config !== 'object') return config;
      const result: any = {
        enabled: config.enabled,
        is_active: config.isActive,
        type: config.type
      };
      
      if (config.model !== undefined) result.model = config.model;
      if (config.apiKey !== undefined) result.api_key = config.apiKey;
      if (config.baseUrl !== undefined) result.base_url = config.baseUrl;
      if (config.temperature !== undefined) result.temperature = config.temperature;
      if (config.httpReferer !== undefined) result.http_referer = config.httpReferer;
      if (config.appName !== undefined) result.app_name = config.appName;
      if (config.azureEndpoint !== undefined) result.azure_endpoint = config.azureEndpoint;
      if (config.deploymentName !== undefined) result.deployment_name = config.deploymentName;
      if (config.apiVersion !== undefined) result.api_version = config.apiVersion;
      
      // Preserve any other fields that aren't in the interface
      Object.keys(config).forEach(key => {
        if (!['enabled', 'isActive', 'type', 'model', 'apiKey', 'baseUrl', 'temperature',
              'httpReferer', 'appName', 'azureEndpoint', 'deploymentName', 'apiVersion'].includes(key)) {
          result[key] = (config as any)[key];
        }
      });
      
      return result;
    };

    const convertProviders = (providers: { [key: string]: LLMProviderConfig }): { [key: string]: any } => {
      if (!providers || typeof providers !== 'object') return {};
      const result: { [key: string]: any } = {};
      Object.keys(providers).forEach(key => {
        result[key] = convertProviderConfig(providers[key]);
      });
      return result;
    };

    const backendSettings = {
      llm_providers: convertProviders(settings.llmProviders),
      embedding_providers: convertProviders(settings.embeddingProviders)
    };
    return this.post('/settings/llm-providers', backendSettings);
  }

  testLLMProvider(providerType: string, config: Partial<LLMProviderConfig>, category: 'llm' | 'embedding' = 'llm'): Observable<LLMProviderTestResult> {
    // Convert camelCase to snake_case for backend
    const backendConfig: any = {};
    Object.keys(config).forEach(key => {
      const snakeKey = key.replace(/([A-Z])/g, '_$1').toLowerCase();
      backendConfig[snakeKey] = config[key as keyof LLMProviderConfig];
    });
    
    return this.post<any>('/settings/llm-providers/test', {
      type: providerType,
      category: category,
      config: backendConfig
    }).pipe(
      map((response: any) => ({
        success: response.success ?? false,
        message: response.message || '',
        testResponse: response.test_response || response.testResponse
      }))
    );
  }

  getActiveLLMProviders(): Observable<{llm: LLMProviderConfig, embedding: LLMProviderConfig}> {
    return this.get<any>('/settings/llm-providers/active').pipe(
      map((response: any) => {
        // Convert snake_case to camelCase for provider configs
        const convertProviderConfig = (config: any): LLMProviderConfig => {
          if (!config || typeof config !== 'object') return config as LLMProviderConfig;
          return {
            enabled: config.enabled ?? false,
            isActive: config.is_active ?? false,
            type: config.type,
            model: config.model,
            apiKey: config.api_key,
            baseUrl: config.base_url,
            temperature: config.temperature,
            httpReferer: config.http_referer,
            appName: config.app_name,
            azureEndpoint: config.azure_endpoint,
            deploymentName: config.deployment_name,
            apiVersion: config.api_version,
            // Preserve any other fields
            ...Object.keys(config).reduce((acc, key) => {
              if (!['enabled', 'is_active', 'type', 'model', 'api_key', 'base_url', 'temperature', 
                     'http_referer', 'app_name', 'azure_endpoint', 'deployment_name', 'api_version'].includes(key)) {
                acc[key] = config[key];
              }
              return acc;
            }, {} as any)
          };
        };

        return {
          llm: convertProviderConfig(response.llm || {}),
          embedding: convertProviderConfig(response.embedding || {})
        };
      })
    );
  }
}

