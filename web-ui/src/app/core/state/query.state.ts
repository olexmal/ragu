import { Injectable, signal } from '@angular/core';
import { QueryResponse } from '../models/query.models';

@Injectable({
  providedIn: 'root'
})
export class QueryState {
  private querySignal = signal<QueryResponse | null>(null);
  private loadingSignal = signal<boolean>(false);
  private errorSignal = signal<string | null>(null);

  readonly query = this.querySignal.asReadonly();
  readonly loading = this.loadingSignal.asReadonly();
  readonly error = this.errorSignal.asReadonly();

  setQuery(response: QueryResponse): void {
    this.querySignal.set(response);
    this.loadingSignal.set(false);
    this.errorSignal.set(null);
  }

  setLoading(loading: boolean): void {
    this.loadingSignal.set(loading);
  }

  setError(error: string | null): void {
    this.errorSignal.set(error);
    this.loadingSignal.set(false);
  }

  clear(): void {
    this.querySignal.set(null);
    this.errorSignal.set(null);
    this.loadingSignal.set(false);
  }
}

