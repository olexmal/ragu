import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '@app/core/services/auth.service';
import { UiState } from '../../core/state/ui.state';
import { SystemNameService } from '../../core/services/system-name.service';

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
  systemNameService = inject(SystemNameService);

  isAuthenticated = this.authService.isAuthenticated;
  sidebarOpen = this.uiState.sidebarOpen;

  toggleSidebar(): void {
    this.uiState.toggleSidebar();
  }

  logout(): void {
    this.authService.logout().subscribe({
      next: () => {
        // Redirect to login page after logout
        window.location.href = '/login';
      },
      error: () => {
        // Even if logout fails, redirect to login
        window.location.href = '/login';
      }
    });
  }
}

