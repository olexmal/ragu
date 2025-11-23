import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CollectionService } from '../../../core/services/collection.service';
import { Collection } from '../../../core/models/collection.models';

@Component({
  selector: 'app-collections',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './collections.component.html',
  styleUrl: './collections.component.scss'
})
export class CollectionsComponent implements OnInit {
  private collectionService = inject(CollectionService);

  collections = signal<Collection[]>([]);
  loading = signal<boolean>(true);
  error = signal<string>('');
  deleting = signal<string | null>(null);

  ngOnInit(): void {
    this.loadCollections();
  }

  loadCollections(): void {
    this.loading.set(true);
    this.collectionService.getCollections().subscribe({
      next: (response) => {
        this.collections.set(response.collections);
        this.loading.set(false);
      },
      error: (error) => {
        this.error.set(error.message || 'Failed to load collections');
        this.loading.set(false);
      }
    });
  }

  deleteCollection(version: string): void {
    if (!confirm(`Are you sure you want to delete collection "${version}"? This action cannot be undone.`)) {
      return;
    }

    this.deleting.set(version);
    this.collectionService.deleteCollection(version).subscribe({
      next: () => {
        this.loadCollections();
        this.deleting.set(null);
      },
      error: (error) => {
        this.error.set(error.message || 'Failed to delete collection');
        this.deleting.set(null);
      }
    });
  }

  extractVersion(name: string): string {
    const match = name.match(/v([\d.]+)$/);
    return match ? match[1] : name;
  }
}

