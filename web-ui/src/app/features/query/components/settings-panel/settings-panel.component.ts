import { Component, Input, Output, EventEmitter, signal, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

export interface QuerySettings {
  version?: string;
  k: number;
  useSimple: boolean;
}

@Component({
  selector: 'app-settings-panel',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './settings-panel.component.html',
  styleUrl: './settings-panel.component.scss'
})
export class SettingsPanelComponent implements OnChanges {
  @Input() versions: string[] = [];
  @Input() settings: QuerySettings = { k: 3, useSimple: false };
  
  @Output() settingsChange = new EventEmitter<QuerySettings>();
  @Output() clearHistory = new EventEmitter<void>();
  @Output() exportConversation = new EventEmitter<void>();

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

  onVersionChange(): void {
    this.emitSettings();
  }

  onKChange(): void {
    this.emitSettings();
  }

  onSimpleToggle(): void {
    this.emitSettings();
  }

  private emitSettings(): void {
    this.settingsChange.emit({
      version: this.selectedVersion(),
      k: this.k(),
      useSimple: this.useSimple()
    });
  }

  onClearHistory(): void {
    if (confirm('Are you sure you want to clear the conversation history?')) {
      this.clearHistory.emit();
    }
  }

  onExportConversation(): void {
    this.exportConversation.emit();
  }
}

