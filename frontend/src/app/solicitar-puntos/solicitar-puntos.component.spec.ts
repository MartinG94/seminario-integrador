import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { ReactiveFormsModule } from '@angular/forms';
import { MatAutocompleteModule } from '@angular/material/autocomplete';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { RouterTestingModule } from '@angular/router/testing';
import { of, throwError } from 'rxjs';

import { ExpedienteApiService, SolicitudT01 } from '../services/expediente-api.service';
import { PadronApiService } from '../services/padron-api.service';
import { SolicitarPuntosComponent } from './solicitar-puntos.component';

describe('SolicitarPuntosComponent', () => {
  let component: SolicitarPuntosComponent;
  let fixture: ComponentFixture<SolicitarPuntosComponent>;
  let expediente: jasmine.SpyObj<ExpedienteApiService>;
  let padron: jasmine.SpyObj<PadronApiService>;
  const draft: SolicitudT01 = {
    id: 'draft-1', estado: 'DRAFT', solicitante: 1, destinatario_socio_id: 7,
    tipo_accion: 'SANCTION', titulo: '', causal: '', puntos: -1, motivo: 'Motivo', razon: '', reglamentos_respaldantes: [],
    anexo_fecha: null, anexo_lugar: '', anexo_relato: '', anexo_testigos: '',
    snapshot_destinatario: null, snapshot_emitido: null, numero_expediente: null,
    created_at: '', updated_at: '', issued_at: null
  };

  beforeEach(() => {
    expediente = jasmine.createSpyObj('ExpedienteApiService', ['crearBorrador', 'actualizarBorrador', 'emitir', 'obtener', 'listarReglamentos']);
    padron = jasmine.createSpyObj('PadronApiService', ['listarSocios']);
    padron.listarSocios.and.returnValue(of([
      { socio_id: 7, legajo: '777', first_name: 'Ana', last_name: 'Prueba', subcomision: { id: 1, name: 'Cómputos' }, is_active: true },
      { socio_id: 8, legajo: '888', first_name: 'Bruno', last_name: 'García', subcomision: null, is_active: true }
    ]));
    expediente.crearBorrador.and.returnValue(of(draft));
    expediente.actualizarBorrador.and.returnValue(of(draft));
    expediente.emitir.and.returnValue(of({ ...draft, estado: 'ISSUED', numero_expediente: 'T01-2026-1', issued_at: '2026-01-01' }));
    expediente.listarReglamentos.and.returnValue(of({ reglamentos: ['Estatuto AVEIT Reforma 2026'] }));
    TestBed.configureTestingModule({
      imports: [FormsModule, ReactiveFormsModule, MatAutocompleteModule, MatButtonModule, MatFormFieldModule, MatInputModule, NoopAnimationsModule, RouterTestingModule],
      declarations: [SolicitarPuntosComponent],
      providers: [
        { provide: ExpedienteApiService, useValue: expediente },
        { provide: PadronApiService, useValue: padron }
      ]
    });
    fixture = TestBed.createComponent(SolicitarPuntosComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('carga y selecciona socios por socio_id', () => {
    expect(component.socios[0].socio_id).toBe(7);
    component.socioSeleccionado = 7;
    expect(component.socioSeleccionado).toBe(7);
  });

  it('no muestra coincidencias con menos de tres caracteres', () => {
    component.filtrarSocios('Pr');
    expect(component.sociosFiltrados).toEqual([]);
  });

  it('filtra por legajo y por nombre o apellido', () => {
    component.filtrarSocios('777');
    expect(component.sociosFiltrados.map(socio => socio.socio_id)).toEqual([7]);
    component.filtrarSocios('gar');
    expect(component.sociosFiltrados.map(socio => socio.socio_id)).toEqual([8]);
  });

  it('conserva socio_id al seleccionar una coincidencia', () => {
    component.seleccionarSocio(component.socios[1]);
    expect(component.socioSeleccionado).toBe(8);
  });

  it('deshabilita el control cuando el expediente está emitido', () => {
    component.estado = 'ISSUED';
    component.sincronizarEstadoSocio();
    fixture.detectChanges();
    expect(component.socioBusqueda.disabled).toBeTrue();
  });

  it('guarda por POST y luego por PATCH, sin exigir anexo', () => {
    component.socioSeleccionado = 7;
    component.guardarBorrador();
    expect(expediente.crearBorrador).toHaveBeenCalled();
    component.guardarBorrador();
    expect(expediente.actualizarBorrador).toHaveBeenCalledWith('draft-1', jasmine.any(Object));
  });

  it('emite usando el id del borrador y bloquea el estado ISSUED', () => {
    component.socioSeleccionado = 7;
    component.razon = 'Motivo';
    component.emitirT01();
    expect(expediente.emitir).toHaveBeenCalledWith('draft-1');
    expect(component.estado).toBe('ISSUED');
    expect(component.numeroExpediente).toBe('T01-2026-1');
  });

  it('muestra errores del backend', () => {
    expediente.crearBorrador.and.returnValue(throwError(() => ({ error: { detail: 'No autorizado' } })));
    component.guardarBorrador();
    expect(component.errorMensaje).toBe('No autorizado');
  });

  it('muestra un mensaje seguro para errores 500', () => {
    expediente.crearBorrador.and.returnValue(throwError(() => ({ status: 500, error: '<pre>traceback</pre>' })));
    component.guardarBorrador();
    expect(component.errorMensaje).toContain('servicio no está disponible');
    expect(component.errorMensaje).not.toContain('traceback');
    expect(component.errorMensaje).not.toContain('<pre>');
  });

  it('no trata una respuesta string o HTML como objeto de errores', () => {
    expediente.crearBorrador.and.returnValue(throwError(() => ({ status: 400, error: '<html>Error interno</html>' })));
    component.guardarBorrador();
    expect(component.errorMensaje).toBe('No se pudo completar la operación.');
    expect(component.errorMensaje).not.toContain('<html>');
  });
});
