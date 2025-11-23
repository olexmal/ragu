import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '@app/core/services/auth.service';
import { UiState } from '../../core/state/ui.state';

@Component({
  selector: 'app-header',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './header.component.html',
  styleUrl: './header.component.scss'
})
export class HeaderComponent {
  private authService = inject(AuthService);
  private uiState = inject(UiState);

  isAuthenticated = this.authService.isAuthenticated;
  sidebarOpen = this.uiState.sidebarOpen;

  toggleSidebar(): void {
    this.uiState.toggleSidebar();
  }

  logout(): void {
    this.authService.logout();
  }
}

