import { Routes } from '@angular/router';

import { MisExpedientesComponent } from '../../mis-expedientes/mis-expedientes.component';
import { ReglamentosComponent } from '../../reglamentos/reglamentos.component';
import { GestionarExpedientesComponent } from '../../gestionar-expedientes/gestionar-expedientes.component';
import { VisorExpedienteComponent } from '../../gestionar-expedientes/visor-expediente/visor-expediente.component';

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
import { AccesoDenegadoComponent } from '../../acceso-denegado/acceso-denegado.component';

export const AdminLayoutRoutes: Routes = [
    { path: 'mis-expedientes',        component: MisExpedientesComponent },
    { path: 'reglamentos',            component: ReglamentosComponent },
    {
      path: 'gestionar-expedientes',
      component: GestionarExpedientesComponent,
      canActivate: [TribunalGuard],
      data: { roles: ['TD', 'CD'] }
    },
    {
      path: 'sala-tribunal',
      redirectTo: 'gestionar-expedientes',
      pathMatch: 'full'
    },
    {
      path: 'gestionar-expedientes/:id/visor',
      component: VisorExpedienteComponent,
      canActivate: [TribunalGuard],
      data: { roles: ['TD', 'CD'] }
    },
    {
      path: 'gestionar-expedientes/:id/descargo/:socioId',
      component: EnDesarrolloComponent,
      canActivate: [TribunalGuard],
      data: {
        titulo: 'Ver Descargo',
        descripcion: 'Visualización y resolución individual del descargo.',
        icono: 'description',
        roles: ['TD', 'CD']
      }
    },
    { path: 'calendario-institucional', component: CalendarioInstitucionalComponent },
    {
      path: 'reportes',
      component: ReportesComponent,
      canActivate: [TribunalGuard],
      data: { roles: ['TD', 'CD', 'REVISORES', 'FISCALIZADORA'] }
    },
    { path: 'ranking-socios',         component: RankingSociosComponent },
    {
      path: 'solicitar-puntos',
      component: SolicitarPuntosComponent,
      canActivate: [TribunalGuard],
      data: { roles: ['AUTORIDAD_SC', 'REVISORES', 'CD', 'TD', 'FISCALIZADORA'] }
    },
    {
      path: 'expedientes/crear',
      redirectTo: 'solicitar-puntos',
      pathMatch: 'full'
    },
    { 
      path: 'eventos-asistencia',     
      component: EventosAsistenciaComponent,
      canActivate: [TribunalGuard],
      data: { roles: ['CD', 'TD', 'AUTORIDAD_SC'] }
    },
    {
      path: 'eventos',
      component: EventosAsistenciaComponent,
      canActivate: [TribunalGuard],
      data: { roles: ['CD', 'TD', 'AUTORIDAD_SC'] }
    },
    { path: '403',                    component: AccesoDenegadoComponent },
    { path: 'acceso-denegado',        redirectTo: '403', pathMatch: 'full' },
    { path: 'dashboard',              component: DashboardComponent },
    { path: 'table-list',             component: TableListComponent },
    { path: 'typography',             component: TypographyComponent },
    { path: 'icons',                  component: IconsComponent },
    { path: 'maps',                   component: MapsComponent },
    { path: 'notifications',          component: NotificationsComponent },
    { path: 'upgrade',                component: UpgradeComponent },
    { path: '',                       redirectTo: 'mis-expedientes', pathMatch: 'full' }
];

