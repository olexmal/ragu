import { Injectable } from '@angular/core';
import { HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { EmbedResponse, BatchEmbedResponse } from '../models/document.models';

@Injectable({
  providedIn: 'root'
})
export class EmbedService extends ApiService {
  embedFile(file: File, version?: string, overwrite: boolean = false): Observable<EmbedResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (version) {
      formData.append('version', version);
    }
    formData.append('overwrite', overwrite.toString());

    return this.postFormData<EmbedResponse>('/embed', formData);
  }

  embedDirectory(directory: string, version?: string, overwrite: boolean = false): Observable<BatchEmbedResponse> {
    const formData = new FormData();
    formData.append('directory', directory);
    if (version) {
      formData.append('version', version);
    }
    formData.append('overwrite', overwrite.toString());

    return this.postFormData<BatchEmbedResponse>('/embed-batch', formData);
  }
}

