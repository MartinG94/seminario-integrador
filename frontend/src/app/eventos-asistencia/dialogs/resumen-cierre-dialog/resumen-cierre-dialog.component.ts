import { Component } from '@angular/core';
import { ResumenCierreDialogComponent } from '../../../pages/eventos/dialogs/resumen-cierre-dialog/resumen-cierre-dialog.component';

export * from '../../../pages/eventos/dialogs/resumen-cierre-dialog/resumen-cierre-dialog.component';

@Component({
  selector: 'app-resumen-cierre-dialog-alias',
  templateUrl: '../../../pages/eventos/dialogs/resumen-cierre-dialog/resumen-cierre-dialog.component.html',
  styleUrls: ['../../../pages/eventos/dialogs/resumen-cierre-dialog/resumen-cierre-dialog.component.scss']
})
export class ResumenCierreDialogComponentAlias extends ResumenCierreDialogComponent {}
