import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { Observable } from 'rxjs';
import { AuthService } from '@app/core/services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent {
  private authService: AuthService = inject(AuthService);
  private router: Router = inject(Router);
  private route: ActivatedRoute = inject(ActivatedRoute);

  apiKey = '';
  rememberMe = false;
  error = '';

  onSubmit(): void {
    if (!this.apiKey.trim()) {
      this.error = 'API key is required';
      return;
    }

    this.error = '';
    const loginObservable: Observable<boolean> = this.authService.login(this.apiKey, this.rememberMe);
    loginObservable.subscribe({
      next: (success: boolean) => {
        if (success) {
          const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/admin';
          this.router.navigate([returnUrl]);
        }
      },
      error: (error: any) => {
        this.error = error.message || 'Login failed';
      }
    });
  }
}

