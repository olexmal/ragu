import { Component, inject, OnInit, signal, ViewChild, ElementRef, AfterViewChecked, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ChatMessageComponent } from './chat-message.component';
import { ChatInputComponent } from './chat-input.component';
import { ChatState, ChatMessage } from '../../../../core/state/chat.state';
import { QueryService } from '../../../../core/services/query.service';
import { CollectionService } from '../../../../core/services/collection.service';
import { QueryRequest, QueryResponse, SourceDocument } from '../../../../core/models/query.models';
import { QuerySettings } from '../settings-panel/settings-panel.component';
import { finalize } from 'rxjs/operators';

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, ChatMessageComponent, ChatInputComponent],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.scss'
})
export class ChatComponent implements OnInit, AfterViewChecked {
  private chatState = inject(ChatState);
  private queryService = inject(QueryService);
  private collectionService = inject(CollectionService);

  @Input() settings: QuerySettings = { k: 3, useSimple: false };
  @ViewChild('messagesContainer') messagesContainer!: ElementRef<HTMLDivElement>;

  messages = this.chatState.messages;
  loading = this.chatState.loading;
  collections = signal<any[]>([]);
  private shouldScroll = false;

  ngOnInit(): void {
    this.loadCollections();
  }

  ngAfterViewChecked(): void {
    if (this.shouldScroll) {
      this.scrollToBottom();
      this.shouldScroll = false;
    }
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

  onSendMessage(event: { message: string; options: { version?: string; k?: number; useSimple?: boolean } }): void {
    const userMessage: ChatMessage = {
      id: this.generateId(),
      role: 'user',
      content: event.message,
      timestamp: new Date(),
      queryParams: event.options
    };

    this.chatState.addMessage(userMessage);
    this.shouldScroll = true;

    this.sendQuery(userMessage.id, event.message, event.options);
  }

  onMessageEdited(event: { id: string; content: string }): void {
    const message = this.messages().find(m => m.id === event.id);
    if (!message || message.role !== 'user') {
      return;
    }

    // Update the message content
    this.chatState.updateMessage(event.id, {
      content: event.content,
      edited: true
    });

    // Remove the assistant response if it exists (next message)
    const messageIndex = this.messages().findIndex(m => m.id === event.id);
    const nextMessage = this.messages()[messageIndex + 1];
    if (nextMessage && nextMessage.role === 'assistant') {
      this.chatState.removeMessage(nextMessage.id);
    }

    // Re-query with edited message
    this.sendQuery(event.id, event.content, message.queryParams || {});
  }

  onMessageDeleted(messageId: string): void {
    this.chatState.removeMessage(messageId);
  }

  onMessageRegenerated(messageId: string): void {
    const message = this.messages().find(m => m.id === messageId);
    if (!message || message.role !== 'assistant') {
      return;
    }

    // Find the previous user message
    const messageIndex = this.messages().findIndex(m => m.id === messageId);
    const userMessage = messageIndex > 0 ? this.messages()[messageIndex - 1] : null;
    
    if (userMessage && userMessage.role === 'user') {
      // Remove current assistant message
      this.chatState.removeMessage(messageId);
      
      // Re-query with the user message
      this.sendQuery(userMessage.id, userMessage.content, userMessage.queryParams || {});
    }
  }

  private sendQuery(userMessageId: string, query: string, options: { version?: string; k?: number; useSimple?: boolean }): void {
    // Create assistant message placeholder
    const assistantMessage: ChatMessage = {
      id: this.generateId(),
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      loading: true
    };

    this.chatState.addMessage(assistantMessage);
    this.chatState.setLoading(true);
    this.shouldScroll = true;

    // Make query request
    const request: QueryRequest = {
      query,
      version: options.version,
      k: options.k,
      simple: options.useSimple
    };

    this.queryService.query(request).pipe(
      finalize(() => {
        this.chatState.setLoading(false);
      })
    ).subscribe({
      next: (response: QueryResponse) => {
        this.chatState.updateMessage(assistantMessage.id, {
          content: response.answer,
          sources: response.sources,
          loading: false
        });
        this.shouldScroll = true;
        // Emit sources update event if needed
      },
      error: (error) => {
        this.chatState.updateMessage(assistantMessage.id, {
          content: '',
          error: error.message || 'Query failed',
          loading: false
        });
        this.shouldScroll = true;
      }
    });
  }

  onClear(): void {
    this.chatState.clearMessages();
  }

  scrollToBottom(): void {
    if (this.messagesContainer) {
      const element = this.messagesContainer.nativeElement;
      element.scrollTop = element.scrollHeight;
    }
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  getVersions(): string[] {
    return this.collections().map(c => c.name);
  }
}

