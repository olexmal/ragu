import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SettingsService } from '../../../core/services/settings.service';
import { ConfluenceSettings, ConfluenceTestResult, ConfluenceFetchResponse } from '../../../core/models/settings.models';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss'
})
export class SettingsComponent implements OnInit {
  private settingsService = inject(SettingsService);

  confluenceSettings = signal<ConfluenceSettings>({
    enabled: false,
    url: '',
    instanceType: 'cloud',
    apiToken: '',
    username: '',
    password: '',
    pageIds: [],
    autoSync: false,
    syncInterval: 3600
  });

  loading = signal<boolean>(false);
  testLoading = signal<boolean>(false);
  fetchLoading = signal<boolean>(false);
  error = signal<string>('');
  success = signal<string>('');
  testResult = signal<{success: boolean, message: string} | null>(null);
  newPageId = signal<string>('');

  ngOnInit(): void {
    this.loadSettings();
  }

  loadSettings(): void {
    this.loading.set(true);
    this.error.set('');
    this.settingsService.getConfluenceSettings().subscribe({
      next: (settings: ConfluenceSettings) => {
        this.confluenceSettings.set(settings);
        this.loading.set(false);
      },
      error: (err: any) => {
        this.error.set(err.message || 'Failed to load settings');
        this.loading.set(false);
      }
    });
  }

  testConnection(): void {
    const settings = this.confluenceSettings();
    if (!settings.url) {
      this.error.set('URL is required');
      return;
    }

    this.testLoading.set(true);
    this.error.set('');
    this.testResult.set(null);

    this.settingsService.testConfluenceConnection(settings).subscribe({
      next: (result: ConfluenceTestResult) => {
        this.testResult.set(result);
        if (result.success) {
          this.success.set('Connection successful!');
        } else {
          this.error.set(result.message);
        }
        this.testLoading.set(false);
      },
      error: (err: any) => {
        this.error.set(err.message || 'Connection test failed');
        this.testResult.set({ success: false, message: err.message || 'Connection test failed' });
        this.testLoading.set(false);
      }
    });
  }

  saveSettings(): void {
    const settings = this.confluenceSettings();
    if (!settings.url) {
      this.error.set('URL is required');
      return;
    }

    this.loading.set(true);
    this.error.set('');
    this.success.set('');

    this.settingsService.saveConfluenceSettings(settings).subscribe({
      next: () => {
        this.success.set('Settings saved successfully');
        this.loading.set(false);
      },
      error: (err: any) => {
        this.error.set(err.message || 'Failed to save settings');
        this.loading.set(false);
      }
    });
  }

  fetchPages(): void {
    const settings = this.confluenceSettings();
    if (!settings.pageIds || settings.pageIds.length === 0) {
      this.error.set('At least one page ID is required');
      return;
    }

    this.fetchLoading.set(true);
    this.error.set('');
    this.success.set('');

    this.settingsService.fetchConfluencePages({
      pageIds: settings.pageIds,
      confluenceConfig: settings
    }).subscribe({
      next: (response: ConfluenceFetchResponse) => {
        this.success.set(`${response.message}. Success: ${response.results.success}, Failed: ${response.results.failed}`);
        this.fetchLoading.set(false);
      },
      error: (err: any) => {
        this.error.set(err.message || 'Failed to fetch pages');
        this.fetchLoading.set(false);
      }
    });
  }

  addPageId(): void {
    const pageId = this.newPageId().trim();
    if (!pageId) {
      return;
    }

    const settings = this.confluenceSettings();
    if (!settings.pageIds.includes(pageId)) {
      this.confluenceSettings.set({
        ...settings,
        pageIds: [...settings.pageIds, pageId]
      });
      this.newPageId.set('');
    }
  }

  removePageId(index: number): void {
    const settings = this.confluenceSettings();
    const newPageIds = [...settings.pageIds];
    newPageIds.splice(index, 1);
    this.confluenceSettings.set({
      ...settings,
      pageIds: newPageIds
    });
  }

  clearMessages(): void {
    this.error.set('');
    this.success.set('');
    this.testResult.set(null);
  }
}

