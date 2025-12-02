import { Component, inject, signal, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EmbedService } from '../../../core/services/embed.service';
import { EmbedResponse, BatchEmbedResponse, ScrapeEmbedResponse, ScrapeTaskStatus } from '../../../core/models/document.models';
import { HelpIconComponent } from '../../../shared/components/help-icon/help-icon.component';
import { environment } from '../../../../environments/environment';

@Component({
  selector: 'app-import',
  standalone: true,
  imports: [CommonModule, FormsModule, HelpIconComponent],
  templateUrl: './import.component.html',
  styleUrl: './import.component.scss'
})
export class ImportComponent implements OnDestroy {
  private embedService = inject(EmbedService);

  // Tab management
  activeTab = signal<string>('upload');
  
  // Upload Documents tab state
  selectedFiles = signal<File[]>([]);
  version = signal<string>('');
  collectionName = signal<string>('');
  overwrite = signal<boolean>(false);
  uploading = signal<boolean>(false);
  uploadResults = signal<EmbedResponse[]>([]);
  uploadError = signal<string>('');

  // Confluence Import tab state
  confluencePageId = signal<string>('');
  confluenceVersion = signal<string>('');
  confluenceCollectionName = signal<string>('');
  confluenceOverwrite = signal<boolean>(false);
  importing = signal<boolean>(false);
  importResult = signal<EmbedResponse | null>(null);
  importError = signal<string>('');

  // Web Scraping tab state
  scrapeUrl = signal<string>('');
  scrapeVersion = signal<string>('');
  scrapeCollectionName = signal<string>('');
  scrapeMaxDepth = signal<number>(3);
  scrapeOverwrite = signal<boolean>(false);
  scraping = signal<boolean>(false);
  scrapeResult = signal<ScrapeEmbedResponse | null>(null);
  scrapeError = signal<string>('');
  scrapeTaskId = signal<string | null>(null);
  scrapeProgress = signal<number>(0);
  scrapeStatusMessage = signal<string>('');
  
  // Polling cleanup references
  private pollIntervalId: ReturnType<typeof setInterval> | null = null;
  private pollTimeoutId: ReturnType<typeof setTimeout> | null = null;

  setActiveTab(tabId: string): void {
    this.activeTab.set(tabId);
  }

  // Upload Documents methods
  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    if (input.files) {
      this.selectedFiles.set(Array.from(input.files));
    }
  }

  onDragOver(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
  }

  onDragLeave(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
  }

  onDrop(event: DragEvent): void {
    event.preventDefault();
    event.stopPropagation();
    
    if (event.dataTransfer?.files) {
      this.selectedFiles.set(Array.from(event.dataTransfer.files));
    }
  }

  removeFile(index: number): void {
    this.selectedFiles.update(files => files.filter((_, i) => i !== index));
  }

  uploadFiles(): void {
    if (this.selectedFiles().length === 0) {
      this.uploadError.set('Please select at least one file');
      return;
    }

    this.uploading.set(true);
    this.uploadError.set('');
    this.uploadResults.set([]);

    const uploadPromises = this.selectedFiles().map(file =>
      this.embedService.embedFile(
        file,
        this.version() || undefined,
        this.collectionName() || undefined,
        this.overwrite()
      ).toPromise()
    );

    Promise.all(uploadPromises).then(results => {
      this.uploadResults.set(results.filter(r => r !== undefined) as EmbedResponse[]);
      this.uploading.set(false);
      if (results.length === this.selectedFiles().length) {
        this.selectedFiles.set([]);
      }
    }).catch(error => {
      this.uploadError.set(error.message || 'Upload failed');
      this.uploading.set(false);
    });
  }

  clearUploadResults(): void {
    this.uploadResults.set([]);
    this.selectedFiles.set([]);
  }

  // Confluence Import methods
  importConfluencePage(): void {
    const pageId = this.confluencePageId().trim();
    if (!pageId) {
      this.importError.set('Please enter a Confluence page ID');
      return;
    }

    this.importing.set(true);
    this.importError.set('');
    this.importResult.set(null);

    this.embedService.importConfluencePage(
      pageId,
      this.confluenceVersion() || undefined,
      this.confluenceCollectionName() || undefined,
      this.confluenceOverwrite()
    ).subscribe({
      next: (result: EmbedResponse) => {
        this.importResult.set(result);
        this.importing.set(false);
        this.confluencePageId.set('');
      },
      error: (error: any) => {
        this.importError.set(error.error?.error || error.message || 'Import failed');
        this.importing.set(false);
      }
    });
  }

  clearImportResult(): void {
    this.importResult.set(null);
    this.confluencePageId.set('');
  }

  // Web Scraping methods
  onScrapeUrl(): void {
    const url = this.scrapeUrl().trim();
    if (!url) {
      this.scrapeError.set('Please enter a valid URL');
      return;
    }

    // Basic URL validation
    try {
      new URL(url);
    } catch {
      this.scrapeError.set('Please enter a valid URL (including http:// or https://)');
      return;
    }

    this.scraping.set(true);
    this.scrapeError.set('');
    this.scrapeResult.set(null);
    this.scrapeProgress.set(0);
    this.scrapeTaskId.set(null);
    this.scrapeStatusMessage.set('');

    this.embedService.scrapeAndEmbedUrl(
      url,
      this.scrapeVersion() || undefined,
      this.scrapeCollectionName() || undefined,
      this.scrapeMaxDepth(),
      this.scrapeOverwrite()
    ).subscribe({
      next: (result: ScrapeEmbedResponse) => {
        // Check if this is an async job (has task_id)
        if (result.task_id) {
          this.scrapeTaskId.set(result.task_id);
          this.scrapeProgress.set(0);
          this.scrapeStatusMessage.set('Starting scraping task...');
          this.pollScrapeStatus(result.task_id);
        } else {
          // Synchronous response (fallback mode)
          this.scrapeResult.set(result);
          this.scraping.set(false);
          this.scrapeUrl.set('');
        }
      },
      error: (error: any) => {
        this.scrapeError.set(error.error?.error || error.message || 'Scraping failed');
        this.scraping.set(false);
      }
    });
  }

  private eventSource: EventSource | null = null;

  pollScrapeStatus(taskId: string): void {
    // Close any existing EventSource connection
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }

    // Use Server-Sent Events for real-time updates
    const streamUrl = `${environment.apiUrl}/embed-url/stream/${taskId}`;
    
    this.eventSource = new EventSource(streamUrl);
    
    this.eventSource.onmessage = (event) => {
      try {
        const status: ScrapeTaskStatus = JSON.parse(event.data);
        
        // Check for authentication errors first
        if (status.state === 'ERROR' && status.error?.includes('Authentication')) {
          this.eventSource?.close();
          this.eventSource = null;
          this.scraping.set(false);
          this.scrapeError.set('Authentication required. Please log in and try again.');
          // Fall back to polling method
          this.fallbackToPolling(taskId);
          return;
        }
        
        // Update progress
        if (status.progress !== undefined) {
          this.scrapeProgress.set(status.progress);
        }
        
        // Update status message
        if (status.state === 'PROGRESS' && status.status) {
          this.scrapeStatusMessage.set(status.status);
        } else if (status.state === 'PENDING') {
          this.scrapeStatusMessage.set('Task is waiting to be processed...');
        } else if (status.state === 'SUCCESS') {
          this.scrapeStatusMessage.set('Completed successfully');
        } else if (status.state === 'FAILURE') {
          this.scrapeStatusMessage.set('Failed');
        } else {
          this.scrapeStatusMessage.set(status.status || '');
        }
        
        // Debug logging
        console.log('SSE update:', {
          state: status.state,
          progress: status.progress,
          status: status.status,
          url: status.url
        });

        if (status.state === 'SUCCESS') {
          this.eventSource?.close();
          this.eventSource = null;
          this.scraping.set(false);
          this.scrapeProgress.set(100);
          this.scrapeError.set('');
          if (status.result) {
            this.scrapeResult.set({
              message: status.result.message || 'Scraping completed',
              results: status.result.results,
              version: status.result.version
            });
          }
          this.scrapeUrl.set('');
          this.scrapeTaskId.set(null);
          this.scrapeStatusMessage.set('');
        } else if (status.state === 'FAILURE') {
          this.eventSource?.close();
          this.eventSource = null;
          this.scraping.set(false);
          this.scrapeError.set(status.error || 'Scraping failed');
          this.scrapeTaskId.set(null);
        } else if (status.state === 'REVOKED') {
          this.eventSource?.close();
          this.eventSource = null;
          this.scraping.set(false);
          this.scrapeError.set('Scraping was cancelled');
          this.scrapeStatusMessage.set('Cancelled');
          this.scrapeTaskId.set(null);
        } else if (status.state === 'TIMEOUT' || status.state === 'ERROR') {
          this.eventSource?.close();
          this.eventSource = null;
          this.scraping.set(false);
          this.scrapeError.set(status.error || status.status || 'Connection error');
          // Keep task ID so user can manually check status
        }
        // PENDING and PROGRESS states continue receiving updates
      } catch (error) {
        console.error('Error parsing SSE message:', error);
        this.eventSource?.close();
        this.eventSource = null;
        this.scraping.set(false);
        this.scrapeError.set('Failed to parse status update');
      }
    };

    this.eventSource.onerror = (error) => {
      // Check if it's an authentication error (401)
      if (this.eventSource?.readyState === EventSource.CLOSED) {
        // Connection was closed, might be auth error
        console.error('SSE connection closed:', error);
        this.eventSource?.close();
        this.eventSource = null;
        this.scraping.set(false);
        this.scrapeError.set('Connection closed - authentication may be required. Falling back to polling.');
        // Fall back to polling method
        this.fallbackToPolling(taskId);
      } else {
        console.error('SSE connection error:', error);
        // Don't close on temporary errors, EventSource will retry
      }
    };
  }

  clearScrapeResult(): void {
    // Close SSE connection if open
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    
    this.scrapeResult.set(null);
          this.scrapeUrl.set('');
          this.scrapeTaskId.set(null);
          this.scrapeProgress.set(0);
          this.scrapeError.set('');
          this.scrapeStatusMessage.set('');
  }

  ngOnDestroy(): void {
    // Clean up SSE connection on component destroy
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
    }
    // Clean up polling timers
    this.clearPollingTimers();
  }
  
  private clearPollingTimers(): void {
    if (this.pollIntervalId) {
      clearInterval(this.pollIntervalId);
      this.pollIntervalId = null;
    }
    if (this.pollTimeoutId) {
      clearTimeout(this.pollTimeoutId);
      this.pollTimeoutId = null;
    }
  }

  private fallbackToPolling(taskId: string): void {
    // Clear any existing polling timers before starting new ones
    this.clearPollingTimers();
    
    // Fallback to polling if SSE fails (e.g., due to auth issues)
    this.pollIntervalId = setInterval(() => {
      this.embedService.getScrapeTaskStatus(taskId).subscribe({
        next: (status: ScrapeTaskStatus) => {
          if (status.progress !== undefined) {
            this.scrapeProgress.set(status.progress);
          }

          if (status.state === 'SUCCESS') {
            this.clearPollingTimers();
            this.scraping.set(false);
            this.scrapeProgress.set(100);
            if (status.result) {
              this.scrapeResult.set({
                message: status.result.message || 'Scraping completed',
                results: status.result.results,
                version: status.result.version
              });
            }
            this.scrapeUrl.set('');
            this.scrapeTaskId.set(null);
          } else if (status.state === 'FAILURE') {
            this.clearPollingTimers();
            this.scraping.set(false);
            this.scrapeError.set(status.error || 'Scraping failed');
            this.scrapeTaskId.set(null);
          } else if (status.state === 'REVOKED') {
            this.clearPollingTimers();
            this.scraping.set(false);
            this.scrapeError.set('Scraping was cancelled');
            this.scrapeStatusMessage.set('Cancelled');
            this.scrapeTaskId.set(null);
          }
          // PENDING and PROGRESS states continue polling
        },
        error: (error: any) => {
          this.clearPollingTimers();
          this.scraping.set(false);
          this.scrapeError.set(error.error?.error || error.message || 'Failed to get task status');
        }
      });
    }, 2000); // Poll every 2 seconds

    // Stop polling after 10 minutes (safety timeout)
    this.pollTimeoutId = setTimeout(() => {
      this.clearPollingTimers();
      if (this.scraping()) {
        this.scraping.set(false);
        this.scrapeError.set('Scraping timeout - task may still be running. Check status manually.');
      }
    }, 600000);
  }

  checkScrapeStatus(): void {
    const taskId = this.scrapeTaskId();
    if (!taskId) {
      this.scrapeError.set('No task ID available. Please start a new scraping task.');
      return;
    }

    this.scraping.set(true);
    this.embedService.getScrapeTaskStatus(taskId).subscribe({
      next: (status: ScrapeTaskStatus) => {
        if (status.progress !== undefined) {
          this.scrapeProgress.set(status.progress);
        }

        if (status.state === 'SUCCESS') {
          this.scraping.set(false);
          this.scrapeProgress.set(100);
          this.scrapeError.set('');
          if (status.result) {
            this.scrapeResult.set({
              message: status.result.message || 'Scraping completed',
              results: status.result.results,
              version: status.result.version
            });
          }
          this.scrapeUrl.set('');
          this.scrapeTaskId.set(null);
        } else if (status.state === 'FAILURE') {
          this.scraping.set(false);
          this.scrapeError.set(status.error || 'Scraping failed');
          this.scrapeTaskId.set(null);
        } else if (status.state === 'REVOKED') {
          this.scraping.set(false);
          this.scrapeError.set('Scraping was cancelled');
          this.scrapeStatusMessage.set('Cancelled');
          this.scrapeTaskId.set(null);
        } else if (status.state === 'PROGRESS') {
          // Task is still running, resume polling
          this.scrapeError.set('');
          this.pollScrapeStatus(taskId);
        } else {
          // PENDING state
          this.scrapeError.set('');
          this.pollScrapeStatus(taskId);
        }
      },
      error: (error: any) => {
        this.scraping.set(false);
        this.scrapeError.set(error.error?.error || error.message || 'Failed to get task status');
      }
    });
  }

  cancelScraping(): void {
    const taskId = this.scrapeTaskId();
    if (!taskId) {
      return;
    }

    if (!confirm('Are you sure you want to stop and cancel the scraping task?')) {
      return;
    }

    this.embedService.cancelScrapeTask(taskId).subscribe({
      next: () => {
        // Close SSE connection
        if (this.eventSource) {
          this.eventSource.close();
          this.eventSource = null;
        }
        
        this.scraping.set(false);
        this.scrapeError.set('Scraping was cancelled');
        this.scrapeStatusMessage.set('Cancelled');
        this.scrapeTaskId.set(null);
      },
      error: (error: any) => {
        this.scrapeError.set(error.error?.error || error.message || 'Failed to cancel task');
      }
    });
  }
}

