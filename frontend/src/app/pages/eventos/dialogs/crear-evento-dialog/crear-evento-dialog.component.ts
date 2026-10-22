import { Component, Inject, OnInit, OnDestroy, Optional } from '@angular/core';
import { FormBuilder, FormGroup, FormControl, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subscription, of } from 'rxjs';
import { debounceTime, distinctUntilChanged, switchMap } from 'rxjs/operators';
import {
  CategoriaEvento,
  CrearEventoPayload,
  ModalidadEvento,
  ModoConvocatoria,
  SubtipoActividad,
  SubtipoEvento,
  SubtipoReunion
} from '../../../../models/evento.model';
import { EventoService } from '../../../../services/evento.service';
import { NotificationService } from '../../../../services/notification.service';
import { SocioApiService, SocioListItemDTO } from '../../../../services/socio-api.service';

export interface SubtipoOption {
  value: SubtipoEvento;
  label: string;
}

@Component({
  selector: 'app-crear-evento-dialog',
  templateUrl: './crear-evento-dialog.component.html',
  styleUrls: ['./crear-evento-dialog.component.scss']
})
export class CrearEventoDialogComponent implements OnInit, OnDestroy {
  form: FormGroup;
  subtiposDisponibles: SubtipoOption[] = [];
  antelacionAviso: 'SANCIONABLE' | 'NO_SANCIONABLE' | null = null;
  guardando = false;

  // Autocompletado reactivo de socios tipo Select2
  filtroSocioControl = new FormControl('');
  buscandoSocios = false;
  sociosEncontrados: SocioListItemDTO[] = [];
  sociosSeleccionados: SocioListItemDTO[] = [];

  subcomisiones = [
    { id: 1, nombre: 'Comunicaciones' },
    { id: 2, nombre: 'Deportes' },
    { id: 3, nombre: 'Extensión Universitaria' },
    { id: 4, nombre: 'Finanzas' },
    { id: 5, nombre: 'Prensa y Difusión' },
    { id: 6, nombre: 'Relaciones Públicas' },
    { id: 7, nombre: 'Tesorería' },
    { id: 8, nombre: 'Cómputos e Informática' }
  ];

  private subs: Subscription[] = [];

  constructor(
    private fb: FormBuilder,
    private eventoService: EventoService,
    private socioService: SocioApiService,
    private notificationService: NotificationService,
    @Optional() public dialogRef: MatDialogRef<CrearEventoDialogComponent>,
    @Optional() @Inject(MAT_DIALOG_DATA) public data: unknown
  ) {
    this.form = this.fb.group({
      titulo: ['', [Validators.required, Validators.minLength(3)]],
      descripcion: [''],
      categoria: ['REUNION' as CategoriaEvento, Validators.required],
      tipo: ['ORDINARIA' as SubtipoEvento, Validators.required],
      modalidad: ['PRESENCIAL_SEDE' as ModalidadEvento, Validators.required],
      ubicacion: [''],
      fecha_programada: ['', Validators.required],
      fecha_fin: [''], // estrictamente opcional
      modo_convocatoria: ['GRUPO' as ModoConvocatoria, Validators.required],
      grupo_convocado: ['G58'],
      subcomision_id: [null],
      tolerancia_tardanza_minutos: [15, [Validators.min(0), Validators.max(60)]],
      tolerancia_retiro_minutos: [15, [Validators.min(0), Validators.max(60)]]
    });
  }

  ngOnInit(): void {
    this.actualizarSubtipos('REUNION');
    this.configurarBuscadorSocios();
  }

  ngOnDestroy(): void {
    this.subs.forEach(s => s.unsubscribe());
  }

  onCategoriaChange(): void {
    const cat = this.form.get('categoria')?.value as CategoriaEvento;
    this.actualizarSubtipos(cat);
  }

  actualizarSubtipos(categoria: CategoriaEvento): void {
    if (categoria === 'REUNION') {
      this.subtiposDisponibles = [
        { value: 'ORDINARIA' as SubtipoReunion, label: 'Reunión Ordinaria' },
        { value: 'EXTRAORDINARIA' as SubtipoReunion, label: 'Reunión Extraordinaria' },
        { value: 'ASAMBLEA' as SubtipoReunion, label: 'Asamblea General' },
        { value: 'PLENARIO' as SubtipoReunion, label: 'Plenario de Comisiones' }
      ];
      this.form.patchValue({ tipo: 'ORDINARIA' });
    } else {
      this.subtiposDisponibles = [
        { value: 'MANTENIMIENTO' as SubtipoActividad, label: 'Jornada de Mantenimiento / Infraestructura' },
        { value: 'VOLUNTARIADO' as SubtipoActividad, label: 'Voluntariado Institucional' },
        { value: 'JORNADA' as SubtipoActividad, label: 'Jornada de Capacitación / Taller' },
        { value: 'EVENTO_SOCIAL' as SubtipoActividad, label: 'Evento Social / Beneficio' },
        { value: 'GUARDIA' as SubtipoActividad, label: 'Guardia / Turno Obligatorio' }
      ];
      this.form.patchValue({ tipo: 'MANTENIMIENTO' });
    }
  }

  onModalidadChange(): void {
    const mod = this.form.get('modalidad')?.value as ModalidadEvento;
    const ubicCtrl = this.form.get('ubicacion');
    if (mod === 'PRESENCIAL_EXTERNA' || mod === 'VIRTUAL') {
      ubicCtrl?.setValidators([Validators.required]);
    } else {
      ubicCtrl?.clearValidators();
      ubicCtrl?.setValue('');
    }
    ubicCtrl?.updateValueAndValidity();
  }

  onModoConvocatoriaChange(): void {
    const modo = this.form.get('modo_convocatoria')?.value as ModoConvocatoria;
    if (modo === 'GRUPO') {
      this.form.patchValue({ grupo_convocado: 'G58', subcomision_id: null });
    } else if (modo === 'SUBCOMISION') {
      this.form.patchValue({ grupo_convocado: null, subcomision_id: 1 });
    } else {
      this.form.patchValue({ grupo_convocado: null, subcomision_id: null });
    }
  }

  verificarAntelacion(): void {
    const fechaProgStr = this.form.get('fecha_programada')?.value;
    if (!fechaProgStr) {
      this.antelacionAviso = null;
      return;
    }

    const fechaInicio = new Date(fechaProgStr);
    const ahora = new Date();

    if (isNaN(fechaInicio.getTime())) {
      this.antelacionAviso = null;
      return;
    }

    // Calcular días hábiles entre ahora y la fecha programada
    const diasHabiles = this.calcularDiasHabilesEntre(ahora, fechaInicio);
    if (diasHabiles >= 2) {
      this.antelacionAviso = 'SANCIONABLE';
    } else {
      this.antelacionAviso = 'NO_SANCIONABLE';
    }
  }

  private calcularDiasHabilesEntre(inicio: Date, fin: Date): number {
    let count = 0;
    const cur = new Date(inicio);
    cur.setHours(0, 0, 0, 0);

    const target = new Date(fin);
    target.setHours(0, 0, 0, 0);

    // Sumar día a día
    while (cur < target) {
      cur.setDate(cur.getDate() + 1);
      const day = cur.getDay();
      // 0 es Domingo, 6 es Sábado
      if (day !== 0 && day !== 6) {
        count++;
      }
    }
    return count;
  }

  configurarBuscadorSocios(): void {
    const searchSub = this.filtroSocioControl.valueChanges
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        switchMap(query => {
          if (!query || query.trim().length < 2) {
            this.sociosEncontrados = [];
            return of(null);
          }
          this.buscandoSocios = true;
          return this.socioService.searchSocios(query);
        })
      )
      .subscribe({
        next: resp => {
          this.buscandoSocios = false;
          if (resp && resp.results) {
            // Filtrar socios que ya hayan sido seleccionados
            const selIds = new Set(this.sociosSeleccionados.map(s => s.id));
            this.sociosEncontrados = resp.results.filter(s => !selIds.has(s.id));
          } else {
            this.sociosEncontrados = [];
          }
        },
        error: () => {
          this.buscandoSocios = false;
          this.sociosEncontrados = [];
        }
      });
    this.subs.push(searchSub);
  }

  agregarSocioPersonalizado(socio: SocioListItemDTO): void {
    if (!this.sociosSeleccionados.some(s => s.id === socio.id)) {
      this.sociosSeleccionados.push(socio);
    }
    this.sociosEncontrados = this.sociosEncontrados.filter(s => s.id !== socio.id);
    this.filtroSocioControl.setValue('');
  }

  quitarSocioPersonalizado(socioId: number): void {
    this.sociosSeleccionados = this.sociosSeleccionados.filter(s => s.id !== socioId);
  }

  guardar(): void {
    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const val = this.form.value;
    const modo = val.modo_convocatoria as ModoConvocatoria;

    if (modo === 'PERSONALIZADA' && this.sociosSeleccionados.length === 0) {
      this.notificationService.error('Debe convocar al menos a un socio en la lista personalizada.');
      return;
    }

    const payload: CrearEventoPayload = {
      titulo: val.titulo,
      descripcion: val.descripcion || '',
      categoria: val.categoria,
      tipo: val.tipo,
      modalidad: val.modalidad,
      ubicacion: val.ubicacion || (val.modalidad === 'PRESENCIAL_SEDE' ? 'Sede Central AVEIT' : ''),
      fecha_programada: new Date(val.fecha_programada).toISOString(),
      fecha_fin: val.fecha_fin ? new Date(val.fecha_fin).toISOString() : null,
      modo_convocatoria: modo,
      grupo_convocado: modo === 'GRUPO' ? val.grupo_convocado : undefined,
      subcomision_id: modo === 'SUBCOMISION' ? Number(val.subcomision_id) : null,
      socios_ids: modo === 'PERSONALIZADA' ? this.sociosSeleccionados.map(s => s.id) : undefined,
      tolerancia_tardanza_minutos: val.tolerancia_tardanza_minutos,
      tolerancia_retiro_minutos: val.tolerancia_retiro_minutos
    };

    this.guardando = true;
    this.eventoService.crearEvento(payload).subscribe({
      next: creado => {
        this.guardando = false;
        this.notificationService.success('Evento institucional programado y publicado exitosamente.');
        if (this.dialogRef) {
          this.dialogRef.close(creado);
        }
      },
      error: () => {
        this.guardando = false;
        this.notificationService.error('No se pudo programar el evento institucional. Verifique los datos.');
      }
    });
  }

  cancelar(): void {
    if (this.dialogRef) {
      this.dialogRef.close(null);
    }
  }
}
