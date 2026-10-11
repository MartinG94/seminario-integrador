import { Component } from '@angular/core';
import { NotificationService, NotificationType } from '../services/notification.service';

@Component({
  selector: 'app-notifications',
  templateUrl: './notifications.component.html',
  styleUrls: ['./notifications.component.css']
})
export class NotificationsComponent {
  readonly examples: { type: NotificationType; label: string; message: string }[] = [
    { type: 'success', label: 'Éxito', message: 'Los cambios se guardaron correctamente.' },
    { type: 'error', label: 'Error', message: 'No se pudo completar la operación. Intentá nuevamente.' },
    { type: 'warning', label: 'Advertencia', message: 'Revisá los datos antes de continuar.' },
    { type: 'info', label: 'Información', message: 'Podés cerrar este aviso con la X.' }
  ];
  constructor(private notifications: NotificationService) {}
  showNotification(type: NotificationType, message: string): void { this.notifications.show(type, message); }
}
