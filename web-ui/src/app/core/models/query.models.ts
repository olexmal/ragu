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
  stats?: QueryStatistics;
}

export interface QueryStatistics {
  total_time?: number;
  cache_lookup_time?: number;
  llm_init_time?: number;
  vector_db_init_time?: number;
  multi_query_generation_time?: number;
  document_retrieval_time?: number;
  answer_generation_time?: number;
  cache_store_time?: number;
  request_overhead_time?: number;
  request_total_time?: number;
}

export interface SourceDocument {
  content: string;
  metadata: {
    version?: string;
    file_path?: string;
    [key: string]: any;
  };
}

