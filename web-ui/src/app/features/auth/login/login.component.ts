import { Component, inject, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { Observable } from 'rxjs';
import { AuthService } from '@app/core/services/auth.service';
import { SystemNameService } from '@app/core/services/system-name.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './login.component.html',
  styleUrl: './login.component.scss'
})
export class LoginComponent implements OnInit {
  private authService: AuthService = inject(AuthService);
  private router: Router = inject(Router);
  private route: ActivatedRoute = inject(ActivatedRoute);
  systemNameService = inject(SystemNameService);

  username = '';
  password = '';
  rememberMe = false;
  error = '';
  authEnabled = this.authService.authEnabled;

  ngOnInit(): void {
    // If auth is disabled, automatically proceed
    if (!this.authService.authEnabled()) {
      const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/admin';
      this.router.navigate([returnUrl]);
    }
  }

  onSubmit(): void {
    // If auth is disabled, automatically proceed
    if (!this.authService.authEnabled()) {
      const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/admin';
      this.router.navigate([returnUrl]);
      return;
    }

    // Validate inputs
    if (!this.username.trim()) {
      this.error = 'Username is required';
      return;
    }

    if (!this.password.trim()) {
      this.error = 'Password is required';
      return;
    }

    this.error = '';
    const loginObservable: Observable<boolean> = this.authService.login(this.username, this.password, this.rememberMe);
    loginObservable.subscribe({
      next: (success: boolean) => {
        if (success) {
          const returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/admin';
          this.router.navigate([returnUrl]);
        }
      },
      error: (error: any) => {
        console.error('Login error:', error);
        
        // Handle HTTP error response - check multiple possible error structures
        if (error?.error?.message) {
          // Backend error response: {error: "Invalid credentials", message: "..."}
          this.error = error.error.message;
        } else if (error?.error?.error) {
          // Alternative error structure
          this.error = error.error.error;
        } else if (error?.message) {
          // Error object with message
          this.error = error.message;
        } else if (typeof error === 'string') {
          // String error
          this.error = error;
        } else {
          // Fallback
          this.error = 'Login failed. Please check your credentials.';
        }
      }
    });
  }
}

