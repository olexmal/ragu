import { Injectable } from '@angular/core';
import { HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ApiService } from './api.service';
import { QueryRequest, QueryResponse } from '../models/query.models';

@Injectable({
  providedIn: 'root'
})
export class QueryService extends ApiService {
  query(request: QueryRequest): Observable<QueryResponse> {
    return this.post<QueryResponse>('/query', request);
  }

  queryMultiVersion(query: string, versions: string[], k: number = 3): Observable<any> {
    return this.post('/query/multi-version', { query, versions, k });
  }

  compareVersions(query: string, versions: string[], k: number = 3): Observable<any> {
    return this.post('/query/compare', { query, versions, k });
  }
}

