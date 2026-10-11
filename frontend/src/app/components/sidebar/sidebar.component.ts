import { Component, OnInit } from '@angular/core';
import { TribunalDataService } from '../../services/tribunal-data.service';
import { AuthService, PerfilSocio, RolRbac } from '../../services/auth.service';

declare const $: any;
export declare interface RouteInfo {
    path: string;
    title: string;
    icon: string;
    class: string;
    roles?: RolRbac[];
}

/** Módulo del sistema. Sólo el Tribunal se despliega y se navega. */
declare interface ModuloInfo {
    title: string;
    icon: string;
    secciones: RouteInfo[];
}

export const ROUTES: RouteInfo[] = [
    { path: '/mis-expedientes',        title: 'Mis Expedientes',       icon: 'folder_shared',    class: '' },
    { path: '/reglamentos',            title: 'Reglamentos',           icon: 'menu_book',        class: '' },
    { path: '/solicitar-puntos',       title: 'Crear Expediente',      icon: 'assignment_add',   class: '', roles: ['FISCALIZADORA', 'CD', 'TD'] },
    { path: '/ranking-socios',         title: 'Ranking de Socios',     icon: 'military_tech',    class: '' },
    { path: '/gestionar-expedientes',  title: 'Gestionar Expedientes', icon: 'gavel',           class: '', roles: ['TD', 'ADMIN', 'CD'] },
    { path: '/calendario-institucional', title: 'Calendario Institucional', icon: 'calendar_month', class: '' },
    { path: '/reportes',               title: 'Reportes & Balance',    icon: 'bar_chart',       class: '' },
    { path: '/eventos-asistencia',     title: 'Eventos & Asistencia',  icon: 'event_available', class: '' },
];

/**
 * Módulos fuera de alcance institucional: vacíos ya que todos se integraron en Tribunal.
 */
export const MODULOS_FUERA_DE_ALCANCE: ModuloInfo[] = [];

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent implements OnInit {
  menuItems: RouteInfo[] = [];
  modulosFueraDeAlcance = MODULOS_FUERA_DE_ALCANCE;
  tribunalDesplegado = true;
  perfil: PerfilSocio | null = null;

  constructor(
    public dataService: TribunalDataService,
    private auth: AuthService
  ) { }

  ngOnInit() {
    this.actualizarMenu();
    this.auth.perfil$.subscribe(perfil => {
      this.perfil = perfil;
      this.actualizarMenu();
    });
  }

  actualizarMenu(): void {
    this.menuItems = ROUTES.filter(route => {
      if (!route.roles || route.roles.length === 0) {
        return true;
      }
      return this.auth.tieneRol(...route.roles);
    });
  }

  alternarTribunal(): void {
    this.tribunalDesplegado = !this.tribunalDesplegado;
  }

  get iniciales(): string {
    if (!this.perfil) {
      return 'AV';
    }
    return `${this.perfil.first_name.charAt(0)}${this.perfil.last_name.charAt(0)}`.toUpperCase();
  }

  isMobileMenu() {
      if ($(window).width() > 991) {
          return false;
      }
      return true;
  };
}
