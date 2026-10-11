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
      ['listarPorLegajo']
    );

    dialogRefSpy = jasmine.createSpyObj(
      'MatDialogRef',
      ['close']
    );

    expedienteApiSpy.listarPorLegajo.and.returnValue(of(expedientesMock));

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

  it('debe consultar las causas usando el legajo recibido', () => {
    expect(expedienteApiSpy.listarPorLegajo).toHaveBeenCalledWith('74907');
    expect(component.expedientes).toEqual(expedientesMock);
    expect(component.cargando).toBeFalse();
    expect(component.error).toBeNull();
  });

  it('debe mostrar los expedientes recibidos', () => {
    const contenido = fixture.nativeElement.textContent as string;

    expect(contenido).toContain('EXP-0001/2026');
    expect(contenido).toContain('Falta reglamentaria');
    expect(contenido).toContain('EXP-0002/2026');
    expect(contenido).toContain('Reconocimiento institucional');
  });

  it('debe informar cuando el socio no posee causas', () => {
    expedienteApiSpy.listarPorLegajo.and.returnValue(of([]));

    component.cargarExpedientes();
    fixture.detectChanges();

    expect(component.expedientes).toEqual([]);
    expect(fixture.nativeElement.textContent).toContain(
      'Este socio no posee causas registradas.'
    );
  });

  it('debe manejar un error 403', () => {
    expedienteApiSpy.listarPorLegajo.and.returnValue(
      throwError(() => ({ status: 403 }))
    );

    component.cargarExpedientes();
    fixture.detectChanges();

    expect(component.error).toBe(
      'No posee autorizaci?n para consultar las causas de este socio.'
    );

    expect(fixture.nativeElement.textContent).toContain(
      'No posee autorizaci?n para consultar las causas de este socio.'
    );
  });

  it('debe convertir los puntos recibidos a n?mero', () => {
    expect(component.puntosNumero(expedientesMock[0])).toBe(-2);
    expect(component.puntosNumero(expedientesMock[1])).toBe(3);
  });

  it('debe cerrar el modal', () => {
    component.cerrar();

    expect(dialogRefSpy.close).toHaveBeenCalled();
  });
});
