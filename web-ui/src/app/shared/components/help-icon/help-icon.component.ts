import { Component, Input } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-help-icon',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './help-icon.component.html',
  styleUrl: './help-icon.component.scss'
})
export class HelpIconComponent {
  @Input() helpText: string = '';
  private static idCounter = 0;
  uniqueId = `help-${HelpIconComponent.idCounter++}`;
}

