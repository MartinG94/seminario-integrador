import { Component, OnInit } from '@angular/core';

import { ExpedienteApiService, SolicitudT01, SolicitudT01Payload, TipoAccionT01 } from '../services/expediente-api.service';
import { PadronApiService, PadronSocio } from '../services/padron-api.service';

@Component({ selector: 'app-solicitar-puntos', templateUrl: './solicitar-puntos.component.html', styleUrls: ['./solicitar-puntos.component.scss'] })
export class SolicitarPuntosComponent implements OnInit {
  socios: PadronSocio[] = [];
  socioSeleccionado: number | null = null;
  tipoAccion: TipoAccionT01 = 'SANCTION';
  puntosSeleccionados: number | null = -1;
  causal = '';
  motivoTexto = '';
  anexoFecha = '';
  anexoLugar = '';
  anexoTestigos = '';
  anexoRelato = '';
  borradorId: string | null = null;
  estado: 'DRAFT' | 'ISSUED' | null = null;
  numeroExpediente: string | null = null;
  cargando = false;
  errorMensaje = '';
  exitoMensaje = '';

  escalasSancion = [
    { valor: -0.5, desc: '-0.5 pts: Falta Leve' }, { valor: -1, desc: '-1.0 pts: Falta Media' },
    { valor: -1.5, desc: '-1.5 pts: Falta Grave' }, { valor: -2, desc: '-2.0 pts: Falta Muy Grave' }
  ];
  escalasMerito = [
    { valor: 0.5, desc: '+0.5 pts: Reconocimiento Leve' }, { valor: 1, desc: '+1.0 pts: Reconocimiento Estándar' },
    { valor: 2, desc: '+2.0 pts: Reconocimiento Destacado' }, { valor: 3, desc: '+3.0 pts: Máximo Reconocimiento' }
  ];

  constructor(private padronApi: PadronApiService, private expedienteApi: ExpedienteApiService) {}

  ngOnInit(): void {
    this.padronApi.listarSocios().subscribe({
      next: socios => this.socios = socios,
      error: error => this.mostrarError(error)
    });
  }

  onTipoAccionChange(tipo: TipoAccionT01): void {
    this.tipoAccion = tipo;
    this.puntosSeleccionados = tipo === 'SANCTION' ? -1 : 1;
  }

  guardarBorrador(): void {
    this.errorMensaje = '';
    this.exitoMensaje = '';
    if (this.estado === 'ISSUED') return;
    this.cargando = true;
    const request = this.borradorId ? this.expedienteApi.actualizarBorrador(this.borradorId, this.payload()) : this.expedienteApi.crearBorrador(this.payload());
    request.subscribe({
      next: solicitud => { this.aplicarSolicitud(solicitud); this.exitoMensaje = 'Borrador guardado.'; this.cargando = false; },
      error: error => { this.mostrarError(error); this.cargando = false; }
    });
  }

  emitirT01(): void {
    this.errorMensaje = '';
    this.exitoMensaje = '';
    if (!this.validarEmision() || this.estado === 'ISSUED') return;
    this.cargando = true;
    const guardar = this.borradorId ? this.expedienteApi.actualizarBorrador(this.borradorId, this.payload()) : this.expedienteApi.crearBorrador(this.payload());
    guardar.subscribe({
      next: solicitud => this.emitirPersistido(solicitud),
      error: error => { this.mostrarError(error); this.cargando = false; }
    });
  }

  private emitirPersistido(solicitud: SolicitudT01): void {
    this.aplicarSolicitud(solicitud);
    this.expedienteApi.emitir(solicitud.id).subscribe({
      next: emitida => { this.aplicarSolicitud(emitida); this.exitoMensaje = `Expediente creado: ${emitida.numero_expediente}.`; this.cargando = false; },
      error: error => { this.mostrarError(error); this.cargando = false; }
    });
  }

  private payload(): SolicitudT01Payload {
    return { destinatario_socio_id: this.socioSeleccionado, tipo_accion: this.tipoAccion, causal: this.causal, puntos: this.puntosSeleccionados, motivo: this.motivoTexto, anexo_fecha: this.anexoFecha || null, anexo_lugar: this.anexoLugar, anexo_relato: this.anexoRelato, anexo_testigos: this.anexoTestigos };
  }

  private validarEmision(): boolean {
    if (this.socioSeleccionado === null) { this.errorMensaje = 'Selecciona al socio destinatario.'; return false; }
    if (!this.motivoTexto.trim()) { this.errorMensaje = 'Describe el motivo de la solicitud.'; return false; }
    if (this.puntosSeleccionados === null || this.puntosSeleccionados === undefined) { this.errorMensaje = 'Indica los puntos antes de emitir.'; return false; }
    if ((this.tipoAccion === 'SANCTION' && this.puntosSeleccionados >= 0) || (this.tipoAccion === 'MERIT' && this.puntosSeleccionados <= 0)) { this.errorMensaje = 'Los puntos no son coherentes con el tipo de acción.'; return false; }
    return true;
  }

  private aplicarSolicitud(solicitud: SolicitudT01): void {
    this.borradorId = solicitud.id;
    this.estado = solicitud.estado;
    this.numeroExpediente = solicitud.numero_expediente;
  }

  private mostrarError(error: { error?: { detail?: string; [key: string]: unknown } }): void {
    const body = error && error.error;
    if (body && body.detail) this.errorMensaje = body.detail;
    else if (body) this.errorMensaje = Object.values(body).flat().join(' ');
    else this.errorMensaje = 'No se pudo completar la operación.';
  }
}
