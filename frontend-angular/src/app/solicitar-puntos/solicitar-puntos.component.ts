import { Component, OnInit } from '@angular/core';
import { TribunalDataService, Socio } from '../services/tribunal-data.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-solicitar-puntos',
  templateUrl: './solicitar-puntos.component.html',
  styleUrls: ['./solicitar-puntos.component.scss']
})
export class SolicitarPuntosComponent implements OnInit {
  socios: Socio[] = [];
  subcomisiones = [
    'Comunicaciones', 'Deportes', 'Extensión Universitaria', 
    'Finanzas', 'Prensa y Difusión', 'Relaciones Públicas', 'Tesorería'
  ];

  // Modelo del Formulario T01
  socioSeleccionado = '';
  subcomisionSeleccionada = 'Finanzas';
  tipoAccion: 'falta' | 'merito' = 'falta';
  puntosSeleccionados = -1.0;
  motivoTexto = '';

  // Hoja de Anexo Circunstanciada Obligatoria
  anexoFecha = new Date().toISOString().split('T')[0];
  anexoTestigos = '';
  anexoRelato = '';

  errorMensaje = '';
  exitoMensaje = '';

  escalasSancion = [
    { valor: -0.5, desc: '-0.5 pts: Falta Leve (Llegada tarde a convocatoria obligatoria)' },
    { valor: -1.0, desc: '-1.0 pts: Falta Media (Inasistencia injustificada a asamblea o evento institucional)' },
    { valor: -1.5, desc: '-1.5 pts: Falta Grave (Omisión reiterada de informes y tareas operativas)' },
    { valor: -2.0, desc: '-2.0 pts: Falta Muy Grave (Conducta lesiva al patrimonio o principios asociativos)' }
  ];

  escalasMerito = [
    { valor: 0.5, desc: '+0.5 pts: Reconocimiento Leve (Colaboración voluntaria en eventos)' },
    { valor: 1.0, desc: '+1.0 pts: Reconocimiento Estándar (Cumplimiento sobresaliente en subcomisión)' },
    { valor: 2.0, desc: '+2.0 pts: Reconocimiento Destacado (Liderazgo exitoso en proyecto técnico o social)' },
    { valor: 3.0, desc: '+3.0 pts: Máximo Reconocimiento (Aporte extraordinario al prestigio de AVEIT)' }
  ];

  constructor(
    public dataService: TribunalDataService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.dataService.socios$.subscribe(list => {
      this.socios = list;
      if (list.length > 0) {
        this.socioSeleccionado = list[0].nombre;
      }
    });
  }

  onTipoAccionChange(nuevoTipo: 'falta' | 'merito'): void {
    this.tipoAccion = nuevoTipo;
    this.puntosSeleccionados = nuevoTipo === 'falta' ? -1.0 : 1.0;
  }

  enviarSolicitud(): void {
    this.errorMensaje = '';
    this.exitoMensaje = '';

    if (!this.socioSeleccionado) {
      this.errorMensaje = 'Selecciona al socio o miembro implicado.';
      return;
    }
    if (!this.motivoTexto.trim()) {
      this.errorMensaje = 'Describe el motivo sucinto de la solicitud reglamentaria.';
      return;
    }
    if (!this.anexoRelato.trim()) {
      this.errorMensaje = 'La Hoja de Anexo Circunstanciada es obligatoria. Describe detalladamente el relato de los hechos.';
      return;
    }
    if (!this.anexoTestigos.trim()) {
      this.errorMensaje = 'Indica al menos un testigo presencial o autoridad informante en el anexo.';
      return;
    }

    const exp = this.dataService.solicitarPuntos({
      socio: this.socioSeleccionado,
      subcomision: this.subcomisionSeleccionada,
      tipo: this.tipoAccion,
      puntos: this.puntosSeleccionados,
      motivo: this.motivoTexto,
      anexoRelato: this.anexoRelato,
      anexoFecha: this.anexoFecha,
      anexoTestigos: this.anexoTestigos
    });

    this.exitoMensaje = `Solicitud procesada con éxito. Se ha generado el expediente ${exp.numero} en estado Expediente Creado.`;

    // Limpiar formulario
    this.motivoTexto = '';
    this.anexoRelato = '';
    this.anexoTestigos = '';

    setTimeout(() => {
      this.router.navigate(['/gestionar-expedientes']);
    }, 2500);
  }
}
