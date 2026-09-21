import { Routes } from '@angular/router';

import { MisExpedientesComponent } from '../../mis-expedientes/mis-expedientes.component';
import { ReglamentosComponent } from '../../reglamentos/reglamentos.component';
import { GestionarExpedientesComponent } from '../../gestionar-expedientes/gestionar-expedientes.component';
import { ReportesComponent } from '../../reportes/reportes.component';
import { RankingSociosComponent } from '../../ranking-socios/ranking-socios.component';
import { SolicitarPuntosComponent } from '../../solicitar-puntos/solicitar-puntos.component';
import { EventosAsistenciaComponent } from '../../eventos-asistencia/eventos-asistencia.component';
import { DashboardComponent } from '../../dashboard/dashboard.component';
import { UserProfileComponent } from '../../user-profile/user-profile.component';
import { TableListComponent } from '../../table-list/table-list.component';
import { TypographyComponent } from '../../typography/typography.component';
import { IconsComponent } from '../../icons/icons.component';
import { MapsComponent } from '../../maps/maps.component';
import { NotificationsComponent } from '../../notifications/notifications.component';
import { UpgradeComponent } from '../../upgrade/upgrade.component';

export const AdminLayoutRoutes: Routes = [
    { path: 'mis-expedientes',        component: MisExpedientesComponent },
    { path: 'reglamentos',            component: ReglamentosComponent },
    { path: 'gestionar-expedientes',  component: GestionarExpedientesComponent },
    { path: 'reportes',               component: ReportesComponent },
    { path: 'ranking-socios',         component: RankingSociosComponent },
    { path: 'solicitar-puntos',       component: SolicitarPuntosComponent },
    { path: 'eventos-asistencia',     component: EventosAsistenciaComponent },
    { path: 'dashboard',              component: DashboardComponent },
    { path: 'user-profile',           component: UserProfileComponent },
    { path: 'table-list',             component: TableListComponent },
    { path: 'typography',             component: TypographyComponent },
    { path: 'icons',                  component: IconsComponent },
    { path: 'maps',                   component: MapsComponent },
    { path: 'notifications',          component: NotificationsComponent },
    { path: 'upgrade',                component: UpgradeComponent },
    { path: '',                       redirectTo: 'mis-expedientes', pathMatch: 'full' }
];

