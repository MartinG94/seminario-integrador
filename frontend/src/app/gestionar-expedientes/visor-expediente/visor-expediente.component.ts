import { Component, OnDestroy, OnInit } from '@angular/core';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { AuthService } from '../../services/auth.service';
import {
  DecisionCausal,
  DescargoVisorDTO,
  EvidenciaVisorDTO,
  ExpedienteApiService,
  ExpedienteVisorData,
  InvolucradoVisorDTO,
} from '../../services/expediente-api.service';
import { NotificationService } from '../../services/notification.service';
import { NivelUrgencia } from '../../services/tribunal-data.service';

@Component({
  selector: 'app-visor-expediente',
  templateUrl: './visor-expediente.component.html',
  styleUrls: ['./visor-expediente.component.scss'],
})
export class VisorExpedienteComponent implements OnInit, OnDestroy {
  expedienteId: number | null = null;
  visorData: ExpedienteVisorData | null = null;
  cargando = true;
  errorCarga: string | null = null;
  anexoExpandido = false;

  // Modal para resolución de causal T02 (integración S4-02)
  modalCausalAbierto = false;
  involucradoSeleccionado: InvolucradoVisorDTO | null = null;
  borradorCausal = {
    decision: '' as DecisionCausal | '',
    fundamento: '',
  };
  registrandoCausal = false;

  // Modal para visualización directa de documentos
  modalPreviewAbierto = false;
  evidenciaPreview: EvidenciaVisorDTO | null = null;
  previewUrlRaw: string | null = null;
  previewUrlSafe: SafeResourceUrl | null = null;
  cargandoPreview = false;

  private destroy$ = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private expedienteApi: ExpedienteApiService,
    private auth: AuthService,
    private notifications: NotificationService,
    private sanitizer: DomSanitizer
  ) {}

  ngOnInit(): void {
    const idParam = this.route.snapshot.paramMap.get('id');
    if (idParam && !isNaN(Number(idParam))) {
      this.expedienteId = Number(idParam);
      this.cargarDatosVisor();
    } else {
      this.errorCarga = 'Identificador de expediente inválido.';
      this.cargando = false;
    }
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  cargarDatosVisor(): void {
    if (!this.expedienteId) return;
    this.cargando = true;
    this.errorCarga = null;

    this.expedienteApi
      .obtenerVisorExpediente(this.expedienteId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (data) => {
          this.visorData = data;
          this.cargando = false;
        },
        error: (err) => {
          this.cargando = false;
          if (err.status === 403) {
            this.errorCarga = 'Acceso denegado: No posee facultades para consultar esta causa reservada.';
            this.notifications.error('No tenés permisos para sustanciar o consultar este expediente.');
          } else if (err.status === 404) {
            this.errorCarga = 'El expediente solicitado no existe o fue archivado.';
            this.notifications.error('Expediente no encontrado.');
          } else {
            this.errorCarga = 'Ocurrió un error al cargar los datos del expediente. Intente nuevamente.';
            this.notifications.error('Error al cargar la causa disciplinaria.');
          }
        },
      });
  }

  volverAlTablero(): void {
    this.router.navigate(['/gestionar-expedientes']);
  }

  toggleAnexo(): void {
    this.anexoExpandido = !this.anexoExpandido;
  }

  descargarEvidencia(ev: EvidenciaVisorDTO): void {
    if (!this.expedienteId) return;

    this.expedienteApi
      .descargarEvidencia(this.expedienteId, ev.id, 'descarga')
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (blob) => {
          const url = URL.createObjectURL(blob);
          const enlace = document.createElement('a');
          enlace.href = url;
          enlace.download = ev.nombre_original || 'evidencia_custodiada';
          enlace.click();
          setTimeout(() => URL.revokeObjectURL(url), 30000);
          this.notifications.info(`Descargando comprobante: ${ev.nombre_original}`);
          // Recargar el visor para reflejar la auditoría de descarga en el timeline
          setTimeout(() => {
            if (this.expedienteId) {
              this.cargarDatosVisor();
            }
          }, 500);
        },
        error: (err) => {
          if (err.status === 403) {
            this.notifications.error('Acceso reservado: no está autorizado a descargar este comprobante médico.');
          } else {
            this.notifications.error('No se pudo descargar el archivo probatorio.');
          }
        },
      });
  }

  verEvidencia(ev: EvidenciaVisorDTO): void {
    if (!this.expedienteId) return;
    this.evidenciaPreview = ev;
    this.cargandoPreview = true;
    this.modalPreviewAbierto = true;

    this.expedienteApi
      .descargarEvidencia(this.expedienteId, ev.id, 'ver')
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (blob) => {
          this.cargandoPreview = false;
          const mime = ev.mime_type || (ev.extension === 'pdf' ? 'application/pdf' : 'image/jpeg');
          const blobConMime = new Blob([blob], { type: mime });
          this.previewUrlRaw = URL.createObjectURL(blobConMime);
          this.previewUrlSafe = this.sanitizer.bypassSecurityTrustResourceUrl(this.previewUrlRaw);
          // Actualizar auditoría en timeline
          setTimeout(() => {
            if (this.expedienteId) this.cargarDatosVisor();
          }, 500);
        },
        error: (err) => {
          this.cargandoPreview = false;
          this.cerrarModalPreview();
          if (err.status === 403) {
            this.notifications.error('Acceso reservado: no está autorizado a visualizar este comprobante médico.');
          } else {
            this.notifications.error('No se pudo abrir el documento probatorio.');
          }
        },
      });
  }

  cerrarModalPreview(): void {
    this.modalPreviewAbierto = false;
    if (this.previewUrlRaw) {
      URL.revokeObjectURL(this.previewUrlRaw);
      this.previewUrlRaw = null;
      this.previewUrlSafe = null;
    }
    this.evidenciaPreview = null;
  }

  esPdf(ev: EvidenciaVisorDTO | null): boolean {
    if (!ev) return false;
    return (ev.extension || '').toLowerCase() === 'pdf' || (ev.mime_type || '').includes('pdf');
  }

  esImagen(ev: EvidenciaVisorDTO | null): boolean {
    if (!ev) return false;
    const ext = (ev.extension || '').toLowerCase();
    const mime = (ev.mime_type || '').toLowerCase();
    return ['png', 'jpg', 'jpeg', 'webp', 'gif'].includes(ext) || mime.startsWith('image/');
  }

  abrirEvaluacionCausal(inv: InvolucradoVisorDTO): void {
    if (!inv.descargo || inv.descargo.tipo !== 'T02_CERTIFICADO') return;
    this.involucradoSeleccionado = inv;
    const regla = inv.descargo.regla_sugerida || 'REJECTED';
    this.borradorCausal = {
      decision: regla,
      fundamento: '',
    };
    this.modalCausalAbierto = true;
  }

  cerrarModalCausal(): void {
    this.modalCausalAbierto = false;
    this.involucradoSeleccionado = null;
    this.borradorCausal = { decision: '', fundamento: '' };
  }

  guardarDecisionCausal(): void {
    const descargo = this.involucradoSeleccionado?.descargo;
    if (!this.expedienteId || !descargo || this.registrandoCausal) return;

    if (!this.borradorCausal.decision) {
      this.notifications.warning('Seleccioná si aceptás o rechazás la causal.');
      return;
    }

    const regla = descargo.regla_sugerida;
    const seAparta = Boolean(regla && this.borradorCausal.decision !== regla);
    const esRechazo = this.borradorCausal.decision === 'REJECTED';

    if ((esRechazo || seAparta) && (!this.borradorCausal.fundamento || this.borradorCausal.fundamento.trim().length < 20)) {
      this.notifications.warning('El fundamento escrito es obligatorio (mínimo 20 caracteres) al rechazar o apartarse de la regla sugerida.');
      return;
    }

    this.registrandoCausal = true;
    const idsEvidencias = (descargo.evidencias || []).filter((e) => e.es_vigente).map((e) => e.id);

    this.expedienteApi
      .registrarDecisionCausal(this.expedienteId, descargo.id, {
        decision: this.borradorCausal.decision,
        fundamento: this.borradorCausal.fundamento.trim(),
        evidencia_ids: idsEvidencias,
      })
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: () => {
          this.registrandoCausal = false;
          this.cerrarModalCausal();
          this.notifications.success('Decisión de causal registrada correctamente.');
          this.cargarDatosVisor();
        },
        error: (err) => {
          this.registrandoCausal = false;
          const msg = err.error?.detail || err.error?.error || 'No se pudo registrar la decisión.';
          this.notifications.error(msg);
        },
      });
  }

  get esVocalTd(): boolean {
    return this.auth.tieneRol('TD', 'ADMIN');
  }

  formatBytes(bytes: number): string {
    if (!bytes || bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  }

  getUrgenciaBadgeClass(urgencia?: NivelUrgencia): string {
    switch (urgencia) {
      case 'urgente':
        return 'badge-urgencia-alta';
      case 'baja':
        return 'badge-urgencia-baja';
      default:
        return 'badge-urgencia-normal';
    }
  }

  getEstadoBadgeClass(estado?: string): string {
    switch (estado) {
      case 'creado':
        return 'badge-estado-creado';
      case 'justificando':
        return 'badge-estado-justificando';
      case 'revision_resolucion':
        return 'badge-estado-revision';
      case 'espera_resolucion':
        return 'badge-estado-espera';
      case 'emitido':
        return 'badge-estado-emitido';
      case 'archivado':
        return 'badge-estado-archivado';
      default:
        return 'badge-estado-default';
    }
  }
}
