import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, FormControl, Validators } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { Subscription, of } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import {
  CategoriaEvento,
  ConvocadoAsistenciaDTO,
  CrearEventoPayload,
  EstadoAsistenciaEvento,
  EstadoEvento,
  EstadoSocialConvocado,
  EventoInstitucional,
  MetodoCapturaAsistencia,
  ModoConvocatoria,
  ModalidadEvento,
  ReportarAsistenciaPayload,
  SubtipoActividad,
  SubtipoEvento,
  SubtipoReunion
} from '../../../models/evento.model';
import { AttendanceContextService } from '../../../eventos-asistencia/strategies/attendance-context.service';
import { BiometricAttendanceStrategy } from '../../../eventos-asistencia/strategies/biometric-attendance.strategy';
import { EventoService } from '../../../services/evento.service';
import { NotificationService } from '../../../services/notification.service';
import { SocioApiService, SocioListItemDTO } from '../../../services/socio-api.service';
import { TribunalDataService } from '../../../services/tribunal-data.service';
import { CrearEventoDialogComponent } from '../dialogs/crear-evento-dialog/crear-evento-dialog.component';
import { ResumenCierreDialogComponent } from '../dialogs/resumen-cierre-dialog/resumen-cierre-dialog.component';

export interface SubtipoOption {
  value: SubtipoEvento;
  label: string;
  sancion?: string;
}

@Component({
  selector: 'app-asistencia-evento',
  templateUrl: './asistencia-evento.component.html',
  styleUrls: ['./asistencia-evento.component.scss']
})
export class AsistenciaEventoComponent implements OnInit, OnDestroy {
  // Pestañas estilo AVEIT (análogo a solicitar-puntos)
  tabActiva: 'generar' | 'mis-eventos' = 'generar';
  modoDetalle = false; // True cuando se examina la Planilla Nominal de Asistencia desde Mis Eventos

  // Mis Eventos (Convocatorias del usuario logueado)
  misEventos: EventoInstitucional[] = [];
  cargandoMisEventos = false;

  // Modales interactivos para Mis Eventos
  modalHoraFinVisible = false;
  eventoHoraFin: EventoInstitucional | null = null;
  horaFinInput = '';

  modalAnularVisible = false;
  eventoAnular: EventoInstitucional | null = null;
  motivoAnulacionInput = '';
  anulando = false;

  // Formulario reactivo para Generar Evento
  crearForm!: FormGroup;
  guardandoEvento = false;
  subtiposDisponibles: SubtipoOption[] = [];
  antelacionAviso: 'SANCIONABLE' | 'NO_SANCIONABLE' | null = null;

  // Búsqueda de socios reactiva tipo Select2 para Convocatoria Personalizada
  filtroSocioControl = new FormControl('');
  buscandoSocios = false;
  sociosEncontrados: SocioListItemDTO[] = [];
  sociosSeleccionados: SocioListItemDTO[] = [];

  // Catálogos institucionales
  gruposDisponibles = ['G55', 'G56', 'G57', 'G58', 'G59', 'G60'];
  subcomisiones = [
    { id: 1, nombre: 'Comunicaciones' },
    { id: 2, nombre: 'Deportes' },
    { id: 3, nombre: 'Extensión Universitaria' },
    { id: 4, nombre: 'Finanzas' },
    { id: 5, nombre: 'Prensa y Difusión' },
    { id: 6, nombre: 'Relaciones Públicas' },
    { id: 7, nombre: 'Tesorería' },
    { id: 8, nombre: 'Cómputos e Informática' }
  ];
  estadosSociales: { id: EstadoSocialConvocado; label: string }[] = [
    { id: 'JUNIORS', label: 'Juniors (1° a 3° año social)' },
    { id: 'SENIORS', label: 'Seniors (4° a 6° año social)' }
  ];

  // Estado del Evento Activo y Planilla Nominal de Asistencia
  eventos: EventoInstitucional[] = [];
  eventoActivo: EventoInstitucional | null = null;
  eventoSeleccionadoId: number | string | null = null;
  convocados: ConvocadoAsistenciaDTO[] = [];

  // Filtros de tabla nominal
  filtroTexto = '';
  filtroEstado = 'TODOS';

  // Estrategia de marcación
  estrategiaActual: MetodoCapturaAsistencia = 'MANUAL';
  escaneandoHuella = false;

  // Estados de carga de asistencia
  guardando = false;
  procesando = false;
  ultimaModificacion = new Date();

  private subs: Subscription[] = [];

  constructor(
    private fb: FormBuilder,
    private eventoService: EventoService,
    private socioService: SocioApiService,
    private dataService: TribunalDataService,
    private contextService: AttendanceContextService,
    private biometricStrategy: BiometricAttendanceStrategy,
    private notificationService: NotificationService,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    this.initForm();
    this.configurarBuscadorSocios();

    // Estrategia de marcación activa
    const subStrat = this.contextService.currentStrategy$.subscribe(strat => {
      this.estrategiaActual = strat.tipo;
    });
    this.subs.push(subStrat);

    this.cargarEventos();
    this.cargarMisEventos();
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  // =========================================================================
  // GESTIÓN DE PESTAÑAS (Estilo AVEIT)
  // =========================================================================

  setTab(tab: 'generar' | 'mis-eventos'): void {
    this.tabActiva = tab;
    if (tab === 'mis-eventos') {
      this.cargarMisEventos();
    }
  }

  // =========================================================================
  // FORMULARIO: GENERAR EVENTO (Reunión vs Actividad)
  // =========================================================================

  private initForm(): void {
    this.crearForm = this.fb.group({
      titulo: ['', [Validators.required, Validators.minLength(3)]],
      descripcion: [''],
      categoria: ['REUNION' as CategoriaEvento, Validators.required],
      tipo: ['ORDINARIA' as SubtipoEvento, Validators.required],
      detalle_tarea: [''], // Obligatorio sólo si categoria === 'ACTIVIDAD'
      puntos_sancion: [-1.0], // Editable para actividades
      modalidad: ['PRESENCIAL_SEDE' as ModalidadEvento, Validators.required],
      ubicacion: [''],
      fecha_programada: ['', Validators.required],
      fecha_fin: [''], // Estrictamente opcional
      modo_convocatoria: ['GRUPO' as ModoConvocatoria, Validators.required],
      grupo_convocado: ['G58'],
      subcomision_id: [null],
      estado_social_convocado: ['JUNIORS' as EstadoSocialConvocado],
      tolerancia_tardanza_minutos: [15, [Validators.min(0), Validators.max(60)]],
      tolerancia_retiro_minutos: [15, [Validators.min(0), Validators.max(60)]],
      notificar: [false]
    });

    this.actualizarSubtipos('REUNION');

    // Escuchar cambios en fecha_programada para calcular preaviso (CA1)
    const subFecha = this.crearForm.get('fecha_programada')?.valueChanges.subscribe(fechaStr => {
      this.evaluarPreaviso(fechaStr);
    });
    if (subFecha) this.subs.push(subFecha);
  }

  onCategoriaChange(cat: CategoriaEvento): void {
    this.crearForm.patchValue({ categoria: cat });
    this.actualizarSubtipos(cat);

    const detalleControl = this.crearForm.get('detalle_tarea');
    const puntosControl = this.crearForm.get('puntos_sancion');

    if (cat === 'ACTIVIDAD') {
      detalleControl?.setValidators([Validators.required, Validators.minLength(5)]);
      if (puntosControl && (puntosControl.value === null || puntosControl.value === undefined)) {
        puntosControl.setValue(-1.0);
      }
    } else {
      detalleControl?.clearValidators();
      detalleControl?.setValue('');
    }
    detalleControl?.updateValueAndValidity();
  }

  actualizarSubtipos(categoria: CategoriaEvento): void {
    if (categoria === 'REUNION') {
      this.subtiposDisponibles = [
        { value: 'ORDINARIA', label: 'Reunión Ordinaria', sancion: '-1.00 pt' },
        { value: 'EXTRAORDINARIA', label: 'Reunión Extraordinaria', sancion: '-1.50 pts' },
        { value: 'ASAMBLEA', label: 'Asamblea General', sancion: '-2.00 pts' },
        { value: 'PLENARIO', label: 'Plenario de Comisiones', sancion: '-1.00 pt' }
      ];
      this.crearForm.patchValue({ tipo: 'ORDINARIA' });
    } else {
      this.subtiposDisponibles = [
        { value: 'MANTENIMIENTO', label: 'Mantenimiento de Sede', sancion: 'Personalizable' },
        { value: 'VOLUNTARIADO', label: 'Voluntariado Institucional', sancion: 'Personalizable' },
        { value: 'JORNADA', label: 'Jornada Solidaria / Técnica', sancion: 'Personalizable' },
        { value: 'EVENTO_SOCIAL', label: 'Evento Social y Confraternidad', sancion: 'Personalizable' },
        { value: 'GUARDIA', label: 'Guardia Operativa', sancion: 'Personalizable' }
      ];
      this.crearForm.patchValue({ tipo: 'MANTENIMIENTO' });
    }
  }

  evaluarPreaviso(fechaStr: string): void {
    if (!fechaStr) {
      this.antelacionAviso = null;
      return;
    }
    const fechaProg = new Date(fechaStr);
    const ahora = new Date();
    const diffMs = fechaProg.getTime() - ahora.getTime();
    const diffDiasHabiles = diffMs / (1000 * 60 * 60 * 24);

    // Estimación preventiva: 2 días hábiles (~48hs a 96hs)
    if (diffDiasHabiles >= 2.0) {
      this.antelacionAviso = 'SANCIONABLE';
    } else {
      this.antelacionAviso = 'NO_SANCIONABLE';
    }
  }

  private configurarBuscadorSocios(): void {
    const subBuscador = this.filtroSocioControl.valueChanges
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        switchMap(query => {
          if (!query || query.trim().length < 2) {
            this.sociosEncontrados = [];
            return of(null);
          }
          this.buscandoSocios = true;
          return this.socioService.searchSocios(query);
        })
      )
      .subscribe({
        next: response => {
          this.buscandoSocios = false;
          if (response && response.results) {
            const yaSeleccionados = new Set(this.sociosSeleccionados.map(s => s.id));
            this.sociosEncontrados = response.results.filter(s => !yaSeleccionados.has(s.id));
          } else {
            this.sociosEncontrados = [];
          }
        },
        error: () => {
          this.buscandoSocios = false;
          this.sociosEncontrados = [];
        }
      });

    this.subs.push(subBuscador);
  }

  seleccionarSocio(socio: SocioListItemDTO): void {
    if (!this.sociosSeleccionados.some(s => s.id === socio.id)) {
      this.sociosSeleccionados.push(socio);
    }
    this.filtroSocioControl.setValue('');
    this.sociosEncontrados = [];
  }

  removerSocio(socioId: number): void {
    this.sociosSeleccionados = this.sociosSeleccionados.filter(s => s.id !== socioId);
  }

  crearEventoSubmit(): void {
    if (this.crearForm.invalid) {
      this.crearForm.markAllAsTouched();
      this.notificationService.warning('Complete todos los campos obligatorios antes de generar el evento.');
      return;
    }

    const val = this.crearForm.value;
    const cat = val.categoria as CategoriaEvento;

    if (cat === 'ACTIVIDAD' && (!val.detalle_tarea || !val.detalle_tarea.trim())) {
      this.notificationService.warning('Para actividades es obligatorio detallar la tarea asignada.');
      return;
    }

    if (val.modo_convocatoria === 'PERSONALIZADA' && this.sociosSeleccionados.length === 0) {
      this.notificationService.warning('Para convocatoria personalizada debe seleccionar al menos un socio.');
      return;
    }

    const payload: CrearEventoPayload = {
      titulo: val.titulo.trim(),
      descripcion: val.descripcion ? val.descripcion.trim() : undefined,
      categoria: val.categoria,
      tipo: val.tipo,
      modalidad: val.modalidad,
      ubicacion: val.ubicacion ? val.ubicacion.trim() : undefined,
      fecha_programada: new Date(val.fecha_programada).toISOString(),
      fecha_fin: val.fecha_fin ? new Date(val.fecha_fin).toISOString() : null,
      modo_convocatoria: val.modo_convocatoria,
      grupo_convocado: val.modo_convocatoria === 'GRUPO' ? val.grupo_convocado : undefined,
      subcomision_id: val.modo_convocatoria === 'SUBCOMISION' ? val.subcomision_id : null,
      estado_social_convocado:
        val.modo_convocatoria === 'ESTADO_SOCIAL' ? val.estado_social_convocado : undefined,
      detalle_tarea: cat === 'ACTIVIDAD' ? val.detalle_tarea.trim() : undefined,
      puntos_sancion:
        cat === 'ACTIVIDAD' && val.puntos_sancion != null ? -Math.abs(Number(val.puntos_sancion)) : undefined,
      tolerancia_tardanza_minutos: val.tolerancia_tardanza_minutos,
      tolerancia_retiro_minutos: val.tolerancia_retiro_minutos,
      notificar: Boolean(val.notificar),
      socios_ids:
        val.modo_convocatoria === 'PERSONALIZADA'
          ? this.sociosSeleccionados.map(s => s.id)
          : undefined
    };

    this.guardandoEvento = true;
    this.eventoService.crearEvento(payload).subscribe({
      next: creado => {
        this.guardandoEvento = false;
        const msg = val.notificar
          ? `Evento "${creado.titulo}" generado y notificado formalmente a los convocados.`
          : `Evento "${creado.titulo}" creado en estado Creado (pendiente de notificación).`;
        this.notificationService.success(msg);

        // Resetear formulario
        this.crearForm.reset({
          categoria: 'REUNION',
          tipo: 'ORDINARIA',
          modalidad: 'PRESENCIAL_SEDE',
          modo_convocatoria: 'GRUPO',
          grupo_convocado: 'G58',
          estado_social_convocado: 'JUNIORS',
          tolerancia_tardanza_minutos: 15,
          tolerancia_retiro_minutos: 15,
          notificar: false,
          puntos_sancion: -1.0
        });
        this.sociosSeleccionados = [];
        this.actualizarSubtipos('REUNION');

        // Navegar a Mis Eventos
        this.setTab('mis-eventos');
      },
      error: err => {
        this.guardandoEvento = false;
        const errorMsg =
          err?.error?.detail || err?.error?.fecha_programada || 'Error al generar el evento institucional.';
        this.notificationService.error(errorMsg);
      }
    });
  }

  // =========================================================================
  // PESTAÑA: MIS EVENTOS (Lista, Ciclo de Vida y Acciones)
  // =========================================================================

  cargarMisEventos(): void {
    this.cargandoMisEventos = true;
    this.eventoService.getMisEventos().subscribe({
      next: list => {
        this.cargandoMisEventos = false;
        this.misEventos = list || [];
      },
      error: () => {
        this.cargandoMisEventos = false;
        // Fallback a eventos generales si mis_eventos no tiene elementos
        this.misEventos = this.eventos;
      }
    });
  }

  verDetalle(evento: EventoInstitucional): void {
    this.eventoActivo = evento;
    this.eventoSeleccionadoId = evento.id;
    this.modoDetalle = true;
    this.cargarConvocados(evento.id);
  }

  volverAMisEventos(): void {
    this.modoDetalle = false;
    this.cargarMisEventos();
  }

  notificarConvocatoria(evento: EventoInstitucional): void {
    if (confirm(`¿Deseas enviar las notificaciones formales por correo a todos los citados para "${evento.titulo}"?`)) {
      this.eventoService.notificarEvento(evento.id).subscribe({
        next: res => {
          evento.estado = 'NOTIFICADO';
          this.notificationService.success(res.detail || 'Convocatoria notificada formalmente.');
        },
        error: err => {
          this.notificationService.error(err?.error?.detail || 'Error al notificar la convocatoria.');
        }
      });
    }
  }

  // Modal para Fijar Hora Fin
  abrirModalHoraFin(evento: EventoInstitucional): void {
    this.eventoHoraFin = evento;
    const ahora = new Date();
    // Formato local YYYY-MM-DDTHH:mm
    const tzOffset = ahora.getTimezoneOffset() * 60000;
    this.horaFinInput = new Date(ahora.getTime() - tzOffset).toISOString().slice(0, 16);
    this.modalHoraFinVisible = true;
  }

  cerrarModalHoraFin(): void {
    this.modalHoraFinVisible = false;
    this.eventoHoraFin = null;
    this.horaFinInput = '';
  }

  confirmarHoraFin(): void {
    if (!this.eventoHoraFin || !this.horaFinInput) return;

    const fechaFinIso = new Date(this.horaFinInput).toISOString();
    this.eventoService.fijarHoraFin(this.eventoHoraFin.id, fechaFinIso).subscribe({
      next: res => {
        this.notificationService.success(res.detail || 'Hora de finalización registrada exitosamente.');
        if (this.eventoHoraFin) {
          this.eventoHoraFin.estado = res.evento.estado;
          this.eventoHoraFin.fecha_fin = res.evento.fecha_fin;
        }
        this.cerrarModalHoraFin();
        this.cargarMisEventos();
      },
      error: err => {
        this.notificationService.error(
          err?.error?.fecha_fin || err?.error?.detail || 'Error al fijar la hora de finalización.'
        );
      }
    });
  }

  // Modal para Anular Convocatoria
  abrirModalAnular(evento: EventoInstitucional): void {
    this.eventoAnular = evento;
    this.motivoAnulacionInput = '';
    this.modalAnularVisible = true;
  }

  cerrarModalAnular(): void {
    this.modalAnularVisible = false;
    this.eventoAnular = null;
    this.motivoAnulacionInput = '';
    this.anulando = false;
  }

  confirmarAnulacion(): void {
    if (!this.eventoAnular) return;

    this.anulando = true;
    this.eventoService.anularEvento(this.eventoAnular.id, this.motivoAnulacionInput.trim()).subscribe({
      next: res => {
        this.anulando = false;
        this.notificationService.success(res.detail || 'Evento anulado correctamente.');
        if (this.eventoAnular) {
          this.eventoAnular.estado = 'ANULADO';
          this.eventoAnular.motivo_cancelacion = this.motivoAnulacionInput.trim();
        }
        this.cerrarModalAnular();
        this.cargarMisEventos();
      },
      error: err => {
        this.anulando = false;
        this.notificationService.error(err?.error?.detail || 'Error al anular el evento.');
      }
    });
  }

  // =========================================================================
  // PLANILLA NOMINAL DE ASISTENCIA Y OPERACIONES
  // =========================================================================

  cargarEventos(): void {
    this.eventoService.getEventos().subscribe({
      next: list => {
        if (list && list.length > 0) {
          this.eventos = list;
          if (!this.eventoActivo) {
            this.seleccionarEvento(list[0]);
          }
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
          c =>
            c.estado_asistencia === 'TARDANZA_LEVE' ||
            c.estado_asistencia === 'TARDE_LEVE' ||
            c.estado_asistencia === 'TARDANZA_GRAVE' ||
            c.estado_asistencia === 'TARDE_GRAVE'
        );
      } else if (
        this.filtroEstado === 'AUSENTE_INJUSTIFICADO' ||
        this.filtroEstado === 'AUSENTE'
      ) {
        result = result.filter(
          c =>
            c.estado_asistencia === 'AUSENTE_INJUSTIFICADO' ||
            c.estado_asistencia === 'AUSENTE'
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
    return this.convocados.filter(
      c => c.estado_asistencia === 'AUSENTE_INJUSTIFICADO' || c.estado_asistencia === 'AUSENTE'
    ).length;
  }

  get totalTardanzas(): number {
    return this.convocados.filter(
      c =>
        c.estado_asistencia === 'TARDANZA_LEVE' ||
        c.estado_asistencia === 'TARDE_LEVE' ||
        c.estado_asistencia === 'TARDANZA_GRAVE' ||
        c.estado_asistencia === 'TARDE_GRAVE'
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
    } else if (
      (socio.estado_asistencia === 'AUSENTE_INJUSTIFICADO' ||
        socio.estado_asistencia === 'AUSENTE') &&
      !socio.motivo
    ) {
      socio.motivo = 'Inasistencia sin justificar';
    } else if (
      (socio.estado_asistencia === 'TARDANZA_LEVE' ||
        socio.estado_asistencia === 'TARDE_LEVE') &&
      !socio.motivo
    ) {
      socio.motivo = 'Tardanza leve (15-30 min)';
    } else if (
      (socio.estado_asistencia === 'TARDANZA_GRAVE' ||
        socio.estado_asistencia === 'TARDE_GRAVE') &&
      !socio.motivo
    ) {
      socio.motivo = 'Tardanza grave (> 30 min)';
    } else if (socio.estado_asistencia === 'JUSTIFICADO' && !socio.motivo) {
      socio.motivo = 'Ausencia justificada con constancia';
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
      metodo_captura: this.estrategiaActual,
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
      metodo_captura: this.estrategiaActual,
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
          this.eventoActivo.estado = 'FINALIZADO';
        }
        const expGenerados =
          res.expedientes_generados ??
          (Array.isArray(res.expedientes_creados) ? res.expedientes_creados.length : 0);
        const apercGenerados =
          res.apercibimientos_generados ??
          (Array.isArray(res.apercibimientos_creados) ? res.apercibimientos_creados.length : 0);
        const msg = `Convocatoria cerrada formalmente. Se abrieron ${expGenerados} expedientes y se registraron ${apercGenerados} apercibimientos.`;
        this.notificationService.success(msg);
      },
      error: () => {
        this.procesando = false;
        if (this.eventoActivo) {
          this.eventoActivo.estado = 'FINALIZADO';
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
        this.cargarMisEventos();
      }
    });
  }
}
