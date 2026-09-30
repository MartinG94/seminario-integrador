import { Component, OnInit, OnDestroy } from '@angular/core';
import { TribunalDataService, Expediente } from '../services/tribunal-data.service';
import { AuthService } from '../services/auth.service';
import { Subscription, interval } from 'rxjs';

@Component({
  selector: 'app-mis-expedientes',
  templateUrl: './mis-expedientes.component.html',
  styleUrls: ['./mis-expedientes.component.scss']
})
export class MisExpedientesComponent implements OnInit, OnDestroy {
  expedientes: Expediente[] = [];
  misExpedientes: Expediente[] = [];
  socioActual = '';
  saldoNeto = 0;

  // Ordenamiento de tabla
  columnaOrden = 'numero';
  ordenAscendente = true;

  // Modal T02/T03
  modalAbierto = false;
  expedienteSeleccionado: Expediente | null = null;
  tipoDescargo: 'T02_CERTIFICADO' | 'T03_EXTRAORDINARIO' = 'T02_CERTIFICADO';
  causalSeleccionada = 'Examen Académico Universitario en UTN FRC';
  nombreArchivo = '';
  relatoTexto = '';
  errorMensaje = '';

  // Temporizador dinámico para cuenta regresiva (CA3)
  private tickerSub: Subscription | null = null;
  ahoraMs: number = Date.now();

  private subs: Subscription[] = [];

  constructor(
    public dataService: TribunalDataService,
    private auth: AuthService
  ) {}

  ngOnInit(): void {
    const subPerfil = this.auth.perfil$.subscribe(perfil => {
      this.socioActual = perfil ? `${perfil.first_name} ${perfil.last_name}` : '';
      this.filtrarMisExpedientes();
    });
    this.subs.push(subPerfil);

    const subExp = this.dataService.expedientes$.subscribe(list => {
      this.expedientes = list;
      this.filtrarMisExpedientes();
    });
    this.subs.push(subExp);

    const subSocios = this.dataService.socios$.subscribe(socios => {
      const s = socios.find(soc => soc.nombre.toLowerCase() === this.socioActual.toLowerCase());
      this.saldoNeto = s ? s.saldo : 0;
    });
    this.subs.push(subSocios);

    // Actualizador dinámico del reloj cada segundo (evita memory leaks desuscribiéndose en ngOnDestroy)
    this.tickerSub = interval(1000).subscribe(() => {
      this.ahoraMs = Date.now();
    });
  }

  /** Los expedientes del socio en sesión; hoy provienen de datos simulados. */
  private filtrarMisExpedientes(): void {
    const nombre = this.socioActual.trim().toLowerCase();
    this.misExpedientes = nombre
      ? this.expedientes.filter(e => e.socio.toLowerCase() === nombre)
      : [];
  }

  ngOnDestroy(): void {
    if (this.tickerSub) {
      this.tickerSub.unsubscribe();
      this.tickerSub = null;
    }
    this.subs.forEach(s => s.unsubscribe());
  }

  /**
   * Determina si el expediente tiene su plazo vencido según el timestamp del límite.
   */
  esPlazoVencido(exp: Expediente): boolean {
    if (!exp.plazoLimiteAt) {
      return exp.horasRestantes <= 0;
    }
    const limiteMs = new Date(exp.plazoLimiteAt).getTime();
    return this.ahoraMs > limiteMs;
  }

  /**
   * Formato de fecha exacta de vencimiento: "Vence: Jueves 15/10/2026 - 18:00 hs".
   */
  getDeadlineLabel(exp: Expediente): string {
    if (!exp.plazoLimiteAt) {
      return 'Vencimiento no fijado';
    }
    const d = new Date(exp.plazoLimiteAt);
    if (isNaN(d.getTime())) {
      return 'Fecha inválida';
    }
    const diasSemana = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
    const diaNom = diasSemana[d.getDay()];
    const diaNum = String(d.getDate()).padStart(2, '0');
    const mesNum = String(d.getMonth() + 1).padStart(2, '0');
    const anio = d.getFullYear();
    const hora = String(d.getHours()).padStart(2, '0');
    const mins = String(d.getMinutes()).padStart(2, '0');

    return `Vence: ${diaNom} ${diaNum}/${mesNum}/${anio} - ${hora}:${mins} hs`;
  }

  /**
   * Formato dinámico del contador: "2d 04h 15m restantes" o "Plazo expirado".
   */
  getCountdownLabel(exp: Expediente): string {
    if (!exp.plazoLimiteAt) {
      return `${exp.horasRestantes}h restantes`;
    }
    const limiteMs = new Date(exp.plazoLimiteAt).getTime();
    const diffMs = limiteMs - this.ahoraMs;

    if (diffMs <= 0) {
      return 'Plazo expirado';
    }

    const segundosTotales = Math.floor(diffMs / 1000);
    const dias = Math.floor(segundosTotales / 86400);
    const horas = Math.floor((segundosTotales % 86400) / 3600);
    const minutos = Math.floor((segundosTotales % 3600) / 60);

    const horasStr = String(horas).padStart(2, '0');
    const minsStr = String(minutos).padStart(2, '0');

    if (dias > 0) {
      return `${dias}d ${horasStr}h ${minsStr}m restantes`;
    }
    const segs = segundosTotales % 60;
    const segsStr = String(segs).padStart(2, '0');
    return `${horasStr}h ${minsStr}m ${segsStr}s restantes`;
  }

  abrirModalDescargo(exp: Expediente): void {
    this.expedienteSeleccionado = exp;
    this.tipoDescargo = 'T02_CERTIFICADO';
    this.causalSeleccionada = 'Examen Académico Universitario en UTN FRC';
    this.nombreArchivo = '';
    this.relatoTexto = '';
    this.errorMensaje = '';
    this.modalAbierto = true;
  }

  cerrarModal(): void {
    this.modalAbierto = false;
    this.expedienteSeleccionado = null;
  }

  onFileSelected(event: any): void {
    const file = event.target.files[0];
    if (file) {
      this.nombreArchivo = file.name;
    }
  }

  enviarDescargo(): void {
    if (!this.expedienteSeleccionado) return;

    if (this.tipoDescargo === 'T02_CERTIFICADO') {
      if (!this.nombreArchivo) {
        this.errorMensaje = 'Es obligatorio adjuntar el comprobante o constancia digital (PDF, JPG o PNG).';
        return;
      }
    } else {
      if (!this.relatoTexto.trim()) {
        this.errorMensaje = 'Por favor expone detalladamente los hechos y motivos extraordinarios.';
        return;
      }
    }

    this.dataService.enviarDescargo(this.expedienteSeleccionado.id, this.tipoDescargo, {
      causal: this.causalSeleccionada,
      archivo: this.nombreArchivo,
      texto: this.relatoTexto || `Justificación formal presentada bajo causal de ${this.causalSeleccionada}.`
    });

    this.cerrarModal();
  }

  getEstadoLabel(estado: string): string {
    switch (estado) {
      case 'creado': return 'Expediente Creado';
      case 'justificando': return 'En período de justificaciones';
      case 'revision_resolucion': return 'En revisión y resolución';
      case 'pendiente_firma': return 'Pendiente de firma y envío';
      case 'emitido': return 'Expedientes ya emitidos';
      default: return estado;
    }
  }

  getEstadoBadgeClass(estado: string): string {
    switch (estado) {
      case 'creado': return 'badge-mat-primary';
      case 'justificando': return 'badge-mat-warning';
      case 'revision_resolucion': return 'badge-mat-info';
      case 'pendiente_firma': return 'badge-mat-rose';
      case 'emitido': return 'badge-mat-success';
      default: return 'badge-mat-primary';
    }
  }

  get expedientesOrdenados(): Expediente[] {
    const lista = [...this.misExpedientes];
    lista.sort((a, b) => {
      let valA = (a as any)[this.columnaOrden];
      let valB = (b as any)[this.columnaOrden];
      if (typeof valA === 'string') valA = valA.toLowerCase();
      if (typeof valB === 'string') valB = valB.toLowerCase();

      if (valA < valB) return this.ordenAscendente ? -1 : 1;
      if (valA > valB) return this.ordenAscendente ? 1 : -1;
      return 0;
    });
    return lista;
  }

  cambiarOrden(col: string): void {
    if (this.columnaOrden === col) {
      this.ordenAscendente = !this.ordenAscendente;
    } else {
      this.columnaOrden = col;
      this.ordenAscendente = true;
    }
  }

  getIconoOrden(col: string): string {
    if (this.columnaOrden !== col) return 'swap_vert';
    return this.ordenAscendente ? 'arrow_upward' : 'arrow_downward';
  }

  getColorClasePuntos(puntos: number): string {
    if (puntos < -9.0) {
      return 'puntos-rojo';
    }
    if (puntos < -7.0) {
      return 'puntos-amarillo';
    }
    if (puntos < 0) {
      return 'puntos-gris';
    }
    return 'puntos-verde';
  }

  getHeaderClassPuntos(puntos: number): string {
    if (puntos < -9.0) {
      return 'card-header-danger';
    }
    if (puntos < -7.0) {
      return 'card-header-warning';
    }
    if (puntos < 0) {
      return 'card-header-secondary';
    }
    return 'card-header-success';
  }
}
