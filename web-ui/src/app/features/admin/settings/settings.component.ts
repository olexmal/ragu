import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { SettingsService } from '../../../core/services/settings.service';
import { SystemNameService } from '../../../core/services/system-name.service';
import { ConfluenceSettings, ConfluenceTestResult, ConfluenceFetchResponse, SystemSettings, LLMProvidersSettings, LLMProviderConfig, LLMProviderType, LLMProviderTestResult } from '../../../core/models/settings.models';
import { finalize } from 'rxjs/operators';
import { HelpIconComponent } from '../../../shared/components/help-icon/help-icon.component';
import { SETTINGS_HELP_TEXT } from './settings-help-text';

@Component({
  selector: 'app-settings',
  standalone: true,
  imports: [CommonModule, FormsModule, HelpIconComponent],
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

  // LLM Provider settings
  llmProviders = signal<LLMProvidersSettings>({
    llmProviders: {},
    embeddingProviders: {}
  });
  llmLoading = signal<boolean>(false);
  llmError = signal<string>('');
  llmSuccess = signal<string>('');
  llmTestLoading = signal<{ [key: string]: boolean }>({});
  llmTestErrors = signal<{ [key: string]: string }>({});
  llmTestSuccess = signal<{ [key: string]: string }>({});
  newProviderType = signal<LLMProviderType | ''>('');
  availableProviderTypes: LLMProviderType[] = ['ollama', 'openrouter', 'openai', 'anthropic', 'azure-openai', 'google'];

  ngOnInit(): void {
    // Clear any previous messages on component initialization
    this.error.set('');
    this.success.set('');
    this.systemError.set('');
    this.systemSuccess.set('');
    this.testResult.set(null);
    this.loadSettings();
    this.loadSystemSettings();
    this.loadLLMProviders();
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

  // LLM Provider methods
  loadLLMProviders(): void {
    this.llmLoading.set(true);
    this.llmError.set('');
    this.settingsService.getLLMProviders().subscribe({
      next: (providers: LLMProvidersSettings) => {
        this.llmProviders.set(providers);
        this.llmLoading.set(false);
      },
      error: (err: any) => {
        this.llmError.set(err?.error?.error || err?.error?.message || err?.message || 'Failed to load LLM provider settings');
        this.llmLoading.set(false);
      }
    });
  }

  saveLLMProviders(): void {
    this.llmLoading.set(true);
    this.llmError.set('');
    this.llmSuccess.set('');

    const providers = this.llmProviders();
    this.settingsService.saveLLMProviders(providers).subscribe({
      next: () => {
        this.llmSuccess.set('LLM provider settings saved successfully');
        this.llmLoading.set(false);
      },
      error: (err: any) => {
        const errorMessage = err?.error?.error || err?.error?.message || err?.message || 'Failed to save settings';
        this.llmError.set(errorMessage);
        this.llmLoading.set(false);
      }
    });
  }

  addLLMProvider(type: 'llm' | 'embedding', providerType: LLMProviderType): void {
    const providers = this.llmProviders();
    const providerKey = `${providerType}_${Date.now()}`;
    
    const defaultConfig: LLMProviderConfig = {
      enabled: false,
      isActive: false,
      type: providerType,
      model: this.getDefaultModel(providerType),
      temperature: 0
    };

    if (type === 'llm') {
      this.llmProviders.set({
        ...providers,
        llmProviders: {
          ...providers.llmProviders,
          [providerKey]: defaultConfig
        }
      });
    } else {
      this.llmProviders.set({
        ...providers,
        embeddingProviders: {
          ...providers.embeddingProviders,
          [providerKey]: defaultConfig
        }
      });
    }
  }

  removeLLMProvider(type: 'llm' | 'embedding', providerKey: string): void {
    const providers = this.llmProviders();
    if (type === 'llm') {
      const { [providerKey]: removed, ...remainingLLMProviders } = providers.llmProviders;
      this.llmProviders.set({
        ...providers,
        llmProviders: remainingLLMProviders
      });
    } else {
      const { [providerKey]: removed, ...remainingEmbeddingProviders } = providers.embeddingProviders;
      this.llmProviders.set({
        ...providers,
        embeddingProviders: remainingEmbeddingProviders
      });
    }
  }

  setActiveLLMProvider(providerKey: string): void {
    const providers = this.llmProviders();
    // Create new objects with updated isActive flags
    const updatedLLMProviders: { [key: string]: LLMProviderConfig } = {};
    Object.keys(providers.llmProviders).forEach(key => {
      updatedLLMProviders[key] = {
        ...providers.llmProviders[key],
        isActive: key === providerKey
      };
    });
    this.llmProviders.set({
      ...providers,
      llmProviders: updatedLLMProviders
    });
  }

  setActiveEmbeddingProvider(providerKey: string): void {
    const providers = this.llmProviders();
    // Create new objects with updated isActive flags
    const updatedEmbeddingProviders: { [key: string]: LLMProviderConfig } = {};
    Object.keys(providers.embeddingProviders).forEach(key => {
      updatedEmbeddingProviders[key] = {
        ...providers.embeddingProviders[key],
        isActive: key === providerKey
      };
    });
    this.llmProviders.set({
      ...providers,
      embeddingProviders: updatedEmbeddingProviders
    });
  }

  testLLMProvider(providerKey: string, type: 'llm' | 'embedding'): void {
    const providers = this.llmProviders();
    const provider = type === 'llm' 
      ? providers.llmProviders[providerKey]
      : providers.embeddingProviders[providerKey];
    
    if (!provider) return;

    // Create a unique key that includes the provider type to avoid conflicts
    const uniqueKey = `${type}-${providerKey}`;

    // Prevent multiple simultaneous tests for the same provider
    if (this.llmTestLoading()[uniqueKey]) {
      return;
    }

    // Clear previous messages for this specific provider before starting new test
    const testErrors = { ...this.llmTestErrors() };
    const testSuccess = { ...this.llmTestSuccess() };
    delete testErrors[providerKey];
    delete testSuccess[providerKey];
    this.llmTestErrors.set(testErrors);
    this.llmTestSuccess.set(testSuccess);
    this.llmTestLoading.set({ ...this.llmTestLoading(), [uniqueKey]: true });

    const providerName = this.getProviderDisplayName(provider.type);

    // Pass the category (llm or embedding) to the service
    this.settingsService.testLLMProvider(provider.type, provider, type).subscribe({
      next: (result: LLMProviderTestResult) => {
        this.llmTestLoading.set({ ...this.llmTestLoading(), [uniqueKey]: false });
        const updatedErrors = { ...this.llmTestErrors() };
        const updatedSuccess = { ...this.llmTestSuccess() };
        
        if (result.success) {
          // Clear error for this provider and set success
          delete updatedErrors[providerKey];
          updatedSuccess[providerKey] = `${providerName}: ${result.message}`;
          this.llmTestErrors.set(updatedErrors);
          this.llmTestSuccess.set(updatedSuccess);
        } else {
          // Clear success for this provider and set error
          delete updatedSuccess[providerKey];
          updatedErrors[providerKey] = `${providerName}: ${result.message}`;
          this.llmTestSuccess.set(updatedSuccess);
          this.llmTestErrors.set(updatedErrors);
        }
      },
      error: (err: any) => {
        this.llmTestLoading.set({ ...this.llmTestLoading(), [uniqueKey]: false });
        const updatedErrors = { ...this.llmTestErrors() };
        const updatedSuccess = { ...this.llmTestSuccess() };
        // Clear success for this provider and set error
        delete updatedSuccess[providerKey];
        const errorMessage = err?.error?.error || err?.error?.message || err?.message || 'Failed to test provider';
        updatedErrors[providerKey] = `${providerName}: ${errorMessage}`;
        this.llmTestSuccess.set(updatedSuccess);
        this.llmTestErrors.set(updatedErrors);
      }
    });
  }

  isProviderTestLoading(providerKey: string, type: 'llm' | 'embedding'): boolean {
    const uniqueKey = `${type}-${providerKey}`;
    return this.llmTestLoading()[uniqueKey] || false;
  }

  getProviderTestError(providerKey: string): string | undefined {
    return this.llmTestErrors()[providerKey];
  }

  getProviderTestSuccess(providerKey: string): string | undefined {
    return this.llmTestSuccess()[providerKey];
  }

  getDefaultModel(providerType: LLMProviderType): string {
    const defaults: { [key in LLMProviderType]: string } = {
      'ollama': 'mistral',
      'openrouter': 'openai/gpt-4',
      'openai': 'gpt-4',
      'anthropic': 'claude-3-opus-20240229',
      'azure-openai': 'gpt-4',
      'google': 'gemini-pro'
    };
    return defaults[providerType] || '';
  }

  getProviderDisplayName(providerType: LLMProviderType): string {
    const names: { [key in LLMProviderType]: string } = {
      'ollama': 'Ollama',
      'openrouter': 'OpenRouter',
      'openai': 'OpenAI',
      'anthropic': 'Anthropic (Claude)',
      'azure-openai': 'Azure OpenAI',
      'google': 'Google (Gemini)'
    };
    return names[providerType] || providerType;
  }

  // Helper methods for template
  getLLMProviderKeys(): string[] {
    return Object.keys(this.llmProviders().llmProviders);
  }

  getEmbeddingProviderKeys(): string[] {
    return Object.keys(this.llmProviders().embeddingProviders);
  }

  addLLMProviderAndClear(type: 'llm' | 'embedding'): void {
    const providerType = this.newProviderType();
    if (providerType) {
      this.addLLMProvider(type, providerType as LLMProviderType);
      this.newProviderType.set('');
    }
  }

  getHelpText(section: string, field: string): string {
    return SETTINGS_HELP_TEXT[section]?.[field] || '';
  }
}

