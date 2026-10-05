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

});
