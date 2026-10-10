# Plan Técnico — Clasificador e Indicador Visual de Urgencia en Expedientes (SCRUM-78 / S3-07)

## Revisión del PO — PR #50 (10/10/2026)

- Reutilizar `SolicitarPuntosComponent`, que sirve al menú **Crear Expediente** y al formulario **Solicitud T01**, incorporando un grupo nativo de selección única (`fieldset`/`legend` e inputs radio), presentado como tres casillas coloreadas con los tokens `success`, `info` y `danger`. Mantener la navegación nativa por teclado, foco visible y bloqueo al cargar o emitir, sin un select desplegable. Tipar la urgencia en los DTOs con `NivelUrgencia`, enviar el valor en POST/PATCH y restaurarlo al retomar el borrador; resetear a `normal` al iniciar otro formulario.
- Conservar el contrato existente de apertura directa y de herencia T01 → Expediente. Agregar `urgencia` a `snapshot_emitido` para mantener evidencia de la elección original aun si el TD modifica después la urgencia del expediente.
- Al abrir desde T01, pasar también los puntos solicitados al servicio de apertura para que la nueva tarjeta refleje la cantidad y signo originales. Este dato de la causa no modifica saldos ni genera asientos del libro mayor.
- Admitir el formato decimal de DRF (`number | string | null`) en la respuesta T01 y convertirlo a número al restaurar el formulario. Normalizar también los puntos del monitoreo en el servicio HTTP para mantener la selección visible al retomar borradores.
- Ampliar la precisión de `Expediente.puntos` a los diez dígitos que ya acepta `SolicitudT01.puntos` mediante una migración de esquema, conservando valores existentes y sin introducir topes nuevos. Cubrir valores válidos positivos y negativos mayores a tres dígitos.
- Simplificar exclusivamente la tarjeta Kanban: cabecera con número sin prefijo de presentación `EXP-`, urgencia y puntos; motivo central; fecha con `DatePipe` en formato `dd/MM/yyyy`. Conservar la numeración almacenada y la apertura del detalle mediante teclado/clic.
- Usar variables CSS canónicas para colores, superficies y foco. Reducir la densidad de los badges dentro de la tarjeta sin cambiar el resto de las vistas.
- Validar primero regresiones de formularios y contenido renderizado, apertura API, herencia y snapshot de T01; luego ejecutar las suites backend/MySQL y frontend/Karma, compilación y auditoría de par. Dejar localhost activo para UAT.
- Alinear el arranque Karma y su configuración TypeScript con Angular 14 instalado. Corregir las pruebas heredadas que exigían el título inicial eliminado, una etiqueta anterior o un SDK externo real; conservar sus verificaciones con módulos y dobles explícitos, sin alterar pantallas ajenas a esta revisión.

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
  - Renderizar badge compacto de urgencia con etiqueta visible en la cabecera de la tarjeta; el icono es opcional en Kanban:
    ```html
    <span class="badge-mat badge-urgencia" [ngClass]="getUrgenciaBadgeClass(exp.urgencia)">
      {{getUrgenciaLabel(exp.urgencia)}}
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
- Badges Kanban: fondo semántico `var(--color-danger)`, `var(--color-info)` o `var(--color-success)` según nivel, y texto `var(--color-text-inverse)`; sin colores arbitrarios ni gradientes propios.
- Tarjeta: superficie `var(--color-surface-card)`, texto `var(--color-text-primary)`, fecha `var(--color-text-secondary)` y borde `var(--color-border-main)`. Las urgentes agregan un borde lateral con `var(--color-danger)`; el foco consume `var(--color-border-focus)`.
