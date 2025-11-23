import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { Collection, CollectionInfo } from '../models/collection.models';

@Injectable({
  providedIn: 'root'
})
export class CollectionService extends ApiService {
  getCollections(): Observable<{ collections: Collection[]; total: number }> {
    return this.get<{ collections: Collection[]; total: number }>('/collections');
  }

  getCollection(version: string): Observable<CollectionInfo> {
    return this.get<CollectionInfo>(`/collections/${version}`);
  }

  deleteCollection(version: string): Observable<{ message: string; version: string }> {
    return this.delete<{ message: string; version: string }>(`/collections/${version}`);
  }
}

