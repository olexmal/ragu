import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class UiState {
  private notificationSignal = signal<{ message: string; type: 'success' | 'error' | 'info' | 'warning' } | null>(null);
  private sidebarOpenSignal = signal<boolean>(false);
  private sidebarCollapsedSignal = signal<boolean>(false);

  readonly notification = this.notificationSignal.asReadonly();
  readonly sidebarOpen = this.sidebarOpenSignal.asReadonly();
  readonly sidebarCollapsed = this.sidebarCollapsedSignal.asReadonly();

  showNotification(message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info'): void {
    this.notificationSignal.set({ message, type });
    setTimeout(() => this.clearNotification(), 5000);
  }

  clearNotification(): void {
    this.notificationSignal.set(null);
  }

  toggleSidebar(): void {
    this.sidebarOpenSignal.update(open => !open);
  }

  setSidebarOpen(open: boolean): void {
    this.sidebarOpenSignal.set(open);
  }

  toggleSidebarCollapsed(): void {
    this.sidebarCollapsedSignal.update(collapsed => !collapsed);
  }

  setSidebarCollapsed(collapsed: boolean): void {
    this.sidebarCollapsedSignal.set(collapsed);
  }
}

