import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { QueryResponse } from '../../../../core/models/query.models';

@Component({
  selector: 'app-query-results',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './query-results.component.html',
  styleUrl: './query-results.component.scss'
})
export class QueryResultsComponent {
  @Input() queryResponse!: QueryResponse;
  
  expandedSources = new Set<number>();

  toggleSource(index: number): void {
    if (this.expandedSources.has(index)) {
      this.expandedSources.delete(index);
    } else {
      this.expandedSources.add(index);
    }
  }

  isExpanded(index: number): boolean {
    return this.expandedSources.has(index);
  }

  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text).then(() => {
      // Could show a toast notification here
    });
  }

  formatTime(seconds: number | undefined): string {
    if (!seconds || seconds === 0) {
      return '0ms';
    }
    if (seconds < 0.001) {
      return '<1ms';
    }
    if (seconds < 1) {
      return `${(seconds * 1000).toFixed(1)}ms`;
    }
    return `${seconds.toFixed(3)}s`;
  }

  getPercentage(value: number | undefined, total: number | undefined): string {
    if (!value || !total || total === 0) {
      return '0';
    }
    return ((value / total) * 100).toFixed(1);
  }
}

