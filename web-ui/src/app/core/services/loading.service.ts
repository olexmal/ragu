import { Injectable, signal } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class LoadingService {
  isLoading = signal<boolean>(false);

  setLoading(loading: boolean): void {
    this.isLoading.set(loading);
  }
}

