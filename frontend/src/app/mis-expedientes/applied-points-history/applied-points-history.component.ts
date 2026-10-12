import { Component, Input, OnChanges, OnDestroy, SimpleChanges } from '@angular/core';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { AppliedPointsEntryDTO } from '../../services/socio-api.service';
import { AppliedResolutionDialogComponent } from '../applied-resolution-dialog/applied-resolution-dialog.component';

export type PointsHistoryStatus = 'idle' | 'loading' | 'ready' | 'error';
let nextHistoryId = 0;

@Component({
  selector: 'app-applied-points-history',
  templateUrl: './applied-points-history.component.html',
  styleUrls: ['./applied-points-history.component.scss']
})
export class AppliedPointsHistoryComponent implements OnChanges, OnDestroy {
  @Input() entries: readonly AppliedPointsEntryDTO[] = [];
  @Input() status: PointsHistoryStatus = 'idle';
  readonly headingId = `applied-history-heading-${++nextHistoryId}`;
  private detail: MatDialogRef<AppliedResolutionDialogComponent> | null = null;

  constructor(private dialog: MatDialog) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['entries'] || changes['status']) { this.closeDetail(); }
  }

  ngOnDestroy(): void { this.closeDetail(); }

  openAppliedResolution(entry: AppliedPointsEntryDTO): void {
    if (this.status !== 'ready' || !this.entries.includes(entry)) { return; }
    this.closeDetail();
    this.detail = this.dialog.open(AppliedResolutionDialogComponent, {
      data: entry, width: 'calc(100vw - 2rem)', maxWidth: '800px', maxHeight: '90vh',
      ariaLabelledBy: 'applied-resolution-title', autoFocus: '.resolution-close', restoreFocus: true,
      exitAnimationDuration: '0ms'
    });
  }

  private closeDetail(): void {
    this.detail?.componentInstance?.clear();
    this.detail?.close();
    this.detail = null;
  }
}
