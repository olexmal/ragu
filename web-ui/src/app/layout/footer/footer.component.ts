import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { SystemNameService } from '../../core/services/system-name.service';

@Component({
  selector: 'app-footer',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './footer.component.html',
  styleUrl: './footer.component.scss'
})
export class FooterComponent {
  systemNameService = inject(SystemNameService);
  currentYear = new Date().getFullYear();
}

