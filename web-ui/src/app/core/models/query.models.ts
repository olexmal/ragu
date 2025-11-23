export interface QueryRequest {
  query: string;
  version?: string;
  k?: number;
  simple?: boolean;
}

export interface QueryResponse {
  answer: string;
  query: string;
  sources: SourceDocument[];
  source_count: number;
}

export interface SourceDocument {
  content: string;
  metadata: {
    version?: string;
    file_path?: string;
    [key: string]: any;
  };
}

