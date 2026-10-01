import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
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
    tipo_accion: 'SANCTION', causal: '', puntos: -1, motivo: 'Motivo',
    anexo_fecha: null, anexo_lugar: '', anexo_relato: '', anexo_testigos: '',
    snapshot_destinatario: null, snapshot_emitido: null, numero_expediente: null,
    created_at: '', updated_at: '', issued_at: null
  };

  beforeEach(() => {
    expediente = jasmine.createSpyObj('ExpedienteApiService', ['crearBorrador', 'actualizarBorrador', 'emitir', 'obtener']);
    padron = jasmine.createSpyObj('PadronApiService', ['listarSocios']);
    padron.listarSocios.and.returnValue(of([{ socio_id: 7, legajo: '77', first_name: 'Ana', last_name: 'Prueba', subcomision: { id: 1, name: 'Cómputos' }, is_active: true }]));
    expediente.crearBorrador.and.returnValue(of(draft));
    expediente.actualizarBorrador.and.returnValue(of(draft));
    expediente.emitir.and.returnValue(of({ ...draft, estado: 'ISSUED', numero_expediente: 'T01-2026-1', issued_at: '2026-01-01' }));
    TestBed.configureTestingModule({
      imports: [FormsModule, MatButtonModule, RouterTestingModule],
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

  it('guarda por POST y luego por PATCH, sin exigir anexo', () => {
    component.socioSeleccionado = 7;
    component.guardarBorrador();
    expect(expediente.crearBorrador).toHaveBeenCalled();
    component.guardarBorrador();
    expect(expediente.actualizarBorrador).toHaveBeenCalledWith('draft-1', jasmine.any(Object));
  });

  it('emite usando el id del borrador y bloquea el estado ISSUED', () => {
    component.socioSeleccionado = 7;
    component.motivoTexto = 'Motivo';
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
