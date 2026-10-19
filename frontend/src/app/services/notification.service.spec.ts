import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { NotificationService, UserNotification, httpErrorMessage } from './notification.service';

describe('NotificationService', () => {
  let service: NotificationService;
  beforeEach(() => { service = TestBed.inject(NotificationService); });

  it('conserva el aviso durante 10 segundos y lo retira al vencer', fakeAsync(() => {
    let messages: readonly UserNotification[] = [];
    service.messages$.subscribe(value => messages = value);
    service.success('Guardado.');
    tick(9999);
    expect(messages.length).toBe(1);
    tick(1);
    expect(messages.length).toBe(0);
  }));

  it('cierra únicamente el aviso elegido y respeta los plazos independientes', fakeAsync(() => {
    let messages: readonly UserNotification[] = [];
    service.messages$.subscribe(value => messages = value);
    const first = service.error('No se pudo guardar.');
    tick(2000);
    service.info('Información.');
    service.dismiss(first);
    expect(messages.map(item => item.message)).toEqual(['Información.']);
    tick(8000);
    expect(messages.length).toBe(1);
    tick(2000);
    expect(messages.length).toBe(0);
  }));

  it('no duplica un mismo aviso vigente ni prolonga su duración', fakeAsync(() => {
    let messages: readonly UserNotification[] = [];
    service.messages$.subscribe(value => messages = value);
    const id = service.warning('Tu sesión expiró.');
    tick(5000);
    expect(service.warning('Tu sesión expiró.')).toBe(id);
    expect(messages.length).toBe(1);
    tick(5000);
    expect(messages.length).toBe(0);
    service.warning('Tu sesión expiró.');
    expect(messages.length).toBe(1);
    tick(10000);
  }));

  it('distingue errores y éxitos y limpia todos los temporizadores al destruirse', fakeAsync(() => {
    let messages: readonly UserNotification[] = [];
    service.messages$.subscribe(value => messages = value);
    service.success('Creado.');
    service.error('Falló.');
    expect(messages.map(item => item.type)).toEqual(['success', 'error']);
    service.ngOnDestroy();
    expect(messages).toEqual([]);
    tick(10000);
  }));
});

describe('httpErrorMessage', () => {
  it('conserva errores de validación y permisos con texto amigable', () => {
    expect(httpErrorMessage({ status: 400, error: { fecha: ['Fecha duplicada.'] } }, 'Falló.'))
      .toBe('Fecha duplicada.');
    expect(httpErrorMessage({ status: 403, error: { detail: 'No autorizado.' } }, 'Falló.'))
      .toBe('No autorizado.');
  });
  it('descarta errores técnicos, cuerpos HTML y fallos de conexión', () => {
    for (const error of [
      { status: 500, error: { detail: 'Traceback: database error' } },
      { status: 0, error: { detail: 'Connection refused' } },
      { status: 400, error: '<html>Error</html>' },
      { status: 400, error: { detail: '<pre>Traceback</pre>' } }
    ]) {
      expect(httpErrorMessage(error, 'Intentá nuevamente.')).toBe('Intentá nuevamente.');
    }
  });
});
