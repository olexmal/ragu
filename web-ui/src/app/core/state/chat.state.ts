import { Injectable, signal } from '@angular/core';
import { SourceDocument } from '../models/query.models';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  queryParams?: {
    version?: string;
    k?: number;
    useSimple?: boolean;
  };
  sources?: SourceDocument[];
  error?: string;
  loading?: boolean;
  edited?: boolean;
}

export interface Conversation {
  id: string;
  name: string;
  messages: ChatMessage[];
  createdAt: Date;
  updatedAt: Date;
}

@Injectable({
  providedIn: 'root'
})
export class ChatState {
  private messagesSignal = signal<ChatMessage[]>([]);
  private currentConversationIdSignal = signal<string | null>(null);
  private conversationsSignal = signal<Conversation[]>([]);
  private loadingSignal = signal<boolean>(false);

  readonly messages = this.messagesSignal.asReadonly();
  readonly currentConversationId = this.currentConversationIdSignal.asReadonly();
  readonly conversations = this.conversationsSignal.asReadonly();
  readonly loading = this.loadingSignal.asReadonly();

  addMessage(message: ChatMessage): void {
    this.messagesSignal.update(messages => [...messages, message]);
  }

  updateMessage(id: string, updates: Partial<ChatMessage>): void {
    this.messagesSignal.update(messages =>
      messages.map(msg => msg.id === id ? { ...msg, ...updates } : msg)
    );
  }

  removeMessage(id: string): void {
    this.messagesSignal.update(messages => messages.filter(msg => msg.id !== id));
  }

  setMessages(messages: ChatMessage[]): void {
    this.messagesSignal.set(messages);
  }

  clearMessages(): void {
    this.messagesSignal.set([]);
  }

  setLoading(loading: boolean): void {
    this.loadingSignal.set(loading);
  }

  setCurrentConversation(id: string | null): void {
    this.currentConversationIdSignal.set(id);
  }

  addConversation(conversation: Conversation): void {
    this.conversationsSignal.update(conversations => [...conversations, conversation]);
  }

  removeConversation(id: string): void {
    this.conversationsSignal.update(conversations => conversations.filter(conv => conv.id !== id));
  }

  updateConversation(id: string, updates: Partial<Conversation>): void {
    this.conversationsSignal.update(conversations =>
      conversations.map(conv => conv.id === id ? { ...conv, ...updates } : conv)
    );
  }

  setConversations(conversations: Conversation[]): void {
    this.conversationsSignal.set(conversations);
  }
}

