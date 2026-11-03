import { Injectable, RendererFactory2, Renderer2 } from '@angular/core';

@Injectable({
  providedIn: 'root'
})
export class ModalScrollLockService {
  private activeLocks = 0;
  private renderer: Renderer2;

  constructor(rendererFactory: RendererFactory2) {
    this.renderer = rendererFactory.createRenderer(null, null);
  }

  lock(): void {
    if (typeof document === 'undefined') return;
    this.activeLocks++;
    if (this.activeLocks === 1) {
      this.aplicarClases(true);
    }
  }

  unlock(): void {
    if (typeof document === 'undefined') return;
    this.activeLocks = Math.max(0, this.activeLocks - 1);
    if (this.activeLocks === 0) {
      this.aplicarClases(false);
    }
  }

  reset(): void {
    this.activeLocks = 0;
    if (typeof document === 'undefined') return;
    this.aplicarClases(false);
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
}
