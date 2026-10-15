# Plan Técnico — Spec 005: Sanciones originadas en reuniones y solicitudes (SCRUM-50 / S3-06)

## 1. Arquitectura General y Servicios de Dominio

La solución aplica los principios de Arquitectura Hexagonal / Domain-Driven Design (DDD) integrados con Django 4.2 LTS y Angular 14.2+:

```
                                  ┌────────────────────────────────┐
                                  │   SPA Angular 14 (Frontend)    │
                                  └───────────────┬────────────────┘
                                                  │ HTTP / REST (JWT)
                                                  ▼
                                  ┌────────────────────────────────┐
                                  │      DRF API Controllers       │
                                  └───────────────┬────────────────┘
                                                  │
                 ┌────────────────────────────────┼────────────────────────────────┐
                 ▼                                ▼                                ▼
   ┌───────────────────────────┐    ┌───────────────────────────┐    ┌───────────────────────────┐
   │ MeetingComplianceService  │    │ AttendanceCaptureStrategy │    │ WarningAccumulationService│
   │   (Plazos CA1 / CA2)      │    │    (Manual / Biométrico)  │    │     (Regla 3:1 CA4)       │
   └─────────────┬─────────────┘    └─────────────┬─────────────┘    └─────────────┬─────────────┘
                 │                                │                                │
                 ▼                                ▼                                ▼
   ┌───────────────────────────┐    ┌───────────────────────────┐    ┌───────────────────────────┐
   │    compute_business_      │    │ AttendanceProcessing      │    │ ExpedienteWorkflowService │
   │         deadline          │    │         Service           │    │    (Apertura CA5)         │
   └───────────────────────────┘    └─────────────┬─────────────┘    └─────────────┬─────────────┘
                                                  │                                │
                                                  └────────────────┬───────────────┘
                                                                   ▼
                                                    ┌─────────────────────────────┐
                                                    │  MySQL 8.0 / InnoDB Ledger  │
                                                    │ (0 UPDATE manual de saldo)  │
                                                    └─────────────────────────────┘
```

---

## 2. Modelo Relacional de Base de Datos (MySQL 8.0)

### 2.1 Tablas y Esquema DDL

```sql
-- 1. Eventos Institucionales: Reuniones y Actividades (CA1 / CA2 / CA8 / CA9 / CA10)
CREATE TABLE `expedientes_evento` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `titulo` VARCHAR(200) NOT NULL,
    `descripcion` LONGTEXT NOT NULL DEFAULT '',
    `categoria` VARCHAR(20) NOT NULL, -- 'REUNION' o 'ACTIVIDAD'
    `tipo` VARCHAR(30) NOT NULL,      -- Subtipo reglamentario según categoría
    `modalidad` VARCHAR(30) NOT NULL DEFAULT 'PRESENCIAL_SEDE', -- 'PRESENCIAL_SEDE', 'PRESENCIAL_EXTERNA', 'VIRTUAL'
    `ubicacion` VARCHAR(255) NULL,    -- Dirección física o enlace de videoconferencia
    `lugar` VARCHAR(200) NOT NULL DEFAULT 'Sede Central AVEIT',
    `fecha_publicacion` DATETIME(6) NOT NULL,
    `fecha_programada` DATETIME(6) NOT NULL, -- Fecha y hora de inicio obligatoria
    `fecha_fin` DATETIME(6) NULL,            -- Fecha y hora de finalización estrictamente opcional
    `fecha_hora_cierre_efectivo` DATETIME(6) NULL, -- Timestamp real de finalización/cierre
    `fecha_reporte` DATETIME(6) NULL,
    `tolerancia_tardanza_minutos` SMALLINT UNSIGNED NOT NULL DEFAULT 15,
    `tolerancia_retiro_minutos` SMALLINT UNSIGNED NOT NULL DEFAULT 15,
    `estado` VARCHAR(30) NOT NULL DEFAULT 'PROGRAMADA',
    `modo_convocatoria` VARCHAR(30) NOT NULL DEFAULT 'PERSONALIZADA',
    `grupo_convocado` VARCHAR(10) NULL,
    `es_obligatoria` TINYINT(1) NOT NULL DEFAULT 1,
    `es_sancionable` TINYINT(1) NOT NULL DEFAULT 0,
    `motivo_no_sancionable` LONGTEXT NULL,
    `convocante_id` BIGINT NOT NULL,
    `subcomision_id` INT NULL,
    `reportado_por_id` BIGINT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    `updated_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6),
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_evento_convocante` FOREIGN KEY (`convocante_id`) REFERENCES `socios_socio` (`id`) ON DELETE PROTECT,
    CONSTRAINT `fk_evento_subcomision` FOREIGN KEY (`subcomision_id`) REFERENCES `socios_subcomision` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_evento_reportante` FOREIGN KEY (`reportado_por_id`) REFERENCES `socios_socio` (`id`) ON DELETE SET NULL,
    CONSTRAINT `chk_evento_publicacion_previa` CHECK (`fecha_publicacion` <= `fecha_programada`),
    CONSTRAINT `chk_evento_fin_coherente` CHECK (`fecha_fin` IS NULL OR `fecha_fin` >= `fecha_programada`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX `idx_evento_fecha_prog_estado` ON `expedientes_evento` (`fecha_programada`, `estado`);
CREATE INDEX `idx_evento_cat_tipo_sancionable` ON `expedientes_evento` (`categoria`, `tipo`, `es_sancionable`);

-- 2. Registros Individuales de Asistencia con Motivo Circunstanciado (CA10)
CREATE TABLE `expedientes_asistencia_evento` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `evento_id` BIGINT NOT NULL,
    `socio_id` BIGINT NOT NULL,
    `estado_asistencia` VARCHAR(30) NOT NULL,
    `hora_registro` DATETIME(6) NULL,
    `hora_salida` DATETIME(6) NULL,
    `minutos_tardanza` INT UNSIGNED NOT NULL DEFAULT 0,
    `minutos_retiro_anticipado` INT UNSIGNED NOT NULL DEFAULT 0,
    `metodo_captura` VARCHAR(20) NOT NULL DEFAULT 'MANUAL',
    `dispositivo_id` VARCHAR(100) NULL,
    `motivo` LONGTEXT NOT NULL DEFAULT '',        -- Motivo explicativo circunstanciado obligatorio/editable
    `observaciones` LONGTEXT NOT NULL DEFAULT '', -- Notas accesorias de la marcación
    `procesado_disciplinario` TINYINT(1) NOT NULL DEFAULT 0,
    `expediente_generado_id` BIGINT NULL,
    `apercibimiento_generado_id` BIGINT NULL,
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (`id`),
    UNIQUE KEY `unique_asistencia_per_evento_socio` (`evento_id`, `socio_id`),
    CONSTRAINT `fk_asist_evento` FOREIGN KEY (`evento_id`) REFERENCES `expedientes_evento` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_asist_socio` FOREIGN KEY (`socio_id`) REFERENCES `socios_socio` (`id`) ON DELETE PROTECT,
    CONSTRAINT `fk_asist_expediente` FOREIGN KEY (`expediente_generado_id`) REFERENCES `expedientes_expediente` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. Libro Mayor de Apercibimientos / Llamados de Atención (CA4)
CREATE TABLE `expedientes_registro_apercibimiento` (
    `id` BIGINT NOT NULL AUTO_INCREMENT,
    `socio_id` BIGINT NOT NULL,
    `origen_tipo` VARCHAR(30) NOT NULL,
    `asistencia_id` BIGINT NULL,
    `expediente_origen_id` BIGINT NULL,
    `solicitud_t01_id` CHAR(36) NULL,
    `fecha_hecho` DATE NOT NULL,
    `motivo` LONGTEXT NOT NULL,
    `articulo_reglamento` VARCHAR(50) NOT NULL DEFAULT 'Art. 83',
    `estado` VARCHAR(20) NOT NULL DEFAULT 'PENDIENTE',
    `lote_consolidacion` CHAR(36) NULL,
    `expediente_sancion_id` BIGINT NULL,
    `fecha_consolidacion` DATETIME(6) NULL,
    `actor_registro` VARCHAR(150) NOT NULL DEFAULT 'SISTEMA',
    `created_at` DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    PRIMARY KEY (`id`),
    CONSTRAINT `fk_aperc_socio` FOREIGN KEY (`socio_id`) REFERENCES `socios_socio` (`id`) ON DELETE PROTECT,
    CONSTRAINT `fk_aperc_asistencia` FOREIGN KEY (`asistencia_id`) REFERENCES `expedientes_asistencia_reunion` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_aperc_exp_sancion` FOREIGN KEY (`expediente_sancion_id`) REFERENCES `expedientes_expediente` (`id`) ON DELETE PROTECT,
    CONSTRAINT `chk_aperc_consolidado` CHECK (
        (`estado` = 'CONSOLIDADO' AND `lote_consolidacion` IS NOT NULL AND `expediente_sancion_id` IS NOT NULL) OR
        (`estado` <> 'CONSOLIDADO')
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX `idx_aperc_socio_est_created` ON `expedientes_registro_apercibimiento` (`socio_id`, `estado`, `created_at`);
```

---

## 3. Patrón Strategy para Captura de Asistencia

### 3.1 Backend (Python 3.12)
Se define la interfaz desacoplada `AttendanceCaptureStrategy` en `backend/expedientes/domain/attendance_strategy.py`:
- `ManualAttendanceStrategy`: Procesa el array de marcación manual enviado desde la SPA. Todo socio convocado no reportado pasa a `AUSENTE_INJUSTIFICADO`.
- `BiometricAttendanceStrategy`: Procesa marcas de reloj / lector biométrico ("pasar el dedo"), calcula deltas de tardanza/retiro y clasifica según tolerancias.
- `AttendanceStrategyFactory`: Factoría para instanciar la estrategia según el parámetro `estrategia` del request.

### 3.2 Frontend (Angular 14 / TypeScript)
Se implementa `IAttendanceCaptureStrategy` en `frontend/src/app/eventos-asistencia/strategies/`:
- `ManualAttendanceStrategy`: Vinculada a los switches y dropdowns de la tabla de asistencia.
- `BiometricAttendanceStrategy`: Simula la captura con feedback auditivo mediante Web Audio API (`AudioContext`) y animación de escaneo.
- `AttendanceContextService`: Contexto inyectable que administra la estrategia seleccionada y notifica al componente principal.

---

## 4. Algoritmos de Dominio

### 4.1 Validación de Plazos Procesales (CA1 / CA2 / CA8)
El servicio `MeetingComplianceService` implementa:
1. `validate_notice_period(fecha_publicacion, fecha_inicio)`:
   - Invoca `compute_business_deadline(fecha_publicacion, business_days=2)`.
   - Si `fecha_inicio < limite`, `es_sancionable = False` ("Convocatoria con menos de 2 días hábiles").
2. `validate_reporting_deadline(fecha_fin, fecha_reporte, fecha_inicio=None, fecha_cierre_efectivo=None)`:
   - Determina el timestamp base de referencia:
     * Si `fecha_cierre_efectivo` existe, utiliza dicho timestamp.
     * De lo contrario, si `fecha_fin` existe, utiliza `fecha_fin`.
     * Si `fecha_fin` es nulo (duración abierta / opcional), toma subsidiariamente `fecha_inicio`.
   - Invoca `compute_business_deadline(base_timestamp, business_days=3)` (72 horas hábiles = 3 días hábiles).
   - Si `fecha_reporte > limite`, `es_sancionable = False` ("Reporte presentado fuera de las 72 hs hábiles").

### 4.2 Acumulación Atómica 3:1 de Apercibimientos (CA4) y Concurrencia
El servicio `WarningAccumulationService` asegura el aislamiento transaccional:
1. `transaction.atomic()` engloba todo el procesamiento.
2. Bloqueo pesimista del socio: `Socio.objects.select_for_update().get(pk=socio_id)`.
3. Inserción del apercibimiento en `PENDIENTE`.
4. Búsqueda de pendientes bloqueados: `RegistroApercibimiento.objects.select_for_update().filter(socio=socio, estado='PENDIENTE').order_by('created_at')`.
5. Si `len(pendientes) >= 3`:
   - Se toma la terna más antigua (3 registros).
   - Se genera el `UUID` del lote.
   - Se crea el expediente de oficio por `-1.0` punto en estado `CREADO` (`ExpedienteWorkflowService.open_expediente`).
   - Se actualizan los 3 registros a `CONSOLIDADO` con el ID del expediente.

### 4.3 Generación de Sanciones Directas (CA3 / CA5 / CA9)
En eventos sancionables (`es_sancionable = True`), las actuaciones se gradúan según categoría y tipo:
- **Categoría REUNIÓN:**
  - Inasistencia injustificada a Ordinaria: Expediente en estado `CREADO` por `-1.0` punto (Art. 85.b).
  - Inasistencia injustificada a Extraordinaria: Expediente en estado `CREADO` por `-1.5` puntos (Art. 85.b).
  - Inasistencia injustificada a Asamblea: Expediente en estado `CREADO` por `-2.0` puntos (Art. 85.c).
- **Categoría ACTIVIDAD:**
  - Inasistencia injustificada a Mantenimiento / Voluntariado: Expediente en estado `CREADO` por `-1.0` punto (Art. 85.a/d).
- **Graduaciones Comunes:**
  - Tardanza o Retiro grave (> 30 min): Expediente en estado `CREADO` por `-0.5` puntos (Art. 100.b/d).
  - Tardanza o Retiro leve (15-30 min): Registro de apercibimiento derivado al motor 3:1 (Art. 100.a/c).

### 4.4 Servicio de Notificación Automática por Correo (CA7 / Art. 95 R.I.)
El servicio `MeetingNoticeNotificationService` (`backend/expedientes/services/meeting_notice_service.py`):
1. Se dispara inmediatamente al crear y publicar la reunión o actividad con éxito en `POST /api/v1/expedientes/eventos/`.
2. Para cada socio en la nómina de convocados (resueltos según grupo, subcomisión o lista personalizada), genera un mensaje encolado en `notifications_email_outbox` mediante `EmailDispatcherService.create_or_get_outbox`:
   - `to`: `[socio.email]`
   - `subject`: `Convocatoria a {evento.categoria}: {evento.titulo}`
   - `body_text` y `body_html`: Fecha, hora de inicio, modalidad (`Sede`, `Externa`, `Virtual`), ubicación o link, tolerancia, carácter reglamentario (`OBLIGATORIA Y SANCIONABLE` o `NO SANCIONABLE`), y link al sistema.
   - `idempotency_key`: `f"meeting_notice_{evento.id}_socio_{socio.id}"` para evitar envíos duplicados ante reintentos.
3. Despacha o programa el envío mediante la cola transaccional Outbox, garantizando entrega auditada y resiliencia ante caídas temporales de red.

---

## 5. Especificación de la API REST (DRF)

| Método | Endpoint | Permiso | Descripción |
|---|---|---|---|
| `POST` | `/api/v1/expedientes/eventos/` | `IsComisionDirectivaOrAdmin` | Alta y publicación de evento/reunión. Payload obligatorio: `titulo`, `fecha_programada`, `categoria` (`REUNION`/`ACTIVIDAD`), `tipo`, `modalidad` (`PRESENCIAL_SEDE`/`PRESENCIAL_EXTERNA`/`VIRTUAL`). Opcionales: `fecha_fin` (null), `ubicacion`/`enlace_virtual`, `descripcion`. Modo de convocatoria: `GRUPO` (`grupo="G58"`), `SUBCOMISION` (`subcomision_id`), o `PERSONALIZADA` (`socios_ids=[...]`). |
| `GET` | `/api/v1/expedientes/eventos/` | `IsTribunalOrDirectiva` | Listado paginado de eventos con filtros por categoría, tipo, estado y convocatoria. |
| `GET` | `/api/v1/expedientes/eventos/{id}/` | `IsTribunalOrDirectiva` | Detalle del evento, convocados individuales, modalidad y auditoría de plazos. |
| `POST` | `/api/v1/expedientes/eventos/{id}/reportar-asistencia/` | `IsComisionDirectivaOrAdmin` | Carga de asistencia y generación de actuaciones. Payload recibe array de socios con `estado_asistencia` y `motivo` (observación explicativa circunstanciada obligatoria/editable para cada persona). |
| `GET` | `/api/v1/expedientes/socios/{id}/apercibimientos/` | Autenticado | Historial de apercibimientos y estado de consolidación. |

---

## 6. Diseño de UI / UX en Angular (`eventos-asistencia`)

1. **Estructura de Vistas:**
   - Barra superior con botón `Programar Convocatoria`, filtro por categoría (`Reunión` / `Actividad`) y estado, y selector de estrategia de asistencia (`Manual` / `Biométrica`).
   - Panel izquierdo con listado de eventos ordenados por fecha con badges semánticos (`Reunión`, `Actividad`, `Presencial Sede`, `Virtual`, `No Sancionable`).
   - Panel derecho con detalle del evento activo, métricas (`Convocados`, `Presentes`, `Ausentes`), buscador reactivo Select2 de socios y tabla interactiva de asistencia.
2. **Modal de Programación con Convocatoria Flexible:**
   - Selector visual excluyente de Categoría: `Reunión` vs `Actividad` (con opciones dependientes de tipo).
   - Campos mínimos obligatorios: `Título`, `Fecha y Hora de Inicio`, `Tipo` y `Modalidad`.
   - Selector de Modalidad:
     * `Presencial en Sede`: Indicador visual "Sede Central AVEIT".
     * `Presencial fuera de Sede`: Campo requerido para ingresar la dirección o locación externa.
     * `Virtual`: Campo requerido para el enlace de videoconferencia (Meet, Zoom, Teams).
   - `Fecha y Hora de Fin`: Claramente rotulado como campo **(Opcional)**.
   - Selector visual de modo de convocatoria: `Por Grupo` (G57-G60), `Por Subcomisión` o `Lista Personalizada de Gente` (Select2 reactivo).
3. **Grilla y Panel de Asistencia con Motivo Circunstanciado:**
   - Para cada socio convocado, además del switch de estado (`Presente`, `Tarde`, `Ausente`), se provee un campo editable de texto para registrar el **Motivo / Observación explicativa** individual que justifique la situación y se traslade al expediente disciplinario si corresponde.
4. **Banner Semántico de Validez (CA1 / CA2):**
   - Si el evento es extemporáneo o no sancionable, se renderiza un banner amarillo/ámbar de advertencia con tokens `{colors.warning}` informando la pérdida del carácter sancionable.
5. **Modal de Cierre y Confirmación:**
   - Previsualiza los expedientes que se generarán con sus motivos circunstanciados antes del impacto formal.
   - Muestra contador en 0 si el evento perdió el carácter sancionable.
6. **Notificaciones Centrales:**
   - Integración con `NotificationService.show` (10 segundos, botón X de cierre accesible).

---

## 7. Estrategia de Pruebas Automatizadas

1. **Backend (Pytest):**
   - `test_meeting_compliance.py`: Pruebas de borde para los 2 días de preaviso y 72 hs de reporte con fines de semana y feriados (CA1).
   - `test_event_non_sanctionable.py`: Comprobación de 0 expedientes ante eventos extemporáneos (CA2).
   - `test_sanction_scale.py`: Validación de escala decimal con 0.5, 1.0, 1.5 y 2.0 (CA3).
   - `test_warning_accumulation.py`: Prueba de concurrencia y consolidación exacta 3:1 de apercibimientos (CA4).
   - `test_zero_update_balance.py`: Comprobación de que `Socio.saldo` no sufre `UPDATE` y solo se crean expedientes `CREADO` (CA5).
2. **Frontend (Karma / Jasmine):**
   - `eventos-asistencia.component.spec.ts`: Tests de alternancia de Strategy, validación reactiva de plazos, renderizado de banners CA1/CA2 y feedback vía `NotificationService`.
