import { CommonModule } from '@angular/common';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { of, throwError } from 'rxjs';

import {
  ExpedienteApiService,
  ExpedienteRankingDetalle
} from '../../services/expediente-api.service';
import { ExpedientesSocioDialogComponent } from './expedientes-socio-dialog.component';

describe('ExpedientesSocioDialogComponent', () => {
  let component: ExpedientesSocioDialogComponent;
  let fixture: ComponentFixture<ExpedientesSocioDialogComponent>;
  let expedienteApiSpy: jasmine.SpyObj<ExpedienteApiService>;
  let dialogRefSpy: jasmine.SpyObj<MatDialogRef<ExpedientesSocioDialogComponent>>;

  const expedientesMock: ExpedienteRankingDetalle[] = [
    {
      id: 1,
      numero: 'EXP-0001/2026',
      motivo: 'Falta reglamentaria',
      puntos: '-2.00',
      estado: 'creado',
      urgencia: 'normal',
      urgencia_display: 'Normal',
      created_at: '2026-10-11T08:00:00Z'
    },
    {
      id: 2,
      numero: 'EXP-0002/2026',
      motivo: 'Reconocimiento institucional',
      puntos: '3.00',
      estado: 'emitido',
      urgencia: 'baja',
      urgencia_display: 'Baja',
      created_at: '2026-10-10T08:00:00Z'
    }
  ];

  beforeEach(async () => {
    expedienteApiSpy = jasmine.createSpyObj(
      'ExpedienteApiService',
      ['listarPorSocio']
    );

    dialogRefSpy = jasmine.createSpyObj(
      'MatDialogRef',
      ['close']
    );

    expedienteApiSpy.listarPorSocio.and.returnValue(of(expedientesMock));

    await TestBed.configureTestingModule({
      imports: [CommonModule],
      declarations: [ExpedientesSocioDialogComponent],
      providers: [
        {
          provide: ExpedienteApiService,
          useValue: expedienteApiSpy
        },
        {
          provide: MatDialogRef,
          useValue: dialogRefSpy
        },
        {
          provide: MAT_DIALOG_DATA,
          useValue: {
            legajo: '74907',
            nombreSocio: 'Lucas Gastiaburu'
          }
        }
      ]
    }).compileComponents();

    fixture = TestBed.createComponent(ExpedientesSocioDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe consultar los expedientes usando el legajo recibido', () => {
    expect(expedienteApiSpy.listarPorSocio).toHaveBeenCalledWith('74907');
    expect(component.expedientes).toEqual(expedientesMock);
    expect(component.cargando).toBeFalse();
    expect(component.error).toBeNull();
  });

  it('debe mostrar los expedientes recibidos', () => {
    const contenido = fixture.nativeElement.textContent as string;

    expect(contenido).toContain('Detalle de expedientes');
    expect(contenido).toContain('1/2026');
    expect(contenido).toContain('Falta reglamentaria');
    expect(contenido).toContain('2/2026');
    expect(contenido).toContain('Reconocimiento institucional');
  });

  it('debe mostrar el estado vacío y los mensajes de carga con la terminología de expedientes', () => {
    expedienteApiSpy.listarPorSocio.and.returnValue(of([]));

    component.cargarExpedientes();
    fixture.detectChanges();

    expect(fixture.nativeElement.textContent).toContain(
      'Este socio no posee expedientes registrados.'
    );
    expect(fixture.nativeElement.textContent).not.toContain('causas');
  });

  it('debe informar cuando el socio no posee expedientes', () => {
    expedienteApiSpy.listarPorSocio.and.returnValue(of([]));

    component.cargarExpedientes();
    fixture.detectChanges();

    expect(component.expedientes).toEqual([]);
    expect(fixture.nativeElement.textContent).toContain(
      'Este socio no posee expedientes registrados.'
    );
  });

  it('debe manejar un error al cargar los expedientes', () => {
    expedienteApiSpy.listarPorSocio.and.returnValue(
      throwError(() => new Error('Error al cargar'))
    );

    component.cargarExpedientes();
    fixture.detectChanges();

    expect(component.error).toBe(
      'No se pudieron cargar los expedientes del socio.'
    );

    expect(fixture.nativeElement.textContent).toContain(
      'No se pudieron cargar los expedientes del socio.'
    );
  });

  it('debe convertir los puntos recibidos a número', () => {
    expect(component.puntosNumero(expedientesMock[0])).toBe(-2);
    expect(component.puntosNumero(expedientesMock[1])).toBe(3);
  });

  it('debe cerrar el modal', () => {
    component.cerrar();

    expect(dialogRefSpy.close).toHaveBeenCalled();
  });
});
