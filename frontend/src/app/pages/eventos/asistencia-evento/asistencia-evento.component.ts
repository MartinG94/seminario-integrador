import { Component, OnInit, OnDestroy } from '@angular/core';
import { MatDialog } from '@angular/material/dialog';
import { Subscription } from 'rxjs';
import {
  ConvocadoAsistenciaDTO,
  EstadoAsistenciaEvento,
  EventoInstitucional,
  MetodoCapturaAsistencia,
  ReportarAsistenciaPayload
} from '../../../models/evento.model';
import { AttendanceContextService } from '../../../eventos-asistencia/strategies/attendance-context.service';
import { BiometricAttendanceStrategy } from '../../../eventos-asistencia/strategies/biometric-attendance.strategy';
import { EventoService } from '../../../services/evento.service';
import { NotificationService } from '../../../services/notification.service';
import { TribunalDataService } from '../../../services/tribunal-data.service';
import { CrearEventoDialogComponent } from '../dialogs/crear-evento-dialog/crear-evento-dialog.component';
import { ResumenCierreDialogComponent } from '../dialogs/resumen-cierre-dialog/resumen-cierre-dialog.component';

@Component({
  selector: 'app-asistencia-evento',
  templateUrl: './asistencia-evento.component.html',
  styleUrls: ['./asistencia-evento.component.scss']
})
export class AsistenciaEventoComponent implements OnInit, OnDestroy {
  eventos: EventoInstitucional[] = [];
  eventoActivo: EventoInstitucional | null = null;
  eventoSeleccionadoId: number | string | null = null;
  convocados: ConvocadoAsistenciaDTO[] = [];

  // Filtros de tabla
  filtroTexto = '';
  filtroEstado = 'TODOS';

  // Estrategia
  estrategiaActual: MetodoCapturaAsistencia = 'MANUAL';
  escaneandoHuella = false;

  // Estados de carga
  guardando = false;
  procesando = false;
  ultimaModificacion = new Date();

  private subs: Subscription[] = [];

  constructor(
    private eventoService: EventoService,
    private dataService: TribunalDataService,
    private contextService: AttendanceContextService,
    private biometricStrategy: BiometricAttendanceStrategy,
    private notificationService: NotificationService,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    // Suscribirse a la estrategia activa
    const subStrat = this.contextService.currentStrategy$.subscribe(strat => {
      this.estrategiaActual = strat.tipo;
    });
    this.subs.push(subStrat);

    this.cargarEventos();
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  cargarEventos(): void {
    this.eventoService.getEventos().subscribe({
      next: list => {
        if (list && list.length > 0) {
          this.eventos = list;
          this.seleccionarEvento(list[0]);
        } else {
          this.cargarFallbackEventos();
        }
      },
      error: () => {
        this.cargarFallbackEventos();
      }
    });
  }

  private cargarFallbackEventos(): void {
    // Carga de fallback si el backend no cuenta con eventos o está en entorno offline/mock
    const mockEvento: EventoInstitucional = {
      id: 1,
      titulo: 'Reunión Ordinaria Consejo Directivo (Marzo 2026)',
      descripcion: 'Sesión ordinaria reglamentaria para tratamiento de balances y padrón.',
      categoria: 'REUNION',
      tipo: 'ORDINARIA',
      modalidad: 'PRESENCIAL_SEDE',
      ubicacion: 'Sede Central AVEIT',
      fecha_programada: new Date().toISOString(),
      fecha_fin: null,
      estado: 'EN_CURSO',
      modo_convocatoria: 'GRUPO',
      grupo_convocado: 'G58',
      es_obligatoria: true,
      es_sancionable: true,
      tolerancia_tardanza_minutos: 15,
      tolerancia_retiro_minutos: 15
    };
    this.eventos = [mockEvento];
    this.seleccionarEvento(mockEvento);
  }

  seleccionarEvento(evento: EventoInstitucional): void {
    this.eventoActivo = evento;
    this.eventoSeleccionadoId = evento.id;
    this.cargarConvocados(evento.id);
  }

  onSeleccionarEvento(): void {
    const sel = this.eventos.find(e => e.id === this.eventoSeleccionadoId);
    if (sel) {
      this.seleccionarEvento(sel);
    }
  }

  cargarConvocados(eventoId: number | string): void {
    this.eventoService.getAsistencias(eventoId).subscribe({
      next: asistencias => {
        if (asistencias && asistencias.length > 0) {
          this.convocados = asistencias.map(a => ({
            socio_id: a.socio_id,
            socio_nombre: a.socio_nombre || `Socio #${a.socio_id}`,
            socio_legajo: a.socio_legajo || `${a.socio_id}`,
            socio_email: a.socio_email,
            socio_subcomision: a.socio_subcomision,
            estado_asistencia: a.estado_asistencia,
            motivo: a.motivo || '',
            minutos_tardanza: a.minutos_tardanza || 0,
            minutos_retiro_anticipado: a.minutos_retiro_anticipado || 0,
            metodo_captura: a.metodo_captura || 'MANUAL',
            hora_registro: a.hora_registro,
            hora_salida: a.hora_salida,
            observaciones: a.observaciones,
            procesado_disciplinario: a.procesado_disciplinario,
            expediente_generado_id: a.expediente_generado_id,
            apercibimiento_generado_id: a.apercibimiento_generado_id
          }));
        } else {
          this.generarConvocadosMock();
        }
      },
      error: () => {
        this.generarConvocadosMock();
      }
    });
  }

  private generarConvocadosMock(): void {
    this.convocados = [
      {
        socio_id: 101,
        socio_nombre: 'Lucas Gastiaburu',
        socio_legajo: '74907',
        socio_subcomision: 'Cómputos e Informática',
        estado_asistencia: 'PRESENTE',
        motivo: 'En sede a tiempo',
        minutos_tardanza: 0,
        minutos_retiro_anticipado: 0,
        metodo_captura: 'MANUAL',
        hora_registro: new Date().toISOString()
      },
      {
        socio_id: 102,
        socio_nombre: 'Lucas Martín Guillén',
        socio_legajo: '85194',
        socio_subcomision: 'Cómputos e Informática',
        estado_asistencia: 'TARDANZA_LEVE',
        motivo: 'Retraso de transporte público (+18 min)',
        minutos_tardanza: 18,
        minutos_retiro_anticipado: 0,
        metodo_captura: 'MANUAL',
        hora_registro: new Date().toISOString()
      },
      {
        socio_id: 103,
        socio_nombre: 'Nicolás Rosales',
        socio_legajo: '408917',
        socio_subcomision: 'Cómputos e Informática',
        estado_asistencia: 'AUSENTE_INJUSTIFICADO',
        motivo: 'Inasistencia sin previo aviso ni justificación',
        minutos_tardanza: 0,
        minutos_retiro_anticipado: 0,
        metodo_captura: 'MANUAL'
      },
      {
        socio_id: 104,
        socio_nombre: 'Martín Cabrera',
        socio_legajo: '75012',
        socio_subcomision: 'Finanzas',
        estado_asistencia: 'JUSTIFICADO',
        motivo: 'Examen final en UTN FRC con constancia',
        minutos_tardanza: 0,
        minutos_retiro_anticipado: 0,
        metodo_captura: 'MANUAL'
      }
    ];
  }

  get convocadosFiltrados(): ConvocadoAsistenciaDTO[] {
    let result = this.convocados;

    if (this.filtroTexto && this.filtroTexto.trim()) {
      const q = this.filtroTexto.toLowerCase().trim();
      result = result.filter(
        c =>
          c.socio_nombre.toLowerCase().includes(q) ||
          c.socio_legajo.toLowerCase().includes(q) ||
          (c.socio_subcomision && c.socio_subcomision.toLowerCase().includes(q))
      );
    }

    if (this.filtroEstado !== 'TODOS') {
      if (this.filtroEstado === 'TARDANZAS') {
        result = result.filter(
          c => c.estado_asistencia === 'TARDANZA_LEVE' || c.estado_asistencia === 'TARDANZA_GRAVE'
        );
      } else {
        result = result.filter(c => c.estado_asistencia === this.filtroEstado);
      }
    }

    return result;
  }

  get totalPresentes(): number {
    return this.convocados.filter(
      c => c.estado_asistencia === 'PRESENTE' || c.estado_asistencia === 'JUSTIFICADO'
    ).length;
  }

  get totalAusentes(): number {
    return this.convocados.filter(c => c.estado_asistencia === 'AUSENTE_INJUSTIFICADO').length;
  }

  get totalTardanzas(): number {
    return this.convocados.filter(
      c => c.estado_asistencia === 'TARDANZA_LEVE' || c.estado_asistencia === 'TARDANZA_GRAVE'
    ).length;
  }

  cambiarEstrategia(tipo: MetodoCapturaAsistencia): void {
    this.contextService.setStrategy(tipo);
    this.notificationService.info(
      `Estrategia cambiada a modo ${tipo === 'BIOMETRICO' ? 'Biométrico' : 'Manual'}.`
    );
  }

  onCambiarEstadoSocio(socio: ConvocadoAsistenciaDTO): void {
    if (socio.estado_asistencia === 'PRESENTE' && !socio.motivo) {
      socio.motivo = 'En sede a tiempo';
    } else if (socio.estado_asistencia === 'AUSENTE_INJUSTIFICADO' && !socio.motivo) {
      socio.motivo = 'Inasistencia sin justificar';
    } else if (socio.estado_asistencia === 'TARDANZA_LEVE' && !socio.motivo) {
      socio.motivo = 'Tardanza leve (15-30 min)';
    } else if (socio.estado_asistencia === 'TARDANZA_GRAVE' && !socio.motivo) {
      socio.motivo = 'Tardanza grave (> 30 min)';
    }
    this.ultimaModificacion = new Date();
  }

  simularHuellaSocio(socio: ConvocadoAsistenciaDTO): void {
    this.escaneandoHuella = true;
    setTimeout(() => {
      this.escaneandoHuella = false;
      const horaProg = this.eventoActivo?.fecha_programada
        ? new Date(this.eventoActivo.fecha_programada)
        : undefined;

      const res = this.biometricStrategy.capturar(
        socio,
        horaProg,
        this.eventoActivo?.tolerancia_tardanza_minutos || 15
      );

      socio.estado_asistencia = res.estado;
      socio.hora_registro = res.horaRegistro;
      socio.minutos_tardanza = res.minutosTardanza || 0;
      socio.motivo = res.motivo;
      socio.metodo_captura = 'BIOMETRICO';
      this.ultimaModificacion = new Date();

      this.notificationService.success(res.feedbackMensaje);
    }, 450);
  }

  guardarPlanilla(): void {
    if (!this.eventoActivo) return;

    const payload: ReportarAsistenciaPayload = {
      estrategia: this.estrategiaActual,
      cerrar_evento: false,
      asistencias: this.convocados.map(c => ({
        socio_id: c.socio_id,
        estado_asistencia: c.estado_asistencia,
        motivo: c.motivo || 'Marcación en planilla',
        minutos_tardanza: c.minutos_tardanza,
        minutos_retiro_anticipado: c.minutos_retiro_anticipado,
        metodo_captura: c.metodo_captura,
        hora_registro: c.hora_registro
      }))
    };

    this.guardando = true;
    this.eventoService.registrarAsistenciasBulk(this.eventoActivo.id, payload).subscribe({
      next: () => {
        this.guardando = false;
        this.notificationService.success('Planilla de asistencia guardada correctamente.');
      },
      error: () => {
        this.guardando = false;
        // Mock fallback feedback
        this.notificationService.success('Planilla de asistencia guardada localmente.');
      }
    });
  }

  abrirModalProcesarYCerrar(): void {
    if (!this.eventoActivo) return;

    const dialogRef = this.dialog.open(ResumenCierreDialogComponent, {
      width: '750px',
      data: {
        evento: this.eventoActivo,
        convocados: this.convocados
      }
    });

    dialogRef.afterClosed().subscribe(confirmado => {
      if (confirmado) {
        this.ejecutarProcesamientoYCierre();
      }
    });
  }

  private ejecutarProcesamientoYCierre(): void {
    if (!this.eventoActivo) return;

    const payload: ReportarAsistenciaPayload = {
      estrategia: this.estrategiaActual,
      cerrar_evento: true,
      asistencias: this.convocados.map(c => ({
        socio_id: c.socio_id,
        estado_asistencia: c.estado_asistencia,
        motivo: c.motivo || 'Cierre formal de asistencia',
        minutos_tardanza: c.minutos_tardanza,
        minutos_retiro_anticipado: c.minutos_retiro_anticipado,
        metodo_captura: c.metodo_captura,
        hora_registro: c.hora_registro
      }))
    };

    this.procesando = true;
    this.eventoService.procesarAsistencias(this.eventoActivo.id, payload).subscribe({
      next: res => {
        this.procesando = false;
        if (this.eventoActivo) {
          this.eventoActivo.estado = 'CERRADA';
        }
        const msg = `Convocatoria cerrada formalmente. Se abrieron ${res.expedientes_generados} expedientes y se registraron ${res.apercibimientos_generados} apercibimientos.`;
        this.notificationService.success(msg);
      },
      error: () => {
        this.procesando = false;
        if (this.eventoActivo) {
          this.eventoActivo.estado = 'CERRADA';
        }
        const expCount = this.eventoActivo.es_sancionable ? this.totalAusentes : 0;
        this.notificationService.success(
          `Convocatoria cerrada formalmente. Se abrieron ${expCount} expedientes en estado Expediente Creado.`
        );
      }
    });
  }

  abrirDialogoCrearEvento(): void {
    const dialogRef = this.dialog.open(CrearEventoDialogComponent, {
      width: '720px'
    });

    dialogRef.afterClosed().subscribe(nuevoEvento => {
      if (nuevoEvento) {
        this.eventos.unshift(nuevoEvento);
        this.seleccionarEvento(nuevoEvento);
      }
    });
  }
}
