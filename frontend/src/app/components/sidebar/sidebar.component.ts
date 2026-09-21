import { Component, OnInit } from '@angular/core';
import { TribunalDataService, RolUsuario } from '../../services/tribunal-data.service';
import { AuthService, PerfilSocio } from '../../services/auth.service';

declare const $: any;
declare interface RouteInfo {
    path: string;
    title: string;
    icon: string;
    class: string;
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
    { path: '/solicitar-puntos',       title: 'Solicitar T-01',        icon: 'assignment_add',   class: '' },
];

/**
 * Módulos que la aplicación contempla pero que quedan fuera del alcance de
 * esta tesis: se listan para dar contexto institucional, sin navegación.
 */
export const MODULOS_FUERA_DE_ALCANCE: ModuloInfo[] = [
    { title: 'Gestionar Expedientes', icon: 'gavel',           secciones: [] },
    { title: 'Reportes & Balance',    icon: 'bar_chart',       secciones: [] },
    { title: 'Ranking de Socios',     icon: 'military_tech',   secciones: [] },
    { title: 'Eventos & Asistencia',  icon: 'event_available', secciones: [] },
];

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent implements OnInit {
  menuItems: any[];
  modulosFueraDeAlcance = MODULOS_FUERA_DE_ALCANCE;
  tribunalDesplegado = true;
  currentRole: RolUsuario = 'tribunal';
  perfil: PerfilSocio | null = null;

  constructor(
    public dataService: TribunalDataService,
    private auth: AuthService
  ) { }

  ngOnInit() {
    this.menuItems = ROUTES.filter(menuItem => menuItem);
    this.dataService.currentRole$.subscribe(role => {
      this.currentRole = role;
    });
    this.auth.perfil$.subscribe(perfil => this.perfil = perfil);
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

  onRoleChange(newRole: RolUsuario): void {
    this.dataService.setRole(newRole);
  }
}
