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

