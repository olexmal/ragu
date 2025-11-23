import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SettingsService } from '../../../core/services/settings.service';
import { SystemNameService } from '../../../core/services/system-name.service';
import { ConfluenceSettings, ConfluenceTestResult, ConfluenceFetchResponse, SystemSettings } from '../../../core/models/settings.models';
import { finalize } from 'rxjs/operators';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './settings.component.html',
  styleUrl: './settings.component.scss'
})
export class SettingsComponent implements OnInit {
  private settingsService = inject(SettingsService);
  private systemNameService = inject(SystemNameService);

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

  systemSettings = signal<SystemSettings>({
    systemName: 'RAG System'
  });

  loading = signal<boolean>(false);
  testLoading = signal<boolean>(false);
  fetchLoading = signal<boolean>(false);
  systemLoading = signal<boolean>(false);
  error = signal<string>('');
  success = signal<string>('');
  systemError = signal<string>('');
  systemSuccess = signal<string>('');
  testResult = signal<{success: boolean, message: string} | null>(null);
  newPageId = signal<string>('');

  ngOnInit(): void {
    // Clear any previous messages on component initialization
    this.error.set('');
    this.success.set('');
    this.systemError.set('');
    this.systemSuccess.set('');
    this.testResult.set(null);
    this.loadSettings();
    this.loadSystemSettings();
  }

  loadSettings(): void {
    this.loading.set(true);
    this.error.set('');
    this.success.set('');
    this.testResult.set(null);
    this.settingsService.getConfluenceSettings().subscribe({
      next: (settings: ConfluenceSettings) => {
        this.confluenceSettings.set(settings);
        this.loading.set(false);
        this.error.set(''); // Clear any previous errors
      },
      error: (err: any) => {
        this.error.set(err.message || 'Failed to load settings');
        this.loading.set(false);
      }
    });
  }

  loadSystemSettings(): void {
    this.settingsService.getSystemSettings().subscribe({
      next: (settings: SystemSettings) => {
        this.systemSettings.set({
          systemName: settings.systemName || 'RAG System'
        });
      },
      error: (err: any) => {
        console.error('Failed to load system settings:', err);
        // Use default if loading fails
        this.systemSettings.set({ systemName: 'RAG System' });
      }
    });
  }

  saveSystemSettings(): void {
    const settings = this.systemSettings();
    if (!settings.systemName || !settings.systemName.trim()) {
      this.systemError.set('System name is required');
      return;
    }

    this.systemLoading.set(true);
    this.systemError.set('');
    this.error.set(''); // Also clear Confluence errors
    this.success.set(''); // Also clear Confluence success
    // Don't clear systemSuccess here - let it persist

    this.settingsService.saveSystemSettings(settings).subscribe({
      next: (response: any) => {
        // Always set a success message - use a hardcoded string to ensure it's not empty
        const successMsg = 'System settings saved successfully';
        console.log('Setting systemSuccess to:', successMsg);
        this.systemSuccess.set(successMsg);
        console.log('systemSuccess after set:', this.systemSuccess());
        
        // Update the system name service immediately
        this.systemNameService.updateSystemName(settings.systemName.trim());
        // Also reload from server to ensure consistency
        this.systemNameService.reloadSystemName();
        this.systemLoading.set(false);
      },
      error: (err: any) => {
        const errorMsg = err.error?.error || err.error?.message || err.message || 'Failed to save system settings';
        this.systemError.set(errorMsg);
        this.systemLoading.set(false);
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

    console.log('Saving Confluence settings:', { ...settings, password: '***', api_token: '***' });

    this.settingsService.saveConfluenceSettings(settings)
      .pipe(
        finalize(() => {
          console.log('Request completed (success or error)');
          this.loading.set(false);
        })
      )
      .subscribe({
        next: (response: any) => {
          console.log('Settings saved successfully:', response);
          this.success.set('Settings saved successfully');
        },
        error: (err: any) => {
          console.error('Error saving settings:', err);
          console.error('Full error object:', JSON.stringify(err, null, 2));
          const errorMessage = err?.error?.error || err?.error?.message || err?.message || 'Failed to save settings';
          this.error.set(errorMessage);
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

