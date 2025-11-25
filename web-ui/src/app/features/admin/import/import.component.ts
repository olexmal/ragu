import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EmbedService } from '../../../core/services/embed.service';
import { EmbedResponse } from '../../../core/models/document.models';
import { HelpIconComponent } from '../../../shared/components/help-icon/help-icon.component';

@Component({
  selector: 'app-import',
  standalone: true,
  imports: [CommonModule, FormsModule, HelpIconComponent],
  templateUrl: './import.component.html',
  styleUrl: './import.component.scss'
})
export class ImportComponent {
  private embedService = inject(EmbedService);

  // Tab management
  activeTab = signal<string>('upload');
  
  // Upload Documents tab state
  selectedFiles = signal<File[]>([]);
  version = signal<string>('');
  overwrite = signal<boolean>(false);
  uploading = signal<boolean>(false);
  uploadResults = signal<EmbedResponse[]>([]);
  uploadError = signal<string>('');

  // Confluence Import tab state
  confluencePageId = signal<string>('');
  confluenceVersion = signal<string>('');
  confluenceOverwrite = signal<boolean>(false);
  importing = signal<boolean>(false);
  importResult = signal<EmbedResponse | null>(null);
  importError = signal<string>('');

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
}

