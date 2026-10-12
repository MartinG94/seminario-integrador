import { A11yModule } from '@angular/cdk/a11y';
import { CommonModule } from '@angular/common';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { Expediente, TribunalDataService } from '../services/tribunal-data.service';
import { GestionarExpedientesComponent } from './gestionar-expedientes.component';

describe('SCRUM-77 detalle de expediente con teclado', () => {
  let fixture: ComponentFixture<GestionarExpedientesComponent>;
  const caseFixture: Expediente = {
    id: '77', numero: 'EXP-77/2026', socio: 'Socio sintético', legajo: '99077001',
    subcomision: 'Cómputos', motivo: 'Causa de prueba de navegación por teclado',
    fechaCreacion: '2026-10-12', estado: 'creado', urgencia: 'normal',
    horasRestantes: 0, tipo: 'falta', puntos: -1, cantidadSocios: 1
  };

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [GestionarExpedientesComponent],
      imports: [CommonModule, FormsModule, MatButtonModule, NoopAnimationsModule, A11yModule],
      providers: [
        { provide: AuthService, useValue: { tieneRol: () => false } },
        {
          provide: TribunalDataService,
          useValue: {
            expedientes$: of([caseFixture]),
            obtenerTablero: () => of({ columns: [] })
          }
        }
      ]
    }).compileComponents();
    fixture = TestBed.createComponent(GestionarExpedientesComponent);
    fixture.detectChanges();
  });

  async function openWithKeyboard(): Promise<HTMLElement> {
    const card = fixture.nativeElement.querySelector('.kanban-card-mat') as HTMLElement;
    card.focus();
    card.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }));
    fixture.detectChanges();
    await fixture.whenStable();
    fixture.detectChanges();
    return card;
  }

  function closeButton(): HTMLButtonElement {
    const buttons = (fixture.nativeElement as HTMLElement).querySelectorAll<HTMLButtonElement>('.modal-backdrop-custom button');
    return Array.from(buttons).find(button => button.textContent?.trim() === 'Cerrar') as HTMLButtonElement;
  }

  it('identifica el detalle abierto como diálogo modal con título accesible', async () => {
    await openWithKeyboard();
    const dialog = fixture.nativeElement.querySelector('[role="dialog"]') as HTMLElement | null;
    expect(dialog).withContext('El overlay debe comunicar su rol a tecnologías de asistencia').not.toBeNull();
    if (!dialog) { return; }
    expect(dialog.getAttribute('aria-modal')).toBe('true');
    const title = document.getElementById(dialog.getAttribute('aria-labelledby') || '');
    expect(title?.textContent).toContain(caseFixture.numero);
  });

  it('lleva el foco a Cerrar al abrir y lo devuelve a la tarjeta al cerrar', async () => {
    const origin = await openWithKeyboard();
    const close = closeButton();
    expect(document.activeElement).withContext('El foco debe entrar al detalle').toBe(close);
    close.click();
    fixture.detectChanges();
    await fixture.whenStable();
    expect(fixture.nativeElement.querySelector('.modal-backdrop-custom')).toBeNull();
    expect(document.activeElement).withContext('Cerrar debe recuperar la tarjeta de origen').toBe(origin);
  });

  it('cierra con Escape desde un control del detalle y recupera el foco de origen', async () => {
    const origin = await openWithKeyboard();
    const close = closeButton();
    close.focus();
    close.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }));
    fixture.detectChanges();
    await fixture.whenStable();
    expect(fixture.nativeElement.querySelector('.modal-backdrop-custom')).toBeNull();
    expect(document.activeElement).toBe(origin);
  });
});
