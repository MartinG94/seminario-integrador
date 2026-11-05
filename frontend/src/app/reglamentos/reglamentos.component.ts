import { Component, OnInit } from '@angular/core';

import { AuthService } from '../services/auth.service';
import {
  ArticuloReglamentoDTO,
  ExpedienteApiService,
  GuardarArticuloReglamentoPayload,
  TipoDocumentoReglamento
} from '../services/expediente-api.service';
import { httpErrorMessage, NotificationService } from '../services/notification.service';

@Component({
  selector: 'app-reglamentos',
  templateUrl: './reglamentos.component.html',
  styleUrls: ['./reglamentos.component.scss']
})
export class ReglamentosComponent implements OnInit {
  tabActiva: TipoDocumentoReglamento = 'Reglamento Interno';
  busqueda = '';
  articulos: ArticuloReglamentoDTO[] = [];
  cargando = false;

  modalAbierto = false;
  modoEdicion = false;
  articuloEnEdicionId: number | null = null;

  articulo: number | null = null;
  inciso = '';
  cuerpo = '';

  modalEliminarAbierto = false;
  articuloAEliminar: ArticuloReglamentoDTO | null = null;

  constructor(
    private expedienteService: ExpedienteApiService,
    private authService: AuthService,
    private notificationService: NotificationService
  ) {}

  ngOnInit(): void {
    this.cargarArticulos();
  }

  puedeGestionar(): boolean {
    return this.authService.tieneRol('TD', 'CD', 'ADMIN');
  }

  seleccionarPestana(tab: TipoDocumentoReglamento): void {
    if (this.tabActiva === tab) {
      return;
    }
    this.tabActiva = tab;
    this.cargarArticulos();
  }

  seleccionarPestaña(tab: TipoDocumentoReglamento): void {
    this.seleccionarPestana(tab);
  }

  cargarArticulos(): void {
    this.cargando = true;
    const params = {
      titulo: this.tabActiva,
      search: this.busqueda ? this.busqueda.trim() : undefined
    };

    this.expedienteService.listarArticulosReglamento(params).subscribe({
      next: (articulos) => {
        this.articulos = articulos || [];
        this.cargando = false;
      },
      error: (err) => {
        this.cargando = false;
        this.notificationService.error(httpErrorMessage(err, 'Error al cargar los artículos del reglamento.'));
      }
    });
  }

  onSearchChange(): void {
    this.cargarArticulos();
  }

  abrirModalCrear(): void {
    this.modoEdicion = false;
    this.articuloEnEdicionId = null;
    this.articulo = null;
    this.inciso = '';
    this.cuerpo = '';
    this.modalAbierto = true;
  }

  abrirModalEditar(art: ArticuloReglamentoDTO): void {
    this.modoEdicion = true;
    this.articuloEnEdicionId = art.id;
    this.articulo = art.articulo;
    this.inciso = art.inciso === '-' ? '' : art.inciso;
    this.cuerpo = art.cuerpo || art.descripcion || '';
    this.modalAbierto = true;
  }

  cerrarModal(): void {
    this.modalAbierto = false;
    this.modoEdicion = false;
    this.articuloEnEdicionId = null;
    this.articulo = null;
    this.inciso = '';
    this.cuerpo = '';
  }

  guardarArticulo(): void {
    if (!this.articulo || this.articulo <= 0 || !this.cuerpo || !this.cuerpo.trim()) {
      this.notificationService.warning('El número de artículo (mayor a 0) y el cuerpo son obligatorios.');
      return;
    }

    const incisoVal = this.inciso ? this.inciso.trim() : '-';
    const cuerpoVal = this.cuerpo.trim();

    if (this.modoEdicion && this.articuloEnEdicionId) {
      const payload: Partial<GuardarArticuloReglamentoPayload> = {
        articulo: this.articulo,
        inciso: incisoVal,
        cuerpo: cuerpoVal
      };

      this.expedienteService.actualizarArticuloReglamento(this.articuloEnEdicionId, payload).subscribe({
        next: () => {
          this.notificationService.success('Artículo modificado con éxito.');
          this.cerrarModal();
          this.cargarArticulos();
        },
        error: (err) => {
          this.notificationService.error(httpErrorMessage(err, 'No se pudo guardar el artículo.'));
        }
      });
    } else {
      const payload: GuardarArticuloReglamentoPayload = {
        titulo: this.tabActiva,
        articulo: this.articulo,
        inciso: incisoVal,
        cuerpo: cuerpoVal
      };

      this.expedienteService.crearArticuloReglamento(payload).subscribe({
        next: () => {
          this.notificationService.success('Artículo creado con éxito.');
          this.cerrarModal();
          this.cargarArticulos();
        },
        error: (err) => {
          this.notificationService.error(httpErrorMessage(err, 'No se pudo guardar el artículo.'));
        }
      });
    }
  }

  abrirModalEliminar(art: ArticuloReglamentoDTO): void {
    this.articuloAEliminar = art;
    this.modalEliminarAbierto = true;
  }

  cerrarModalEliminar(): void {
    this.modalEliminarAbierto = false;
    this.articuloAEliminar = null;
  }

  confirmarEliminar(): void {
    if (!this.articuloAEliminar) {
      return;
    }

    const id = this.articuloAEliminar.id;
    this.expedienteService.eliminarArticuloReglamento(id).subscribe({
      next: () => {
        this.notificationService.success('Artículo eliminado con éxito.');
        this.cerrarModalEliminar();
        this.cargarArticulos();
      },
      error: (err) => {
        this.notificationService.error(httpErrorMessage(err, 'No se pudo eliminar el artículo.'));
      }
    });
  }
}
