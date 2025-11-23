import { Component, inject, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { CollectionService } from '../../../core/services/collection.service';
import { Collection, Document } from '../../../core/models/collection.models';

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
  deletingDocument = signal<{ version: string; docId: string } | null>(null);
  
  // Track expanded collections
  expandedCollections = signal<Set<string>>(new Set());
  
  // Store documents for each collection
  collectionDocuments = signal<Map<string, Document[]>>(new Map());
  
  // Track loading state for documents
  loadingDocuments = signal<Set<string>>(new Set());
  
  // Track errors for document loading
  documentErrors = signal<Map<string, string>>(new Map());

  ngOnInit(): void {
    this.loadCollections();
  }

  loadCollections(): void {
    this.loading.set(true);
    this.collectionService.getCollections().subscribe({
      next: (response: { collections: Collection[]; total: number }) => {
        this.collections.set(response.collections);
        this.loading.set(false);
      },
      error: (error: any) => {
        this.error.set(error.message || 'Failed to load collections');
        this.loading.set(false);
      }
    });
  }

  toggleCollection(version: string): void {
    const expanded = new Set(this.expandedCollections());
    
    if (expanded.has(version)) {
      // Collapse
      expanded.delete(version);
    } else {
      // Expand - load documents if not already loaded
      expanded.add(version);
      if (!this.collectionDocuments().has(version)) {
        this.loadDocuments(version);
      }
    }
    
    this.expandedCollections.set(expanded);
  }

  isExpanded(version: string): boolean {
    return this.expandedCollections().has(version);
  }

  loadDocuments(version: string): void {
    const loading = new Set(this.loadingDocuments());
    loading.add(version);
    this.loadingDocuments.set(loading);
    
    const errors = new Map(this.documentErrors());
    errors.delete(version);
    this.documentErrors.set(errors);
    
    this.collectionService.getDocuments(version).subscribe({
      next: (response: { version: string; collection_name: string; documents: Document[]; total: number }) => {
        const documents = new Map(this.collectionDocuments());
        documents.set(version, response.documents);
        this.collectionDocuments.set(documents);
        
        loading.delete(version);
        this.loadingDocuments.set(loading);
      },
      error: (error: any) => {
        const errorMsg = error.error?.error || error.message || 'Failed to load documents';
        errors.set(version, errorMsg);
        this.documentErrors.set(errors);
        
        loading.delete(version);
        this.loadingDocuments.set(loading);
      }
    });
  }

  getDocuments(version: string): Document[] {
    return this.collectionDocuments().get(version) || [];
  }

  isLoadingDocuments(version: string): boolean {
    return this.loadingDocuments().has(version);
  }

  getDocumentError(version: string): string | undefined {
    return this.documentErrors().get(version);
  }

  deleteCollection(version: string): void {
    const collection = this.collections().find((c: Collection) => this.extractVersion(c.name) === version);
    const collectionName = collection?.name || `v${version}`;
    
    if (!confirm(`Are you sure you want to delete collection "${collectionName}"?\n\nThis will permanently delete all documents in this collection. This action cannot be undone.`)) {
      return;
    }

    this.deleting.set(version);
    this.error.set('');
    
    this.collectionService.deleteCollection(version).subscribe({
      next: () => {
        // Clean up expanded state and documents
        const expanded = new Set(this.expandedCollections());
        expanded.delete(version);
        this.expandedCollections.set(expanded);
        
        const documents = new Map(this.collectionDocuments());
        documents.delete(version);
        this.collectionDocuments.set(documents);
        
        this.loadCollections();
        this.deleting.set(null);
      },
      error: (error: any) => {
        this.error.set(error.error?.error || error.message || 'Failed to delete collection');
        this.deleting.set(null);
      }
    });
  }

  deleteDocument(version: string, docId: string, source: string): void {
    if (!confirm(`Are you sure you want to delete this document?\n\nSource: ${source}\n\nThis action cannot be undone.`)) {
      return;
    }

    this.deletingDocument.set({ version, docId });
    
    this.collectionService.deleteDocument(version, docId).subscribe({
      next: () => {
        // Remove document from local state
        const documents = new Map<string, Document[]>(this.collectionDocuments());
        const existingDocs = documents.get(version);
        const collectionDocs: Document[] = Array.isArray(existingDocs) ? existingDocs : [];
        const updatedDocs = collectionDocs.filter((doc: Document) => doc.id !== docId);
        documents.set(version, updatedDocs);
        this.collectionDocuments.set(documents);
        
        // Update collection count
        const collections = this.collections().map((c: Collection) => {
          const v = this.extractVersion(c.name);
          if (v === version) {
            return { ...c, count: Math.max(0, c.count - 1) };
          }
          return c;
        });
        this.collections.set(collections);
        
        this.deletingDocument.set(null);
      },
      error: (error: any) => {
        this.error.set(error.error?.error || error.message || 'Failed to delete document');
        this.deletingDocument.set(null);
      }
    });
  }

  isDeletingDocument(version: string, docId: string): boolean {
    const deleting = this.deletingDocument();
    return deleting?.version === version && deleting?.docId === docId;
  }

  extractVersion(name: string): string {
    const match = name.match(/v([\d.]+)$/);
    return match ? match[1] : name;
  }
}

