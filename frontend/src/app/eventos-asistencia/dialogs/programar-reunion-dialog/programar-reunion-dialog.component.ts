import { Component } from '@angular/core';
import { CrearEventoDialogComponent } from '../../../pages/eventos/dialogs/crear-evento-dialog/crear-evento-dialog.component';

@Component({
  selector: 'app-programar-reunion-dialog',
  templateUrl: '../../../pages/eventos/dialogs/crear-evento-dialog/crear-evento-dialog.component.html',
  styleUrls: ['../../../pages/eventos/dialogs/crear-evento-dialog/crear-evento-dialog.component.scss']
})
export class ProgramarReunionDialogComponent extends CrearEventoDialogComponent {}
