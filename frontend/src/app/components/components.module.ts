import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule } from '@angular/router';

import { FooterComponent } from './footer/footer.component';
import { NavbarComponent } from './navbar/navbar.component';
import { SidebarComponent } from './sidebar/sidebar.component';
import { TablaReglamentosComponent } from './tabla-reglamentos/tabla-reglamentos.component';

@NgModule({
  imports: [
    CommonModule,
    RouterModule,
  ],
  declarations: [
    FooterComponent,
    NavbarComponent,
    SidebarComponent,
    TablaReglamentosComponent
  ],
  exports: [
    FooterComponent,
    NavbarComponent,
    SidebarComponent,
    TablaReglamentosComponent
  ]
})
export class ComponentsModule { }
