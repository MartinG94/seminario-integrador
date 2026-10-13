import {
  HttpErrorResponse,
  HttpEvent,
  HttpHandler,
  HttpInterceptor,
  HttpRequest
} from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Router } from '@angular/router';
import { EMPTY, Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';

import { AuthService } from './auth.service';
import { environment } from '../../environments/environment';

@Injectable()
export class AuthInterceptor implements HttpInterceptor {
  private anonymousRecoveryStarted = false;
  constructor(private auth: AuthService, private router: Router) {}

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    const token = this.auth.getToken();
    const apiRequest = request.url.startsWith(`${environment.apiUrl}/`);
    const isLogin = apiRequest && /\/auth\/login\/?(?:\?|$)/.test(request.url);
    const protectedApi = apiRequest && !isLogin;
    if (protectedApi && token) { this.anonymousRecoveryStarted = false; }
    const autorizada = token && protectedApi
      ? request.clone({ setHeaders: { Authorization: `Bearer ${token}` } })
      : request;

    return next.handle(autorizada).pipe(
      catchError((error: HttpErrorResponse) => {
        if (error.status === 401 && protectedApi) {
          if (this.auth.getToken() === token && (token || !this.anonymousRecoveryStarted)) {
            this.anonymousRecoveryStarted = true;
            this.auth.logout();
            this.router.navigate(['/login'], { queryParams: { expirada: 1 } });
          }
          // La pantalla anterior no debe emitir otro aviso ni cerrar una sesión nueva.
          return EMPTY;
        }
        return throwError(() => error);
      })
    );
  }
}
