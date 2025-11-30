import { Component, signal, inject, OnInit, effect } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatComponent } from './components/chat/chat.component';
import { SettingsPanelComponent, QuerySettings } from './components/settings-panel/settings-panel.component';
import { SourcesPanelComponent } from './components/sources-panel/sources-panel.component';
import { ChatState } from '../../core/state/chat.state';
import { CollectionService } from '../../core/services/collection.service';

@Component({
  selector: 'app-query',
  standalone: true,
  imports: [CommonModule, ChatComponent, SettingsPanelComponent, SourcesPanelComponent],
  templateUrl: './query.component.html',
  styleUrl: './query.component.scss'
})
export class QueryComponent implements OnInit {
  private chatState = inject(ChatState);
  private collectionService = inject(CollectionService);

  showSettings = signal<boolean>(false);
  showSources = signal<boolean>(false);
  activeTab = signal<'settings' | 'sources'>('settings');

  currentSources = signal<any[]>([]);
  selectedSourceIndex = signal<number | null>(null);
  collections = signal<any[]>([]);

  settings: QuerySettings = { k: 3, useSimple: false };

  constructor() {
    // Watch for message changes to update sources
    effect(() => {
      this.chatState.messages(); // Track changes
      this.updateSources();
    });
  }

  ngOnInit(): void {
    this.loadCollections();
  }

  loadCollections(): void {
    this.collectionService.getCollections().subscribe({
      next: (response) => {
        this.collections.set(response.collections || []);
      },
      error: (error) => {
        console.error('Failed to load collections:', error);
      }
    });
  }

  toggleSettings(): void {
    if (this.showSettings()) {
      this.showSettings.set(false);
    } else {
      this.showSettings.set(true);
      this.showSources.set(false);
      this.activeTab.set('settings');
    }
  }

  toggleSources(): void {
    if (this.showSources()) {
      this.showSources.set(false);
    } else {
      this.showSources.set(true);
      this.showSettings.set(false);
      this.activeTab.set('sources');
    }
  }

  onSettingsChange(settings: QuerySettings): void {
    this.settings = settings;
  }

  onClearHistory(): void {
    this.chatState.clearMessages();
  }

  onExportConversation(): void {
    const messages = this.chatState.messages();
    const dataStr = JSON.stringify(messages, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `conversation-${new Date().toISOString()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }

  // Update sources when messages change
  updateSources(): void {
    const messages = this.chatState.messages();
    const lastAssistantMessage = [...messages].reverse().find(m => m.role === 'assistant' && m.sources);
    if (lastAssistantMessage?.sources) {
      this.currentSources.set(lastAssistantMessage.sources);
    } else {
      this.currentSources.set([]);
    }
  }

  getVersions(): string[] {
    return this.collections().map(c => c.name);
  }
}

