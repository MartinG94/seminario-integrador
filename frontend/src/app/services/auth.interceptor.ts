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
        if (error.status === 401 && token) {
          if (this.auth.getToken() === token) {
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
