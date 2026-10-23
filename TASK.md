# TASK.md — Hoja de Ruta y Tareas del Proyecto SGD-AVEIT

Documento maestro de seguimiento y gobernanza de tareas bajo la metodología **Spec-Driven Development (SDD)**. Articula el cronograma macro por Sprints con el desglose granular atómico de tareas verificables (`<30 minutos`).

---

## 1. Roadmap Macro de Sprints (Ciclo Lectivo 2026)

| Iteración | Fechas | Enfoque / Incremento Comprometido | User Stories / Issues | Estado |
| :---: | :---: | :--- | :---: | :---: |
| **Sprint 0** | 18/08 al 08/09 | **Fundacional:** Relevamiento, Anteproyecto, ERS, BPMN, Arquitectura, Acuerdos de Trabajo, Prototipado UX y Gobernanza SDD. | — | **Completado** |
| **Sprint 1** | 09/09 al 22/09 | **Walking Skeleton:** Autenticación JWT, Roles RBAC, Padrón institucional, Ranking oficial de puntos y Legajo de socio. | `SCRUM-34` a `SCRUM-39` (20 SP) | **Completado (20 SP)** |
| **Sprint 2** | 23/09 al 06/10 | **Expedientes, Notificaciones y Monitoreo:** Formulario T01 multi-socio, competencias (Arts. 21-26), Outbox email, Tablero 6 Estados y Mis Solicitudes T01. | `SCRUM-40` a `SCRUM-44`, `SCRUM-75` (23 SP) | **Completado (23 SP)** |
| **Sprint 3** | 08/10 al 20/10 | **Descargos, Evidencias, Calendario y Asistencias:** Formularios T02 y T03 con adjuntos protegidos, calendario de días hábiles, urgencia, asistencias, detalle Sala TD y resolución T02. | `SCRUM-45` a `SCRUM-50`, `SCRUM-52`, `SCRUM-76` a `SCRUM-84` (36 SP) | **Completado (36 SP)** |
| **Sprint 4** | 22/10 al 03/11 | **Sustanciación en Sala TD, Suplencias, Apelación T01 y Resolución Oficial:** Visor unificado, sana crítica T03, apartamiento/suplencia, apelación T01 y resolución oficial sin votación nominal. | `SCRUM-51`, `SCRUM-53`, `SCRUM-54`, `SCRUM-56`, `SCRUM-70` (19 SP) | **En Curso (Activo)** |
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

## 8.1. Sprint 3 — Desglose Atómico: S3-06 / SCRUM-50 (Sanciones originadas en reuniones y solicitudes)

> **Historia de Usuario:** S3-06 / SCRUM-50: Como autoridad competente quiero transformar asistencia y solicitudes aprobadas en propuestas trazables.  
> **Criterios de Aceptación:** CA1 (Valida publicación de reunión con 2 días hábiles y reporte dentro de 72 horas hábiles), CA2 (No sanciona eventos que no cumplen requisitos), CA3 (Escala admite valores de 0,5 incluido 1,5), CA4 (Cada tres apercibimientos generan -1 una sola vez), CA5 (Integración no escribe saldo manualmente).

- [x] **TS3-06.1 Modelos ORM para Eventos, Asistencias y Apercibimientos:** Implementar `EventoInstitucional` (alias `Reunion`), `AsistenciaEvento` (alias `AsistenciaReunion`) y `RegistroApercibimiento` en `backend/expedientes/models.py`. Campos obligatorios: `titulo`, `fecha_programada` (inicio), `categoria` (`REUNION` / `ACTIVIDAD`), `tipo` (subtipos condicionados) y `modalidad` (`PRESENCIAL_SEDE`, `PRESENCIAL_EXTERNA`, `VIRTUAL`). Campo opcional: `fecha_fin` (`null=True`). Campo `motivo` circunstanciado en `AsistenciaEvento`. Relaciones foráneas, constraints e índices (`idx_evento_fecha_prog_estado`, `idx_evento_cat_tipo_sancionable`, `idx_aperc_socio_est_created`). Soportar modos de convocatoria (Grupo completo, Subcomisión completa, o Listas personalizadas de gente).
- [x] **TS3-06.2 Migración Django Segura (0012):** Generar y aplicar la migración `backend/expedientes/migrations/0012_reuniones_asistencias_y_apercibimientos.py` dependiente de `0011_merge_calendar_and_urgency`, verificando compatibilidad en MySQL 8.0.
- [x] **TS3-06.3 Seed Data y Fixtures de Prueba (G57 a G60):** Incorporar en `docker/mysql/init/02-initial-data.sql` y `seed_production_data.py` los casos testigo con distribución real de socios para G57, G58, G59 y G60, reuniones ordinarias/extraordinarias, actividades y registros de apercibimientos previos.
- [x] **TS3-06.4 Servicio de Validación de Plazos Procesales (CA1 / CA2 / CA8):** Implementar `MeetingComplianceService` en `backend/expedientes/services/meeting_compliance_service.py` con `validate_notice_period` (2 días hábiles) y `validate_reporting_deadline` (72 horas hábiles a partir de cierre efectivo, fecha fin o fecha inicio cuando fin es opcional) usando `compute_business_deadline`. Tests unitarios en `backend/tests/expedientes/test_meeting_compliance.py`.
- [x] **TS3-06.5 Patrón Strategy para Captura de Asistencia:** Implementar `AttendanceCaptureStrategy`, `ManualAttendanceStrategy`, `BiometricAttendanceStrategy` y `AttendanceStrategyFactory` en `backend/expedientes/domain/attendance_strategy.py`. Tests unitarios con fixtures de marcas horarias y tolerancias.
- [x] **TS3-06.6 Motor de Acumulación Atómica 3:1 de Apercibimientos (CA4):** Implementar `WarningAccumulationService.register_warning` en `backend/expedientes/services/warning_service.py` con transacción atómica, bloqueo pesimista `select_for_update()` por socio, consolidación de terna mediante UUID de lote y apertura de expediente de oficio por -1.0 pt. Tests de concurrencia y no duplicación en `backend/tests/expedientes/test_warning_service.py`.
- [x] **TS3-06.7 Servicio Orquestador de Asistencias y Sanciones (CA3 / CA5 / CA9):** Implementar `AttendanceProcessingService` en `backend/expedientes/services/attendance_processing_service.py` que coordina compliance, strategy, graduación de escala (0.5, 1.0, 1.5, 2.0 según categoría/tipo) y emisión de expedientes en estado `CREADO` sin tocar saldos manualmente.
- [x] **TS3-06.8 Servicio de Notificación Automática de Convocatoria por Correo (CA7 / Art. 95):** Implementar `MeetingNoticeNotificationService` en `backend/expedientes/services/meeting_notice_service.py` que genera mensajes en `notifications_email_outbox` mediante `EmailDispatcherService` con clave de idempotencia por socio y evento, notificando modalidad y link/ubicación. Tests unitarios en `backend/tests/expedientes/test_meeting_notice_service.py`.
- [x] **TS3-06.9 Serializadores y Permisos RBAC:** Implementar `EventoInstitucionalSerializer`, `AsistenciaEventoSerializer`, `ReportarAsistenciaSerializer` (validando `motivo` circunstanciado obligatorio por convocado) y permiso `IsComisionDirectivaOrAdmin` en `backend/expedientes/`.
- [x] **TS3-06.10 Endpoints de Eventos y Cierre de Asistencia:** Implementar viewset `/api/v1/expedientes/eventos/` integrando notificación automática tras creación, y acción `POST /{id}/reportar-asistencia/`. Implementar endpoint `/api/v1/expedientes/socios/{id}/apercibimientos/`.
- [x] **TS3-06.11 Suite Integral de Pruebas de API DRF:** Crear `backend/tests/expedientes/test_eventos_api.py` verificando casos válidos (201/200), despacho de correo outbox (CA7), casos extemporáneos sin sanción (CA2), escala de 1.5 pts (CA3), fecha fin opcional (CA8), categorías y modalidades (CA9/CA10) y verificación de saldo inalterado en MySQL (CA5).
- [x] **TS3-06.12 Modelos, DTOs y Patrón Strategy en TypeScript:** Crear interfaces en `frontend/src/app/eventos-asistencia/models/eventos-asistencia.models.ts` (`CategoriaEvento`, `ModalidadEvento`, `ConvocadoAsistenciaDTO` con `motivo`, etc.) e implementar `IAttendanceCaptureStrategy`, `ManualAttendanceStrategy`, `BiometricAttendanceStrategy` y `AttendanceContextService`. Tests unitarios de las estrategias.
- [x] **TS3-06.13 Integración de Servicios Frontend:** Actualizar `TribunalDataService` y crear métodos en `ExpedienteApiService` para consumir los endpoints de eventos, cálculo de antelación con `CalendarioApiService` y reporte de asistencia con motivos.
- [x] **TS3-06.14 Diálogo de Programación con Categorías y Modalidades (CA1 / CA8 / CA9):** Crear `ProgramarReunionDialogComponent` con selector `Reunión` vs `Actividad`, campos obligatorios mínimos (`Título`, `Fecha/Hora Inicio`, `Tipo`, `Modalidad`), `Fecha/Hora Fin` opcional, locación/enlace virtual, selección Select2/autocompletado de socios y grupos (`G57`-`G60`), y validación visual inmediata de antelación mínima de 2 días hábiles.
- [x] **TS3-06.15 Panel Interactivo de Asistencia y Motivos Circunstanciados (CA10):** Rediseñar `EventosAsistenciaComponent` y `PanelAsistenciaComponent` con tabla de convocados, campo editable de `Motivo / Observación` por socio, alternancia en vivo entre Modo Manual y Modo Biométrico, y banner semántico de advertencia si el evento perdió el carácter sancionable.
- [x] **TS3-06.16 Diálogo de Cierre y Previsualización de Sanciones:** Crear `ResumenCierreDialogComponent` que exhibe la tabla previa de expedientes y motivos que se generarán antes de confirmar el cierre formal.
- [x] **TS3-06.17 Suite de Pruebas Unitarias Frontend:** Implementar y ejecutar `eventos-asistencia.component.spec.ts` en Karma/Jasmine garantizando 100% de cobertura en los flujos de CA1, CA2, CA8, CA9, CA10 y selección de estrategias.
- [x] **TS3-06.18 Verificación de Regresión Backend:** Ejecutar suite completa `pytest` contra MySQL comprobando que todos los tests pasen en verde (0 errores).
- [x] **TS3-06.19 Verificación de Regresión Frontend:** Ejecutar `npm test -- --watch=false` comprobando 0 errores en Karma.
- [x] **TS3-06.20 Chequeo de Consistencia con Notas del PO:** Contrastar la implementación con [`docs/gestion-proyecto/notasPO.md`](docs/gestion-proyecto/notasPO.md) confirmando:
  - Cero sentencias `UPDATE`/`DELETE` manuales en MySQL para saldos de puntos.
  - Regla de apercibimientos 3:1 inmutable (sin fracciones ±0,33 ni ±0,5).
  - Inmutabilidad estricta de las notas del PO.
- [x] **TS3-06.21 Preparación de Documento UAT y Smoke Test en Localhost:** Redactar guía UAT en `docs/gestion-proyecto/` con los 5 casos de prueba ejecutables en localhost:4200.
- [x] **TS3-06.22 Resolver conflictos y corregir CI de PR #56:** Integrar `main` conservando SCRUM-50 y SCRUM-76; derivar la base temporal desde la configuración de MySQL y conservar `TEST_DATABASE_NAME` explícito. Completar las tablas externas requeridas por el seed antes de las transacciones de prueba, sin cargar datos ni alterar tablas existentes. Siete regresiones de configuración/esquema y 252 pruebas frontend en verde; Ruff, build y control de migraciones correctos. La suite MySQL se verifica en CI tras publicar el commit.
- [x] **TS3-06.23 Sincronizar evidencia protegida de PR #53:** Integrar `main` en `ef9facc`, conservar las rutas y servicios de eventos/evidencias y combinar los seguimientos de SCRUM-50, SCRUM-48 y SCRUM-76. Agregar `0013_merge_evidence_and_events` sin operaciones sobre tablas y una regresión del grafo de migraciones. 84 pruebas backend enfocadas y 267 frontend en verde; Ruff, build y control de migraciones correctos. Regresión completa MySQL verificada por CI tras publicar.
- [x] **TS3-06.24 Alineación con Esquema Legacy de AVEIT y Migración Oficial:** Alinear nombres de entidades y tablas con el sistema legacy de AVEIT (`tribunal_categoriaevento`, `tribunal_evento`, `tribunal_evento_convocado`, `tribunal_asistente`, `atencionFelicitacion`). Implementar scripts SQL idempotentes en `backend/core/sql/03-scrum50-eventos-asistencias-apercibimientos.sql` y `docker/mysql/init/03-scrum50-eventos-asistencias-apercibimientos.sql`, actualizar la migración Django `0012` mediante `SeparateDatabaseAndState` con comprobación de `makemigrations --check` en limpio, y validar la regla 3:1 de `atencionFelicitacion` (3 llamadas = 1 sanción -1.00 pt; 3 felicitaciones = 1 mérito +1.00 pt) con 667/667 tests de backend y build de frontend en verde.
- [x] **TS3-06.25 Rediseño en 2 Pestañas (Generar Evento y Mis Eventos), Ciclo de Vida y Puntuación:** Rediseñar la pantalla en dos pestañas (`Generar Evento` y `Mis Eventos`) idénticas en estilo a `solicitar-puntos`. Distinción clara de Reunión (escala reglamentaria fija) vs Actividad (detalle de tarea multilínea obligatorio y sanción configurable al crear). Soporte de convocatorias por Estado Social (`JUNIORS` y `SENIORS`), grupos y subcomisiones. Ciclo de vida completo en 6 estados (`CREADO`, `NOTIFICADO`, `EN_CURSO`, `ABIERTO`, `FINALIZADO`, `ANULADO`) con anulación automática o manual con aviso formal de disculpas a convocados, y acción de fijar hora fin para eventos abiertos. Conmutación a la planilla nominal de asistencia con botón de retorno. 49 pruebas unitarias de eventos y 677 de backend en verde, y compilación en producción de Angular en verde (0 errores).
- [x] **TS3-06.26 Conciliación Full-Stack, Idempotencia de Cierre y Protección RBAC (PR #56):** Unificación del contrato de estados de asistencia (`AUSENTE`/`AUSENTE_INJUSTIFICADO`, `TARDE_LEVE`/`TARDANZA_LEVE`, `TARDE_GRAVE`/`TARDANZA_GRAVE`, `JUSTIFICADO`) y respuestas (`expedientes_generados`, `apercibimientos_generados`), resolución filtrada por cohorte/estado social en `AttendanceProcessingService`, idempotencia ante reintentos de cierre disciplinario, previsualización de `puntos_sancion` personalizados en `ResumenCierreDialogComponent`, protección RBAC en rutas y sidebar para ocultar el módulo a socios ordinarios, y sincronización documental en `spec.md`, `plan.md` y `UAT_SCRUM_50_REUNIONES_Y_SANCIONES.md`.

---

## 9. Sprint 3 — Desglose Atómico: S3-04 / SCRUM-48 (Adjuntar y Custodiar Evidencia Protegida)

> **Historia de Usuario:** S3-04 / SCRUM-48: Adjuntar y custodiar evidencia protegida.  
> **Criterios de Aceptación:** CA1 (Límites y formatos: PDF/JPG/PNG <= 5MB; T02 1-3 docs, T03 0-5 docs), CA2 (Validación real magic bytes, hash SHA-256, extensión y sanitización), CA3 (Custodia en BD BLOB MySQL y RBAC por objeto IsImputadoOrTribunal), CA4 (Auditoría inmutable de descargas con nosniff), CA5 (Advertencia estatutaria Art. 102 en Frontend y notificaciones globales 10s), CA6 (Preservación histórica en base de datos es_vigente=False), CA7 (Suites de pruebas en verde).

- [x] **TS3-04.1 Dominio y Validación Binaria (Magic Bytes, Hash, Sanitización) [TDD]:** Implementar `backend/expedientes/domain/evidence_validator.py` con validación de magic bytes (PDF, JPEG, PNG), límite de 5 MB, sanitización de nombre contra path traversal, cálculo SHA-256 y control de cupos (T02 máx 3, T03 máx 5).
- [x] **TS3-04.2 Modelos ORM, Persistencia BLOB y Auditoría de Descargas [TDD]:** Implementar `EvidenciaDescargo` y `AuditoriaDescargaEvidencia` en `backend/expedientes/models.py`. Generar migración Django.
- [x] **TS3-04.3 Servicio de Aplicación y Serializadores:** Implementar `EvidenceService` en `backend/expedientes/services/evidence_service.py` y serializadores `EvidenciaMetadataSerializer` en `backend/expedientes/serializers.py`. Adaptar `PresentarDescargoSerializer`.
- [x] **TS3-04.4 Endpoints REST de Carga y Descarga Segura Auditada [TDD]:** Implementar `EvidenciaUploadView` y `EvidenciaDownloadView` en `backend/expedientes/views.py`, registrar rutas en `backend/expedientes/urls.py`, aplicar permiso por objeto `IsImputadoOrTribunal`, auditoría de descargas y headers `nosniff`.
- [x] **TS3-04.5 Servicio Frontend y DTOs (`ExpedienteApiService`) [TDD]:** Agregar métodos `subirEvidencias` y `descargarEvidencia` con DTOs en `frontend/src/app/services/expediente-api.service.ts`.
- [x] **TS3-04.6 Componente Frontend `MisExpedientes` (Adjuntos Múltiples, Art. 102 y Descarga Segura):** Integrar en `mis-expedientes.component.html` y `.ts`: selector múltiple con límites de 3 (T02) y 5 (T03), advertencia estatutaria visible Art. 102, previsualización/eliminación de adjuntos, visualización en modal de detalle de causa con descarga directa y notificaciones globales de 10s.
- [x] **TS3-04.7 Verificación Integral, Cobertura, Linters y Consistencia PO:** Ejecutar suite completa de backend (`pytest`) y frontend (`Karma`), linters (`ruff check/format`), verificar inmutabilidad de `notasPO.md` y consistencia con las directivas del PO.

### Observaciones del Revisor en PR — S3-04 / SCRUM-48

- [x] **TS3-04.8 Simplificación de Modal y Unificación de Justificativos:** Eliminar bloque "Modalidad de Justificación Asignada", modelar descargo extraordinario como opción "Otro" en combobox "Tipo de Justificación", renombrar a "Adjuntar documentos", unificar sección de carga y eliminar jerga técnica y referencias a "T0". 218 tests unitarios de frontend en Karma y 569 tests de backend en Pytest en verde (0 errores).

---

## 9.1 Sprint 3 — Desglose Atómico: S3-05 / SCRUM-49 (Presentar T03 Extraordinario con Fundamento Libre)

> **Historia de Usuario:** S3-05 / SCRUM-49: Presentar T03 extraordinario con fundamento libre.  
> **Criterios de Aceptación:** CA1 (distinción T02/T03 sin regresiones; el cambio de modalidad en plazo queda como versión), CA2 (cada alta/corrección genera una versión inmutable con sus evidencias; el retiro no destruye datos), CA3 (mismo plazo y controles de acceso), límite de 5.000 caracteres y historial real desde la API. CA4 (vinculación de fundamento/precedente por el TD) se movió a SCRUM-53 por decisión del PO.

- [x] **TS3-05.1 Límite de 5.000 Caracteres [TDD]:** Constante única `MAX_DESCARGO_TEXT_LENGTH` en `backend/expedientes/domain/descargo_rules.py`, usada por el serializer, y límite equivalente en el frontend.
- [x] **TS3-05.2 Modelo de Versiones y Migraciones [TDD]:** `DescargoVersion` inmutable, evidencias protegidas contra borrado en cascada, migración de esquema `0013` y backfill reversible `0014` con la versión 1 de los descargos existentes.
- [x] **TS3-05.3 Versionado, Retiro Lógico y Re-presentación [TDD]:** `PresentarDescargoView` versiona cada alta, corrección y cambio T02↔T03; el retiro pasa a ser lógico (`RETIRADO`, solo en estado `justificando` y dentro del plazo) y los lectores filtran por vigencia.
- [x] **TS3-05.4 Endpoint de Historial `GET /descargo/versiones/` [TDD]:** Historial ordenado por `numero` con permisos por rol (socio titular, TD, CD y ADMIN).
- [x] **TS3-05.5 Frontend: Historial desde la API y Panel de Detalle Sincronizado:** `obtenerVersionesDescargo` alimenta el «Registro de Operaciones y Auditoría» en `mis-expedientes`, el botón pasa a «Retirar Descargo» y el panel abierto se actualiza con la lista del backend.
- [x] **TS3-05.6 Verificación Integral y Consistencia PO:** 633 tests de backend en Pytest y 238 de frontend en Karma en verde; `ruff check` y `ruff format --check` limpios; `notasPO.md` sin modificaciones.
- [x] **TS3-05.7 Prueba Manual en Navegador:** Recorrido completo (presentar, corregir, retirar, re-presentar y ver historial) en `localhost:4200`, validado por el equipo.

---

## 10. Sprint 3 — Investigación I+D: SCRUM-76 (Investigación y Especificación de IA — Laya System 1, Datos, Hardware y SLMs)

> **Tarea de I+D:** SCRUM-76: Investigar Laya (System 1), requerimientos de fine-tuning/datos/hardware y evaluación de SLMs (<4B) con RAG, CAG y MAG.  
> **Referencia Rector:** [`docs/gestion-proyecto/notasPO.md`](docs/gestion-proyecto/notasPO.md) (Sección 2, Líneas 144–148).  
> **Entregables:** Documentos técnicos modulares en [`docs/Implementacion IA/`](docs/Implementacion%20IA/).

- [x] **TS-76.1 Escenarios y Casos de Uso (Laya System 1):** Documentación técnica de primitivas `score` (urgencia procesal), `choice` (sugerencias reglamentarias no vinculantes) y `noul` (consistencia en descargos y flagrancia) junto con la arquitectura desacoplada en contenedor sidecar (`laya-service` en Docker Compose).  
      *Hecho cuando:* `docs/Implementacion IA/01_escenarios_y_casos_de_uso.md` generado y alineado a directivas del PO.
- [x] **TS-76.2 Metodología de Entrenamiento, Datos y Hardware:** Esquema del dataset en JSONL con soft targets, pipeline de Teacher Distillation a partir de resoluciones históricas del TD, algoritmo RLCD con ECE $\le 0.10$ y perfiles cuantitativos agnósticos de hardware (GPU local 8–16 GB VRAM para fine-tuning vs. CPU pura <1.5 GB RAM para inferencia en oficina).  
      *Hecho cuando:* `docs/Implementacion IA/02_entrenamiento_datos_y_hardware.md` redactado con comandos reproducibles CLI y ONNX.
- [x] **TS-76.3 Evaluación de SLMs (<4B), RAG, CAG y MAG:** Comparativa multidimensional de SLMs (Qwen 2.5, Llama 3.2, Phi-3.5-mini), matriz Laya vs. SLMs, casos de uso viables (borrador de considerandos, síntesis de expedientes, asistente estatutario) y análisis en profundidad de RAG, CAG (context caching de reglamentos) y las 3 vertientes de MAG (Memory, Multi-Agent y Model-Augmented híbrido System 1 + System 2).  
      *Hecho cuando:* `docs/Implementacion IA/03_evaluacion_slm_rag_cag_mag.md` consolidado con dictamen y hoja de ruta.
- [x] **TS-76.4 Memos Ejecutivos de Propuesta y Persuasión Institucional:** Redacción de 3 propuestas de valor estructuradas bajo PNL y redacción humanizada para la toma de decisión: Cómputos (Ing. en Sistemas/Electrónica — arquitectura sidecar, ONNX INT8, CPU pura, observabilidad), Tribunal de Disciplina (Ing. Industrial — optimización de procesos, reducción de lead time, soberanía judicial humana estricta) y Comisión Directiva (multidisciplinar — gobernanza, paz social, salvaguarda patrimonial temprana, costo operativo $0).  
      *Hecho cuando:* `docs/Implementacion IA/presentacion/` completo con los 3 memos y sección de objeciones.

---

## 11. Sprint 4 — Desglose Atómico: S4-02 (Resolver Causal T02 con Fundamento Trazable)

> **Spec de Referencia:** [`specs/006-resolver-causal-t02/spec.md`](specs/006-resolver-causal-t02/spec.md)  
> **Plan Técnico:** [`specs/006-resolver-causal-t02/plan.md`](specs/006-resolver-causal-t02/plan.md)  
> **Tareas:** [`specs/006-resolver-causal-t02/tasks.md`](specs/006-resolver-causal-t02/tasks.md)

- [x] **TS4-02.1 Dominio de decisión por causal [TDD]:** Regla sugerida y fundamento obligatorio al rechazar o apartarse de la regla.
- [x] **TS4-02.2 Modelo inmutable y migración [TDD]:** `DecisionCausalDescargo` versionado por descargo, sin modificación ni eliminación.
- [x] **TS4-02.3 Servicio de aplicación [TDD]:** Etapa procesal, T02, evidencia vigente, versión y copia del descargo valorado.
- [x] **TS4-02.4 Endpoints REST y permisos [TDD]:** `GET`/`POST /api/v1/expedientes/{id}/descargos/{descargo_id}/decisiones/` (registro exclusivo TD).
- [x] **TS4-02.5 Servicio frontend y DTOs [TDD]:** Métodos de detalle, historial y registro en `ExpedienteApiService`.
- [x] **TS4-02.6 Panel "Causales T02" en el detalle del TD:** Aceptar/Rechazar, fundamento, comprobantes valorados e historial.
- [x] **TS4-02.7 Verificación integral y consistencia PO:** Suites `pytest` y `Karma`, `ruff` y control contra `notasPO.md`.
- [x] **TS4-02.8 Revisión PR — Rendimiento y consistencia [TDD]:** Sin N+1 en el listado de gestión y criterio único de comprobantes vigentes entre la regla sugerida y el detalle.
- [x] **TS4-02.9 Revisión PR — Pruebas de aislamiento [TDD]:** Descargo de otro expediente (404), comprobante de otro imputado (400), T03 (400), historial para ADMIN (200) y anónimo (401).
- [x] **TS4-02.10 Revisión PR — Evaluación en dos pasos en el detalle:** Tabla de Involucrados con "Evaluar justificación", panel con "Ver comprobante", Aprobar/Desaprobar, fundamento accesible e historial consultable tras la emisión.
- [x] **TS4-02.11 Revisión PR — Datos de prueba:** Escenarios EXP-0901/2026 a EXP-0904/2026 en `seed_production_data`.

---

## 12. Sprint 3 — Desglose Atómico: SCRUM-84 (Apertura y Cierre Sprint en Documentación)

> **Tarea Metodológica:** SCRUM-84: Apertura y Cierre de Sprint 3 en Documentación (Definición de Producto y Seguimiento de Proyecto).  
> **Responsable:** Lucas Martín Guillén (Scrum Master).  
> **Criterios de Aceptación:** CA1 (Formalización de S3 Apertura y Cierre en `docs/gestion-proyecto/DEFINICION_DE_PRODUCTO_S3_APERTURA_Y_CIERRE.md`), CA2 (Actualización de Sección 2.6 en `docs/gestion-proyecto/Seguimiento de Proyecto.md` con métricas reales, DoD e incremento demostrado), CA3 (Retrospectiva del Sprint 3 con técnica Barco de Vela y plan de acción para Sprint 4), CA4 (Formato listo para copiar y pegar en los documentos de Google Drive compartidos con Cátedra).

- [x] **TS3-84.1 Documentación S3 Apertura en Definición de Producto:** Formalización de objetivos, requerimientos funcionales (`RF-08`, `RF-09`, `RF-10`, `RF-14`, `RF-16`, `RF-17`, `RF-18`), criterios EARS/Gherkin y casos de uso impactados (`CU-05`, `CU-06`, `CU-13`, `CU-14`).
- [x] **TS3-84.2 Documentación S3 Cierre en Definición de Producto:** Formalización de directivas del PO del 07/10/2026 (simplificación de votación en Sala TD, firmas con grupo Gxx y suplencias, formato canónico VISTO-CONSIDERANDO-RESUELVE, cambio terminológico a Revisores de Cuentas, regla 3:1 de apercibimientos inmutable), matriz de trazabilidad y Release Plan a Sprint 4.
- [x] **TS3-84.3 Documentación S3 Apertura en Seguimiento de Proyecto:** Planificación y Sprint Backlog con 36 Story Points y 14 ítems en `docs/gestion-proyecto/Seguimiento de Proyecto.md` (Sección 2.6.1).
- [x] **TS3-84.4 Documentación S3 Cierre en Seguimiento de Proyecto:** Resultado final del sprint con desglose de 36 SP finalizados (14/14 ítems mergeados en `main`), 0% Carry-over, DoD 100% verificado, incremento tangible y enlaces a PRs en `docs/gestion-proyecto/Seguimiento de Proyecto.md` (Sección 2.6.2).
- [x] **TS3-84.5 Retrospectiva y Mejora Continua de Sprint 3:** Sailboat Retrospective con vientos, anclas, rocas y plan de acción concreto (A1: integración continua y control UTF-8; A2: foco en visor unificado y editor de resoluciones sin votación nominal) en `docs/gestion-proyecto/Seguimiento de Proyecto.md` (Sección 2.6.3).
- [x] **TS3-84.6 Entrega de Bloques para Google Drive:** Archivo `docs/gestion-proyecto/DEFINICION_DE_PRODUCTO_S3_APERTURA_Y_CIERRE.md` generado en Markdown limpio para volcado inmediato en Google Drive ("ctrl+C, ctrl+V").
- [x] **TS3-84.7 Apertura de Sprint 4 en Seguimiento de Proyecto:** Documentación de la planificación y Sprint Backlog activo de Sprint 4 (`SCRUM-51`, `SCRUM-53`, `SCRUM-54`, `SCRUM-56` y `SCRUM-70` — 19 SP) sincronizada con Jira en `docs/gestion-proyecto/Seguimiento de Proyecto.md` (Sección 2.7.1).

---

## 13. Sprint 4 — Desglose Atómico: PB-02 (Tramitar Apelación y Adecuación del T01)

> **Spec de Referencia:** [`specs/008-apelacion-adecuacion-t01/spec.md`](specs/008-apelacion-adecuacion-t01/spec.md)  
> **Plan Técnico:** [`specs/008-apelacion-adecuacion-t01/plan.md`](specs/008-apelacion-adecuacion-t01/plan.md)  
> **Tareas:** [`specs/008-apelacion-adecuacion-t01/tasks.md`](specs/008-apelacion-adecuacion-t01/tasks.md)

- [x] **TPB-02.1 Dominio de apelación y adecuación [TDD]:** Plazo de 1 a 30 días hábiles, texto de apelación, cambios de puntos e involucrados, agravamiento y socios afectados.
- [x] **TPB-02.2 Modelos inmutables y migración [TDD]:** `ParametroPlazoApelacion`, `PeriodoApelacion`, `ApelacionT01` y `AdecuacionT01` sólo-inserción (migración `0017`).
- [x] **TPB-02.3 Plazo parametrizado y períodos por socio [TDD]:** Apertura con el parámetro vigente al entrar a `justificando` y vencimiento según el último período abierto.
- [x] **TPB-02.4 Servicio de apelación y adecuación [TDD]:** Apelación versionada con constancia por mail, rechazo de T02/T03 en T01, adecuación con mail de motivos y nuevo período aprobado por el TD.
- [x] **TPB-02.5 Endpoints REST y permisos [TDD]:** Parámetro del plazo, apelación, adecuación e historial del T01.
- [x] **TPB-02.6 Servicio frontend y DTOs [TDD]:** Métodos en `ExpedienteApiService`.
- [x] **TPB-02.7 Apelación en "Mis Expedientes":** "Apelar"/"Editar apelación" en lugar del justificativo T02/T03, plazo propio y adecuaciones comunicadas.
- [x] **TPB-02.8 Debate y adecuación en el detalle del TD:** Apelaciones por socio, formulario con autocompletado de socios, nuevo plazo opcional e historial.
- [x] **TPB-02.9 Parámetro del plazo en "Calendario Institucional":** Consulta para TD, CD y Administración; edición para TD y Administración.
- [x] **TPB-02.10 Verificación integral y consistencia PO:** Suites `pytest` y `Karma`, `ruff`, build y control contra `notasPO.md`.

---

## 14. Instrucciones para la Actualización de este Archivo

1. Cuando inicies una tarea del Sprint activo, mantenla visible como tu objetivo único.
2. Al finalizar la tarea y validar que todos sus tests estén en verde, edita este archivo y marca el casillero correspondiente: `- [x] Tn. ...`.
3. Sincroniza simultáneamente el archivo `specs/<spec>/tasks.md`.
4. Al culminar la totalidad de las tareas de una spec, actualiza la tabla del **Roadmap Macro** indicando el estado `Completado` y avanza a la siguiente fase.


