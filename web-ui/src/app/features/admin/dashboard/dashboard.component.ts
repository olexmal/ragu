import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { StatsService } from '../../../core/services/stats.service';
import { CollectionService } from '../../../core/services/collection.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.component.html',
  styleUrl: './dashboard.component.scss'
})
export class DashboardComponent implements OnInit {
  private statsService = inject(StatsService);
  private collectionService = inject(CollectionService);

  stats = signal<any>(null);
  collections = signal<any[]>([]);
  loading = signal<boolean>(true);

  ngOnInit(): void {
    this.loadStats();
    this.loadCollections();
  }

  loadStats(): void {
    this.statsService.getStats(7).subscribe({
      next: (data) => {
        this.stats.set(data);
        this.loading.set(false);
      },
      error: (error) => {
        console.error('Failed to load stats:', error);
        this.loading.set(false);
      }
    });
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
}

