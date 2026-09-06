import { Component, OnInit } from '@angular/core';
import { TribunalDataService, RolUsuario } from '../../services/tribunal-data.service';

declare const $: any;
declare interface RouteInfo {
    path: string;
    title: string;
    icon: string;
    class: string;
}
export const ROUTES: RouteInfo[] = [
    { path: '/mis-expedientes',        title: 'Mis Expedientes',       icon: 'folder_shared',    class: '' },
    { path: '/gestionar-expedientes',  title: 'Gestionar Expedientes', icon: 'gavel',            class: '' },
    { path: '/reportes',               title: 'Reportes & Balance',    icon: 'bar_chart',        class: '' },
    { path: '/ranking-socios',         title: 'Ranking de Socios',     icon: 'military_tech',    class: '' },
    { path: '/solicitar-puntos',       title: 'Solicitar Puntos',      icon: 'assignment_add',   class: '' },
    { path: '/eventos-asistencia',     title: 'Eventos & Asistencia',  icon: 'event_available',  class: '' },
];

@Component({
  selector: 'app-sidebar',
  templateUrl: './sidebar.component.html',
  styleUrls: ['./sidebar.component.css']
})
export class SidebarComponent implements OnInit {
  menuItems: any[];
  currentRole: RolUsuario = 'tribunal';

  constructor(public dataService: TribunalDataService) { }

  ngOnInit() {
    this.menuItems = ROUTES.filter(menuItem => menuItem);
    this.dataService.currentRole$.subscribe(role => {
      this.currentRole = role;
    });
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
