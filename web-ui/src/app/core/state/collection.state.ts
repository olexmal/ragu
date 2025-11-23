import { Injectable, signal } from '@angular/core';
import { Collection } from '../models/collection.models';

@Injectable({
  providedIn: 'root'
})
export class CollectionState {
  private collectionsSignal = signal<Collection[]>([]);
  private loadingSignal = signal<boolean>(false);
  private errorSignal = signal<string | null>(null);

  readonly collections = this.collectionsSignal.asReadonly();
  readonly loading = this.loadingSignal.asReadonly();
  readonly error = this.errorSignal.asReadonly();

  setCollections(collections: Collection[]): void {
    this.collectionsSignal.set(collections);
    this.loadingSignal.set(false);
    this.errorSignal.set(null);
  }

  setLoading(loading: boolean): void {
    this.loadingSignal.set(loading);
  }

  setError(error: string): void {
    this.errorSignal.set(error);
    this.loadingSignal.set(false);
  }

  addCollection(collection: Collection): void {
    this.collectionsSignal.update(collections => [...collections, collection]);
  }

  removeCollection(name: string): void {
    this.collectionsSignal.update(collections => 
      collections.filter(c => c.name !== name)
    );
  }

  clear(): void {
    this.collectionsSignal.set([]);
    this.errorSignal.set(null);
    this.loadingSignal.set(false);
  }
}

