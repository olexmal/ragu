import { Component, Input, signal, EventEmitter, Output } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatMessage } from '../../../../core/state/chat.state';

@Component({
  selector: 'app-chat-message',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-message.component.html',
  styleUrl: './chat-message.component.scss'
})
export class ChatMessageComponent {
  @Input() message!: ChatMessage;

  isEditing = signal<boolean>(false);
  editedContent = signal<string>('');
  showActions = signal<boolean>(false);
  isFavorited = signal<boolean>(false);

  @Output() messageEdited = new EventEmitter<{ id: string; content: string }>();
  @Output() messageDeleted = new EventEmitter<string>();
  @Output() messageRegenerated = new EventEmitter<string>();

  startEdit(): void {
    this.editedContent.set(this.message.content);
    this.isEditing.set(true);
  }

  cancelEdit(): void {
    this.isEditing.set(false);
    this.editedContent.set('');
  }

  saveEdit(): void {
    if (this.editedContent().trim()) {
      this.messageEdited.emit({
        id: this.message.id,
        content: this.editedContent()
      });
      this.isEditing.set(false);
    }
  }

  deleteMessage(): void {
    if (confirm('Are you sure you want to delete this message?')) {
      this.messageDeleted.emit(this.message.id);
    }
  }

  regenerateResponse(): void {
    this.messageRegenerated.emit(this.message.id);
  }

  toggleFavorite(): void {
    this.isFavorited.update(fav => !fav);
  }

  formatTimestamp(date: Date): string {
    const now = new Date();
    const messageDate = new Date(date);
    const diffMs = now.getTime() - messageDate.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) {
      return 'Just now';
    } else if (diffMins < 60) {
      return `${diffMins}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return messageDate.toLocaleDateString();
    }
  }

  copyToClipboard(text: string): void {
    navigator.clipboard.writeText(text).then(() => {
      // Could show toast notification
    });
  }
}

