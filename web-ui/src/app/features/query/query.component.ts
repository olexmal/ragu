import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { finalize } from 'rxjs/operators';
import { QueryService } from '../../core/services/query.service';
import { CollectionService } from '../../core/services/collection.service';
import { QueryState } from '../../core/state/query.state';
import { CollectionState } from '../../core/state/collection.state';
import { QueryRequest } from '../../core/models/query.models';
import { QueryResultsComponent } from './components/query-results/query-results.component';

@Component({
  selector: 'app-query',
  standalone: true,
  imports: [CommonModule, FormsModule, QueryResultsComponent],
  templateUrl: './query.component.html',
  styleUrl: './query.component.scss'
})
export class QueryComponent {
  private queryService = inject(QueryService);
  private collectionService = inject(CollectionService);
  queryState = inject(QueryState);
  collectionState = inject(CollectionState);

  queryText = signal<string>('');
  selectedVersion = signal<string | undefined>(undefined);
  k = signal<number>(3);
  useSimple = signal<boolean>(false);
  collections = signal<any[]>([]);

  constructor() {
    this.loadCollections();
  }

  loadCollections(): void {
    this.collectionService.getCollections().subscribe({
      next: (response) => {
        this.collections.set(response.collections);
      },
      error: (error) => {
        console.error('Failed to load collections:', error);
      }
    });
  }

  onSubmit(): void {
    // Prevent multiple submissions
    if (this.queryState.loading()) {
      return;
    }

    const query = this.queryText().trim();
    if (!query) {
      return;
    }

    this.queryState.setLoading(true);
    this.queryState.setError(null);

    const request: QueryRequest = {
      query,
      version: this.selectedVersion(),
      k: this.k(),
      simple: this.useSimple()
    };

    this.queryService.query(request).pipe(
      finalize(() => {
        // Ensure loading is always set to false when request completes
        this.queryState.setLoading(false);
      })
    ).subscribe({
      next: (response) => {
        this.queryState.setQuery(response);
      },
      error: (error) => {
        this.queryState.setError(error.message || 'Query failed');
      }
    });
  }

  clearQuery(): void {
    this.queryText.set('');
    this.queryState.clear();
  }
}

