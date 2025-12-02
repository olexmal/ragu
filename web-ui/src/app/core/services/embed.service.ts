import { Injectable } from '@angular/core';
import { HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { EmbedResponse, BatchEmbedResponse, ScrapeEmbedResponse, ScrapeTaskStatus } from '../models/document.models';

@Injectable({
  providedIn: 'root'
})
export class EmbedService extends ApiService {
  embedFile(file: File, version?: string, collectionName?: string, overwrite: boolean = false): Observable<EmbedResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (version) {
      formData.append('version', version);
    }
    if (collectionName) {
      formData.append('collection_name', collectionName);
    }
    formData.append('overwrite', overwrite.toString());

    return this.postFormData<EmbedResponse>('/embed', formData);
  }

  embedDirectory(directory: string, version?: string, collectionName?: string, overwrite: boolean = false): Observable<BatchEmbedResponse> {
    const formData = new FormData();
    formData.append('directory', directory);
    if (version) {
      formData.append('version', version);
    }
    if (collectionName) {
      formData.append('collection_name', collectionName);
    }
    formData.append('overwrite', overwrite.toString());

    return this.postFormData<BatchEmbedResponse>('/embed-batch', formData);
  }

  importConfluencePage(pageId: string, version?: string, collectionName?: string, overwrite: boolean = false): Observable<EmbedResponse> {
    const body: any = {
      page_id: pageId
    };
    if (version) {
      body.version = version;
    }
    if (collectionName) {
      body.collection_name = collectionName;
    }
    body.overwrite = overwrite;

    return this.post<EmbedResponse>('/confluence/import', body);
  }

  scrapeAndEmbedUrl(url: string, version?: string, collectionName?: string, maxDepth: number = 3, overwrite: boolean = false): Observable<ScrapeEmbedResponse> {
    const body: any = {
      url,
      max_depth: maxDepth,
      overwrite
    };
    if (version) {
      body.version = version;
    }
    if (collectionName) {
      body.collection_name = collectionName;
    }

    return this.post<ScrapeEmbedResponse>('/embed-url', body);
  }

  getScrapeTaskStatus(taskId: string): Observable<ScrapeTaskStatus> {
    return this.get<ScrapeTaskStatus>(`/embed-url/status/${taskId}`);
  }

  cancelScrapeTask(taskId: string): Observable<{ message: string; task_id: string }> {
    return this.post<{ message: string; task_id: string }>(`/embed-url/cancel/${taskId}`, {});
  }
}
