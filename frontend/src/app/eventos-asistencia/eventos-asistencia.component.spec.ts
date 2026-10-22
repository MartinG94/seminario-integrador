import { ComponentFixture, TestBed, fakeAsync, tick } from '@angular/core/testing';
import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { HttpClientTestingModule } from '@angular/common/http/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { EventosAsistenciaComponent } from './eventos-asistencia.component';
import { TribunalDataService } from '../services/tribunal-data.service';
import { NotificationService } from '../services/notification.service';

describe('EventosAsistenciaComponent (T17)', () => {
  let component: EventosAsistenciaComponent;
  let fixture: ComponentFixture<EventosAsistenciaComponent>;
  let tribunalService: TribunalDataService;
  let notificationSpy: jasmine.SpyObj<NotificationService>;

  beforeEach(async () => {
    notificationSpy = jasmine.createSpyObj('NotificationService', ['show', 'success', 'error', 'info', 'warning']);

    await TestBed.configureTestingModule({
      imports: [HttpClientTestingModule, RouterTestingModule],
      declarations: [EventosAsistenciaComponent],
      providers: [
        TribunalDataService,
        { provide: NotificationService, useValue: notificationSpy }
      ],
      schemas: [CUSTOM_ELEMENTS_SCHEMA]
    }).compileComponents();

    fixture = TestBed.createComponent(EventosAsistenciaComponent);
    component = fixture.componentInstance;
    tribunalService = TestBed.inject(TribunalDataService);
    fixture.detectChanges();
  });

  it('debe crearse correctamente e inicializar listas de eventos y socios', () => {
    expect(component).toBeTruthy();
    expect(component.eventos.length).toBeGreaterThan(0);
    expect(component.eventoActivo).toBeTruthy();
  });

  it('seleccionarEvento debe cambiar el evento activo', () => {
    const otroEvento = component.eventos[0];
    component.seleccionarEvento(otroEvento);
    expect(component.eventoActivo).toBe(otroEvento);
  });

  it('pasarElDedo debe simular lectura biométrica y notificar éxito', fakeAsync(() => {
    spyOn(tribunalService, 'registrarAsistenciaBiometrica').and.returnValue(true);

    component.pasarElDedo();
    expect(component.estaEscaneando).toBeTrue();

    tick(650);

    expect(component.estaEscaneando).toBeFalse();
    expect(notificationSpy.show).toHaveBeenCalledWith('success', jasmine.stringMatching(/Asistencia confirmada/));
  }));

  it('pasarElDedo no debe permitir registrar en un evento CERRADO', () => {
    if (component.eventoActivo) {
      component.eventoActivo.estado = 'CERRADO';
    }
    component.pasarElDedo();
    expect(notificationSpy.show).toHaveBeenCalledWith('error', jasmine.stringMatching(/formalmente cerrado/));
  });

  it('cerrarEvento debe abrir expedientes y notificar', () => {
    spyOn(window, 'confirm').and.returnValue(true);
    spyOn(tribunalService, 'cerrarEvento').and.returnValue({ expedientesGenerados: 5 });

    component.cerrarEvento();

    expect(notificationSpy.show).toHaveBeenCalledWith('info', jasmine.stringMatching(/Evento cerrado formalmente/));
  });
});
