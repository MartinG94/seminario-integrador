# Plan Técnico — Clasificador e Indicador Visual de Urgencia en Expedientes (SCRUM-78 / S3-07)

## 1. Arquitectura de la Solución

El incremento incorpora el atributo e indicador visual de urgencia a lo largo de las capas de dominio, persistencia, API REST e interfaz de usuario de SGD-AVEIT.

```
[ Frontend: GestionarExpedientesComponent ]
     │ (Kanban Card Badge / Table Cell / Urgency Filter / Detail Modal)
     ▼
[ Frontend Service: TribunalDataService ]
     │ GET /api/v1/expedientes/board/?urgencia=...
     │ PATCH /api/v1/expedientes/<id>/ { urgencia: '...' }
     ▼
[ Backend REST API: expedientes/views.py ]
     │ BoardExpedientesView (ExpedienteFilter)
     │ ExpedienteDetailView (PATCH con IsTribunalOrDirectiva)
     ▼
[ Backend Model: expedientes/models.py (Expediente) ]
     │ urgencia: CharField(choices=UrgenciaExpedienteEnum.choices, default="normal", db_index=True)
     ▼
[ MySQL 8.0 / SQLite: expedientes_expediente.urgencia ]
```

---

## 2. Cambios en Backend (Python / Django)

### 2.1. Modelo `Expediente` (`backend/expedientes/models.py`)
- Agregar enum `UrgenciaExpedienteEnum(models.TextChoices)`:
  - `BAJA = "baja", "Baja"`
  - `NORMAL = "normal", "Normal"`
  - `URGENTE = "urgente", "Urgente"`
- Incorporar campo `urgencia`:
  ```python
  urgencia = models.CharField(
      max_length=20,
      choices=UrgenciaExpedienteEnum.choices,
      default=UrgenciaExpedienteEnum.NORMAL,
      db_index=True,
      help_text="Nivel de urgencia procesal (Baja, Normal, Urgente).",
  )
  ```
- Opcionalmente en `SolicitudT01`:
  ```python
  urgencia = models.CharField(
      max_length=20,
      choices=UrgenciaExpedienteEnum.choices,
      default=UrgenciaExpedienteEnum.NORMAL,
      blank=True,
  )
  ```
- Soporte en `ExpedienteWorkflowService.open_expediente(..., urgencia="normal")`.

### 2.2. Migración Django
- Generar y aplicar migración en `backend/expedientes/migrations/` agregando el campo `urgencia` con default `"normal"`.

### 2.3. Serializadores (`backend/expedientes/serializers.py`)
- `ExpedienteListSerializer`:
  - Agregar campos `urgencia` y `urgencia_display`.
- `BoardExpedienteSerializer`:
  - Agregar campos `urgencia` y `urgencia_display`.
- `UpdateUrgenciaExpedienteSerializer`:
  - Valida el payload de actualización parcial (`urgencia in UrgenciaExpedienteEnum.values`).

### 2.4. Filtros (`backend/expedientes/filters.py`)
- `ExpedienteFilter`:
  - Agregar `urgencia = django_filters.ChoiceFilter(choices=UrgenciaExpedienteEnum.choices)` para soportar `GET /api/v1/expedientes/board/?urgencia=urgente`.

### 2.5. Vistas y Endpoints (`backend/expedientes/views.py`)
- En `ExpedienteDetailView`:
  - Implementar método `patch(self, request: Request, pk: int) -> Response`.
  - Permisos: `IsAuthenticated` y `IsTribunalOrDirectiva` (para actualización de urgencia por autoridades procesales).
  - Valida y persiste el nuevo nivel de urgencia.

---

## 3. Cambios en Frontend (Angular / TypeScript)

### 3.1. Tipos y DTOs (`frontend/src/app/services/tribunal-data.service.ts`)
- Definir tipo:
  ```typescript
  export type NivelUrgencia = 'baja' | 'normal' | 'urgente';
  ```
- Actualizar `BoardCaseDTO`:
  ```typescript
  urgencia?: NivelUrgencia;
  urgencia_display?: string;
  ```
- Actualizar `Expediente`:
  ```typescript
  urgencia: NivelUrgencia;
  urgenciaDisplay?: string;
  ```
- En `TribunalDataService.mapearBoardCaseAExpediente()`:
  - Mapear `urgencia: c.urgencia || 'normal'` y `urgenciaDisplay: c.urgencia_display || 'Normal'`.
- Agregar método `actualizarUrgencia(expedienteId: string | number, urgencia: NivelUrgencia): Observable<any>`.

### 3.2. Componente `GestionarExpedientesComponent`
- **Filtros:**
  - Agregar variable `filtroUrgencia: string = ''` y control `<select>` en la barra de herramientas.
  - Sincronizar en `cargarDatosTablero()` enviando `filtros.urgencia = this.filtroUrgencia`.
  - Fallback en memoria en `expedientesFiltrados`: filtrar por `e.urgencia === this.filtroUrgencia`.
- **Kanban Cards:**
  - Renderizar badge de urgencia en la cabecera de la tarjeta:
    ```html
    <span class="badge-mat badge-urgencia" [ngClass]="getUrgenciaBadgeClass(exp.urgencia)">
      <i class="material-icons urgencia-icon">{{getUrgenciaIcon(exp.urgencia)}}</i> {{getUrgenciaLabel(exp.urgencia)}}
    </span>
    ```
  - Añadir clase condicional `kanban-card-urgente` cuando `exp.urgencia === 'urgente'` para destacar visualmente con borde sutil según `DESIGN.md`.
- **Tabla Explorer:**
  - Agregar columna "Urgencia" con ordenamiento dinámico: `(click)="cambiarOrden('urgencia')"`.
  - Renderizar badge con color semántico e icono en cada fila.
- **Modal de Detalle:**
  - Mostrar la urgencia actual en el resumen de la causa.
  - Si el usuario tiene rol TD/Admin (`puedeVotarOFirmar`), proveer un selector interactivo para modificar la urgencia directamente desde el modal con confirmación.

---

## 4. Alineación con Tokens de Diseño (`DESIGN.md`)
- `urgente`: Rojo semántico `{colors.danger}: #B91C1C`, fondo claro `rgba(244, 67, 54, 0.12)`, borde `1px solid rgba(244, 67, 54, 0.3)`.
- `normal`: Azul informativo `{colors.info}: #0369A1`, fondo claro `rgba(0, 188, 212, 0.12)`.
- `baja`: Verde atenuado `{colors.success}: #15803D`, fondo claro `rgba(76, 175, 80, 0.12)`.
