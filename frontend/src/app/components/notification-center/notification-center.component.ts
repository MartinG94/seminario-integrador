import { DOCUMENT } from '@angular/common';
import { AfterViewInit, Component, HostListener, Inject, OnDestroy, ViewChild } from '@angular/core';
import { Overlay, OverlayRef } from '@angular/cdk/overlay';
import { CdkPortal, DomPortal, DomPortalOutlet } from '@angular/cdk/portal';
import { MatDialog, MatDialogRef, MatDialogState } from '@angular/material/dialog';
import { Subscription } from 'rxjs';
import { NotificationService, NotificationType, UserNotification } from '../../services/notification.service';

@Component({
  selector: 'app-notification-center',
  templateUrl: './notification-center.component.html',
  styleUrls: ['./notification-center.component.scss']
})
export class NotificationCenterComponent implements AfterViewInit, OnDestroy {
  @ViewChild(CdkPortal, { static: true }) portal: CdkPortal;
  private overlayRef: OverlayRef | null = null;
  private notificationElement: HTMLElement | null = null;
  private dialogOutlet: DomPortalOutlet | null = null;
  private activeDialog: MatDialogRef<unknown> | null = null;
  private dialogSubscriptions = new Subscription();
  private subscriptions = new Subscription();
  private lastFocusedElement: HTMLElement | null = null;
  readonly icons: Record<NotificationType, string> = {
    success: 'check_circle', error: 'error_outline', warning: 'warning_amber', info: 'info'
  };
  readonly labels: Record<NotificationType, string> = {
    success: 'Éxito', error: 'Error', warning: 'Atención', info: 'Información'
  };

  constructor(public notifications: NotificationService, private overlay: Overlay,
    private dialog: MatDialog, @Inject(DOCUMENT) private document: Document) {}

  ngAfterViewInit(): void {
    this.overlayRef = this.overlay.create({
      positionStrategy: this.overlay.position().global().bottom('1rem').right('1rem'),
      scrollStrategy: this.overlay.scrollStrategies.noop(),
      hasBackdrop: false
    });
    // Un portal fuera de app-root sigue accesible cuando MatDialog oculta la página.
    this.overlayRef.hostElement.style.zIndex = '2000';
    const view = this.overlayRef.attach(this.portal);
    this.notificationElement = view.rootNodes.find(node => node instanceof HTMLElement) || null;
    this.subscriptions.add(this.dialog.afterOpened.subscribe(ref => {
      this.subscriptions.add(ref.afterOpened().subscribe(() => this.followDialog(ref)));
    }));
    this.subscriptions.add(this.notifications.messages$.subscribe(items => {
      const focused = this.document.activeElement as HTMLElement | null;
      const notice = focused?.closest('[data-notification-id]');
      if (notice && this.notificationElement?.contains(notice) &&
        !items.some(item => String(item.id) === notice.getAttribute('data-notification-id'))) {
        this.restoreFocus();
      }
    }));
    this.followDialog();
  }

  @HostListener('document:focusin', ['$event'])
  rememberFocus(event: FocusEvent): void {
    const target = event.target;
    if (target instanceof HTMLElement && !this.notificationElement?.contains(target)) {
      this.lastFocusedElement = target;
    }
  }

  private followDialog(ref?: MatDialogRef<unknown>): void {
    this.dialogSubscriptions.unsubscribe();
    this.dialogSubscriptions = new Subscription();
    this.releaseDialogOutlet();
    this.activeDialog = ref || [...this.dialog.openDialogs].reverse()
      .find(item => item.getState() === MatDialogState.OPEN) || null;
    const container = this.activeDialog && this.document.getElementById(this.activeDialog.id);
    if (!container || !this.notificationElement) { return; }
    // El mismo DOM y sus temporizadores pasan al foco/árbol accesible del modal.
    const outletElement = this.document.createElement('div');
    container.appendChild(outletElement);
    this.dialogOutlet = new DomPortalOutlet(outletElement, undefined, undefined, undefined, this.document);
    this.dialogOutlet.attach(new DomPortal(this.notificationElement));
    this.dialogSubscriptions.add(this.activeDialog.beforeClosed().subscribe(() => this.releaseDialogOutlet()));
    this.dialogSubscriptions.add(this.activeDialog.afterClosed().subscribe(() => this.followDialog()));
  }

  private releaseDialogOutlet(): void {
    this.dialogOutlet?.dispose();
    this.dialogOutlet = null;
  }

  private restoreFocus(): void {
    const container = this.activeDialog && this.document.getElementById(this.activeDialog.id);
    const last = this.lastFocusedElement;
    const target = last?.isConnected && !last.closest('[aria-hidden="true"]') &&
      (!container || container.contains(last)) ? last : container;
    target?.focus();
  }

  trackNotification(_index: number, item: UserNotification): number { return item.id; }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    this.dialogSubscriptions.unsubscribe();
    this.releaseDialogOutlet();
    this.overlayRef?.dispose();
  }
}
