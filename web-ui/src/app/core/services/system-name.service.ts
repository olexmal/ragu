import { Injectable, signal, inject } from '@angular/core';
import { SettingsService } from './settings.service';
import { SystemSettings } from '../models/settings.models';

@Injectable({
  providedIn: 'root'
})
export class SystemNameService {
  private settingsService = inject(SettingsService);
  
  systemName = signal<string>('RAGU');

  constructor() {
    this.loadSystemName();
  }

  private loadSystemName(): void {
    // Try to load from settings, fallback to default
    this.settingsService.getSystemSettings().subscribe({
      next: (settings) => {
        this.systemName.set(settings.systemName || 'RAGU');
      },
      error: () => {
        // Use default if loading fails
        this.systemName.set('RAGU');
      }
    });
  }

  updateSystemName(name: string): void {
    this.systemName.set(name);
  }

  reloadSystemName(): void {
    this.loadSystemName();
  }
}

