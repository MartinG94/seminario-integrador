# Plan Técnico — Spec 004: Calendario institucional de días hábiles (SCRUM-45 / S3-01)

## 1. Arquitectura y Dominio Hexagonal

### 1.1 Puerto y Adaptadores de Feriados
- Se conserva el puerto puro de dominio `HolidayProviderPort(Protocol)` en `expedientes.domain.ports`.
- Se crea el adaptador de infraestructura `DbHolidayProvider(HolidayProviderPort)` que implementa la consulta contra la versión activa (o versión específica) de la base de datos persistida.
- Se adapta `Argentina2026HolidayProvider` y `InMemoryHolidayProvider` para testing unitario aislado sin acoplamiento a base de datos.
- La función de dominio puro `compute_business_deadline(start_at, business_days, holiday_provider)` se mantiene desacoplada de Django y agnóstica a la persistencia.

### 1.2 Mapeo de Persistencia y ORM (`expedientes/models.py`)
- **`CalendarioVersion`**:
  - `id`: AutoField / BigAutoField
  - `version`: PositiveIntegerField (único, secuencial ascendente: 1, 2, 3...)
  - `nombre`: CharField(max_length=150) (ej. "Calendario Oficial AVEIT 2026")
  - `vigencia_desde`: DateField()
  - `vigencia_hasta`: DateField(null=True, blank=True)
  - `activa`: BooleanField(default=True) — Solo una versión puede estar activa a la vez para nuevos cómputos.
  - `motivo_cambio`: TextField(help_text="Justificación formal de auditoría para la creación/modificación de la versión.")
  - `creado_por`: ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
  - `created_at`: DateTimeField(auto_now_add=True)
  - `updated_at`: DateTimeField(auto_now=True)
- **`FeriadoExcepcion`**:
  - `id`: AutoField / BigAutoField
  - `calendario_version`: ForeignKey(CalendarioVersion, on_delete=models.CASCADE, related_name='feriados')
  - `fecha`: DateField()
  - `descripcion`: CharField(max_length=200)
  - `tipo`: CharField(max_length=30, choices=TipoFeriadoEnum.choices, default=TipoFeriadoEnum.NACIONAL)
  - `es_laborable`: BooleanField(default=False)
  - `created_at`: DateTimeField(auto_now_add=True)
  - `updated_at`: DateTimeField(auto_now=True)
  - `UniqueConstraint(fields=['calendario_version', 'fecha'], name='unique_fecha_per_calendario_version')`
- **Vinculación con `Expediente`**:
  - `calendario_version`: ForeignKey(CalendarioVersion, on_delete=models.PROTECT, null=True, blank=True, related_name='expedientes_congelados')
  - En `Expediente.iniciar_plazo_descargo(fecha_hora_inicio, dias_habiles=5, holiday_provider=None, calendario_version=None, actor="SISTEMA")`:
    - Si no se pasa `calendario_version`, se toma la versión activa actual de la base de datos (con fallback a la versión sembrada de 2026).
    - Se instancia `DbHolidayProvider(version=version_aplicada)`.
    - Se calcula el deadline `compute_business_deadline(fecha_hora_inicio, dias_habiles, provider)`.
    - Se persiste de forma inmutable `self.calendario_version = version_aplicada`, `self.plazo_inicio_at = fecha_hora_inicio`, `self.plazo_limite_at = limite`.

### 1.3 Seeder Inicial (Migración de Datos)
- Una migración de datos siembra la `CalendarioVersion(version=1, nombre="Calendario Oficial AVEIT 2026", vigencia_desde="2026-01-01", activa=True, motivo_cambio="Carga inicial del calendario institucional con los feriados nacionales oficiales de Argentina para el ciclo lectivo 2026.")`.
- Pobla los 16 feriados oficiales de 2026 ya catalogados en `Argentina2026HolidayProvider.OFFICIAL_2026_HOLIDAYS`.

---

## 2. Diseño del Contrato REST API

### 2.1 Endpoints
- `GET /api/v1/expedientes/calendario/versiones/`
  - Permiso: `IsAuthenticated` (Cualquier usuario autenticado puede ver el historial de versiones).
  - Retorna: Lista de versiones con metadata de vigencia, auditoría y conteo de feriados.
- `POST /api/v1/expedientes/calendario/versiones/`
  - Permiso: `CanManageCalendar` (ADMIN, CD, TD).
  - Payload: `{ "nombre": "...", "vigencia_desde": "YYYY-MM-DD", "vigencia_hasta": null, "motivo_cambio": "...", "clonar_de_version_id": 1, "feriados": [...] }`
  - Crea una nueva versión inmutable con su auditoría. Si `activa: true`, desactiva las versiones anteriores.
- `GET /api/v1/expedientes/calendario/versiones/{id}/`
  - Permiso: `IsAuthenticated`.
  - Retorna: Detalle completo de la versión y array de todos sus feriados y excepciones.
- `GET /api/v1/expedientes/calendario/feriados/`
  - Permiso: `IsAuthenticated`.
  - Query params: `version_id` (opcional, default: activa), `year` (opcional), `month` (opcional).
  - Retorna: Lista de feriados de la versión seleccionada o activa.
- `POST /api/v1/expedientes/calendario/calcular-plazo/`
  - Permiso: `IsAuthenticated`.
  - Payload: `{ "start_at": "2026-10-08T12:00:00-03:00", "business_days": 5, "version_id": null }`
  - Retorna:
    ```json
    {
      "start_at": "2026-10-08T12:00:00-03:00",
      "business_days": 5,
      "deadline": "2026-10-15T12:00:00-03:00",
      "calendario_version": { "id": 1, "version": 1, "nombre": "Calendario Oficial AVEIT 2026" },
      "excluded_days": [
        { "date": "2026-10-10", "reason": "Sábado (Fin de semana)" },
        { "date": "2026-10-11", "reason": "Domingo (Fin de semana)" },
        { "date": "2026-10-12", "reason": "Feriado: Día del Respeto a la Diversidad Cultural" }
      ]
    }
    ```

---

## 3. Frontend Angular (SPA)

### 3.1 DTOs y Servicio
- `CalendarioApiService` en `frontend/src/app/services/calendario-api.service.ts`:
  - `getVersiones()`, `getVersion(id)`, `createVersion(payload)`, `getFeriados(params)`, `calcularPlazo(payload)`.
- Modelos TypeScript tipados: `CalendarioVersionDto`, `FeriadoExcepcionDto`, `CalcularPlazoRequest`, `CalcularPlazoResponse`.

### 3.2 Componente de Gestión de Calendario
- Ruta: `/calendario-institucional` (accesible en el menú lateral para autoridades y administradores, o visualizable).
- Vista en 3 paneles acordes a `DESIGN.md`:
  1. **Tarjeta Resumen & Versión Activa:** Muestra la versión vigente, su rango de vigencia, fecha de creación y motivo formal.
  2. **Listado de Feriados y Excepciones:** Tabla interactiva con badges estilizados (Nacional, Institucional, Excepción), buscador y selector de año.
  3. **Simulador Interactivo de Plazos:** Permite ingresar fecha/hora de inicio y días hábiles, calculando en tiempo real el vencimiento exacto y desglosando los días hábiles y días excluidos (fines de semana y feriados) con la zona horaria `America/Argentina/Buenos_Aires`.
  4. **Diálogo Modal para Nueva Versión / Excepción:** Formulario para administradores para registrar un nuevo feriado o excepción, exigiendo obligatoriamente el motivo formal del cambio para auditoría.

---

## 4. Estrategia de Testing (TDD)
- **Tests Unitarios de Dominio (`backend/tests/expedientes/test_business_calendar.py`):**
  - Verificación de exclusión de feriados y fines de semana (CA1).
  - Verificación de zona horaria `America/Argentina/Buenos_Aires` (CA4).
- **Tests de Persistencia y Modelos (`backend/tests/expedientes/test_calendar_models.py`):**
  - Unicidad de versión, fechas duplicadas en la misma versión, clave foránea de auditoría.
  - Inmutabilidad del plazo y preservación de versión aplicada en `Expediente` (CA2, CA3).
- **Tests de Endpoints y RBAC (`backend/tests/expedientes/test_calendar_api.py`):**
  - Autorización: 403 para socios sin rol de gestión al intentar crear versiones/feriados (CA5).
  - 200/201 para ADMIN, CD, TD.
  - Cálculo de plazo exacto en API (CA1, CA4).
- **Tests Frontend Jasmine/Karma (`frontend/src/app/...`):**
  - Servicio `CalendarioApiService` y componente de calendario institucional.
