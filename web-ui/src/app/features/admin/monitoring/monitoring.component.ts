import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { StatsService } from '../../../core/services/stats.service';

@Component({
  selector: 'app-monitoring',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './monitoring.component.html',
  styleUrl: './monitoring.component.scss'
})
export class MonitoringComponent implements OnInit {
  statsService = inject(StatsService);

  stats = signal<any>(null);
  loading = signal<boolean>(true);
  days = signal<number>(7);

  ngOnInit(): void {
    this.loadStats();
  }

  loadStats(): void {
    this.loading.set(true);
    this.statsService.getStats(this.days()).subscribe({
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

  onDaysChange(days: number): void {
    this.days.set(days);
    this.loadStats();
  }

  clearCache(): void {
    this.statsService.clearCache().subscribe({
      next: () => {
        this.loadStats();
      },
      error: (error) => {
        console.error('Failed to clear cache:', error);
      }
    });
  }
}

