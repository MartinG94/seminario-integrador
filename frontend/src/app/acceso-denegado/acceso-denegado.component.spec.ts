import { ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { AccesoDenegadoComponent } from './acceso-denegado.component';

describe('AccesoDenegadoComponent', () => {
  let component: AccesoDenegadoComponent;
  let fixture: ComponentFixture<AccesoDenegadoComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      declarations: [AccesoDenegadoComponent],
      imports: [RouterTestingModule],
    }).compileComponents();
  });

  beforeEach(() => {
    fixture = TestBed.createComponent(AccesoDenegadoComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('muestra el encabezado de Acceso Denegado (403)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('.card-title')?.textContent).toContain('Acceso Denegado (403)');
    expect(compiled.querySelector('a')?.textContent).toContain('Volver a Mis Expedientes');
  });
});
