export interface Collection {
  name: string;
  count: number;
  version?: string;
}

export interface CollectionInfo {
  name: string;
  count: number;
  version: string;
}

export interface Document {
  id: string;
  metadata: Record<string, any>;
  source: string;
  page?: string;
  chunk_index?: string;
}

export interface CollectionDocumentsResponse {
  version: string;
  collection_name: string;
  documents: Document[];
  total: number;
}

