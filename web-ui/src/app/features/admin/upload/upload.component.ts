import { Component, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { EmbedService } from '../../../core/services/embed.service';
import { EmbedResponse } from '../../../core/models/document.models';

@Component({
  selector: 'app-upload',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './upload.component.html',
  styleUrl: './upload.component.scss'
})
export class UploadComponent {
  private embedService = inject(EmbedService);

  selectedFiles = signal<File[]>([]);
  version = signal<string>('');
  overwrite = signal<boolean>(false);
  uploading = signal<boolean>(false);
  uploadResults = signal<EmbedResponse[]>([]);
  error = signal<string>('');

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
      this.error.set('Please select at least one file');
      return;
    }

    this.uploading.set(true);
    this.error.set('');
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
      this.error.set(error.message || 'Upload failed');
      this.uploading.set(false);
    });
  }

  clearResults(): void {
    this.uploadResults.set([]);
    this.selectedFiles.set([]);
  }
}

