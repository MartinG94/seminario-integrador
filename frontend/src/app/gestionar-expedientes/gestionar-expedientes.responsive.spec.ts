import { A11yModule } from '@angular/cdk/a11y';
import { CommonModule } from '@angular/common';
import { TestBed } from '@angular/core/testing';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { NoopAnimationsModule } from '@angular/platform-browser/animations';
import { of } from 'rxjs';

import { AuthService } from '../services/auth.service';
import { TribunalDataService } from '../services/tribunal-data.service';
import { GestionarExpedientesComponent } from './gestionar-expedientes.component';

describe('SCRUM-77 selector de vistas en un contenedor angosto', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [GestionarExpedientesComponent],
      imports: [CommonModule, FormsModule, MatButtonModule, NoopAnimationsModule, A11yModule],
      providers: [
        { provide: AuthService, useValue: { tieneRol: () => false } },
        { provide: TribunalDataService, useValue: {
          expedientes$: of([]), obtenerTablero: () => of({ columns: [] })
        } }
      ]
    }).compileComponents();
  });

  [360, 414].forEach(width => {
    it(`mantiene ambos botones completos dentro de la tarjeta en un contenedor de ${width}px`, () => {
      const fixture = TestBed.createComponent(GestionarExpedientesComponent);
      const root = fixture.nativeElement as HTMLElement;
      root.style.display = 'block';
      root.style.width = `${width}px`;
      fixture.detectChanges();
      const group = root.querySelector('[aria-label="Selector de Vista"]') as HTMLElement;
      const card = group.closest('.card-body') as HTMLElement;
      const bounds = card.getBoundingClientRect();
      const buttons = group.querySelectorAll<HTMLButtonElement>('button');
      expect(buttons.length).toBe(2);
      buttons.forEach(button => {
        const rect = button.getBoundingClientRect();
        expect(rect.left).withContext('Inicio del botón dentro de la tarjeta').toBeGreaterThanOrEqual(bounds.left);
        expect(rect.right).withContext('Fin del botón dentro de la tarjeta').toBeLessThanOrEqual(bounds.right + 1);
        expect(button.scrollWidth).withContext('Etiqueta completa, sin recorte horizontal').toBeLessThanOrEqual(button.clientWidth + 1);
      });
      buttons[1].click();
      fixture.detectChanges();
      expect(root.querySelector('.kanban-board-mat')).toBeNull();
      buttons[0].click();
      fixture.detectChanges();
      expect(root.querySelector('.kanban-board-mat')).not.toBeNull();
    });
  });
});
