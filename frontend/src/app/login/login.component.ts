import { HttpErrorResponse } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';

import { AuthService } from '../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent implements OnInit {
  formulario: FormGroup;
  enviando = false;
  mensajeError = '';
  sesionExpirada = false;

  private volverA = '/mis-expedientes';

  constructor(
    private fb: FormBuilder,
    private auth: AuthService,
    private router: Router,
    private route: ActivatedRoute
  ) {
    this.formulario = this.fb.group({
      identifier: ['', Validators.required],
      password: ['', Validators.required]
    });
  }

  ngOnInit(): void {
    const params = this.route.snapshot.queryParams;
    this.sesionExpirada = params['expirada'] === '1';
    if (params['volverA']) {
      this.volverA = params['volverA'];
    }
    if (this.auth.isAuthenticated()) {
      this.router.navigateByUrl(this.volverA);
    }
  }

  ingresar(): void {
    if (this.formulario.invalid || this.enviando) {
      this.formulario.markAllAsTouched();
      return;
    }

    this.enviando = true;
    this.mensajeError = '';
    this.sesionExpirada = false;

    const { identifier, password } = this.formulario.value;
    this.auth.login(identifier, password).subscribe({
      next: () => {
        this.enviando = false;
        this.router.navigateByUrl(this.volverA);
      },
      error: (error: HttpErrorResponse) => {
        this.enviando = false;
        // El backend no informa si el legajo existe ni cuál dato falló; la
        // interfaz replica ese mensaje genérico sin agregar detalles.
        this.mensajeError =
          error.status === 401
            ? 'Credenciales inválidas. Verificá tu legajo y tu contraseña.'
            : 'No pudimos conectar con el servidor. Intentá nuevamente en unos instantes.';
      }
    });
  }
}
