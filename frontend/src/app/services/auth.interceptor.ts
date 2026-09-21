import {
  HttpErrorResponse,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest
} from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { AuthService } from './auth.service';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  constructor(private auth: AuthService, private router: Router) {}

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    const token = this.auth.getToken();
    const autorizada = token
      ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
      : request;

    return next.handle(autorizada).pipe(
      catchError((error: HttpErrorResponse) => {
        // 401 sobre una sesión que el navegador creía válida significa token
        // vencido o revocado: se limpia y se vuelve al login.
        if (error.status === 401 && this.auth.isAuthenticated()) {
          this.auth.logout();
          this.router.navigate(['/login'], { queryParams: { expirada: 1 } });
        }
        return throwError(() => error);
      })
    );
  }
}
