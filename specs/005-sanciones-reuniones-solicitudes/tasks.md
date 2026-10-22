# Tareas — Spec 005: Sanciones originadas en reuniones y solicitudes (SCRUM-50 / S3-06)

## Fase 1: Base de Datos, Modelos y Persistencia (DBA)

- [x] **T01. Modelos ORM para Eventos, Asistencias y Apercibimientos:** Implementar `EventoInstitucional` (alias `Reunion`), `AsistenciaEvento` (alias `AsistenciaReunion`) y `RegistroApercibimiento` en `backend/expedientes/models.py`. Campos obligatorios: `titulo`, `fecha_programada` (inicio), `categoria` (`REUNION` / `ACTIVIDAD`), `tipo` (subtipos reglamentarios condicionados) y `modalidad` (`PRESENCIAL_SEDE`, `PRESENCIAL_EXTERNA`, `VIRTUAL`). Campo opcional: `fecha_fin` (`null=True, blank=True`). Campo `motivo` (observación explicativa circunstanciada) en `AsistenciaEvento`. Relaciones foráneas, constraints e índices (`idx_evento_fecha_prog_estado`, `idx_evento_cat_tipo_sancionable`, `idx_aperc_socio_est_created`). Soportar modos de convocatoria (Grupo completo, Subcomisión completa, o Listas personalizadas de gente).
- [x] **T02. Migración Django Segura (0012):** Generar y aplicar la migración `backend/expedientes/migrations/0012_reuniones_asistencias_y_apercibimientos.py` dependiente de `0011_merge_calendar_and_urgency`, verificando compatibilidad en MySQL 8.0.
- [x] **T03. Seed Data y Fixtures de Prueba (G57 a G60):** Incorporar en `docker/mysql/init/02-initial-data.sql` y `seed_production_data.py` los casos testigo con distribución real de socios para G57, G58, G59 y G60, reuniones ordinarias/extraordinarias, actividades y registros de apercibimientos previos.

---

## Fase 2: Servicios de Dominio y Lógica Reglamentaria (TDD Backend)

- [x] **T04. Servicio de Validación de Plazos Procesales (CA1 / CA2 / CA8):** Implementar `MeetingComplianceService` en `backend/expedientes/services/meeting_compliance_service.py` con `validate_notice_period` (2 días hábiles) y `validate_reporting_deadline` (72 horas hábiles a partir de cierre efectivo, fecha fin o fecha inicio cuando fin es opcional) usando `compute_business_deadline`. Tests unitarios en `backend/tests/expedientes/test_meeting_compliance.py`.
- [x] **T05. Patrón Strategy para Captura de Asistencia:** Implementar `AttendanceCaptureStrategy`, `ManualAttendanceStrategy`, `BiometricAttendanceStrategy` y `AttendanceStrategyFactory` en `backend/expedientes/domain/attendance_strategy.py`. Tests unitarios con fixtures de marcas horarias y tolerancias.
- [x] **T06. Motor de Acumulación Atómica 3:1 de Apercibimientos (CA4):** Implementar `WarningAccumulationService.register_warning` en `backend/expedientes/services/warning_service.py` con transacción atómica, bloqueo pesimista `select_for_update()` por socio, consolidación de terna mediante UUID de lote y apertura de expediente de oficio por -1.0 pt. Tests de concurrencia y no duplicación en `backend/tests/expedientes/test_warning_service.py`.
- [x] **T07. Servicio Orquestador de Asistencias y Sanciones (CA3 / CA5 / CA9):** Implementar `AttendanceProcessingService` en `backend/expedientes/services/attendance_processing_service.py` que coordina compliance, strategy, graduación de escala (0.5, 1.0, 1.5, 2.0 según categoría/tipo) y emisión de expedientes en estado `CREADO` sin tocar saldos manualmente.
- [x] **T08. Servicio de Notificación Automática de Convocatoria por Correo (CA7 / Art. 95):** Implementar `MeetingNoticeNotificationService` en `backend/expedientes/services/meeting_notice_service.py` que genera mensajes en `notifications_email_outbox` mediante `EmailDispatcherService` con clave de idempotencia por socio y evento, notificando modalidad y link/ubicación. Tests unitarios en `backend/tests/expedientes/test_meeting_notice_service.py`.

---

## Fase 3: Endpoints REST, Serializadores y Permisos RBAC (TDD Backend)

- [x] **T09. Serializadores y Permisos RBAC:** Implementar `EventoInstitucionalSerializer`, `AsistenciaEventoSerializer`, `ReportarAsistenciaSerializer` (validando `motivo` circunstanciado obligatorio por convocado) y permiso `IsComisionDirectivaOrAdmin` en `backend/expedientes/`.
- [x] **T10. Endpoints de Eventos y Cierre de Asistencia:** Implementar viewset `/api/v1/expedientes/eventos/` integrando notificación automática tras creación, y acción `POST /{id}/reportar-asistencia/`. Implementar endpoint `/api/v1/expedientes/socios/{id}/apercibimientos/`.
- [x] **T11. Suite Integral de Pruebas de API DRF:** Crear `backend/tests/expedientes/test_eventos_api.py` verificando casos válidos (201/200), despacho de correo outbox (CA7), casos extemporáneos sin sanción (CA2), escala de 1.5 pts (CA3), fecha fin opcional (CA8), categorías y modalidades (CA9/CA10) y verificación de saldo inalterado en MySQL (CA5).

---

## Fase 4: Arquitectura, Estrategias y Componentes Frontend (Angular TDD)

- [x] **T12. Modelos, DTOs y Patrón Strategy en TypeScript:** Crear interfaces en `frontend/src/app/eventos-asistencia/models/eventos-asistencia.models.ts` (`CategoriaEvento`, `ModalidadEvento`, `ConvocadoAsistenciaDTO` con `motivo`, etc.) e implementar `IAttendanceCaptureStrategy`, `ManualAttendanceStrategy`, `BiometricAttendanceStrategy` y `AttendanceContextService`. Tests unitarios de las estrategias.
- [x] **T13. Integración de Servicios Frontend:** Actualizar `TribunalDataService` y crear métodos en `ExpedienteApiService` para consumir los endpoints de eventos, cálculo de antelación con `CalendarioApiService` y reporte de asistencia con motivos.
- [x] **T14. Diálogo de Programación con Categorías y Modalidades (CA1 / CA8 / CA9):** Crear `ProgramarReunionDialogComponent` con selector `Reunión` vs `Actividad`, campos obligatorios mínimos (`Título`, `Fecha/Hora Inicio`, `Tipo`, `Modalidad`), `Fecha/Hora Fin` opcional, locación/enlace virtual, selección Select2/autocompletado de socios y grupos (`G57`-`G60`), y validación visual inmediata de antelación mínima de 2 días hábiles.
- [x] **T15. Panel Interactivo de Asistencia y Motivos Circunstanciados (CA10):** Rediseñar `EventosAsistenciaComponent` y `PanelAsistenciaComponent` con tabla de convocados, campo editable de `Motivo / Observación` por socio, alternancia en vivo entre Modo Manual y Modo Biométrico, y banner semántico de advertencia si el evento perdió el carácter sancionable.
- [x] **T16. Diálogo de Cierre y Previsualización de Sanciones:** Crear `ResumenCierreDialogComponent` que exhibe la tabla previa de expedientes y motivos que se generarán antes de confirmar el cierre formal.
- [x] **T17. Suite de Pruebas Unitarias Frontend:** Implementar y ejecutar `eventos-asistencia.component.spec.ts` en Karma/Jasmine garantizando 100% de cobertura en los flujos de CA1, CA2, CA8, CA9, CA10 y selección de estrategias.

---

## Fase 5: Regresión Full Stack, Verificación y UAT

- [x] **T18. Verificación de Regresión Backend:** Ejecutar suite completa `pytest` contra MySQL comprobando que todos los tests pasen en verde (0 errores).
- [x] **T19. Verificación de Regresión Frontend:** Ejecutar `npm test -- --watch=false` comprobando 0 errores en Karma.
- [x] **T20. Chequeo de Consistencia con Notas del PO:** Contrastar la implementación con [`docs/gestion-proyecto/notasPO.md`](../../docs/gestion-proyecto/notasPO.md) confirmando:
  - Cero sentencias `UPDATE`/`DELETE` manuales en MySQL para saldos de puntos.
  - Regla de apercibimientos 3:1 inmutable (sin fracciones ±0,33 ni ±0,5).
  - Inmutabilidad estricta de las notas del PO.
- [x] **T21. Preparación de Documento UAT y Smoke Test en Localhost:** Redactar guía UAT en `docs/gestion-proyecto/` con los casos de prueba ejecutables en localhost:4200.
- [x] **T22. Alineación con Esquema Legacy de AVEIT y Migración Oficial:** Alinear nombres de entidades y tablas con el sistema legacy de AVEIT (`tribunal_categoriaevento`, `tribunal_evento`, `tribunal_evento_convocado`, `tribunal_asistente`, `atencionFelicitacion`). Implementar scripts SQL idempotentes en `backend/core/sql/03-scrum50-eventos-asistencias-apercibimientos.sql` y `docker/mysql/init/03-scrum50-eventos-asistencias-apercibimientos.sql`, actualizar la migración Django `0012` mediante `SeparateDatabaseAndState` con comprobación de `makemigrations --check` en limpio, y validar la regla 3:1 de `atencionFelicitacion` (3 llamadas = 1 sanción -1.00 pt; 3 felicitaciones = 1 mérito +1.00 pt) con 667/667 tests de backend pasando en verde.
- [x] **T23. Conciliación Full-Stack, Idempotencia de Cierre y Protección RBAC (PR #56):** Unificación del contrato de estados de asistencia (`AUSENTE`/`AUSENTE_INJUSTIFICADO`, `TARDE_LEVE`/`TARDANZA_LEVE`, `TARDE_GRAVE`/`TARDANZA_GRAVE`, `JUSTIFICADO`) y respuestas (`expedientes_generados`, `apercibimientos_generados`), resolución filtrada por cohorte/estado social en `AttendanceProcessingService`, idempotencia ante reintentos de cierre disciplinario, previsualización de `puntos_sancion` personalizados en `ResumenCierreDialogComponent`, protección RBAC en rutas y sidebar para ocultar el módulo a socios ordinarios, y sincronización documental en `spec.md`, `plan.md` y `UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md`.

