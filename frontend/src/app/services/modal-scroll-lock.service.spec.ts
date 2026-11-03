import { TestBed } from '@angular/core/testing';
import { ModalScrollLockService } from './modal-scroll-lock.service';

describe('ModalScrollLockService', () => {
  let service: ModalScrollLockService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ModalScrollLockService]
    });
    service = TestBed.inject(ModalScrollLockService);
    service.reset();
  });

  afterEach(() => {
    service.reset();
  });

  it('debe crearse correctamente', () => {
    expect(service).toBeTruthy();
    expect(service.isLocked).toBeFalse();
  });

  it('debe agregar la clase modal-open-scroll-lock en lock y quitarla en unlock', () => {
    service.lock();
    expect(service.isLocked).toBeTrue();
    expect(document.body.classList.contains('modal-open-scroll-lock')).toBeTrue();
    expect(document.documentElement.classList.contains('modal-open-scroll-lock')).toBeTrue();

    service.unlock();
    expect(service.isLocked).toBeFalse();
    expect(document.body.classList.contains('modal-open-scroll-lock')).toBeFalse();
    expect(document.documentElement.classList.contains('modal-open-scroll-lock')).toBeFalse();
  });

  it('debe manejar conteo anidado de locks correctamente', () => {
    service.lock();
    service.lock();
    expect(service.isLocked).toBeTrue();
    expect(document.body.classList.contains('modal-open-scroll-lock')).toBeTrue();

    service.unlock();
    expect(service.isLocked).toBeTrue();
    expect(document.body.classList.contains('modal-open-scroll-lock')).toBeTrue();

    service.unlock();
    expect(service.isLocked).toBeFalse();
    expect(document.body.classList.contains('modal-open-scroll-lock')).toBeFalse();
  });

  it('debe resetear todos los bloqueos con reset()', () => {
    service.lock();
    service.lock();
    expect(service.isLocked).toBeTrue();

    service.reset();
    expect(service.isLocked).toBeFalse();
    expect(document.body.classList.contains('modal-open-scroll-lock')).toBeFalse();
  });
});
