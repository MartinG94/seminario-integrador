# TASK.md — Hoja de Ruta y Tareas del Proyecto SGD-AVEIT

Documento maestro de seguimiento y gobernanza de tareas bajo la metodología **Spec-Driven Development (SDD)**. Articula el cronograma macro por Sprints con el desglose granular atómico de tareas verificables (`<30 minutos`).

---

## 1. Roadmap Macro de Sprints (Ciclo Lectivo 2026)

| Iteración | Fechas | Enfoque / Incremento Comprometido | User Stories | Estado |
| :---: | :---: | :--- | :---: | :---: |
| **Sprint 0** | 18/08 al 08/09 | **Fundacional:** Relevamiento, Anteproyecto, ERS, BPMN, Arquitectura, Acuerdos de Trabajo, Prototipado UX y Gobernanza SDD. | — | **En Cierre** |
| **Sprint 1** | 09/09 al 22/09 | **Walking Skeleton:** Autenticación JWT, Roles RBAC, Padrón institucional, Ranking oficial de puntos y Legajo de socio. | `US-01` a `US-04` | **Próximo a Iniciar (Spec 001)** |
| **Sprint 2** | 23/09 al 06/10 | **Expedientes y Apertura T01:** Formulario T01 digital con hoja de Anexo, validación de competencias (Arts. 21-26), notificaciones y Tablero de 6 Estados. | `US-05` a `US-08` | Planificado |
| **Sprint 3** | 07/10 al 20/10 | **Descargos y Plazos Preclusivos:** Formularios T02 y T03 con adjuntos probatorios (PDF/imágenes) y temporizador regresivo de 5 días hábiles. | `US-09` a `US-11` | Planificado |
| **Sprint 4** | 21/10 al 03/11 | **Sustanciación y Votación Colegiada:** Módulo 'Justificaciones' del TD, gestión de inhibiciones/suplencias, votación nominal remota y firma colegiada de Activos. | `US-12` a `US-14` | Planificado |
| **Sprint 5** | 04/11 al 17/11 | **Sumatoria Inmutable de Puntos y Alertas:** Actualización transaccional auditada (cero UPDATE), portal 'Mis Expedientes' y motor de alertas automáticas (7 pts y 10 pts). | `US-15` a `US-17` | Planificado |
| **Sprint 6** | 18/11 al 01/12 | **Auditoría, Balances y Cierre:** Generador de Balances Cuatrimestrales (Art. 137), repositorio de jurisprudencia, homologación institucional y entrega final. | `US-18` a `US-19` | Planificado |

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
> **Regla de Ejecución:** Una tarea a la vez, tests primero (TDD), ejecutar suite de verificación, marcar checkbox y detenerse.

- [x] **T1. Esqueleto Backend Django & Configuración:** Inicializar estructura del proyecto en `backend/` con `core/settings.py`, `pytest.ini` y dependencias en `requirements.txt`.  
      *(RF: —)* **Hecho cuando:** `pytest -q` corre en `backend/` sin errores de configuración (0 tests).

- [x] **T2. Conexión MySQL y Healthcheck en Docker:** Configurar conector MySQL y endpoint de estado `/api/health/`.  
      *(RF: —)* **Hecho cuando:** `docker compose up` levanta `db` y `backend`, y `curl http://localhost:8000/api/health/` devuelve `{"status": "ok", "db": "connected"}`.

- [x] **T3. Modelo de Socios y Subcomisiones:** Implementar modelos `Subcomision` y `Socio` con validación de año social y categorización automática Pasivo/Activo.
      *(RF: RF-06-WS)* **Hecho cuando:** Tests unitarios de creación de socios, unicidad de legajo y cálculo de categoría social en verde.

- [ ] **T4. Libro Mayor de Puntos (Transacciones Inmutables):** Crear modelo `TransaccionPuntos` y servicio `calculate_socio_balance(socio_id)`.  
      *(RF: RF-06-WS)* **Hecho cuando:** Tests con transacciones positivas (+2.0), negativas (-1.0) y sin transacciones (0.0) en verde.

- [x] **T5. Autenticación JWT y Roles RBAC:** Configurar SimpleJWT con claims personalizados (`legajo`, `role`, `category`) y permisos DRF (`IsTribunalOrDirectiva`).  
      *(RF: RF-01-WS, RF-02-WS, RF-05-WS)* **Hecho cuando:** Tests de login exitoso (retorna access/refresh), login con credenciales inválidas (401) y acceso prohibido para socios ordinarios a rutas de gestión (403) en verde.

- [ ] **T6. Endpoint de Ranking Oficial:** Implementar viewset `/api/v1/ranking/` con agregación de saldos, filtros por subcomisión, categoría y ordenamiento descendente.  
      *(RF: RF-03-WS, RF-06-WS)* **Hecho cuando:** Tests de endpoint retornando lista paginada de socios con saldos correctos y ordenamiento en verde.

- [x] **T7. Endpoint de Búsqueda y Detalle de Legajo:** Implementar búsqueda insensible a mayúsculas/tildes en `/api/v1/socios/` y detalle `/api/v1/socios/<id>/legajo/`.  
      *(RF: RF-04-WS)* **Hecho cuando:** Tests de búsqueda por nombre, apellido y legajo con tiempo de respuesta < 500 ms en verde.

- [x] **T8. Servicio Angular de Autenticación (`AuthService`):** Crear servicio en `frontend` con métodos `login()`, `logout()`, `getToken()` e interceptor HTTP para Bearer token.  
      *(RF: RF-01-WS)* **Hecho cuando:** Tests de `AuthService` en Jasmine pasan en verde.

- [ ] **T9. Integración de Componente `RankingSociosComponent`:** Conectar el componente existente en Angular con el endpoint `/api/v1/ranking/`, agregando controles de filtro y paginación con estilos AVEIT.  
      *(RF: RF-03-WS, RNF-02)* **Hecho cuando:** `ng test --include=**/ranking-socios.component.spec.ts` en verde y renderizado correcto en viewport móvil.

- [x] **T10. Modal de Legajo de Socio en Angular:** Implementar diálogo modal para consultar el legajo del socio seleccionado con su historial de puntos.  
      *(RF: RF-04-WS)* **Hecho cuando:** Al hacer clic en un socio del ranking se despliega el modal con sus datos y saldo auditado.

- [ ] **T11. Verificación End-to-End y Smoke Test:** Validación integral del Walking Skeleton mediante demo manual y checklist de criterios de aceptación de la Spec 001.  
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
> **Criterios vigentes tras la revisión del PR #49:** CA1 (Calendario único e impacto inmediato), CA2 (Auditoría por feriado), CA3 (Vencimientos persistidos inmutables), CA4 (Zona institucional), CA5 (Lectura autenticada y alta ADMIN/CD/TD), CA6 (UX/UI simplificada y alineada), CA7 (Fecha >= hoy y sin duplicados), CA8 (Actualización y reaplicación segura de migraciones).

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

---

## 8. Instrucciones para la Actualización de este Archivo

1. Cuando inicies una tarea del Sprint activo, mantenla visible como tu objetivo único.
2. Al finalizar la tarea y validar que todos sus tests estén en verde, edita este archivo y marca el casillero correspondiente: `- [x] Tn. ...`.
3. Sincroniza simultáneamente el archivo `specs/<spec>/tasks.md`.
4. Al culminar la totalidad de las tareas de una spec, actualiza la tabla del **Roadmap Macro** indicando el estado `Completado` y avanza a la siguiente fase.

