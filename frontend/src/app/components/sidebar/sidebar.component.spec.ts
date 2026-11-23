import { HttpClientTestingModule } from '@angular/common/http/testing';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';

import { AuthService } from '../../services/auth.service';
import { ROUTES, SidebarComponent } from './sidebar.component';

describe('SidebarComponent', () => {
  let component: SidebarComponent;
  let fixture: ComponentFixture<SidebarComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      imports: [ HttpClientTestingModule, RouterTestingModule ],
      declarations: [ SidebarComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(SidebarComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });

  it('oculta Gestionar Expedientes para un socio ordinario', () => {
    const authService = TestBed.inject(AuthService);
    spyOn(authService, 'tieneRol').and.callFake((...roles) => roles.includes('SOCIO'));
    component.actualizarMenu();
    const titulos = component.menuItems.map(m => m.title);
    expect(titulos).not.toContain('Gestionar Expedientes');
  });

  it('muestra Gestionar Expedientes para miembros del TD, CD y ADMIN', () => {
    const authService = TestBed.inject(AuthService);
    spyOn(authService, 'tieneRol').and.callFake((...roles) => roles.includes('TD'));
    component.actualizarMenu();
    const titulos = component.menuItems.map(m => m.title);
    expect(titulos).toContain('Gestionar Expedientes');
  });

  it('incluye Reportes & Balance y Eventos & Asistencia en el menú de Tribunal', () => {
    const authService = TestBed.inject(AuthService);
    spyOn(authService, 'tieneRol').and.callFake((...roles) => roles.includes('TD'));
    component.actualizarMenu();
    const titulos = component.menuItems.map(m => m.title);
    expect(titulos).toContain('Reportes & Balance');
    expect(titulos).toContain('Eventos & Asistencia');
  });

  it('oculta Crear Expediente para un socio ordinario', () => {
    const authService = TestBed.inject(AuthService);
    spyOn(authService, 'tieneRol').and.callFake((...roles) => roles.includes('SOCIO'));
    component.actualizarMenu();
    const titulos = component.menuItems.map(m => m.title);
    expect(titulos).not.toContain('Crear Expediente');
  });

  it('muestra Crear Expediente para autoridades procesales', () => {
    const authService = TestBed.inject(AuthService);
    spyOn(authService, 'tieneRol').and.callFake((...roles) => roles.includes('CD'));
    component.actualizarMenu();
    const titulos = component.menuItems.map(m => m.title);
    expect(titulos).toContain('Crear Expediente');
  });

  it('muestra Administración sólo al rol ADMIN', () => {
    const authService = TestBed.inject(AuthService);
    const spy = spyOn(authService, 'tieneRol').and.callFake((...roles) => roles.includes('TD'));
    component.actualizarMenu();
    expect(component.menuItems.map(m => m.title)).not.toContain('Administración');

    spy.and.callFake((...roles) => roles.includes('ADMIN'));
    component.actualizarMenu();
    expect(component.menuItems.map(m => m.title)).toContain('Administración');
    expect(ROUTES.find(item => item.path === '/admin/parametros')?.roles).toEqual(['ADMIN']);
  });

  it('declara los roles procesales para Crear Expediente', () => {
    const route = ROUTES.find(item => item.path === '/solicitar-puntos');
    expect(route?.roles).toEqual(['FISCALIZADORA', 'CD', 'TD']);
  });

  it('incluye Crear Expediente en el menu para un rol autorizado', () => {
    const authService = TestBed.inject(AuthService);
    spyOn(authService, 'tieneRol').and.returnValue(true);
    component.actualizarMenu();
    const titulos = component.menuItems.map(m => m.title);
    expect(titulos).toContain('Crear Expediente');
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
    expect(fixture.nativeElement.querySelector('.user-role')?.textContent).toContain('N° de Socio 74907 · SOCIO');

    component.perfil = { ...component.perfil, numero_socio: null };
    fixture.detectChanges();
    expect(fixture.nativeElement.querySelector('.user-role')?.textContent).toContain('N° de Socio — · SOCIO');
  });

});
