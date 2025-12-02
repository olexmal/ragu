export interface EmbedRequest {
  file: File;
  version?: string;
  overwrite?: boolean;
}

export interface EmbedResponse {
  message: string;
  version?: string;
  mode: 'overwrite' | 'incremental';
  filename: string;
}

export interface BatchEmbedRequest {
  directory: string;
  version?: string;
  overwrite?: boolean;
}

export interface BatchEmbedResponse {
  message: string;
  results: EmbedResult[];
  version?: string;
}

export interface EmbedResult {
  filename: string;
  success: boolean;
  error?: string;
}

export interface ScrapePageResult {
  url: string;
  title: string;
  status: 'success' | 'failed';
}

export interface ScrapeEmbedResponse {
  message: string;
  results?: {
    success: number;
    failed: number;
    errors: Array<{ url: string; error: string }>;
    pages: ScrapePageResult[];
  };
  version?: string;
  // Async job fields
  task_id?: string;
  status_url?: string;
}

export interface ScrapeTaskStatus {
  state: 'PENDING' | 'PROGRESS' | 'SUCCESS' | 'FAILURE' | 'TIMEOUT' | 'ERROR' | 'REVOKED';
  status: string;
  progress?: number;
  url?: string;
  result?: ScrapeEmbedResponse;
  error?: string;
}

