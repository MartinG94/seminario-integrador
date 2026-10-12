import { Component, Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { AppliedPointsEntryDTO } from '../../services/socio-api.service';

@Component({
  selector: 'app-applied-resolution-dialog',
  templateUrl: './applied-resolution-dialog.component.html',
  styleUrls: ['./applied-resolution-dialog.component.scss']
})
export class AppliedResolutionDialogComponent {
  constructor(
    @Inject(MAT_DIALOG_DATA) public entry: AppliedPointsEntryDTO | null,
    private dialogRef: MatDialogRef<AppliedResolutionDialogComponent>
  ) {}

  clear(): void { this.entry = null; }

  close(): void { this.dialogRef.close(); }
}
