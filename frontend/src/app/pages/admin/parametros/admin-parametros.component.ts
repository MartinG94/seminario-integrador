import { Component, OnDestroy, OnInit, TemplateRef, ViewChild } from '@angular/core';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { of, Subject } from 'rxjs';
import { catchError, debounceTime, distinctUntilChanged, map, switchMap, takeUntil } from 'rxjs/operators';

import {
  AdminApiService, CambioParametroDTO, CategoriaParametro, MiembroTribunalDTO,
  ParametroSistemaDTO, ValorParametro
} from '../../../services/admin-api.service';
import { NotificationService, httpErrorMessage } from '../../../services/notification.service';
import { SocioApiService, SocioListItemDTO } from '../../../services/socio-api.service';

interface TarjetaParametros {
  categoria: CategoriaParametro;
  titulo: string;
  icono: string;
}

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

  parametros: ParametroSistemaDTO[] = [];
  borradores: Record<string, ValorParametro> = {};
  guardando: Record<string, boolean> = {};
  cargandoParametros = false;
  errorParametros = '';

  historialClave: string | null = null;
  historial: CambioParametroDTO[] = [];
  @ViewChild('historialTemplate', { static: true }) historialTemplate: TemplateRef<unknown>;
  private historialDialog: MatDialogRef<unknown> | null = null;

  miembros: MiembroTribunalDTO[] = [];
  cargandoMiembros = false;
  errorMiembros = '';
  @ViewChild('altaTemplate', { static: true }) altaTemplate: TemplateRef<unknown>;
  @ViewChild('revocarTemplate', { static: true }) revocarTemplate: TemplateRef<unknown>;
  private altaDialog: MatDialogRef<unknown> | null = null;
  private revocarDialog: MatDialogRef<unknown> | null = null;
  busqueda = '';
  candidatos: SocioListItemDTO[] = [];
  socioSeleccionado: SocioListItemDTO | null = null;
  miembroARevocar: MiembroTribunalDTO | null = null;
  procesandoMiembro = false;

  private readonly busqueda$ = new Subject<string>();
  private readonly destroy$ = new Subject<void>();

  constructor(
    private api: AdminApiService,
    private socioApi: SocioApiService,
    private notifications: NotificationService,
    private dialog: MatDialog
  ) {}

  ngOnInit(): void {
    this.busqueda$.pipe(
      debounceTime(300),
      distinctUntilChanged(),
      switchMap(termino => termino.trim().length < 2
        ? of([] as SocioListItemDTO[])
        : this.socioApi.searchSocios(termino).pipe(
          map(respuesta => respuesta.results || []),
          catchError(() => of([] as SocioListItemDTO[]))
        )),
      takeUntil(this.destroy$)
    ).subscribe(socios => {
      this.candidatos = socios.filter(s => s.role === 'SOCIO');
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

  guardar(p: ParametroSistemaDTO): void {
    if (!this.tieneCambios(p) || this.guardando[p.clave]) { return; }
    const borrador = this.borradores[p.clave];
    if (borrador === null || borrador === '' || (typeof borrador === 'number' && Number.isNaN(borrador))) {
      this.notifications.error(`Indicá un valor para ${p.etiqueta}.`);
      return;
    }
    const valor = p.tipo === 'DECIMAL' ? String(borrador) : borrador;
    this.guardando[p.clave] = true;
    this.api.actualizarParametro(p.clave, valor).pipe(takeUntil(this.destroy$)).subscribe({
      next: actualizado => {
        this.guardando[p.clave] = false;
        this.parametros = this.parametros.map(x => x.clave === actualizado.clave ? actualizado : x);
        this.borradores[actualizado.clave] = this.aBorrador(actualizado);
        this.notifications.success(`${actualizado.etiqueta} actualizado.`);
      },
      error: err => {
        this.guardando[p.clave] = false;
        this.notifications.error(httpErrorMessage(err, `No se pudo actualizar ${p.etiqueta}.`));
      }
    });
  }

  descartar(p: ParametroSistemaDTO): void {
    this.borradores[p.clave] = this.aBorrador(p);
  }

  formatearValor(p: ParametroSistemaDTO, valor: ValorParametro): string {
    if (valor === null || valor === undefined || valor === '') { return '—'; }
    if (p.tipo === 'BOOLEAN') { return valor ? 'Sí' : 'No'; }
    if (p.tipo === 'DECIMAL') { return String(Number(valor)).replace('.', ','); }
    return String(valor);
  }

  get parametroHistorial(): ParametroSistemaDTO | undefined {
    return this.parametros.find(p => p.clave === this.historialClave);
  }

  verHistorial(p: ParametroSistemaDTO): void {
    this.historialClave = p.clave;
    this.historial = [];
    this.api.historialParametro(p.clave).pipe(takeUntil(this.destroy$)).subscribe({
      next: cambios => {
        this.historial = cambios;
        this.historialDialog = this.dialog.open(this.historialTemplate, {
          width: '44rem', maxWidth: 'calc(100vw - 2rem)', ariaLabelledBy: 'historial-title',
          restoreFocus: true, closeOnNavigation: true
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

  abrirAlta(): void {
    this.busqueda = '';
    this.candidatos = [];
    this.socioSeleccionado = null;
    this.altaDialog = this.dialog.open(this.altaTemplate, {
      width: '36rem', maxWidth: 'calc(100vw - 2rem)', ariaLabelledBy: 'alta-title',
      autoFocus: '#alta-busqueda', restoreFocus: true, closeOnNavigation: true
    });
  }

  buscar(termino: string): void {
    this.socioSeleccionado = null;
    this.busqueda$.next(termino || '');
  }

  seleccionar(socio: SocioListItemDTO): void {
    this.socioSeleccionado = socio;
    this.busqueda = `${socio.last_name}, ${socio.first_name} (${socio.legajo})`;
  }

  mostrarSocio(socio: SocioListItemDTO | string | null): string {
    if (!socio) { return ''; }
    if (typeof socio === 'string') { return socio; }
    return `${socio.last_name}, ${socio.first_name} (${socio.legajo})`;
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
    this.miembroARevocar = miembro;
    this.revocarDialog = this.dialog.open(this.revocarTemplate, {
      width: '32rem', maxWidth: 'calc(100vw - 2rem)', ariaLabelledBy: 'revocar-title',
      restoreFocus: true, closeOnNavigation: true
    });
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
