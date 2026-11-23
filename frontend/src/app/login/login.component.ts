import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

import { AuthService } from '../services/auth.service';
import { NotificationService } from '../services/notification.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  formulario: FormGroup;
  enviando = false;
  reiniciandoDb = false;

  cuentasDemo = [
    { numero_socio: '74907', rol: 'SOCIO', nombre: 'Lucas Gastiaburu' },
    { numero_socio: '85194', rol: 'FISCALIZADORA', nombre: 'Lucas Guillén' },
    { numero_socio: '87414', rol: 'CD', nombre: 'Diego Sánchez' },
    { numero_socio: '408917', rol: 'TD', nombre: 'Nicolás Rosales' },
    { numero_socio: '403655', rol: 'ADMIN', nombre: 'Axel Villegas' },
  ];

  private volverA = '/mis-expedientes';

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private router: Router,
    private route: ActivatedRoute,
    private notifications: NotificationService
  ) {
    this.formulario = this.fb.group({
      identifier: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    const params = this.route.snapshot.queryParams;
    if (params['expirada'] === '1' && !this.auth.isAuthenticated()) {
      this.notifications.warning('Tu sesión expiró. Volvé a iniciar sesión para continuar.');
    }
    if (params['volverA']) {
      this.volverA = params['volverA'];
    }
    if (this.auth.isAuthenticated()) {
      this.router.navigateByUrl(this.volverA);
    }
  }

  seleccionarDemo(numeroSocio: string): void {
    this.formulario.patchValue({ identifier: numeroSocio });
    this.ingresar();
  }

  reiniciarBaseDatos(): void {
    if (this.reiniciandoDb) { return; }
    this.reiniciandoDb = true;
    this.auth.resetDemoDatabase().subscribe({
      next: res => {
        this.reiniciandoDb = false;
        this.notifications.success(
          res?.detail || 'Base de datos reiniciada con 2 expedientes de demostración.'
        );
      },
      error: (error: HttpErrorResponse) => {
        this.reiniciandoDb = false;
        const detail = error?.error?.detail;
        this.notifications.error(
          typeof detail === 'string' && detail.trim()
            ? detail
            : 'No pudimos reiniciar la base de datos. Intentá nuevamente en unos instantes.'
        );
      }
    });
  }

  ingresar(): void {
    if (this.enviando) { return; }
    if (this.formulario.invalid) {
      this.formulario.markAllAsTouched();
      this.notifications.error('Ingresá tu Número de Socio.');
      return;
    }

    this.enviando = true;

    const { identifier } = this.formulario.value;
    this.auth.login(identifier).subscribe({
      next: () => {
        this.enviando = false;
        this.router.navigateByUrl(this.volverA);
      },
      error: (error: HttpErrorResponse) => {
        this.enviando = false;
        this.notifications.error(
          error.status === 401
            ? 'Número de Socio no encontrado o cuenta no habilitada.'
            : 'No pudimos conectar con el servidor. Intentá nuevamente en unos instantes.');
      }
    });
  }
}
