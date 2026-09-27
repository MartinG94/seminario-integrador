import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute } from '@angular/router';
import { RouterTestingModule } from '@angular/router/testing';

import { EnDesarrolloComponent } from './en-desarrollo.component';

describe('EnDesarrolloComponent', () => {
  let component: EnDesarrolloComponent;
  let fixture: ComponentFixture<EnDesarrolloComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [RouterTestingModule],
      declarations: [EnDesarrolloComponent],
      providers: [
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              data: {
                titulo: 'Reportes & Balance',
                descripcion: 'Emisión de balances cuatrimestrales y estadísticas.',
                icono: 'bar_chart'
              }
            }
          }
        }
      ]
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(EnDesarrolloComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('debe leer los datos configurados en la ruta activa', () => {
    expect(component.titulo).toBe('Reportes & Balance');
    expect(component.descripcion).toBe('Emisión de balances cuatrimestrales y estadísticas.');
    expect(component.icono).toBe('bar_chart');
  });
});
