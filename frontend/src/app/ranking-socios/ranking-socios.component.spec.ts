import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { of, throwError } from 'rxjs';

import { RankingSociosComponent } from './ranking-socios.component';
import { RankingService } from '../services/ranking.service';
import { NotificationService } from '../services/notification.service';
import { RankingSocio } from './ranking-socio.model';
import { RANKING_THRESHOLDS } from './ranking-thresholds';
import { ExpedientesSocioDialogComponent } from './expedientes-socio-dialog/expedientes-socio-dialog.component';

describe('RankingSociosComponent', () => {
  let component: RankingSociosComponent;
  let fixture: ComponentFixture<RankingSociosComponent>;
  let rankingServiceSpy: jasmine.SpyObj<RankingService>;
  let dialogSpy: jasmine.SpyObj<MatDialog>;
  let notifications: jasmine.SpyObj<NotificationService>;

  const sociosMock: RankingSocio[] = [
    {
      id: '1',
      legajo: '1001',
      nombre: 'Ana',
      apellido: 'Gómez',
      categoria: 'ACTIVO',
      subcomision: 'Cómputos',
      grupo: 'G2',
      saldo: 5,
      saldoHistorico: 5,
      saldoPuntajeGeneral: 5,
      diferencia: 0,
      reconciliado: true
    },
    {
      id: '2',
      legajo: '1002',
      nombre: 'Bruno',
      apellido: 'Pérez',
      categoria: 'PASIVO',
      subcomision: 'Deportes',
      grupo: 'G1',
      saldo: -1,
      saldoHistorico: -1,
      saldoPuntajeGeneral: -1,
      diferencia: 0,
      reconciliado: true
    }
  ];

  beforeEach(async () => {
    rankingServiceSpy = jasmine.createSpyObj('RankingService', ['obtenerRanking']);
    dialogSpy = jasmine.createSpyObj('MatDialog', ['open']);
    notifications = jasmine.createSpyObj('NotificationService', ['error']);

    rankingServiceSpy.obtenerRanking.and.returnValue(of(sociosMock));

    await TestBed.configureTestingModule({
      imports: [FormsModule],
      declarations: [RankingSociosComponent],
      providers: [
        { provide: NotificationService, useValue: notifications },
        { provide: RankingService, useValue: rankingServiceSpy },
        { provide: MatDialog, useValue: dialogSpy }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(RankingSociosComponent);
    component = fixture.componentInstance;
  });

  it('debería crear el componente', () => {
    expect(component).toBeTruthy();
  });

  it('notifica un fallo sin repetirlo en la tabla y permite reintentar', () => {
    rankingServiceSpy.obtenerRanking.and.returnValue(throwError(() => ({ status: 500 })));
    fixture.detectChanges();
    expect(notifications.error).toHaveBeenCalledOnceWith(
      'No se pudo cargar el ranking. Intentá nuevamente.'
    );
    expect(fixture.nativeElement.textContent).not.toContain('No se pudo cargar el ranking');
    const retry = fixture.nativeElement.querySelector(
      '[aria-label="Reintentar carga del ranking"]'
    ) as HTMLButtonElement;
    expect(retry).toBeTruthy();
    rankingServiceSpy.obtenerRanking.and.returnValue(of(sociosMock));
    retry.click();
    fixture.detectChanges();
    expect(component.socios.length).toBe(2);
  });

  it('debería cargar socios desde RankingService', () => {
    fixture.detectChanges();

    expect(component.socios.length).toBe(2);
    expect(component.cargando).toBeFalse();
    expect(component.error).toBeNull();
    expect(component.subcomisiones).toEqual(['Cómputos', 'Deportes']);
    expect(component.grupos).toEqual(['G1', 'G2']);
  });

  it('debería mostrar la acción de Expedientes con su etiqueta accesible', () => {
    fixture.detectChanges();

    const contenido = fixture.nativeElement.textContent as string;
    const boton = fixture.nativeElement.querySelector(
      '[aria-label="Ver expedientes de Ana Gómez"]'
    ) as HTMLButtonElement;

    expect(contenido).toContain('Expedientes');
    expect(contenido).not.toContain('Causas');
    expect(boton).toBeTruthy();
  });

  it('debería renderizar exactamente las 8 columnas canónicas en orden', () => {
    fixture.detectChanges();
    const ths: NodeListOf<HTMLTableHeaderCellElement> =
      fixture.nativeElement.querySelectorAll('thead th');

    expect(ths.length).toBe(8);
    const titulos = Array.from(ths).map((th) => th.textContent?.trim().replace(/[↑↓▲▼]/g, '').trim());
    expect(titulos[0]).toContain('Posición');
    expect(titulos[1]).toContain('Socio');
    expect(titulos[2]).toContain('N° de Socio');
    expect(titulos[3]).toContain('Categoría');
    expect(titulos[4]).toContain('Grupo');
    expect(titulos[5]).toContain('Subcomisión');
    expect(titulos[6]).toContain('Saldo');
    expect(titulos[7]).toContain('Acciones');
  });

  it('debería formatear saldo numéricamente con signo y 2 decimales sin texto pts ni badges', () => {
    rankingServiceSpy.obtenerRanking.and.returnValue(
      of([
        { ...sociosMock[0], id: '1', apellido: 'Alonso', grupo: 'G1', saldo: 4.5 },
        { ...sociosMock[0], id: '2', apellido: 'Bustos', grupo: 'G1', saldo: -7.25 },
        { ...sociosMock[0], id: '3', apellido: 'Castro', grupo: 'G1', saldo: 0 }
      ])
    );
    fixture.detectChanges();

    const filas: NodeListOf<HTMLTableRowElement> =
      fixture.nativeElement.querySelectorAll('tbody tr');
    expect(filas.length).toBe(3);

    // Celda 7 (índice 6) es Saldo
    const celda1 = filas[0].cells[6].textContent?.trim();
    const celda2 = filas[1].cells[6].textContent?.trim();
    const celda3 = filas[2].cells[6].textContent?.trim();

    expect(celda1).toContain('+4.50');
    expect(celda1).not.toContain('pts');
    expect(celda1).not.toContain('Habilitado Regular');

    expect(celda2).toContain('-7.25');
    expect(celda2).not.toContain('pts');

    expect(celda3).toContain('0.00');
    expect(celda3).not.toContain('+0.00');
  });

  it('debería asignar clases de alerta .row-cese (<= -10) y .row-alerta (-10 < saldo <= -7) según RANKING_THRESHOLDS', () => {
    expect(RANKING_THRESHOLDS.cese).toBe(-10);
    expect(RANKING_THRESHOLDS.alerta).toBe(-7);

    const sCese1 = { ...sociosMock[0], saldo: -10 };
    const sCese2 = { ...sociosMock[0], saldo: -14.5 };
    const sAlerta1 = { ...sociosMock[0], saldo: -7 };
    const sAlerta2 = { ...sociosMock[0], saldo: -9.99 };
    const sNormal1 = { ...sociosMock[0], saldo: -6.99 };
    const sNormal2 = { ...sociosMock[0], saldo: 3 };

    expect(component.getRowClass(sCese1)).toBe('row-cese');
    expect(component.getRowClass(sCese2)).toBe('row-cese');
    expect(component.getRowClass(sAlerta1)).toBe('row-alerta');
    expect(component.getRowClass(sAlerta2)).toBe('row-alerta');
    expect(component.getRowClass(sNormal1)).toBe('');
    expect(component.getRowClass(sNormal2)).toBe('');

    rankingServiceSpy.obtenerRanking.and.returnValue(
      of([sCese1, sAlerta1, sNormal2])
    );
    fixture.detectChanges();

    const filas: NodeListOf<HTMLTableRowElement> =
      fixture.nativeElement.querySelectorAll('tbody tr');
    expect(filas[0].classList.contains('row-cese')).toBeTrue();
    expect(filas[1].classList.contains('row-alerta')).toBeTrue();
    expect(filas[2].classList.contains('row-cese')).toBeFalse();
    expect(filas[2].classList.contains('row-alerta')).toBeFalse();
  });

  it('debería precalcular posición fija sobre el padrón completo y mantenerla inmutable al filtrar o reordenar', () => {
    rankingServiceSpy.obtenerRanking.and.returnValue(
      of([
        { ...sociosMock[0], id: '1', nombre: 'Carlos', apellido: 'Zeta', saldo: 10 },
        { ...sociosMock[0], id: '2', nombre: 'Ana', apellido: 'Gómez', saldo: 5 },
        { ...sociosMock[0], id: '3', nombre: 'Beto', apellido: 'Alonso', saldo: 5 },
        { ...sociosMock[0], id: '4', nombre: 'Damián', apellido: 'Díaz', saldo: -2 }
      ])
    );
    fixture.detectChanges();

    // Posiciones esperadas por saldo desc, desempate apellido asc, nombre asc:
    // 1: Carlos Zeta (10) -> Posición 1
    // 2: Beto Alonso (5)  -> Posición 2
    // 3: Ana Gómez (5)    -> Posición 3
    // 4: Damián Díaz (-2) -> Posición 4
    const s1 = component.socios.find((s) => s.id === '1');
    const s2 = component.socios.find((s) => s.id === '2');
    const s3 = component.socios.find((s) => s.id === '3');
    const s4 = component.socios.find((s) => s.id === '4');

    expect(s1?.posicion).toBe(1);
    expect(s3?.posicion).toBe(2);
    expect(s2?.posicion).toBe(3);
    expect(s4?.posicion).toBe(4);

    // Reordenar por saldo ascendente no altera s.posicion
    component.alternarOrden('saldo');
    component.alternarOrden('saldo'); // 'asc'
    expect(component.sortDir).toBe('asc');
    expect(s1?.posicion).toBe(1);
    expect(s4?.posicion).toBe(4);

    // Filtrar tampoco altera la posición
    component.filtroTexto = 'Damián';
    expect(component.sociosOrdenados.length).toBe(1);
    expect(component.sociosOrdenados[0].posicion).toBe(4);
  });

  it('debería filtrar socios por categoría', () => {
    fixture.detectChanges();

    component.filtroCategoria = 'ACTIVO';

    expect(component.sociosOrdenados.length).toBe(1);
    expect(component.sociosOrdenados[0].nombre).toBe('Ana');
  });

  it('debería filtrar socios por grupo dinámico', () => {
    rankingServiceSpy.obtenerRanking.and.returnValue(
      of([
        { ...sociosMock[0], id: '1', grupo: 'G58' },
        { ...sociosMock[0], id: '2', grupo: 'G60' },
        { ...sociosMock[0], id: '3', grupo: null }
      ])
    );
    fixture.detectChanges();

    expect(component.grupos).toEqual(['G58', 'G60']);

    component.filtroGrupo = 'G58';
    expect(component.sociosOrdenados.length).toBe(1);
    expect(component.sociosOrdenados[0].id).toBe('1');

    component.filtroGrupo = 'SIN_GRUPO';
    expect(component.sociosOrdenados.length).toBe(1);
    expect(component.sociosOrdenados[0].id).toBe('3');

    component.limpiarFiltros();
    expect(component.filtroGrupo).toBe('');
    expect(component.sociosOrdenados.length).toBe(3);
  });

  it('debería filtrar socios por texto', () => {
    fixture.detectChanges();

    component.filtroTexto = 'bruno';

    expect(component.sociosOrdenados.length).toBe(1);
    expect(component.sociosOrdenados[0].apellido).toBe('Pérez');
  });

  it('onFiltroChange debería actualizar filtroTexto y resetear paginaActual a 1', () => {
    component.paginaActual = 2;
    component.onFiltroChange('computos');
    expect(component.filtroTexto).toBe('computos');
    expect(component.paginaActual).toBe(1);
  });

  it('debería ordenar por defecto por grupo numérico y desempatar por apellido y nombre', () => {
    const crearSocio = (
      id: string,
      apellido: string,
      nombre: string,
      saldo: number,
      grupo: string | null
    ): RankingSocio => ({
      id,
      legajo: id,
      apellido,
      nombre,
      saldo,
      grupo,
      categoria: 'ACTIVO',
      subcomision: 'Cómputos'
    });

    rankingServiceSpy.obtenerRanking.and.returnValue(
      of([
        crearSocio('1', 'Zapata', 'Ana', 5, 'G2'),
        crearSocio('2', 'Alonso', 'Bruno', 5, 'G1'),
        crearSocio('3', 'Alonso', 'Ana', 5, 'G1'),
        crearSocio('4', 'Zapata', 'Zoe', 10, 'G1'),
        crearSocio('5', 'Abad', 'Ana', -2, null)
      ])
    );

    fixture.detectChanges();

    expect(component.sociosOrdenados.map((s) => s.id)).toEqual([
      '3', '2', '4', '1', '5'
    ]);
  });

  it('debería soportar ordenamiento universal en todas las columnas', () => {
    rankingServiceSpy.obtenerRanking.and.returnValue(
      of([
        { ...sociosMock[0], id: '1', legajo: '105', nombre: 'Zoe', apellido: 'Alonso', categoria: 'PASIVO', subcomision: 'Deportes', grupo: 'G2', saldo: 1 },
        { ...sociosMock[0], id: '2', legajo: '98', nombre: 'Ana', apellido: 'Bustos', categoria: 'ACTIVO', subcomision: 'Buffet', grupo: 'G10', saldo: 10 },
        { ...sociosMock[0], id: '3', legajo: '1002', nombre: 'Carlos', apellido: 'Castro', categoria: 'ACTIVO', subcomision: 'Cómputos', grupo: 'G1', saldo: -5 }
      ])
    );
    fixture.detectChanges();

    // 1. Ordenar por legajo numérico (asc: 98, 105, 1002)
    component.alternarOrden('legajo');
    expect(component.sortKey).toBe('legajo');
    expect(component.sortDir).toBe('asc');
    expect(component.sociosOrdenados.map((s) => s.id)).toEqual(['2', '1', '3']);

    // Legajo desc
    component.alternarOrden('legajo');
    expect(component.sortDir).toBe('desc');
    expect(component.sociosOrdenados.map((s) => s.id)).toEqual(['3', '1', '2']);

    // 2. Ordenar por socio (apellido asc)
    component.alternarOrden('socio');
    expect(component.sortKey).toBe('socio');
    expect(component.sortDir).toBe('asc');
    expect(component.sociosOrdenados.map((s) => s.id)).toEqual(['1', '2', '3']);

    // 3. Ordenar por categoría (ACTIVO asc -> PASIVO)
    component.alternarOrden('categoria');
    expect(component.sortKey).toBe('categoria');
    expect(component.sociosOrdenados.map((s) => s.id)).toEqual(['2', '3', '1']);

    // 4. Ordenar por subcomisión
    component.alternarOrden('subcomision');
    expect(component.sortKey).toBe('subcomision');
    expect(component.sociosOrdenados.map((s) => s.id)).toEqual(['2', '3', '1']);

    // 5. Ordenar por grupo numérico (G1, G2, G10)
    component.alternarOrden('grupo');
    expect(component.sortKey).toBe('grupo');
    expect(component.sociosOrdenados.map((s) => s.id)).toEqual(['3', '1', '2']);
  });

  it('debería alternar saldo descendente, ascendente y volver al orden por grupo', () => {
    fixture.detectChanges();
    component.paginaActual = 2;

    component.alternarOrdenSaldo();
    expect(component.ordenSaldo).toBe('desc');
    expect(component.paginaActual).toBe(1);

    component.paginaActual = 2;
    component.alternarOrdenSaldo();
    expect(component.ordenSaldo).toBe('asc');
    expect(component.paginaActual).toBe(1);

    component.paginaActual = 2;
    component.alternarOrdenSaldo();
    expect(component.ordenSaldo).toBeNull();
    expect(component.paginaActual).toBe(1);
  });

  it('debería paginar correctamente y soportar ver todas las filas (tamanoPagina = 0)', () => {
    const sociosPagina: RankingSocio[] = Array.from({ length: 13 }, (_, i) => ({
      ...sociosMock[0],
      id: String(i + 1),
      legajo: String(2001 + i),
      saldo: 13 - i
    }));
    rankingServiceSpy.obtenerRanking.and.returnValue(of(sociosPagina));
    fixture.detectChanges();

    expect(component.totalPaginas).toBe(2);
    expect(component.sociosPaginados.length).toBe(10);
    expect(component.textoContador).toBe('Mostrando 1–10 de 13 socios');

    component.cambiarPagina(2);
    expect(component.paginaActual).toBe(2);
    expect(component.sociosPaginados.length).toBe(3);
    expect(component.textoContador).toBe('Mostrando 11–13 de 13 socios');

    // Cambiar a todas las filas
    component.cambiarTamanoPagina(0);
    expect(component.tamanoPagina).toBe(0);
    expect(component.totalPaginas).toBe(1);
    expect(component.sociosPaginados.length).toBe(13);
    expect(component.textoContador).toBe('Mostrando 1–13 de 13 socios');
  });

  it('abrirExpedientesSocio debe abrir el diálogo con legajo, nombre y saldo correspondiente', () => {
    fixture.detectChanges();
    const socio = component.socios[0];
    component.abrirExpedientesSocio(socio);

    expect(dialogSpy.open).toHaveBeenCalledWith(ExpedientesSocioDialogComponent, {
      width: '100%',
      maxWidth: '700px',
      data: {
        legajo: '1001',
        nombreSocio: 'Ana Gómez',
        saldo: 5
      }
    });
  });

  it('onRowKeyDown debe abrir expedientes al presionar Enter o Space', () => {
    fixture.detectChanges();
    const socio = component.socios[0];

    const enterEvent = new KeyboardEvent('keydown', { key: 'Enter' });
    spyOn(enterEvent, 'preventDefault');
    component.onRowKeyDown(enterEvent, socio);
    expect(enterEvent.preventDefault).toHaveBeenCalled();
    expect(dialogSpy.open).toHaveBeenCalledWith(ExpedientesSocioDialogComponent, jasmine.any(Object));

    dialogSpy.open.calls.reset();

    const spaceEvent = new KeyboardEvent('keydown', { key: ' ' });
    spyOn(spaceEvent, 'preventDefault');
    component.onRowKeyDown(spaceEvent, socio);
    expect(spaceEvent.preventDefault).toHaveBeenCalled();
    expect(dialogSpy.open).toHaveBeenCalledWith(ExpedientesSocioDialogComponent, jasmine.any(Object));
  });

  it('onRowKeyDown con ArrowDown debe prevenir scroll y dar foco a la siguiente fila', () => {
    fixture.detectChanges();
    const socio = component.socios[0];
    const nextTr = document.createElement('tr');
    spyOn(nextTr, 'focus');

    const currentTr = document.createElement('tr');
    const tbody = document.createElement('tbody');
    tbody.appendChild(currentTr);
    tbody.appendChild(nextTr);

    const event = new KeyboardEvent('keydown', { key: 'ArrowDown' });
    spyOn(event, 'preventDefault');
    Object.defineProperty(event, 'target', { value: currentTr });

    component.onRowKeyDown(event, socio);

    expect(event.preventDefault).toHaveBeenCalled();
    expect(nextTr.focus).toHaveBeenCalled();
  });

  it('onRowKeyDown con ArrowUp debe prevenir scroll y dar foco a la fila anterior', () => {
    fixture.detectChanges();
    const socio = component.socios[1];
    const prevTr = document.createElement('tr');
    spyOn(prevTr, 'focus');

    const currentTr = document.createElement('tr');
    const tbody = document.createElement('tbody');
    tbody.appendChild(prevTr);
    tbody.appendChild(currentTr);

    const event = new KeyboardEvent('keydown', { key: 'ArrowUp' });
    spyOn(event, 'preventDefault');
    Object.defineProperty(event, 'target', { value: currentTr });

    component.onRowKeyDown(event, socio);

    expect(event.preventDefault).toHaveBeenCalled();
    expect(prevTr.focus).toHaveBeenCalled();
  });

  it('debería alternar entre pestaña general y alertas disciplinarias con cabecera teal', () => {
    rankingServiceSpy.obtenerRanking.and.returnValue(
      of([
        { ...sociosMock[0], id: '1', apellido: 'Gómez', saldo: 5.0 },
        { ...sociosMock[0], id: '2', apellido: 'Pérez', saldo: -8.0 },
        { ...sociosMock[0], id: '3', apellido: 'López', saldo: -10.5 }
      ])
    );
    component.ngOnInit();
    fixture.detectChanges();

    expect(component.tabActiva).toBe('general');
    expect(component.cantidadSociosEnAlerta).toBe(2);
    expect(component.sociosOrdenados.length).toBe(3);

    const cabeceraTeal = fixture.nativeElement.querySelector('.card-header-tabs-teal');
    expect(cabeceraTeal).toBeTruthy();

    component.setTab('alertas');
    fixture.detectChanges();

    expect(component.tabActiva).toBe('alertas');
    expect(component.sociosOrdenados.length).toBe(2);
    expect(component.sociosOrdenados.every((s) => s.saldo <= -7)).toBeTrue();

    component.setTab('general');
    fixture.detectChanges();
    expect(component.sociosOrdenados.length).toBe(3);
  });
});
