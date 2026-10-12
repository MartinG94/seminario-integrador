import { OverlayContainer } from '@angular/cdk/overlay';
import { CommonModule } from '@angular/common';
import { ApplicationRef } from '@angular/core';
import { fakeAsync, flush, TestBed } from '@angular/core/testing';
import { MatButtonModule } from '@angular/material/button';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatIconModule } from '@angular/material/icon';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';

import { SolicitudMonitoreo } from '../../services/expediente-api.service';
import { SolicitudDetalleDialogComponent } from './solicitud-detalle-dialog.component';

function luminance(color: number[]): number {
  const channels = color.map(value => {
    const channel = value / 255;
    return channel <= 0.04045 ? channel / 12.92 : Math.pow((channel + 0.055) / 1.055, 2.4);
  });
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}

function contrast(element: HTMLElement): number {
  const foreground = getComputedStyle(element).color.match(/[\d.]+/g)!.map(Number);
  const layers: number[][] = [];
  let surface: HTMLElement | null = element;
  while (surface) {
    const background = getComputedStyle(surface).backgroundColor.match(/[\d.]+/g)!.map(Number);
    layers.push(background);
    if (background.length === 3 || background[3] === 1) {
      let composite = background.slice(0, 3);
      layers.reverse().forEach(layer => {
        const alpha = layer.length === 3 ? 1 : layer[3];
        composite = composite.map((value, index) => layer[index] * alpha + value * (1 - alpha));
      });
      const alpha = foreground.length === 3 ? 1 : foreground[3];
      const text = luminance(composite.map((value, index) => foreground[index] * alpha + value * (1 - alpha)));
      const value = luminance(composite);
      return (Math.max(text, value) + 0.05) / (Math.min(text, value) + 0.05);
    }
    surface = surface.parentElement;
  }
  throw new Error('El diálogo debe tener una superficie opaca real.');
}

describe('SCRUM-77 detalle T01 accesible con MatDialog real', () => {
  let container: HTMLElement;
  let launcher: HTMLButtonElement;
  let previousTheme: string | null;
  let previousHtmlDark: boolean;
  let previousBodyDark: boolean;

  const request: SolicitudMonitoreo = {
    id: 't01-demo-accessibility', numero: 'EXP-0004/2026', numero_expediente: 'T01-0001/2026',
    fecha: '2026-10-12T19:58:02Z', estado: 'ISSUED', tipo_accion: 'SANCTION', puntos: -2,
    titulo: 'SCRUM-77 [t01.cd.issued.multi]', causal: 'Escena sintética de demostración',
    motivo: 'Antecedente ficticio para verificar la lectura del detalle. '.repeat(12),
    razon: 'Hechos ficticios detallados, sin efectos sobre personas reales. '.repeat(12),
    reglamentos_respaldantes: ['Reglamento institucional de prueba'],
    anexo_fecha: '2026-10-12', anexo_lugar: 'Sede AVEIT — espacio ficticio de demostración',
    anexo_relato: 'Relato circunstanciado sintético para comprobar el desplazamiento. '.repeat(12),
    anexo_testigos: 'No se incluyen personas reales.', destinatarios_socios_ids: [770001, 770006],
    estado_procesal: 'justificando', estado_procesal_display: 'En período de justificaciones',
    urgencia: 'urgente', urgencia_display: 'Urgente',
    involucrados: [
      { socio_id: 770001, legajo: '99077001', first_name: 'Ámbar', last_name: 'Faro Demo', subcomision: 'Cómputos' },
      { socio_id: 770006, legajo: '99077006', first_name: 'Galatea', last_name: 'García de las Nubes de Ensayo', subcomision: 'Relaciones Institucionales' }
    ],
    resolucion_final: null, created_at: '2026-10-12T19:58:02Z', issued_at: '2026-10-12T19:58:02Z'
  };

  beforeEach(async () => {
    previousTheme = document.documentElement.getAttribute('data-theme');
    previousHtmlDark = document.documentElement.classList.contains('dark');
    previousBodyDark = document.body.classList.contains('dark-edition');
    container = document.createElement('div');
    container.className = 'cdk-overlay-container';
    document.body.appendChild(container);
    launcher = document.createElement('button');
    launcher.textContent = 'Ver socios de la solicitud';
    document.body.appendChild(launcher);
    await TestBed.configureTestingModule({
      declarations: [SolicitudDetalleDialogComponent],
      imports: [CommonModule, MatDialogModule, MatButtonModule, MatIconModule, NoopAnimationsModule],
      providers: [{ provide: OverlayContainer, useValue: { getContainerElement: () => container } }]
    }).compileComponents();
  });

  afterEach(() => {
    TestBed.inject(MatDialog).closeAll();
    container.remove();
    launcher.remove();
    if (previousTheme === null) document.documentElement.removeAttribute('data-theme');
    else document.documentElement.setAttribute('data-theme', previousTheme);
    document.documentElement.classList.toggle('dark', previousHtmlDark);
    document.body.classList.toggle('dark-edition', previousBodyDark);
  });

  function open(): void {
    launcher.focus();
    TestBed.inject(MatDialog).open(SolicitudDetalleDialogComponent, {
      width: '100%', maxWidth: '750px', data: request
    });
    TestBed.inject(ApplicationRef).tick();
    flush();
  }

  ['light', 'dark'].forEach(theme => {
    it(`permite leer título, causal y etiquetas sobre sus superficies en modo ${theme}`, fakeAsync(() => {
      document.documentElement.setAttribute('data-theme', theme);
      document.documentElement.classList.toggle('dark', theme === 'dark');
      document.body.classList.toggle('dark-edition', theme === 'dark');
      open();
      const elements = container.querySelectorAll<HTMLElement>(
        '.mat-dialog-content .card .font-weight-bold, .mat-dialog-content label, .mat-dialog-content small, .badge-mat'
      );
      expect(elements.length).toBeGreaterThan(8);
      elements.forEach(element => {
        if (element.textContent!.trim()) {
          expect(contrast(element)).withContext(element.textContent!.trim()).toBeGreaterThanOrEqual(4.5);
        }
      });
      const causal = Array.from(container.querySelectorAll<HTMLElement>('.mat-dialog-content div'))
        .find(element => element.children.length === 0 && element.textContent!.trim() === request.causal);
      expect(causal).withContext('La causal completa permanece visible').toBeDefined();
      if (causal) expect(contrast(causal)).withContext('Causal reglamentaria').toBeGreaterThanOrEqual(4.5);
    }));
  });

  [360, 414].forEach(width => {
    it(`contiene cabecera, contenido y Cerrar en un overlay real de ${width}×800`, fakeAsync(() => {
      container.style.width = `${width}px`;
      container.style.height = '800px';
      open();
      const bounds = container.getBoundingClientRect();
      const panel = container.querySelector('.mat-dialog-container') as HTMLElement;
      const content = container.querySelector('.mat-dialog-content') as HTMLElement;
      const title = container.querySelector('h4') as HTMLElement;
      const footer = container.querySelector('.mat-dialog-actions') as HTMLElement;
      [panel, content, title, footer].forEach(element => {
        const rectangle = element.getBoundingClientRect();
        expect(rectangle.left).withContext('Sin recorte izquierdo').toBeGreaterThanOrEqual(bounds.left);
        expect(rectangle.right).withContext('Sin desborde derecho').toBeLessThanOrEqual(bounds.right + 1);
      });
      expect(footer.getBoundingClientRect().bottom).withContext('Cerrar alcanzable sin salir del panel').toBeLessThanOrEqual(bounds.bottom + 1);
      expect(content.scrollWidth).withContext('El desplazamiento de tabla queda dentro de su región').toBeLessThanOrEqual(content.clientWidth + 1);
      content.scrollTop = content.scrollHeight;
      expect(content.scrollTop).withContext('Contenido largo accesible por desplazamiento').toBeGreaterThan(0);
    }));
  });

  it('nombra el diálogo, inicia en Cerrar y devuelve el foco al cerrar con Escape', fakeAsync(() => {
    open();
    const panel = container.querySelector('[role="dialog"]') as HTMLElement;
    const labelledBy = panel.getAttribute('aria-labelledby');
    expect(labelledBy).withContext('Nombre accesible del diálogo').toBeTruthy();
    if (labelledBy) expect(document.getElementById(labelledBy)!.textContent).toContain('Solicitud EXP-0004/2026');
    const close = container.querySelector<HTMLButtonElement>('button[aria-label="Cerrar ventana"]');
    expect(close).withContext('Cerrar con nombre accesible explícito').not.toBeNull();
    expect(document.activeElement).toBe(close);
    panel.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape', keyCode: 27, bubbles: true }));
    flush();
    expect(TestBed.inject(MatDialog).openDialogs.length).toBe(0);
    expect(document.activeElement).toBe(launcher);
  }));
});
