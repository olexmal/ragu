import { Component, Input, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SourceDocument } from '../../../../core/models/query.models';

@Component({
  selector: 'app-sources-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './sources-panel.component.html',
  styleUrl: './sources-panel.component.scss'
})
export class SourcesPanelComponent {
  @Input() sources: SourceDocument[] = [];
  @Input() selectedSourceIndex: number | null = null;

  expandedSources = signal<Set<number>>(new Set());
  searchTerm = signal<string>('');

  toggleSource(index: number): void {
    const expanded = this.expandedSources();
    if (expanded.has(index)) {
      expanded.delete(index);
    } else {
      expanded.add(index);
    }
    this.expandedSources.set(new Set(expanded));
  }

  isExpanded(index: number): boolean {
    return this.expandedSources().has(index);
  }

  get filteredSources(): SourceDocument[] {
    const term = this.searchTerm().toLowerCase();
    if (!term) {
      return this.sources;
    }
    return this.sources.filter((source, index) => {
      const content = source.content?.toLowerCase() || '';
      const filePath = source.metadata.file_path?.toLowerCase() || '';
      return content.includes(term) || filePath.includes(term);
    });
  }

  getSourceTitle(source: SourceDocument, index: number): string {
    return source.metadata.file_path || `Source ${index + 1}`;
  }

  copySourceContent(content: string): void {
    navigator.clipboard.writeText(content).then(() => {
      // Could show toast notification
    });
  }
}

