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

