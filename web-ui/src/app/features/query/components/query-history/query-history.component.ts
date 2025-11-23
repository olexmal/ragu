import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HistoryService } from '../../../../core/services/history.service';
import { QueryService } from '../../../../core/services/query.service';

@Component({
  selector: 'app-query-history',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './query-history.component.html',
  styleUrl: './query-history.component.scss'
})
export class QueryHistoryComponent implements OnInit {
  private historyService = inject(HistoryService);
  private queryService = inject(QueryService);

  history = signal<any[]>([]);
  loading = signal<boolean>(true);
  searchTerm = signal<string>('');

  ngOnInit(): void {
    this.loadHistory();
  }

  loadHistory(): void {
    this.loading.set(true);
    this.historyService.getHistory(50, 0).subscribe({
      next: (data) => {
        this.history.set(data.history || []);
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Failed to load history:', error);
        this.loading.set(false);
      }
    });
  }

  searchHistory(): void {
    if (!this.searchTerm().trim()) {
      this.loadHistory();
      return;
    }

    this.loading.set(true);
    this.historyService.searchHistory(this.searchTerm()).subscribe({
      next: (data) => {
        this.history.set(data.results || []);
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Failed to search history:', error);
        this.loading.set(false);
      }
    });
  }

  rerunQuery(query: string): void {
    // Navigate to query page with pre-filled query
    // This would be handled by routing
    console.log('Rerun query:', query);
  }

  formatDate(timestamp: any): string {
    if (!timestamp) return 'N/A';
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return 'N/A';
    }
  }
}

