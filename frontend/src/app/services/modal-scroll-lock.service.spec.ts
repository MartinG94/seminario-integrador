import { TestBed } from '@angular/core/testing';
import { ModalScrollLockService } from './modal-scroll-lock.service';

describe('ModalScrollLockService', () => {
  let service: ModalScrollLockService;
  let mainPanelEl: HTMLElement;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [ModalScrollLockService]
    });
    service = TestBed.inject(ModalScrollLockService);

    mainPanelEl = document.createElement('div');
    mainPanelEl.className = 'main-panel';
    mainPanelEl.style.height = '200px';
    mainPanelEl.style.overflow = 'auto';
    const panelContent = document.createElement('div');
    panelContent.style.height = '1000px';
    mainPanelEl.appendChild(panelContent);
    document.body.appendChild(mainPanelEl);

    service.reset();
  });

  afterEach(() => {
    service.reset();
    if (mainPanelEl && mainPanelEl.parentElement) {
      mainPanelEl.parentElement.removeChild(mainPanelEl);
    }
    document.querySelectorAll('.modal-reglamentos-backdrop, .modal-backdrop-custom').forEach(el => el.remove());
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

  it('debe conservar fijo el scrollTop de .main-panel ante eventos scroll y wheel mientras está bloqueado', () => {
    mainPanelEl.scrollTop = 200;
    service.lock();

    // Simular que PerfectScrollbar o el navegador intentaron mover el main-panel
    mainPanelEl.scrollTop = 350;
    window.dispatchEvent(new Event('scroll'));
    expect(mainPanelEl.scrollTop).toBe(200);

    // Simular evento wheel en window
    const wheelEvent = new WheelEvent('wheel', { deltaY: 60, bubbles: true, cancelable: true });
    window.dispatchEvent(wheelEvent);
    expect(mainPanelEl.scrollTop).toBe(200);

    service.unlock();
  });

  it('debe redirigir deltaY al cuerpo del modal activo al hacer wheel sobre el backdrop o cabecera sin mover main-panel', () => {
    const backdrop = document.createElement('div');
    backdrop.className = 'modal-backdrop-custom';
    const dialog = document.createElement('div');
    dialog.className = 'modal-dialog-custom';
    const header = document.createElement('div');
    header.className = 'card-header';
    const body = document.createElement('div');
    body.className = 'modal-detalle-body';

    let bodyScroll = 10;
    Object.defineProperty(body, 'scrollTop', {
      get: () => bodyScroll,
      set: (val: number) => { bodyScroll = val; },
      configurable: true
    });

    dialog.appendChild(header);
    dialog.appendChild(body);
    backdrop.appendChild(dialog);
    document.body.appendChild(backdrop);

    mainPanelEl.scrollTop = 100;
    service.lock();

    // Wheel sobre la cabecera del modal
    const wheelHeader = new WheelEvent('wheel', { deltaY: 30, bubbles: true, cancelable: true });
    header.dispatchEvent(wheelHeader);
    expect(body.scrollTop).toBe(40);
    expect(mainPanelEl.scrollTop).toBe(100);

    // Wheel sobre el fondo oscuro (backdrop)
    const wheelBackdrop = new WheelEvent('wheel', { deltaY: 25, bubbles: true, cancelable: true });
    backdrop.dispatchEvent(wheelBackdrop);
    expect(body.scrollTop).toBe(65);
    expect(mainPanelEl.scrollTop).toBe(100);

    service.unlock();
  });
});
