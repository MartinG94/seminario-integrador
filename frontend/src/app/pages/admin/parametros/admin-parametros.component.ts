import { Component, OnDestroy, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { MatDialog, MatDialogConfig, MatDialogRef } from '@angular/material/dialog';
import { of, Subject } from 'rxjs';
import { catchError, debounceTime, distinctUntilChanged, finalize, switchMap, takeUntil, tap } from 'rxjs/operators';

import {
  AdminApiService, CambioParametroDTO, CandidatoTribunalDTO, CategoriaParametro, MiembroTribunalDTO,
  ParametroSistemaDTO, ValorParametro
} from '../../../services/admin-api.service';
import { NotificationService, httpErrorMessage } from '../../../services/notification.service';
import { ParametrosVigentesService } from '../../../services/parametros-vigentes.service';

interface TarjetaParametros {
  categoria: CategoriaParametro;
  titulo: string;
  icono: string;
}

/** Huso horario institucional (Córdoba, Argentina) para fechas de auditoría. */
export const HUSO_INSTITUCIONAL = '-0300';
/** Mínimo de caracteres para consultar candidatos al servidor. */
export const MIN_CARACTERES_BUSQUEDA = 2;

/** Panel de diálogo tokenizado: fondo y texto siguen el tema claro u oscuro. */
const DIALOGO_BASE: MatDialogConfig = {
  maxWidth: 'calc(100vw - 2rem)',
  panelClass: 'aveit-dialog-panel',
  restoreFocus: true,
  closeOnNavigation: true
};

@Component({
  selector: 'app-admin-parametros',
  templateUrl: './admin-parametros.component.html',
  styleUrls: ['./admin-parametros.component.scss']
})
export class AdminParametrosComponent implements OnInit, OnDestroy {
  readonly tarjetas: TarjetaParametros[] = [
    { categoria: 'PLAZOS', titulo: 'Plazos', icono: 'schedule' },
    { categoria: 'UMBRALES', titulo: 'Umbrales de puntos', icono: 'warning' },
    { categoria: 'CORREOS', titulo: 'Correos institucionales', icono: 'mail' },
    { categoria: 'ADJUNTOS', titulo: 'Comprobantes adjuntos', icono: 'attach_file' },
  ];
  readonly huso = HUSO_INSTITUCIONAL;
  readonly minCaracteres = MIN_CARACTERES_BUSQUEDA;

  parametros: ParametroSistemaDTO[] = [];
  borradores: Record<string, ValorParametro> = {};
  guardando: Record<string, boolean> = {};
  /** Último error de validación del servidor por clave (para aria-invalid). */
  errores: Record<string, string> = {};
  cargandoParametros = false;
  errorParametros = '';

  historialClave: string | null = null;
  historial: CambioParametroDTO[] = [];
  cargandoHistorial = false;
  @ViewChild('historialTemplate', { static: true }) historialTemplate!: TemplateRef<unknown>;
  private historialDialog: MatDialogRef<unknown> | null = null;

  miembros: MiembroTribunalDTO[] = [];
  cargandoMiembros = false;
  errorMiembros = '';
  @ViewChild('altaTemplate', { static: true }) altaTemplate!: TemplateRef<unknown>;
  @ViewChild('revocarTemplate', { static: true }) revocarTemplate!: TemplateRef<unknown>;
  private altaDialog: MatDialogRef<unknown> | null = null;
  private revocarDialog: MatDialogRef<unknown> | null = null;
  busqueda: string | CandidatoTribunalDTO = '';
  candidatos: CandidatoTribunalDTO[] = [];
  buscandoCandidatos = false;
  /** Término efectivamente consultado (para el estado "Sin coincidencias"). */
  terminoConsultado = '';
  socioSeleccionado: CandidatoTribunalDTO | null = null;
  miembroARevocar: MiembroTribunalDTO | null = null;
  procesandoMiembro = false;

  private readonly busqueda$ = new Subject<string>();
  private readonly destroy$ = new Subject<void>();

  constructor(
    private api: AdminApiService,
    private notifications: NotificationService,
    private dialog: MatDialog,
    private parametrosVigentes: ParametrosVigentesService
  ) {}

  ngOnInit(): void {
    this.busqueda$.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      tap(termino => {
        this.buscandoCandidatos = termino.length >= MIN_CARACTERES_BUSQUEDA;
        this.terminoConsultado = '';
      }),
      switchMap(termino => termino.length < MIN_CARACTERES_BUSQUEDA
        ? of({ termino, socios: [] as CandidatoTribunalDTO[] })
        : this.api.buscarCandidatosTribunal(termino).pipe(
          catchError(err => {
            this.notifications.error(httpErrorMessage(err, 'No se pudo buscar socios.'));
            return of([] as CandidatoTribunalDTO[]);
          }),
          switchMap(socios => of({ termino, socios }))
        )),
      takeUntil(this.destroy$)
    ).subscribe(({ termino, socios }) => {
      this.candidatos = socios;
      this.terminoConsultado = termino.length >= MIN_CARACTERES_BUSQUEDA ? termino : '';
      this.buscandoCandidatos = false;
    });
    this.cargarParametros();
    this.cargarMiembros();
  }

  ngOnDestroy(): void {
    this.dialog.closeAll();
    this.destroy$.next();
    this.destroy$.complete();
  }

  // --- Parámetros ---

  parametrosDe(categoria: CategoriaParametro): ParametroSistemaDTO[] {
    return this.parametros.filter(p => p.categoria === categoria);
  }

  cargarParametros(): void {
    this.cargandoParametros = true;
    this.errorParametros = '';
    this.api.listarParametros().pipe(takeUntil(this.destroy$)).subscribe({
      next: parametros => {
        this.parametros = parametros;
        this.borradores = {};
        this.errores = {};
        parametros.forEach(p => this.borradores[p.clave] = this.aBorrador(p));
        this.cargandoParametros = false;
      },
      error: () => {
        this.cargandoParametros = false;
        this.errorParametros = 'No se pudieron cargar los parámetros. Intentá nuevamente.';
        this.notifications.error(this.errorParametros);
      }
    });
  }

  private aBorrador(p: ParametroSistemaDTO): ValorParametro {
    if (p.tipo === 'INTEGER' || p.tipo === 'DECIMAL') { return p.valor === null ? null : Number(p.valor); }
    return p.valor;
  }

  tieneCambios(p: ParametroSistemaDTO): boolean {
    return p.editable && this.borradores[p.clave] !== this.aBorrador(p);
  }

  alEditar(p: ParametroSistemaDTO): void {
    delete this.errores[p.clave];
  }

  guardar(p: ParametroSistemaDTO): void {
    if (!this.tieneCambios(p) || this.guardando[p.clave]) { return; }
    const borrador = this.borradores[p.clave];
    if (borrador === null || borrador === '' || (typeof borrador === 'number' && Number.isNaN(borrador))) {
      this.errores[p.clave] = `Indicá un valor para ${p.etiqueta}.`;
      this.notifications.error(this.errores[p.clave]);
      return;
    }
    const valor = p.tipo === 'DECIMAL' ? String(borrador) : borrador;
    this.guardando[p.clave] = true;
    this.api.actualizarParametro(p.clave, valor).pipe(takeUntil(this.destroy$)).subscribe({
      next: actualizado => {
        this.guardando[p.clave] = false;
        delete this.errores[p.clave];
        this.parametros = this.parametros.map(x => x.clave === actualizado.clave ? actualizado : x);
        this.borradores[actualizado.clave] = this.aBorrador(actualizado);
        this.parametrosVigentes.invalidar();
        this.notifications.success(`${actualizado.etiqueta} actualizado.`);
      },
      error: err => {
        this.guardando[p.clave] = false;
        this.errores[p.clave] = httpErrorMessage(err, `No se pudo actualizar ${p.etiqueta}.`);
        this.notifications.error(this.errores[p.clave]);
      }
    });
  }

  descartar(p: ParametroSistemaDTO): void {
    this.borradores[p.clave] = this.aBorrador(p);
    delete this.errores[p.clave];
  }

  /** Número en notación rioplatense: coma decimal. */
  formatearNumero(valor: string | number | null): string {
    if (valor === null || valor === undefined || valor === '') { return '—'; }
    const numero = Number(valor);
    return Number.isFinite(numero) ? String(numero).replace('.', ',') : String(valor);
  }

  formatearValor(p: ParametroSistemaDTO, valor: ValorParametro): string {
    if (valor === null || valor === undefined || valor === '') { return '—'; }
    if (p.tipo === 'BOOLEAN') { return valor ? 'Sí' : 'No'; }
    if (p.tipo === 'DECIMAL') { return this.formatearNumero(valor as string | number); }
    return String(valor);
  }

  get parametroHistorial(): ParametroSistemaDTO | undefined {
    return this.parametros.find(p => p.clave === this.historialClave);
  }

  verHistorial(p: ParametroSistemaDTO): void {
    if (this.cargandoHistorial || this.historialDialog) { return; }
    this.cargandoHistorial = true;
    this.historialClave = p.clave;
    this.historial = [];
    this.api.historialParametro(p.clave).pipe(
      finalize(() => this.cargandoHistorial = false),
      takeUntil(this.destroy$)
    ).subscribe({
      next: cambios => {
        this.historial = cambios;
        this.historialDialog = this.dialog.open(this.historialTemplate, {
          ...DIALOGO_BASE, width: '44rem', ariaLabelledBy: 'historial-title'
        });
        this.historialDialog.afterClosed().pipe(takeUntil(this.destroy$)).subscribe(() => {
          this.historialDialog = null;
        });
      },
      error: err => this.notifications.error(httpErrorMessage(err, 'No se pudo cargar el historial.'))
    });
  }

  cerrarHistorial(): void {
    this.historialDialog?.close();
    this.historialDialog = null;
  }

  // --- Miembros del Tribunal ---

  cargarMiembros(): void {
    this.cargandoMiembros = true;
    this.errorMiembros = '';
    this.api.listarMiembrosTribunal().pipe(takeUntil(this.destroy$)).subscribe({
      next: miembros => {
        this.miembros = miembros;
        this.cargandoMiembros = false;
      },
      error: () => {
        this.cargandoMiembros = false;
        this.errorMiembros = 'No se pudo cargar la nómina del Tribunal. Intentá nuevamente.';
        this.notifications.error(this.errorMiembros);
      }
    });
  }

  trackMiembro(_index: number, miembro: MiembroTribunalDTO): number { return miembro.id; }

  trackCandidato(_index: number, candidato: CandidatoTribunalDTO): number { return candidato.id; }

  numeroSocio(socio: { numero_socio: number | null }): string {
    return socio.numero_socio === null || socio.numero_socio === undefined ? 'S/D' : String(socio.numero_socio);
  }

  abrirAlta(): void {
    if (this.altaDialog) { return; }
    this.busqueda = '';
    this.candidatos = [];
    this.terminoConsultado = '';
    this.socioSeleccionado = null;
    this.altaDialog = this.dialog.open(this.altaTemplate, {
      ...DIALOGO_BASE, width: '36rem', ariaLabelledBy: 'alta-title', autoFocus: '#alta-busqueda'
    });
    this.altaDialog.afterClosed().pipe(takeUntil(this.destroy$)).subscribe(() => this.altaDialog = null);
  }

  /**
   * Recibe lo que emite el input: texto mientras se escribe, o el candidato elegido en el
   * autocompletado. Sólo el texto dispara una búsqueda; la selección se maneja en `seleccionar`.
   */
  buscar(termino: string | CandidatoTribunalDTO | null): void {
    if (termino !== null && typeof termino !== 'string') { return; }
    const texto: string = typeof termino === 'string' ? termino : '';
    this.socioSeleccionado = null;
    this.busqueda$.next(texto.trim());
  }

  seleccionar(socio: CandidatoTribunalDTO): void {
    this.socioSeleccionado = socio;
    this.busqueda = socio;
  }

  readonly mostrarSocio = (socio: CandidatoTribunalDTO | string | null): string => {
    if (!socio) { return ''; }
    if (typeof socio === 'string') { return socio; }
    return `${socio.last_name}, ${socio.first_name} (N° de Socio ${this.numeroSocio(socio)})`;
  };

  get sinCoincidencias(): boolean {
    return !this.buscandoCandidatos && !!this.terminoConsultado && this.candidatos.length === 0
      && !this.socioSeleccionado;
  }

  confirmarAlta(): void {
    if (!this.socioSeleccionado || this.procesandoMiembro) { return; }
    this.procesandoMiembro = true;
    this.api.asignarMiembroTribunal(this.socioSeleccionado.id).pipe(takeUntil(this.destroy$)).subscribe({
      next: miembro => {
        this.procesandoMiembro = false;
        this.altaDialog?.close();
        this.notifications.success(`${miembro.first_name} ${miembro.last_name} ahora integra el Tribunal de Disciplina.`);
        this.cargarMiembros();
      },
      error: err => {
        this.procesandoMiembro = false;
        this.notifications.error(httpErrorMessage(err, 'No se pudo designar al socio.'));
      }
    });
  }

  cerrarAlta(): void { this.altaDialog?.close(); }

  pedirRevocacion(miembro: MiembroTribunalDTO): void {
    if (this.revocarDialog) { return; }
    this.miembroARevocar = miembro;
    this.revocarDialog = this.dialog.open(this.revocarTemplate, {
      ...DIALOGO_BASE, width: '32rem', ariaLabelledBy: 'revocar-title', autoFocus: '.btn-cancelar-revocar'
    });
    this.revocarDialog.afterClosed().pipe(takeUntil(this.destroy$)).subscribe(() => this.revocarDialog = null);
  }

  cerrarRevocacion(): void { this.revocarDialog?.close(); }

  confirmarRevocacion(): void {
    const miembro = this.miembroARevocar;
    if (!miembro || this.procesandoMiembro) { return; }
    this.procesandoMiembro = true;
    this.api.revocarMiembroTribunal(miembro.id).pipe(takeUntil(this.destroy$)).subscribe({
      next: () => {
        this.procesandoMiembro = false;
        this.revocarDialog?.close();
        this.miembros = this.miembros.filter(m => m.id !== miembro.id);
        this.notifications.success(`${miembro.first_name} ${miembro.last_name} volvió a ser Socio Ordinario.`);
      },
      error: err => {
        this.procesandoMiembro = false;
        this.notifications.error(httpErrorMessage(err, 'No se pudo revocar el rol.'));
      }
    });
  }
}
