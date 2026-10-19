import { Routes } from '@angular/router';

import { MisExpedientesComponent } from '../../mis-expedientes/mis-expedientes.component';
import { ReglamentosComponent } from '../../reglamentos/reglamentos.component';
import { GestionarExpedientesComponent } from '../../gestionar-expedientes/gestionar-expedientes.component';
import { ReportesComponent } from '../../reportes/reportes.component';
import { RankingSociosComponent } from '../../ranking-socios/ranking-socios.component';
import { SolicitarPuntosComponent } from '../../solicitar-puntos/solicitar-puntos.component';
import { EventosAsistenciaComponent } from '../../eventos-asistencia/eventos-asistencia.component';
import { DashboardComponent } from '../../dashboard/dashboard.component';
import { TableListComponent } from '../../table-list/table-list.component';
import { TypographyComponent } from '../../typography/typography.component';
import { IconsComponent } from '../../icons/icons.component';
import { MapsComponent } from '../../maps/maps.component';
import { NotificationsComponent } from '../../notifications/notifications.component';
import { UpgradeComponent } from '../../upgrade/upgrade.component';
import { TribunalGuard } from '../../services/tribunal.guard';
import { EnDesarrolloComponent } from '../../components/en-desarrollo/en-desarrollo.component';
import { CalendarioInstitucionalComponent } from '../../calendario-institucional/calendario-institucional.component';

export const AdminLayoutRoutes: Routes = [
    { path: 'mis-expedientes',        component: MisExpedientesComponent },
    { 
      path: 'reglamentos',            
      component: EnDesarrolloComponent,
      data: {
        titulo: 'Reglamentos',
        descripcion: 'Consulta del Estatuto Social, el Reglamento Interno de Disciplina y el Reglamento Procesal Disciplinario 2026.',
        icono: 'construction'
      }
    },
    { path: 'gestionar-expedientes',  component: GestionarExpedientesComponent, canActivate: [TribunalGuard] },
    { path: 'calendario-institucional', component: CalendarioInstitucionalComponent },
    { 
      path: 'reportes',               
      component: EnDesarrolloComponent,
      data: {
        titulo: 'Reportes & Balance',
        descripcion: 'Emisión de balances cuatrimestrales, métricas de sanciones y reconocimientos por subcomisión.',
        icono: 'bar_chart'
      }
    },
    { path: 'ranking-socios',         component: RankingSociosComponent },
    {
      path: 'solicitar-puntos',
      component: SolicitarPuntosComponent,
      canActivate: [TribunalGuard],
      data: { roles: ['FISCALIZADORA', 'CD', 'TD'] }
    },
    { 
      path: 'eventos-asistencia',     
      component: EnDesarrolloComponent,
      data: {
        titulo: 'Eventos & Asistencia',
        descripcion: 'Programación de actividades institucionales obligatorias con registro digital de asistencia.',
        icono: 'event_available'
      }
    },
    { path: 'dashboard',              component: DashboardComponent },
    { path: 'table-list',             component: TableListComponent },
    { path: 'typography',             component: TypographyComponent },
    { path: 'icons',                  component: IconsComponent },
    { path: 'maps',                   component: MapsComponent },
    { path: 'notifications',          component: NotificationsComponent },
    { path: 'upgrade',                component: UpgradeComponent },
    { path: '',                       redirectTo: 'mis-expedientes', pathMatch: 'full' }
];

