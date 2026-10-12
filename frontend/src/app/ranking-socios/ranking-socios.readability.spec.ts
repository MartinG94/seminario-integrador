import { CommonModule } from '@angular/common';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MAT_DIALOG_DATA, MatDialog, MatDialogRef } from '@angular/material/dialog';
import { of } from 'rxjs';

import { RankingService } from '../services/ranking.service';
import { SocioApiService, SocioLegajoDTO } from '../services/socio-api.service';
import { RankingSociosComponent } from './ranking-socios.component';
import { SocioLegajoDialogComponent } from './socio-legajo-dialog/socio-legajo-dialog.component';
import { AuthService } from '../services/auth.service';
import { AppliedPointsHistoryComponent } from '../mis-expedientes/applied-points-history/applied-points-history.component';
import { AppliedResolutionDialogComponent } from '../mis-expedientes/applied-resolution-dialog/applied-resolution-dialog.component';

type Color = [number, number, number, number];

function channels(value: string): Color {
  const values = value.match(/[\d.]+/g)?.map(Number) || [];
  if (value.startsWith('color(srgb')) {
    return [values[0] * 255, values[1] * 255, values[2] * 255, values[3] ?? 1];
  }
  if (!value.startsWith('rgb') || values.length < 3) {
    throw new Error(`Formato de color no reconocido: ${value}`);
  }
  return [values[0], values[1], values[2], values[3] ?? 1];
}

function composite(top: Color, bottom: Color): Color {
  return [0, 1, 2].map(index => top[index] * top[3] + bottom[index] * (1 - top[3]))
    .concat(1) as Color;
}

function background(element: HTMLElement | null): Color {
  if (!element) { return [255, 255, 255, 1]; }
  const own = channels(getComputedStyle(element).backgroundColor);
  return own[3] === 1 ? own : composite(own, background(element.parentElement));
}

function luminance(color: Color): number {
  const values = color.slice(0, 3).map(channel => {
    const value = channel / 255;
    return value <= 0.04045 ? value / 12.92 : Math.pow((value + 0.055) / 1.055, 2.4);
  });
  return values[0] * 0.2126 + values[1] * 0.7152 + values[2] * 0.0722;
}

function expectReadable(element: HTMLElement): void {
  const surface = background(element);
  const foreground = composite(channels(getComputedStyle(element).color), surface);
  const light = Math.max(luminance(surface), luminance(foreground));
  const dark = Math.min(luminance(surface), luminance(foreground));
  expect((light + 0.05) / (dark + 0.05))
    .withContext(`Texto legible: ${element.textContent?.trim()} (${getComputedStyle(element).color})`)
    .toBeGreaterThanOrEqual(4.5);
}

describe('SCRUM-77 legibilidad de ranking y ficha en ambos temas', () => {
  let originalBodyClass: string;
  let originalHtmlClass: string;
  const legajo: SocioLegajoDTO = {
    id: 770007, legajo: '99077007', first_name: 'Galatea',
    last_name: 'García de las Nubes de Ensayo', email: 'g58.03@scrum77.test',
    role: 'SOCIO', category: 'SENIOR', category_display: 'Senior',
    subcomision: 'Cómputos', social_year: 6, is_enabled: true, points_balance: 2
  };

  beforeEach(async () => {
    originalBodyClass = document.body.className;
    originalHtmlClass = document.documentElement.className;
    await TestBed.configureTestingModule({
      imports: [CommonModule, FormsModule],
      declarations: [RankingSociosComponent, SocioLegajoDialogComponent, AppliedPointsHistoryComponent, AppliedResolutionDialogComponent],
      providers: [
        { provide: AuthService, useValue: { perfil$: of(null) } },
        { provide: SocioApiService, useValue: {
          getLegajo: () => of(legajo),
          getPointsHistory: () => of({ points_balance: 2, entries: [{
            movement_id: 17, applied_points: 2,
            historical_case: { id: 101, number: 'HIST-101', recorded_at: null, state: 'emitido' },
            resolution: { id: 201, text: 'Resolución de prueba', regulations: ['Art. 93'] },
            managed_case: null
          }] })
        } },
        { provide: MatDialogRef, useValue: { close: () => undefined } },
        { provide: MAT_DIALOG_DATA, useValue: { socioId: legajo.id } },
        { provide: MatDialog, useValue: { open: () => undefined } },
        { provide: RankingService, useValue: { obtenerRanking: () => of([{
          id: '770007', legajo: legajo.legajo, nombre: legajo.first_name,
          apellido: legajo.last_name, categoria: 'SENIOR', subcomision: 'Cómputos', saldo: 2
        }]) } }
      ]
    }).compileComponents();
  });

  afterEach(() => {
    document.body.className = originalBodyClass;
    document.documentElement.className = originalHtmlClass;
  });

  function setTheme(dark: boolean): void {
    document.body.classList.toggle('dark-edition', dark);
    document.documentElement.classList.toggle('dark', dark);
  }

  [false, true].forEach(dark => {
    [false, true].forEach(enabled => {
      it(`mantiene el badge ${enabled ? 'Habilitado' : 'Inactivo'} legible en tema ${dark ? 'oscuro' : 'claro'}`, () => {
        setTheme(dark);
        const fixture = TestBed.createComponent(SocioLegajoDialogComponent);
        fixture.detectChanges();
        fixture.componentInstance.legajo = { ...legajo, is_enabled: enabled };
        fixture.detectChanges();
        const items = Array.from((fixture.nativeElement as HTMLElement).querySelectorAll('.data-item'));
        const state = items.find(item => item.querySelector('.data-label')?.textContent === 'Estado de la Cuenta');
        const badge = state?.querySelector('.badge-mat') as HTMLElement;
        expect(badge.textContent?.trim()).toBe(enabled ? 'Habilitado' : 'Inactivo');
        expectReadable(badge);
      });
    });

    it(`mantiene los datos, nombre completo, iniciales y saldo legibles en tema ${dark ? 'oscuro' : 'claro'}`, () => {
      setTheme(dark);
      const fixture: ComponentFixture<SocioLegajoDialogComponent> = TestBed.createComponent(SocioLegajoDialogComponent);
      fixture.detectChanges();
      const root = fixture.nativeElement as HTMLElement;
      const selectors = '.dialog-title, .dialog-subtitle, .socio-full-name, .socio-avatar span, .socio-legajo-badge strong, .data-label, .notice-text small';
      root.querySelectorAll<HTMLElement>(selectors).forEach(expectReadable);
      root.querySelectorAll<HTMLElement>('.data-value').forEach(element => {
        if (element.children.length === 0) { expectReadable(element); }
      });
      expect(root.querySelector('.socio-full-name')?.textContent).toContain(legajo.last_name);
      const saldo = Array.from(root.querySelectorAll('.data-item'))
        .find(item => item.querySelector('.data-label')?.textContent === 'Saldo de Puntos');
      expect(saldo?.textContent).toContain('+2 pts');
    });

    it(`mantiene el nombre del socio legible en el ranking con tema ${dark ? 'oscuro' : 'claro'}`, () => {
      setTheme(dark);
      const fixture = TestBed.createComponent(RankingSociosComponent);
      fixture.detectChanges();
      const name = fixture.nativeElement.querySelector('tbody tr td:nth-child(2) div') as HTMLElement;
      expect(name.textContent).toContain(legajo.last_name);
      expectReadable(name);
    });
  });
});
