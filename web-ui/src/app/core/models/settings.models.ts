export interface ConfluenceSettings {
  enabled: boolean;
  url: string;
  instanceType: 'cloud' | 'server';
  apiToken: string;
  username?: string;
  password?: string;
  pageIds: string[];
  autoSync: boolean;
  syncInterval: number;
}

export interface ConfluenceTestResult {
  success: boolean;
  message: string;
  instance_type?: string;
  url?: string;
}

export interface ConfluenceFetchRequest {
  pageIds?: string[];
  confluenceConfig?: ConfluenceSettings;
  collectionName?: string;
  version?: string;
  overwrite?: boolean;
}

export interface ConfluenceFetchResponse {
  message: string;
  results: {
    success: number;
    failed: number;
    errors: Array<{
      page_id: string;
      error: string;
    }>;
  };
}

export interface SystemSettings {
  systemName: string;
}

export type LLMProviderType = 'ollama' | 'openrouter' | 'openai' | 'anthropic' | 'azure-openai' | 'google';

export interface LLMProviderConfig {
  enabled: boolean;
  isActive: boolean;
  type: LLMProviderType;
  model?: string;
  apiKey?: string;
  baseUrl?: string;
  temperature?: number;
  // Provider-specific fields
  httpReferer?: string;
  appName?: string;
  azureEndpoint?: string;
  deploymentName?: string;
  apiVersion?: string;
  [key: string]: any;
}

export interface LLMProvidersSettings {
  llmProviders: { [key: string]: LLMProviderConfig };
  embeddingProviders: { [key: string]: LLMProviderConfig };
}

export interface LLMProviderTestResult {
  success: boolean;
  message: string;
  testResponse?: string;
}

