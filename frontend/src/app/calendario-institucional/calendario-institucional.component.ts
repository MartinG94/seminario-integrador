import { Component, OnInit } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import {
  CalendarioApiService,
  CalendarioVersionDto,
  CalcularPlazoRequest,
  CalcularPlazoResponse,
  FeriadoExcepcionDto,
  TipoFeriado
} from '../services/calendario-api.service';
import { AuthService } from '../services/auth.service';
import { NuevaVersionDialogComponent } from './nueva-version-dialog/nueva-version-dialog.component';

@Component({
  selector: 'app-calendario-institucional',
  templateUrl: './calendario-institucional.component.html',
  styleUrls: ['./calendario-institucional.component.scss']
})
export class CalendarioInstitucionalComponent implements OnInit {
  versiones: CalendarioVersionDto[] = [];
  versionSeleccionadaId: number | null = null;
  versionDetalle: CalendarioVersionDto | null = null;
  feriadosFiltrados: FeriadoExcepcionDto[] = [];

  cargando = false;
  errorMensaje = '';
  exitoMensaje = '';

  // Filtros
  filtroTipo = 'TODOS';
  busqueda = '';

  // Simulador de plazos
  simuladorFechaInicio = '';
  simuladorDiasHabiles = 5;
  simuladorCalculando = false;
  simuladorResultado: CalcularPlazoResponse | null = null;
  simuladorError = '';

  // Formulario rápido de excepción
  mostrandoFormFeriado = false;
  nuevoFeriadoFecha = '';
  nuevoFeriadoDesc = '';
  nuevoFeriadoTipo: TipoFeriado = 'INSTITUCIONAL';
  nuevoFeriadoEsLaborable = false;

  get versionActiva(): CalendarioVersionDto | null {
    return this.versiones.find(v => v.activa) || null;
  }

  get puedeGestionar(): boolean {
    return this.auth.tieneRol('ADMIN', 'CD', 'TD');
  }

  constructor(
    private calendarioApi: CalendarioApiService,
    private dialog: MatDialog,
    public auth: AuthService
  ) {}

  ngOnInit(): void {
    this.initSimuladorFecha();
    this.cargarVersiones();
  }

  private initSimuladorFecha(): void {
    const now = new Date();
    // Formato local YYYY-MM-DDTHH:mm
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    this.simuladorFechaInicio = `${year}-${month}-${day}T${hours}:${minutes}`;
  }

  cargarVersiones(): void {
    this.cargando = true;
    this.errorMensaje = '';
    this.calendarioApi.getVersiones().subscribe({
      next: versiones => {
        this.versiones = versiones;
        this.cargando = false;
        if (versiones.length > 0) {
          const activa = versiones.find(v => v.activa) || versiones[0];
          this.seleccionarVersion(activa.id);
        }
      },
      error: err => {
        this.cargando = false;
        this.errorMensaje = 'Error al cargar las versiones del calendario institucional.';
      }
    });
  }

  seleccionarVersion(id: number): void {
    this.versionSeleccionadaId = id;
    this.cargando = true;
    this.calendarioApi.getVersionDetail(id).subscribe({
      next: detalle => {
        this.versionDetalle = detalle;
        this.cargando = false;
        this.aplicarFiltros();
      },
      error: err => {
        this.cargando = false;
        this.errorMensaje = 'Error al obtener los detalles y feriados de la versión seleccionada.';
      }
    });
  }

  aplicarFiltros(): void {
    if (!this.versionDetalle || !this.versionDetalle.feriados) {
      this.feriadosFiltrados = [];
      return;
    }

    let items = [...this.versionDetalle.feriados];

    if (this.filtroTipo !== 'TODOS') {
      items = items.filter(f => f.tipo === this.filtroTipo);
    }

    if (this.busqueda.trim()) {
      const q = this.busqueda.trim().toLowerCase();
      items = items.filter(f =>
        f.descripcion.toLowerCase().includes(q) ||
        f.fecha.includes(q) ||
        (f.tipo_display && f.tipo_display.toLowerCase().includes(q))
      );
    }

    this.feriadosFiltrados = items;
  }

  abrirDialogoNuevaVersion(): void {
    const ref = this.dialog.open(NuevaVersionDialogComponent, {
      width: '650px',
      data: {
        versionesDisponibles: this.versiones,
        versionActivaActual: this.versionActiva
      }
    });

    ref.afterClosed().subscribe(resultado => {
      if (resultado) {
        this.cargando = true;
        this.errorMensaje = '';
        this.calendarioApi.createVersion(resultado).subscribe({
          next: nueva => {
            this.exitoMensaje = `Versión v${nueva.version} (${nueva.nombre}) publicada con éxito.`;
            this.cargarVersiones();
          },
          error: err => {
            this.cargando = false;
            this.errorMensaje = err.error?.detail || 'Error al publicar la nueva versión de calendario.';
          }
        });
      }
    });
  }

  toggleFormFeriado(): void {
    this.mostrandoFormFeriado = !this.mostrandoFormFeriado;
    this.nuevoFeriadoFecha = '';
    this.nuevoFeriadoDesc = '';
  }

  guardarFeriado(): void {
    if (!this.nuevoFeriadoFecha || !this.nuevoFeriadoDesc.trim() || !this.versionSeleccionadaId) {
      return;
    }

    this.errorMensaje = '';
    this.exitoMensaje = '';

    const payload = {
      version_id: this.versionSeleccionadaId,
      fecha: this.nuevoFeriadoFecha,
      descripcion: this.nuevoFeriadoDesc.trim(),
      tipo: this.nuevoFeriadoTipo,
      es_laborable: this.nuevoFeriadoEsLaborable
    };

    this.calendarioApi.addFeriado(payload).subscribe({
      next: nuevo => {
        this.exitoMensaje = `Feriado/Excepción agregado exitosamente: ${nuevo.fecha} (${nuevo.descripcion}).`;
        this.mostrandoFormFeriado = false;
        this.nuevoFeriadoFecha = '';
        this.nuevoFeriadoDesc = '';
        this.seleccionarVersion(this.versionSeleccionadaId!);
        this.cargarVersiones();
      },
      error: err => {
        const errObj = err.error;
        let msg = 'Error al registrar feriado.';
        if (typeof errObj === 'string') {
          msg = errObj;
        } else if (errObj?.detail) {
          msg = errObj.detail;
        } else if (errObj) {
          const firstKey = Object.keys(errObj)[0];
          const val = errObj[firstKey];
          msg = Array.isArray(val) ? val[0] : (typeof val === 'string' ? val : msg);
        }
        this.errorMensaje = msg;
      }
    });
  }

  calcularPlazoSimulado(): void {
    this.simuladorError = '';
    this.simuladorResultado = null;

    if (!this.simuladorFechaInicio) {
      this.simuladorError = 'Debe indicar la fecha y hora de inicio del plazo.';
      return;
    }

    if (!this.simuladorDiasHabiles || this.simuladorDiasHabiles < 1) {
      this.simuladorError = 'La cantidad de días hábiles debe ser al menos 1.';
      return;
    }

    // Convertir fecha-hora local a ISO string con zona horaria
    const fechaObj = new Date(this.simuladorFechaInicio);
    const isoString = fechaObj.toISOString();

    const request: CalcularPlazoRequest = {
      start_at: isoString,
      business_days: this.simuladorDiasHabiles,
      version_id: this.versionSeleccionadaId
    };

    this.simuladorCalculando = true;
    this.calendarioApi.calcularPlazo(request).subscribe({
      next: res => {
        this.simuladorCalculando = false;
        this.simuladorResultado = res;
      },
      error: err => {
        this.simuladorCalculando = false;
        this.simuladorError = 'Error al calcular el plazo perentorio con el servidor.';
      }
    });
  }
}
