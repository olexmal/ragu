import { Component, inject, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { AuthService } from '@app/core/services/auth.service';
import { UiState } from '../../core/state/ui.state';

@Component({
  selector: 'app-navigation',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive],
  templateUrl: './navigation.component.html',
  styleUrl: './navigation.component.scss'
})
export class NavigationComponent {
  private authService = inject(AuthService);
  uiState = inject(UiState);

  isAuthenticated = this.authService.isAuthenticated;
  sidebarOpen = this.uiState.sidebarOpen;

  userMenuItems = [
    { path: '/query', label: 'Query', icon: 'search' },
    { path: '/history', label: 'History', icon: 'clock' },
  ];

  adminMenuItems = [
    { path: '/admin', label: 'Dashboard', icon: 'dashboard' },
    { path: '/admin/upload', label: 'Upload Documents', icon: 'upload' },
    { path: '/admin/collections', label: 'Collections', icon: 'folder' },
    { path: '/admin/monitoring', label: 'Monitoring', icon: 'chart' },
    { path: '/admin/settings', label: 'Settings', icon: 'settings' },
  ];

  get menuItems() {
    return this.isAuthenticated() 
      ? [...this.userMenuItems, ...this.adminMenuItems]
      : this.userMenuItems;
  }
}

