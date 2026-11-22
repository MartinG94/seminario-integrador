import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { NavbarComponent } from './navbar.component';

describe('NavbarComponent', () => {
  let component: NavbarComponent;
  let fixture: ComponentFixture<NavbarComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [ HttpClientTestingModule, RouterTestingModule ],
      declarations: [ NavbarComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(NavbarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('muestra numero_socio cuando está definido y — como fallback', () => {
    component.perfil = {
      legajo: '99999',
      numero_socio: 74907,
      first_name: 'Lucas',
      last_name: 'Gastiaburu',
      email: '74907@aveit.test',
      role: 'SOCIO',
      category: 'ACTIVE',
      category_display: 'Socio Activo',
      subcomision: 'Cómputos'
    };
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('N° 74907 · SOCIO');
    expect(fixture.nativeElement.textContent).toContain('Número de Socio 74907');

    component.perfil = { ...component.perfil, numero_socio: null };
    fixture.detectChanges();
    expect(fixture.nativeElement.textContent).toContain('N° — · SOCIO');
    expect(fixture.nativeElement.textContent).toContain('Número de Socio —');
  });
});
