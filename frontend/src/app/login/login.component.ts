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

  cuentasDemo = [
    { legajo: '74907', rol: 'SOCIO', nombre: 'Lucas Gastiaburu' },
    { legajo: '85194', rol: 'FISCALIZADORA', nombre: 'Lucas Guillén' },
    { legajo: '87414', rol: 'CD', nombre: 'Diego Sánchez' },
    { legajo: '408917', rol: 'TD', nombre: 'Nicolás Rosales' },
    { legajo: '403655', rol: 'ADMIN', nombre: 'Axel Villegas' },
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

  seleccionarDemo(legajo: string): void {
    this.formulario.patchValue({ identifier: legajo });
    this.ingresar();
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
