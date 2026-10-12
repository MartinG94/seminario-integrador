# TASK.md — Hoja de Ruta y Tareas del Proyecto SGD-AVEIT

Documento maestro de seguimiento y gobernanza de tareas bajo la metodología **Spec-Driven Development (SDD)**. Articula el cronograma macro por Sprints con el desglose granular atómico de tareas verificables (`<30 minutos`).

---

## 1. Roadmap Macro de Sprints (Ciclo Lectivo 2026)

| Iteración | Fechas | Enfoque / Incremento Comprometido | User Stories / Issues | Estado |
| :---: | :---: | :--- | :---: | :---: |
| **Sprint 0** | 18/08 al 08/09 | **Fundacional:** Relevamiento, Anteproyecto, ERS, BPMN, Arquitectura, Acuerdos de Trabajo, Prototipado UX y Gobernanza SDD. | — | **Completado** |
| **Sprint 1** | 09/09 al 22/09 | **Walking Skeleton:** Autenticación JWT, Roles RBAC, Padrón institucional, Ranking oficial de puntos y Legajo de socio. | `SCRUM-34` a `SCRUM-39` (20 SP) | **Completado (20 SP)** |
| **Sprint 2** | 23/09 al 06/10 | **Expedientes, Notificaciones y Monitoreo:** Formulario T01 multi-socio, competencias (Arts. 21-26), Outbox email, Tablero 6 Estados y Mis Solicitudes T01. | `SCRUM-40` a `SCRUM-44`, `SCRUM-75` (23 SP) | **Completado (23 SP)** |
| **Sprint 3** | 07/10 al 20/10 | **Descargos y Plazos Preclusivos:** Formularios T02 y T03 con adjuntos probatorios (PDF/imágenes) y temporizador regresivo de 5 días hábiles. | `SCRUM-45` a `SCRUM-50` (19 SP) | **Próximo a Iniciar / En Curso** |
| **Sprint 4** | 21/10 al 03/11 | **Sustanciación y Votación Colegiada:** Módulo 'Justificaciones' del TD, gestión de inhibiciones/suplencias, votación nominal remota y firma colegiada de Activos. | `SCRUM-51` a `SCRUM-56` (22 SP) | Planificado |
| **Sprint 5** | 04/11 al 17/11 | **Sumatoria Inmutable de Puntos y Alertas:** Actualización transaccional auditada (cero UPDATE), portal 'Mis Expedientes' y motor de alertas automáticas (7 pts y 10 pts). | `SCRUM-57` a `SCRUM-62` (20 SP) | Planificado |
| **Sprint 6** | 18/11 al 01/12 | **Auditoría, Balances y Cierre:** Generador de Balances Cuatrimestrales (Art. 137), repositorio de jurisprudencia, homologación institucional y entrega final. | `SCRUM-63` a `SCRUM-68` (24 SP) | Planificado |

---

## 2. Cierre de Sprint 0 (Fase Fundacional) — Checklist

- [x] **T0.1 Relevamiento Normativo e Institucional:** Análisis del Estatuto 2026, Reglamento Interno de Disciplina 2026, Reglamento Procesal 2026 y Circular 001/2026.  
      *Hecho cuando:* Documentos consolidados en `docs/analisis-proceso-actual/` y `docs/formales/`.
- [x] **T0.2 Modelado de Procesos de Negocio:** Diagramación BPMN 2.0 del ciclo de vida procesal del expediente en sus 6 estados oficiales.  
      *Hecho cuando:* `docs/analisis-proceso-actual/BPMN_Proceso_Operativo_Tribunal.md` generado y aprobado.
- [x] **T0.3 Especificación de Requerimientos de Software (ERS):** Formalización de 19 Requerimientos Funcionales (`RF-01` a `RF-19`), 6 RNF bajo ISO 25010 y 11 Reglas de Negocio (`RN-01` a `RN-11`).  
      *Hecho cuando:* `docs/especificaciones/ERS-SGD-AVEIT.md` completo con trazabilidad normativa.
- [x] **T0.4 Modelo Conceptual de Dominio:** Elaboración del diagrama de clases de dominio en UML/Mermaid con multiplicidades exactas.  
      *Hecho cuando:* `docs/especificaciones/MODELO_DOMINIO_SGD_AVEIT.md` redactado con diccionario de datos.
- [x] **T0.5 Catálogo de Actores y Matriz RBAC:** Caracterización de los 7 actores clave del sistema (5 humanos y 2 automatizados).  
      *Hecho cuando:* `docs/analisis-proceso-actual/ACTORES_DEL_SISTEMA_SGD_AVEIT.md` finalizado.
- [x] **T0.6 Acuerdos de Trabajo y Gobernanza Ágil:** Definición de Sprints de 14 días, Definition of Ready (DoR), Definition of Done (DoD) y Product Backlog estimado en Story Points.  
      *Hecho cuando:* `docs/gestion-proyecto/Seguimiento de Proyecto.md` y `docs/gestion-proyecto/PLAN_DE_PROYECTO_SGD_AVEIT.md` aprobados por Cátedra.
- [x] **T0.7 Prototipos y Sistema de Diseño:** Formalización de tokens de diseño AVEIT y maquetación de pantallas preliminares.  
      *Hecho cuando:* `DESIGN.md` creado y prototipos interactivos en `prototipos/` operativos.
- [x] **T0.8 Gobernanza SDD y Dockerización:** Configuración del estándar Spec-Driven Development de MoureDev, `AGENTS.md`, `constitution.md` y `docker-compose.yml`.  
      *Hecho cuando:* Entorno de desarrollo local unificado y listo para iniciar desarrollo de código.

---

## 3. Sprint 1 — Desglose Atómico: Spec 001 (Walking Skeleton)

> **Spec de Referencia:** [`specs/001-walking-skeleton/spec.md`](specs/001-walking-skeleton/spec.md)  
> **Plan Técnico:** [`specs/001-walking-skeleton/plan.md`](specs/001-walking-skeleton/plan.md)  
> **Estado:** **Completado (20 SP logrados)**

- [x] **T1. Esqueleto Backend Django & Configuración:** Inicializar estructura del proyecto en `backend/` con `core/settings.py`, `pytest.ini` y dependencias en `requirements.txt`.  
      *(RF: —)* **Hecho cuando:** `pytest -q` corre en `backend/` sin errores de configuración (0 tests).

- [x] **T2. Conexión MySQL y Healthcheck en Docker:** Configurar conector MySQL y endpoint de estado `/api/health/`.  
      *(RF: —)* **Hecho cuando:** `docker compose up` levanta `db` y `backend`, y `curl http://localhost:8000/api/health/` devuelve `{"status": "ok", "db": "connected"}`.

- [x] **T3. Modelo de Socios y Subcomisiones:** Implementar modelos `Subcomision` y `Socio` con validación de año social y categorización automática Pasivo/Activo.
      *(RF: RF-06-WS)* **Hecho cuando:** Tests unitarios de creación de socios, unicidad de legajo y cálculo de categoría social en verde.

- [x] **T4. Libro Mayor de Puntos (Transacciones Inmutables):** Crear modelo `TransaccionPuntos` y servicio `calculate_socio_balance(socio_id)`.  
      *(RF: RF-06-WS)* **Hecho cuando:** Tests con transacciones positivas (+2.0), negativas (-1.0) y sin transacciones (0.0) en verde.

- [x] **T5. Autenticación JWT y Roles RBAC:** Configurar SimpleJWT con claims personalizados (`legajo`, `role`, `category`) y permisos DRF (`IsTribunalOrDirectiva`).  
      *(RF: RF-01-WS, RF-02-WS, RF-05-WS)* **Hecho cuando:** Tests de login exitoso (retorna access/refresh), login con credenciales inválidas (401) y acceso prohibido para socios ordinarios a rutas de gestión (403) en verde.

- [x] **T6. Endpoint de Ranking Oficial:** Implementar viewset `/api/v1/ranking/` con agregación de saldos, filtros por subcomisión, categoría y ordenamiento descendente.  
      *(RF: RF-03-WS, RF-06-WS)* **Hecho cuando:** Tests de endpoint retornando lista paginada de socios con saldos correctos y ordenamiento en verde.

- [x] **T7. Endpoint de Búsqueda y Detalle de Legajo:** Implementar búsqueda insensible a mayúsculas/tildes en `/api/v1/socios/` y detalle `/api/v1/socios/<id>/legajo/`.  
      *(RF: RF-04-WS)* **Hecho cuando:** Tests de búsqueda por nombre, apellido y legajo con tiempo de respuesta < 500 ms en verde.

- [x] **T8. Servicio Angular de Autenticación (`AuthService`):** Crear servicio en `frontend` con métodos `login()`, `logout()`, `getToken()` e interceptor HTTP para Bearer token.  
      *(RF: RF-01-WS)* **Hecho cuando:** Tests de `AuthService` en Jasmine pasan en verde.

- [x] **T9. Integración de Componente `RankingSociosComponent`:** Conectar el componente existente en Angular con el endpoint `/api/v1/ranking/`, agregando controles de filtro y paginación con estilos AVEIT.  
      *(RF: RF-03-WS, RNF-02)* **Hecho cuando:** `ng test --include=**/ranking-socios.component.spec.ts` en verde y renderizado correcto en viewport móvil.

- [x] **T10. Modal de Legajo de Socio en Angular:** Implementar diálogo modal para consultar el legajo del socio seleccionado con su historial de puntos.  
      *(RF: RF-04-WS)* **Hecho cuando:** Al hacer clic en un socio del ranking se despliega el modal con sus datos y saldo auditado.

- [x] **T11. Verificación End-to-End y Smoke Test:** Validación integral del Walking Skeleton mediante demo manual y checklist de criterios de aceptación de la Spec 001.  
      *(Todos los RF de Spec 001)* **Hecho cuando:** Login funcional desde Angular contra Django/MySQL, ranking poblado y búsqueda operativa sin errores en consola ni en logs.

---

## 3.1. Sprint 2 — Desglose Atómico: S2-04 / SCRUM-43 (Notificar Apertura con Entrega y Reintentos Auditables)

> **Historia de Usuario:** S2-04 / SCRUM-43: Notificar apertura con entrega y reintentos auditables.  
> **Criterios de Aceptación:** CA1 (Transición condicionada), CA2 (Plantilla segura sin datos médicos), CA3 (Outbox, idempotencia y auditoría), CA4 (Enlace seguro con RBAC por objeto), CA5 (Inmutabilidad de fecha base).

- [x] **T1. Capa de Dominio: Sanitización de Privacidad y Plantilla Institucional (TDD):** `NotificationSanitizer` (fallo cerrado ante datos médicos o sensibles) y `OpeningNotificationTemplate` (composición HTML/texto, enlace seguro, `idempotency_key`).
- [x] **T2. Capa de Aplicación: Servicio de Despacho Atómico e Idempotencia (TDD):** `OpeningNotificationService.dispatch_opening(...)` y `CaseNotificationQueryService`.
- [x] **T3. Capa de Seguridad: Autorización RBAC por Objeto (TDD):** `IsImputadoOrTribunal(BasePermission)`.
- [x] **T4. API REST: Endpoints de Despacho y Auditoría de Entrega para el TD (TDD):** `POST /despachar-notificacion/` y `GET /notificaciones/`.
- [x] **T5. API REST: Endpoint Seguro de Detalle de Causa para el Enlace de Correo (TDD):** `GET /api/v1/expedientes/<id>/` protegido con `IsImputadoOrTribunal`.
- [x] **T6. Regresión Global, Inmutabilidad, Cobertura y Linter:** Suite completa, inmutabilidad CA5, ruff check/format y chequeo PO.

---

## 4. Sprint 3 — Desglose Atómico: S3-02 / SCRUM-46 (Cálculo y Cierre de Plazo de 5 Días Hábiles)

> **Historia de Usuario:** S3-02 / SCRUM-46: Calcular y Cerrar el Plazo de Cinco Días Hábiles.  
> **Criterios de Aceptación:** CA1 (Inicio formal), CA2 (Servidor autoritativo y rechazo 409), CA3 (UI con fecha/hora exacta y cuenta regresiva dinámica), CA4 (Cierre idempotente y concurrente con auditoría), CA5 (Cobertura de fines de semana, feriados Carnaval, Semana Santa y límite inclusivo).

- [x] **TS3-02.1 Dominio del Calendario Laboral y Feriados:** Implementación del puerto `HolidayProviderPort`, proveedores `Argentina2026HolidayProvider` y cálculo puro determinista `compute_business_deadline()` con preservación horaria y timezone `America/Argentina/Buenos_Aires`.  
      *Hecho cuando:* 14 tests unitarios de calendario pasando en verde (cubriendo fines de semana, feriados consecutivos, Carnaval, Semana Santa y cambios de mes/año).
- [x] **TS3-02.2 Persistencia de Plazos y Congelamiento de Deadline:** Modelo `Expediente` con los 6 estados canónicos, campos `plazo_inicio_at`, `plazo_limite_at` congelado, `descargo_presentado` y modelo de auditoría `CambioEstadoExpediente`.  
      *Hecho cuando:* Migraciones generadas y tests de persistencia y congelamiento pasando en verde.
- [x] **TS3-02.3 Servicio de Aplicación y Cierre Idempotente Concurrente:** `DeadlineEnforcementService` con patrón *Double-Checked Locking* bajo `transaction.atomic()` y `select_for_update()`, auditoría `SISTEMA_CRON` y management command `close_expired_deadlines`.  
      *Hecho cuando:* Tests de ejecución única, ejecuciones repetidas y no afectación de expedientes en plazo o justificados pasando en verde.
- [x] **TS3-02.4 Endpoint de Descargo con Protección en Servidor y HTTP 409:** Endpoint `/api/v1/expedientes/<id>/descargo/` con bloqueo pesimista contra condiciones de carrera (buzzer-beater), aceptación en límite inclusivo (`now <= plazo_limite_at`), rechazo con HTTP `409 Conflict` ante expiración y endpoint `/api/v1/expedientes/mis-expedientes/`.  
      *Hecho cuando:* Tests de integración de API pasando en verde.
- [x] **TS3-02.5 Frontend Reactivo de Temporizador y Vencimiento Exacto:** Integración en `mis-expedientes` con fecha/hora exacta (`Vence: Jueves 15/10/2026 - 18:00 hs`), cuenta regresiva dinámica reactiva con `interval(1000)`, deshabilitación inmediata del formulario/botón al llegar a cero ("Plazo Expirado") y cero fugas de memoria con `ngOnDestroy`.  
      *Hecho cuando:* Pruebas unitarias de frontend agregadas y verificadas.

---

## 5. Sprint 2 — Desglose Atómico: S2-01 / SCRUM-40 (Apertura y Trazabilidad del Expediente)

> **Historia de Usuario:** S2-01 / SCRUM-40: Como integrante habilitado quiero abrir y seguir un expediente con trazabilidad completa.  
> **Criterios de Aceptación:** CA1 (Número único y correlativo), CA2 (Exactamente los seis estados del Art. 12), CA3 (Cada transición registra actor, fecha y motivo y rechaza saltos), CA4 (La concurrencia no duplica la numeración).

- [x] **S2-01.1 Especificar criterios y flujo:** `specs/002-expediente-trazabilidad/` con CA, seis estados, roles de apertura y múltiples socios.
- [x] **S2-01.2 Pruebas de apertura y trazabilidad:** Creación autorizada, numeración correlativa sin huecos, auditoría inicial e historial consultable.
- [x] **S2-01.3 Servicio de transición secuencial:** `ExpedienteWorkflowService` con bloqueo pesimista que registra actor/fecha/motivo y rechaza saltos o retrocesos.
- [x] **S2-01.4 Socios múltiples y compatibilidad:** Relación `socios`, descargo individual por socio y migración de los expedientes existentes.
- [x] **S2-01.5 Verificación de integración:** Suite backend contra MySQL 8, `makemigrations --check` y test de concurrencia multihilo (CA4).

---

## 6. Sprint 2 — Desglose Atómico: SCRUM-75 / PB-04 (Monitorear Solicitudes T01 Iniciadas)

> **Historia de Usuario:** SCRUM-75 / PB-04: Como autoridad solicitante (CD/TD/Subcomisión) quiero consultar la lista y el estado procesal de los expedientes que inicié mediante T01 para monitorear el avance de las solicitudes sin acceder a la deliberación interna reservada del TD.  
> **Criterios de Aceptación:** CA1 (Aislamiento de Creador), CA2 (Datos Visibles y Estado Procesal), CA3 (Confidencialidad Estricta del TD), CA4 (Control de Acceso RBAC CanCreateT01), CA5 (Interfaz Responsive e Interacciones).

- [x] **TS-75.1 Modelo y Vinculación T01 ➔ Expediente:** Vincular `SolicitudT01` con `Expediente` (campo `expediente = OneToOneField(Expediente, ...)`). Al emitir solicitud en `EmitirT01Serializer.save()`, abrir atómicamente el `Expediente` mediante `ExpedienteWorkflowService.open_expediente` asociando socios involucrados y motivo.
- [x] **TS-75.2 Serializer y Queryset Sanitizado para Monitoreo (Backend TDD):** Implementar `MisSolicitudesT01Serializer` sanitizado excluyendo deliberaciones, notas y votos del TD (CA2, CA3).
- [x] **TS-75.3 Endpoint REST `GET /api/v1/expedientes/mis-solicitudes/` (Backend TDD):** Implementar vista protegida con `CanCreateT01`, filtrado estricto por `solicitante = request.user.socio`, filtros por estado y buscador textual (CA1, CA4, CA5). Pruebas de permisos y aislamiento.
- [x] **TS-75.4 Servicio Angular y DTOs (`ExpedienteApiService`):** Definir interfaces DTOs y métodos en `ExpedienteApiService` para listar solicitudes iniciadas y eliminar borradores. Tests unitarios en Jasmine.
- [x] **TS-75.5 Componente e Interfaz de Usuario ("Mis Solicitudes T01" en `SolicitarPuntosComponent`):** Incorporar panel inferior reactivo en `solicitar-puntos` con buscador, filtro de estados, tabla responsive y acciones de reanudación y descarte de borradores (CA5).
- [x] **TS-75.6 Modal de Detalle Resumido y Trazabilidad:** Incorporar diálogo modal para visualizar la solicitud emitida con su estado procesal y resolución final sin datos reservados del TD (CA2, CA3).
- [x] **TS-75.7 Suite Integral de Pruebas, Verificación y Consistencia:** Ejecutar suite backend (`pytest`), frontend (`npm test`), linters y corroborar consistencia con `notasPO.md`.

---

## 7. Sprint 3 — Desglose Atómico: S3-01 / SCRUM-45 (Configurar Calendario Institucional de Días Hábiles)

> **Historia de Usuario:** S3-01 / SCRUM-45: Como autoridad habilitada quiero mantener los feriados del calendario institucional único para calcular plazos auditables.
> **Criterios vigentes tras la revisión del PR #49 y los cambios adicionales del PM:** CA1 (Calendario único e impacto inmediato), CA2 (Auditoría por feriado), CA3 (Vencimientos persistidos inmutables), CA4 (Zona institucional), CA5 (Lectura autenticada y alta ADMIN/CD/TD), CA6 (UX/UI simplificada y simulador modal con reinicio), CA7 (Fecha >= hoy y sin duplicados), CA8 (Actualización y reaplicación segura de migraciones), CA9 (Notificaciones globales de 10 segundos con cierre manual).

### Implementación original (antecedente del PR)

- [x] **TS3-01.1 Modelos ORM y Dominio de Calendario:** Implementar `CalendarioVersion` y `FeriadoExcepcion` en `backend/expedientes/models.py` con restricciones de unicidad y auditoría (CA2). Vincular `Expediente.calendario_version` con ForeignKey protegida (CA3).
- [x] **TS3-01.2 Adaptador de Infraestructura y Cálculo de Plazos:** Implementar `DbHolidayProvider` en `backend/expedientes/domain/holiday_provider.py` que consulta feriados por versión de calendario. Actualizar `Expediente.iniciar_plazo_descargo` para asociar y congelar la versión activa o pasada explícitamente (CA1, CA3, CA4).
- [x] **TS3-01.3 Migraciones y Carga Inicial de Feriados 2026 (Seeder):** Generar migraciones de esquema y migración de datos para crear la Versión 1 ("Calendario Oficial AVEIT 2026") y poblar los 16 feriados oficiales de 2026.
- [x] **TS3-01.4 Tests de Dominio y Persistencia (TDD Backend):** Crear `backend/tests/expedientes/test_calendar_models.py` para probar la inmutabilidad de la versión en el expediente, exclusión de fines de semana/feriados, y preservación de zona horaria (CA1, CA2, CA3, CA4).
- [x] **TS3-01.5 Serializers y Permisos RBAC de Calendario:** Implementar `CalendarioVersionSerializer`, `FeriadoExcepcionSerializer`, `CalcularPlazoSerializer` y el permiso `CanManageCalendar` (ADMIN, CD, TD) en `backend/expedientes/`.
- [x] **TS3-01.6 Endpoints REST de Calendario (TDD Backend):** Implementar vistas y router en `backend/expedientes/` para listar versiones, crear nueva versión auditada, listar feriados y calcular plazos. Crear `backend/tests/expedientes/test_calendar_api.py` verificando RBAC y cálculos.
- [x] **TS3-01.7 DTOs y Servicio Angular (`CalendarioApiService`):** Crear interfaces tipadas y servicio Angular en `frontend/src/app/services/calendario-api.service.ts` con sus tests unitarios en Jasmine.
- [x] **TS3-01.8 Componente Angular e Interfaz de Usuario:** Crear componente `CalendarioInstitucionalComponent` en `frontend/src/app/calendario-institucional/`, con vista de feriados, simulador de plazos interactivo en tiempo real y formulario modal para nuevas excepciones/versiones conforme a `DESIGN.md`. Registrar ruta y enlace en sidebar para autoridades.
- [x] **TS3-01.9 Verificación Integral, Cobertura y Consistencia PO:** Ejecutar suite completa `pytest` y `npm test`, linters (`ruff` y `ng lint`), verificar consistencia con `notasPO.md` y preparar el levantamiento en localhost.

### Correcciones de la revisión del PO — PR #49

- [x] **R1. Calendario único y migración auditable:** Importación de inhábiles del último calendario activo, conservación de referencias y timestamps históricos, fechas oficiales corregidas y sin autores inferidos.
- [x] **R2. API y cómputo unificados (TDD):** Lectura para todo usuario autenticado, alta por ADMIN/CD/TD, validación de fecha institucional, auditoría del servidor y duplicados concurrentes controlados.
- [x] **R3. UX/UI simplificada (TDD):** Crear Feriado, Año/Mes, orden Fecha y autoría visible; fechas independientes de zona del navegador y recálculo de simulaciones pendientes tras un alta.
- [x] **R4. Verificación y entorno UAT:** Backend 505/505, frontend 153/153, dominio 99%, build/Ruff y migraciones en verde. Auditoría sin hallazgos pendientes y localhost disponible. La limitación del lint Angular se registra en [UAT del PR #49](docs/gestion-proyecto/UAT-PR49-calendario.md).
- [x] **R5. Ajustes visuales de UAT:** Año/Mes en una misma fila; etiquetas e inputs del simulador alineados en escritorio. Verificación a 320/393 px, 153 tests frontend y compilación en verde; auditoría de par sin hallazgos. UAT aprobada por el usuario el 10/10/2026.

### Segunda review del PM — PR #49

- [x] **R6. Migraciones y lectura (TDD):** Importación 0010 idempotente que conserva registros/auditoría. Ocho casos de importación y MigrationExecutor sobre MySQL; GET real 200 para SOCIO, FISCALIZADORA, CD, TD y ADMIN.
- [x] **R7. Interfaz y recuperación (TDD):** Tarjeta de alta blanca con radio de 8 px; botones institucionales con iconos y controles alineados. Estados vacío/error centrados, reintento real y bloqueo de alta hasta recuperar la carga completa.
- [x] **R8. Verificación y entorno:** Backend 510/510, frontend 156/156, compilación/Ruff/migraciones y DESIGN.md lint sin errores. Auditoría independiente cerrada; escritorio, 768/393/320 px, teclado y recuperación de carga verificados. Localhost disponible; UAT aprobada por el usuario el 10/10/2026.

### Integración con main — PR #49

- [x] **R9. Resolver conflictos con main:** Calendario y urgencia preservados; migración de unión 0011 sin reescribir historiales publicados. Actualización desde ambas ramas comprobada con datos existentes; backend 537/537, frontend 175/175, build/Ruff/migraciones en verde y auditoría independiente sin hallazgos pendientes.

### Modificaciones adicionales del PM — PR #49

- [x] **R10. Notificaciones centrales (TDD):** Avisos abajo a la derecha, 10 segundos, X accesible y temporizadores independientes; host visible e integrado al foco de modales. Regla en AGENTS.md.
- [x] **R11. Login, calendario y sesión (TDD):** Feedback centralizado y errores de sesión sin duplicados ni afectación de una sesión nueva.
- [x] **R12. T01 y descargos (TDD):** Validaciones y resultados centralizados, con borradores, emisión, urgencia y evidencia preservados.
- [x] **R13. Gestión y restantes vistas (TDD):** Gestión, ranking/legajo, asistencia y demo mediante el mismo servicio; errores y recuperación verificados.
- [x] **R14. Simulador modal (TDD):** Botón junto a Crear Feriado; cierre cancela solicitudes y reinicia campos y resultado.
- [x] **R15. Verificación y auditoría:** Frontend 205/205, build y diseño sin errores; auditoría independiente cerrada, consistencia PO y QA real a 1306/393/320 px con teclado. Localhost activo y UAT del nuevo alcance aprobada por el usuario el 10/10/2026 en la guía del PR #49.

---

## 8. Sprint 3 — Desglose Atómico: S3-07 / SCRUM-78 (Clasificador e Indicador Visual de Urgencia en Expedientes)

> **Historia de Usuario:** S3-07 / SCRUM-78: Implementar clasificador e indicador visual de urgencia en expedientes.  
> **Criterios de Aceptación:** CA1 (Tres niveles de urgencia: Baja, Normal, Urgente con default Normal), CA2 (Filtro por urgencia en API y Frontend), CA3 (Indicador visual distintivo en tarjetas Kanban y tabla), CA4 (Actualización de urgencia autorizada vía PATCH para TD/CD), CA5 (Inmutabilidad de notas del PO y estricto respeto a tokens de diseño).

- [x] **TS3-07.1 Modelo y Migración de Urgencia (Backend TDD):** Enumeración `UrgenciaExpedienteEnum` (`baja`, `normal`, `urgente`), campo `urgencia` con default `normal` e índice en `Expediente` y `SolicitudT01`. Migración Django `0007_expediente_urgencia.py`.
- [x] **TS3-07.2 Serialización y Filtro por Urgencia en API REST (Backend TDD):** Inclusión de `urgencia` y `urgencia_display` en `BoardExpedienteSerializer` y `ExpedienteListSerializer`. Filtro por urgencia en `ExpedienteFilter`.
- [x] **TS3-07.3 Endpoint PATCH de Actualización de Urgencia (Backend TDD):** `PATCH /api/v1/expedientes/<id>/` con `UpdateUrgenciaExpedienteSerializer` y permiso `IsTribunalOrDirectiva`.
- [x] **TS3-07.4 DTOs, Mapeo y Servicio en Frontend (Angular TDD):** Tipado `NivelUrgencia`, mapeo en `TribunalDataService` y método `actualizarUrgencia()`.
- [x] **TS3-07.5 Indicadores Visuales y Filtro en Tablero Kanban y Tabla (Frontend):** Filtro de urgencia en toolbar, badge semántico compacto (icono opcional en Kanban), resaltado de borde rojo en tarjetas urgentes (`.kanban-card-urgente`), columna en tabla explorer y selector de urgencia en modal de detalle.
- [x] **TS3-07.6 Verificación Integral, Cobertura y Consistencia con PO:** 9 tests unitarios e integrales backend en verde, 13 tests frontend en Karma pasando en verde y compilación de producción exitosa.

---

### Observaciones del PO en PR #50 — S3-07 / SCRUM-78

- [x] **TS3-07.7 Urgencia en origen:** Selector Crear Expediente / T01, persistencia de borrador, herencia al expediente y snapshot inmutable de emisión con pruebas. 57 pruebas backend y 30 del formulario Angular en verde.
- [x] **TS3-07.8 Tarjeta Kanban simplificada:** Únicamente ID sin quiebres, urgencia compacta, puntos, título/motivo y fecha institucional con pruebas de renderizado. 18 pruebas del componente Angular en verde.
- [x] **TS3-07.9 Verificación y UAT:** 490 pruebas backend/MySQL y 151 frontend/Karma en verde (0 errores), build de producción correcto, Ruff y migraciones verificados, consistencia con PO y auditoría full stack sin hallazgos pendientes. UAT funcional/visual en escritorio y móvil (375 px), con http://localhost:4201 activo. Lint frontend bloqueado por la configuración TSLint heredada.

- [x] **TS3-07.10 Selección visual de urgencia (TDD):** Casillas Baja/Normal/Urgente con tokens verde/azul/rojo, selección única y estados bloqueados. 32 pruebas del formulario y 153 frontend en verde (0 errores), build correcto y auditoría sin bloqueantes. Guardado/reanudación/emisión, teclado y controles a 320/375 px verificados en localhost:4201. UAT aprobada por el usuario el 10/10/2026.

---


## 7.1. Sprint 3 — SCRUM-77 / S3-PO2 (MySQL y datos sintéticos G57–G60)

> **Spec:** [005-mysql-seed-g57-g60](specs/005-mysql-seed-g57-g60/spec.md).
>
> **Plan técnico:** [plan.md](specs/005-mysql-seed-g57-g60/plan.md).
>
> **Tareas:** [tasks.md](specs/005-mysql-seed-g57-g60/tasks.md).
>
> **Objetivo autorizado:** Terminar TS77.09–27 sin confirmaciones individuales, con los subagentes necesarios; TS77.08 integrada como prerrequisito de carga. Se conservan TDD, dependencias y un runner MySQL/Karma por vez.
>
> **Estado:** SCRUM-77 completada: TS77.01–43 verificadas y cerradas, con auditoría integral aprobada sin hallazgos abiertos. 1008 backend y 222 frontend verdes (0 errores), cobertura 93,91% en 22 módulos y build 6fae4265931dc3f8 correcto. Catálogo cargado, repetición y persistencia sin reseed verificadas; 78 controles HTTP reforzados y recorridos reales de escritorio/360/414 px en ambos temas. Lint frontend mantiene el builder TSLint heredado ausente. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts770827) y [uso/recuperación](docs/gestion-proyecto/GUIA_CARGA_DEMO_SCRUM-77.md).
>
> **Aclaración PO:** DP77-01 cerrado por versión corregida: G57 exviajero; G58/G59/G60 en 6/5/4. Junior 1–2 / Senior 3+.
>
> **Prerrequisito del seed:** DEP77-02 cerrado por TS77.37; guardias, propiedad, carga y manifiesto implementados. Clasificación, rol, vigencia y facultades independientes.

- [x] **TS77.01 Registrar alcance autorizado y pendientes:** Datos sintéticos y límites definidos; mapa inicialmente abierto, cerrado luego por aclaración corregida del PO.
- [x] **TS77.02 Formalizar spec, plan y tareas:** EARS, criterios y seguimiento atómico, sin cambios en notasPO ni Seguimiento de Proyecto.
- [x] **TS77.03 Configuración Docker demo aislada:** Archivo standalone con nombres, puertos loopback, mounts del checkout y volumen propio. 8 pruebas enfocadas y 498 backend en verde (0 errores), Ruff correcto y auditoría sin bloqueantes. CA77-00 verificado; preflight completado en TS77.04 y persistencia/seed pendientes.
- [x] **TS77.04 Preflight MySQL y grants:** Comando de diagnóstico SELECT-only, consulta autenticada y grants demo/tests en MySQL 8.0.46; HTTP 200 local, sin proxies/redirecciones. 34 pruebas enfocadas y 532 backend en verde (0 errores), Ruff correcto y auditoría sin hallazgos abiertos. CA77-01 sigue abierto por guardias de carga TS77.08.
- [x] **TS77.05 DDL y cierre de FKs:** Script mínimo de 27 tablas/39 FKs, auth_user externo y precisión Decimal compatible con Django. 6 pruebas enfocadas y 538 backend en verde (0 errores), Ruff y control de migraciones correctos; auditoría sin hallazgos. Ensayo temporal entregado en esta unidad; aplicación/repetición demo verificadas posteriormente en TS77.06.
- [x] **TS77.06 Verificar bootstrap vacío y repetido:** Aplicador protegido, 30 pruebas de bootstrap (36 combinadas con DDL) y 568 backend en verde (0 errores). Demo MySQL con 47 tablas, 27 legadas/39 FKs y 29 migraciones; repetición con cero creaciones/migraciones y hashes conservados. Divergencias y colisiones managed/CreateModel/AddField M2M sin historial rechazadas antes de escribir; aislamiento de RunPython en ensayos verificado y auditoría favorable. Sin seed ni adecuación societaria.
- [x] **TS77.07 Catálogo y mapa de identidades:** Catálogo v1 puro aceptado tras TS77.37: 16 identidades/cuatro por grupo, rangos/corte/referencias y oráculos de saldo futuro, 62 casos verdes. DP77-02 cerrado; sin carga/manifiesto aún. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts774335363707).
- [x] **TS77.08 Guardias del seed:** Entorno/base/perfil/esquema inválidos sin escrituras.
- [x] **TS77.09 Propiedad de fixtures:** Registro, namespace, unicidad y ejecución serializada.
- [x] **TS77.10 Usuarios y socios locales:** Coexistencia con seed_demo y conservación de credenciales/permisos.
- [x] **TS77.11 Grupos y socios institucionales:** G57–G60, subcomisiones e historial; depende de DEP77-02.
- [x] **TS77.12 Causas simples y multisocio:** Workflow, correlativo y auditoría.
- [x] **TS77.13 T01 de dos solicitantes:** Borradores/emitidas, aislamiento y urgencia.
- [x] **TS77.14 Plazos actuales y urgencias:** Dos etapas seed y regresión de los seis estados.
- [x] **TS77.15 Antecedentes históricos legados:** Resolución y movimientos individuales trazables.
- [x] **TS77.16 Segunda ejecución:** IDs/contador estables y ediciones conservadas.
- [x] **TS77.17 Colisión y fallo intermedio:** Rollback integral del DML y contador.
- [x] **TS77.18 Conciliar SQL/API/manifiesto:** Relaciones, saldo y límites de legajo.
- [x] **TS77.19 Persistencia sin reseed:** Nuevo contenedor y mismo volumen/datos.
- [x] **TS77.20 Smoke login/permisos:** HTTP y perfiles reales.
- [x] **TS77.21 Smoke ranking/legajo:** Filtros, paginación y saldos cotejados.
- [x] **TS77.22 Smoke T01/Mis Solicitudes:** Selección múltiple e aislamiento.
- [x] **TS77.23 Smoke board/tabla:** HTTP/IDs/filtros contra DB y fallbacks detectados.
- [x] **TS77.24 Responsive y teclado:** Escritorio y 360/414 px.
- [x] **TS77.25 Regresión backend:** MySQL, cobertura, Ruff y migraciones.
- [x] **TS77.26 Regresión frontend:** Suite/build y fallos clasificados.
- [x] **TS77.27 Cierre documental y PO:** Evidencia de criterios y uso/recuperación.
- [x] **TS77.28 Registrar aclaración corregida del PO:** Fuentes, cierre DP77-01 y actualización SDD; 43 enlaces locales verificados, estados sincronizados y auditoría documental aprobada sin hallazgos abiertos.
- [x] **TS77.29 Revisar impacto y compatibilidad:** Inventario y decisiones en [impacto/compatibilidad](docs/gestion-proyecto/IMPACTO_COMPATIBILIDAD_SOCIOS_SCRUM-77.md); exviajero explícito/año nulo, contratos canónicos, datos por año, perfil, transición demo e identidad del legajo. 568 pruebas de baseline verdes (0 errores), 43 IDs sincronizados y auditoría independiente aprobada sin hallazgos pendientes. Implementación de la adecuación pendiente.
- [x] **TS77.30 Alinear documentación activa:** Constitución, spec 001, ADR, ERS, modelo/actores y referencias pertinentes alineadas con Junior/Senior y exviajeros; fuentes históricas preservadas y facultades pendientes separadas. 568 pruebas backend verdes (0 errores), 197 enlaces válidos, hashes protegidos conservados y auditoría aprobada. Sin cambios de código, notasPO ni seguimiento macro.
- [x] **TS77.31 Representar exviajeros:** Modelo local EX_TRAVELER/año nulo explícito, longitud 12, CHECK y migración nueva con guardias de avance/reversión. Demo aplicada/repetida, 594 pruebas verdes (0 errores) y auditoría integral aprobada; sin año ficticio ni deshabilitación automática. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7731).
- [x] **TS77.32 Clasificación de socios operativos:** Junior 1/2 y Senior 3–6, con EX_TRAVELER/null conservado y roles/vigencia independientes. 621 pruebas verdes (0 errores), cobertura local 97%, migración de opciones aplicada/repetida y auditoría integral aprobada. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7732).
- [x] **TS77.33 Migrar categorías existentes:** Migración histórica por año/situación, rechazo previo y rollback DML en ambas direcciones; conserva identidades, credenciales, vínculos, snapshots y saldos. 642 pruebas verdes (0 errores), cobertura de migración 100%, demo aplicada/repetida y auditoría integral aprobada. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7733).
- [x] **TS77.34 Alinear padrón/ranking backend:** Implementada; 53 casos propios incluidos en 827 pruebas verdes. Clasificación canónica, EX_TRAVELER explícito/UNKNOWN separados y filtros/count/paginación SQL sin N+1; aliases sólo de entrada. Cierre integral aprobado sin hallazgos pendientes. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7740344142).
- [x] **TS77.35 Alinear contratos/filtros frontend:** Cuatro categorías y nulos coherentes, caché confirmado por me con control de errores/sesiones tardías; ranking abre legajo institucional. Incluida en 202 pruebas frontend verdes; revisión cruzada e integral aprobadas. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts774335363707).
- [x] **TS77.36 Actualizar etiquetas y datos demo:** Labels/tokens/modal/mock y ayuda/tipos seed_demo alineados; 33 identidades mock y cuentas/credenciales/roles/saldos conservados. 202 frontend/8 casos seed_demo verdes y build correcto; auditada, sin cargar demo. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts774335363707).
- [x] **TS77.37 Verificar adecuación transversal:** 932 backend/202 frontend verdes (0 errores), cobertura 94,72%, build correcto y auditoría integral/PO aprobados sin hallazgos. CA77-08/DEP77-02 y CF77-01/02 cerrados; demo/protegidos intactos, lint heredado registrado y US aún en curso. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts774335363707).
- [x] **TS77.38 Evolucionar contrato DDL demo:** anoSocial nullable sólo en el DDL demo; exactamente tres adaptaciones frente al fuente, cierre vacío/repetición y rechazo previo del contrato anterior. 644 pruebas verdes (0 errores), auditoría integral aprobada; demo preparada, modelos, bootstrap y fuente intactos. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7738).
- [x] **TS77.39 Transicionar demo preparada:** Comando protegido y ALTER acotado, filas/IDs/contador/FKs conservados y repetición vacía; 670 pruebas verdes (0 errores), demo aplicada/repetida y auditoría integral aprobada sin hallazgos pendientes. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7739).
- [x] **TS77.40 Condición institucional explícita:** Implementada; metadato por nroSocio real, fuente/corte, PK/CHECK y escritor transaccional idempotente, sin FK al legado. 37 casos y bootstrap previo al legado incluidos en 827 pruebas verdes; migración 0005 aplicada/repetida. Propiedad/manifiesto del seed siguen en TS77.09/11. Cierre integral aprobado sin hallazgos pendientes. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7740344142).
- [x] **TS77.41 Integrar clasificación en T01:** Implementada; 36 casos incluidos en 827 pruebas verdes, EX_TRAVELER/null e identidad institucional inequívoca sin atajo por PK. Conserva credenciales, rol/vigencia y snapshots históricos; rollback de emisión y rechazo de legajo ambiguo. Cierre integral aprobado sin hallazgos pendientes. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7740344142).
- [x] **TS77.42 Actualizar claims y perfil servidor:** Implementada; 30 casos JWT incluidos en 827 pruebas verdes y 3 rotaciones con blacklist real en proceso aislado. Refresh relee categoría del socio, preservando otros claims/opciones; RBAC sigue leyendo rol/vigencia. SPA completada posteriormente en TS77.35. Cierre integral aprobado sin hallazgos pendientes. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts7740344142).
- [x] **TS77.43 Resolver identidad del legajo:** Fuente explícita sólo resuelve PK del namespace; 400 para fuente inválida/repetida, 404 genérico para ambigüedad y llamadas antiguas inequívocas conservadas. Propietario por vínculo/legajo institucional real, legajo ausente null; roles/vigencia/saldos intactos. 33 casos nuevos más dos BIGINT incluidos en 932 pruebas verdes; auditoría integral aprobada. [Evidencia](specs/005-mysql-seed-g57-g60/tasks.md#verificación-de-ts774335363707).

---

### Ampliación posterior a UAT — SCRUM-77

UAT original aprobada por el usuario el 12/10/2026. Sincronización con main y datos Junior autorizados en el mismo pedido; evidencias históricas conservadas.

- [x] **TS77.44 Sincronizar main y preservar feedback PR #49:** Respaldo, conflictos combinados, migraciones protegidas y avisos centrales funcionales.
- [x] **TS77.45 Ampliar catálogo con Juniors:** Cuatro socios/cuentas de G62–G63, años 2/1, saldo cero; carga aditiva y repetición verificadas.
- [x] **TS77.46 Verificar ampliación y auditar:** Suites/build/HTTP/navegador, conservación de datos y revisión independiente.

## 9. Instrucciones para la Actualización de este Archivo

1. Cuando inicies una tarea del Sprint activo, mantenla visible como tu objetivo único.
2. Al finalizar la tarea y validar que todos sus tests estén en verde, edita este archivo y marca el casillero correspondiente: `- [x] Tn. ...`.
3. Sincroniza simultáneamente el archivo `specs/<spec>/tasks.md`.
4. Al culminar la totalidad de las tareas de una spec, actualiza la tabla del **Roadmap Macro** indicando el estado `Completado` y avanza a la siguiente fase.

