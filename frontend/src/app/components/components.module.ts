import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { FormsModule } from '@angular/forms';

import { FooterComponent } from './footer/footer.component';
import { NavbarComponent } from './navbar/navbar.component';
import { SidebarComponent } from './sidebar/sidebar.component';
import { TablaReglamentosComponent } from './tabla-reglamentos/tabla-reglamentos.component';
import { TablaExpedientesReferenciadosComponent } from './tabla-expedientes-referenciados/tabla-expedientes-referenciados.component';
import { ModalSelectorExpedientesComponent } from './modal-selector-expedientes/modal-selector-expedientes.component';

@NgModule({
  imports: [
    CommonModule,
    RouterModule,
    FormsModule,
  ],
  declarations: [
    FooterComponent,
    NavbarComponent,
    SidebarComponent,
    TablaReglamentosComponent,
    TablaExpedientesReferenciadosComponent,
    ModalSelectorExpedientesComponent
  ],
  exports: [
    FooterComponent,
    NavbarComponent,
    SidebarComponent,
    TablaReglamentosComponent,
    TablaExpedientesReferenciadosComponent,
    ModalSelectorExpedientesComponent
  ]
})
export class ComponentsModule { }
