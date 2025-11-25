import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./layout/main-layout/main-layout.component').then(m => m.MainLayoutComponent),
    children: [
      { path: '', redirectTo: 'query', pathMatch: 'full' },
      { 
        path: 'query', 
        loadComponent: () => import('./features/query/query.component').then(m => m.QueryComponent)
      },
      { 
        path: 'history', 
        loadComponent: () => import('./features/query/components/query-history/query-history.component').then(m => m.QueryHistoryComponent)
      },
      {
        path: 'admin',
        canActivate: [authGuard],
        children: [
          { 
            path: '', 
            loadComponent: () => import('./features/admin/dashboard/dashboard.component').then(m => m.DashboardComponent)
          },
          { 
            path: 'import', 
            loadComponent: () => import('./features/admin/import/import.component').then(m => m.ImportComponent)
          },
          { 
            path: 'collections', 
            loadComponent: () => import('./features/admin/collections/collections.component').then(m => m.CollectionsComponent)
          },
          { 
            path: 'monitoring', 
            loadComponent: () => import('./features/admin/monitoring/monitoring.component').then(m => m.MonitoringComponent)
          },
          { 
            path: 'settings', 
            loadComponent: () => import('./features/admin/settings/settings.component').then(m => m.SettingsComponent)
          },
        ]
      },
    ]
  },
  { 
    path: 'login', 
    loadComponent: () => import('./features/auth/login/login.component').then(m => m.LoginComponent)
  },
  { path: '**', redirectTo: '' }
];
