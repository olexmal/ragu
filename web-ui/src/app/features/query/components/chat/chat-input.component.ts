import { Component, EventEmitter, Input, Output, signal, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { QuerySettings } from '../settings-panel/settings-panel.component';

export interface ChatInputOptions {
  version?: string;
  k?: number;
  useSimple?: boolean;
}

@Component({
  selector: 'app-chat-input',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat-input.component.html',
  styleUrl: './chat-input.component.scss'
})
export class ChatInputComponent implements OnChanges {
  @Input() versions: string[] = [];
  @Input() disabled = false;
  @Input() loading = false;
  @Input() settings: QuerySettings = { k: 3, useSimple: false };
  
  @Output() send = new EventEmitter<{ message: string; options: ChatInputOptions }>();

  message = signal<string>('');
  selectedVersion = signal<string | undefined>(undefined);
  k = signal<number>(3);
  useSimple = signal<boolean>(false);

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['settings'] && this.settings) {
      this.selectedVersion.set(this.settings.version);
      this.k.set(this.settings.k);
      this.useSimple.set(this.settings.useSimple);
    }
  }

  onSend(): void {
    const text = this.message().trim();
    if (!text || this.disabled || this.loading) {
      return;
    }

    this.send.emit({
      message: text,
      options: {
        version: this.selectedVersion(),
        k: this.k(),
        useSimple: this.useSimple()
      }
    });

    this.message.set('');
  }

  onKeyDown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.onSend();
    }
  }
}

