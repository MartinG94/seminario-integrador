import { Injectable, RendererFactory2, Renderer2 } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ModalScrollLockService {
  private static globalListenersAttached = false;
  private static activeServiceInstance: ModalScrollLockService | null = null;

  private static staticOnWheel = (event: WheelEvent): void => {
    ModalScrollLockService.activeServiceInstance?.onWheel(event);
  };

  private static staticOnTouchMove = (event: TouchEvent): void => {
    ModalScrollLockService.activeServiceInstance?.onTouchMove(event);
  };

  private static staticOnScroll = (event: Event): void => {
    ModalScrollLockService.activeServiceInstance?.onScroll(event);
  };

  private activeLocks = 0;
  private renderer: Renderer2;
  private savedMainPanelScrollTop = 0;
  private savedDocScrollTop = 0;
  private savedBodyScrollTop = 0;
  private listenersAttached = false;

  constructor(rendererFactory: RendererFactory2) {
    this.renderer = rendererFactory.createRenderer(null, null);
  }

  lock(): void {
    if (typeof document === 'undefined') return;
    this.activeLocks++;
    if (this.activeLocks === 1) {
      const mainPanel = document.querySelector('.main-panel') as HTMLElement | null;
      this.savedMainPanelScrollTop = mainPanel ? mainPanel.scrollTop : 0;
      this.savedDocScrollTop = document.documentElement ? document.documentElement.scrollTop : 0;
      this.savedBodyScrollTop = document.body ? document.body.scrollTop : 0;

      this.aplicarClases(true);
      this.attachListeners();
    }
  }

  unlock(): void {
    if (typeof document === 'undefined') return;
    this.activeLocks = Math.max(0, this.activeLocks - 1);
    if (this.activeLocks === 0) {
      this.detachListeners();
      this.aplicarClases(false);
      this.restaurarScroll();
    }
  }

  reset(): void {
    this.activeLocks = 0;
    if (typeof document === 'undefined') return;
    this.detachListeners();
    this.aplicarClases(false);
    this.restaurarScroll();
  }

  get isLocked(): boolean {
    return this.activeLocks > 0;
  }

  private aplicarClases(bloquear: boolean): void {
    const clase = 'modal-open-scroll-lock';
    const targets: HTMLElement[] = [
      document.body,
      document.documentElement,
      document.querySelector('.main-panel') as HTMLElement,
      document.querySelector('.wrapper') as HTMLElement
    ].filter(Boolean);

    targets.forEach(el => {
      if (bloquear) {
        this.renderer.addClass(el, clase);
      } else {
        this.renderer.removeClass(el, clase);
      }
    });
  }

  private attachListeners(): void {
    ModalScrollLockService.activeServiceInstance = this;
    if (ModalScrollLockService.globalListenersAttached || typeof window === 'undefined') return;
    window.addEventListener('wheel', ModalScrollLockService.staticOnWheel, { passive: false, capture: true });
    window.addEventListener('touchmove', ModalScrollLockService.staticOnTouchMove, { passive: false, capture: true });
    window.addEventListener('scroll', ModalScrollLockService.staticOnScroll, { passive: false, capture: true });
    document.addEventListener('scroll', ModalScrollLockService.staticOnScroll, { passive: false, capture: true });
    ModalScrollLockService.globalListenersAttached = true;
  }

  private detachListeners(): void {
    if (ModalScrollLockService.activeServiceInstance === this) {
      ModalScrollLockService.activeServiceInstance = null;
    }
    if (!ModalScrollLockService.globalListenersAttached || typeof window === 'undefined') return;
    window.removeEventListener('wheel', ModalScrollLockService.staticOnWheel, { capture: true });
    window.removeEventListener('touchmove', ModalScrollLockService.staticOnTouchMove, { capture: true });
    window.removeEventListener('scroll', ModalScrollLockService.staticOnScroll, { capture: true });
    document.removeEventListener('scroll', ModalScrollLockService.staticOnScroll, { capture: true });
    ModalScrollLockService.globalListenersAttached = false;
  }

  private restaurarScroll(): void {
    const mainPanel = document.querySelector('.main-panel') as HTMLElement | null;
    if (mainPanel) {
      mainPanel.scrollTop = this.savedMainPanelScrollTop;
    }
    if (document.documentElement) {
      document.documentElement.scrollTop = this.savedDocScrollTop;
    }
    if (document.body) {
      document.body.scrollTop = this.savedBodyScrollTop;
    }
  }

  private normalizeWheelDeltaY(event: WheelEvent): number {
    if (event.deltaMode === 1) {
      return event.deltaY * 40;
    }
    if (event.deltaMode === 2) {
      return event.deltaY * 800;
    }
    return event.deltaY;
  }

  private canElementScrollInDirection(el: HTMLElement, deltaY: number): boolean {
    if (el.scrollHeight <= el.clientHeight) {
      return false;
    }
    if (deltaY < 0) {
      return el.scrollTop > 0;
    }
    if (deltaY > 0) {
      return Math.ceil(el.scrollTop + el.clientHeight) < el.scrollHeight;
    }
    return false;
  }

  private onWheel = (event: WheelEvent): void => {
    if (!this.isLocked) return;

    const target = event.target as HTMLElement | null;
    const mainPanel = document.querySelector('.main-panel') as HTMLElement | null;
    const deltaY = this.normalizeWheelDeltaY(event);
    const scrollable = this.findScrollableModalContainer(target, deltaY);

    if (scrollable) {
      const canScroll = this.canElementScrollInDirection(scrollable, deltaY);
      event.preventDefault();
      event.stopPropagation();
      if (canScroll) {
        scrollable.scrollTop += deltaY;
      }
    } else {
      const modalBody = this.getActiveModalBody();
      event.preventDefault();
      event.stopPropagation();
      if (modalBody) {
        modalBody.scrollTop += deltaY;
      }
    }

    if (mainPanel && mainPanel.scrollTop !== this.savedMainPanelScrollTop) {
      mainPanel.scrollTop = this.savedMainPanelScrollTop;
    }
  };

  private onTouchMove = (event: TouchEvent): void => {
    if (!this.isLocked) return;
    const target = event.target as HTMLElement | null;
    const scrollable = this.findScrollableModalContainer(target, 0);
    if (!scrollable) {
      event.preventDefault();
      event.stopPropagation();
    }
  };

  private onScroll = (event: Event): void => {
    if (!this.isLocked) return;
    const mainPanel = document.querySelector('.main-panel') as HTMLElement | null;
    if (mainPanel && mainPanel.scrollTop !== this.savedMainPanelScrollTop) {
      mainPanel.scrollTop = this.savedMainPanelScrollTop;
    }
  };

  private isPrimaryModalBody(el: HTMLElement): boolean {
    return (
      el.classList.contains('modal-reglamentos-body') ||
      el.classList.contains('modal-detalle-body') ||
      el.classList.contains('card-body') ||
      el.classList.contains('mat-dialog-content')
    );
  }

  private findScrollableModalContainer(target: HTMLElement | null, deltaY: number): HTMLElement | null {
    if (!target || !(target instanceof HTMLElement)) return null;

    const modalDialog = target.closest(
      '.modal-reglamentos-dialog, .modal-dialog-custom, .cdk-overlay-pane'
    ) as HTMLElement | null;

    if (!modalDialog) return null;

    let current: HTMLElement | null = target;
    let fallbackPrimary: HTMLElement | null = null;

    while (current && current !== modalDialog.parentElement) {
      if (this.isPrimaryModalBody(current)) {
        return current;
      }

      const style = typeof window !== 'undefined' ? window.getComputedStyle(current) : null;
      if (style) {
        const overflowY = style.overflowY;
        if ((overflowY === 'auto' || overflowY === 'scroll') && current.scrollHeight > current.clientHeight) {
          if (deltaY === 0 || this.canElementScrollInDirection(current, deltaY)) {
            return current;
          }
          if (!fallbackPrimary) {
            fallbackPrimary = current;
          }
        }
      }

      if (current === modalDialog) break;
      current = current.parentElement;
    }

    return fallbackPrimary;
  }

  private getActiveModalBody(): HTMLElement | null {
    if (typeof document === 'undefined') return null;
    return document.querySelector(
      '.modal-reglamentos-body, .modal-descargo-backdrop .card-body, .modal-resolucion-backdrop .card-body, .modal-backdrop-custom .modal-detalle-body, .modal-backdrop-custom .card-body, .cdk-overlay-pane .mat-dialog-content'
    ) as HTMLElement | null;
  }
}

