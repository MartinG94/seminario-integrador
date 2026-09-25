import { ComponentFixture, TestBed } from '@angular/core/testing';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { of, throwError } from 'rxjs';

import { SocioApiService, SocioLegajoDTO } from '../../services/socio-api.service';
import { SocioLegajoDialogComponent } from './socio-legajo-dialog.component';

describe('SocioLegajoDialogComponent', () => {
  let component: SocioLegajoDialogComponent;
  let fixture: ComponentFixture<SocioLegajoDialogComponent>;
  let socioApiServiceSpy: jasmine.SpyObj<SocioApiService>;
  let dialogRefSpy: jasmine.SpyObj<MatDialogRef<SocioLegajoDialogComponent>>;

  const mockLegajo: SocioLegajoDTO = {
    id: 1,
    legajo: '74907',
    first_name: 'Lucas',
    last_name: 'Gastiaburu',
    email: '74907@aveit.test',
    role: 'SOCIO',
    category: 'ACTIVE',
    category_display: 'Activo',
    subcomision: 'Cómputos',
    social_year: 4,
    is_enabled: true,
    points_balance: 3.5
  };

  beforeEach(async () => {
    socioApiServiceSpy = jasmine.createSpyObj('SocioApiService', ['getLegajo']);
    dialogRefSpy = jasmine.createSpyObj('MatDialogRef', ['close']);

    socioApiServiceSpy.getLegajo.and.returnValue(of(mockLegajo));

    await TestBed.configureTestingModule({
      declarations: [SocioLegajoDialogComponent],
      providers: [
        { provide: SocioApiService, useValue: socioApiServiceSpy },
        { provide: MatDialogRef, useValue: dialogRefSpy },
        { provide: MAT_DIALOG_DATA, useValue: { socioId: 1, nombreSocio: 'Lucas Gastiaburu' } }
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(SocioLegajoDialogComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe cargar los datos del legajo al inicializar (CA2)', () => {
    expect(socioApiServiceSpy.getLegajo).toHaveBeenCalledWith(1);
    expect(component.cargando).toBeFalse();
    expect(component.legajo).toEqual(mockLegajo);
    expect(component.errorHttp).toBeNull();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('74907');
    expect(compiled.textContent).toContain('Gastiaburu');
    expect(compiled.textContent).toContain('Cómputos');
    expect(compiled.textContent).toContain('Saldo de Puntos');
    expect(compiled.textContent).toContain('3.5 pts');
  });

  it('debe manejar error 403 Forbidden cuando un socio intenta ver un legajo ajeno (CA4)', () => {
    socioApiServiceSpy.getLegajo.and.returnValue(
      throwError(() => ({ status: 403, error: { detail: 'Forbidden' } }))
    );

    component.cargarLegajo();
    fixture.detectChanges();

    expect(component.cargando).toBeFalse();
    expect(component.errorHttp).toContain('No posee autorización para consultar este legajo (CA4)');
  });

  it('debe reflejar el saldo recibido en data.saldo si está definido', () => {
    component.data.saldo = -7.5;
    expect(component.saldoPuntos).toBe(-7.5);
  });

  it('debe cerrar el modal al invocar cerrar()', () => {
    component.cerrar();
    expect(dialogRefSpy.close).toHaveBeenCalled();
  });
});
