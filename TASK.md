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

## 7. Sprint 3 — Desglose Atómico: S3-07 / SCRUM-78 (Clasificador e Indicador Visual de Urgencia en Expedientes)

> **Historia de Usuario:** S3-07 / SCRUM-78: Implementar clasificador e indicador visual de urgencia en expedientes.  
> **Criterios de Aceptación:** CA1 (Tres niveles de urgencia: Baja, Normal, Urgente con default Normal), CA2 (Filtro por urgencia en API y Frontend), CA3 (Indicador visual distintivo en tarjetas Kanban y tabla), CA4 (Actualización de urgencia autorizada vía PATCH para TD/CD), CA5 (Inmutabilidad de notas del PO y estricto respeto a tokens de diseño).

- [x] **TS3-07.1 Modelo y Migración de Urgencia (Backend TDD):** Enumeración `UrgenciaExpedienteEnum` (`baja`, `normal`, `urgente`), campo `urgencia` con default `normal` e índice en `Expediente` y `SolicitudT01`. Migración Django `0007_expediente_urgencia.py`.
- [x] **TS3-07.2 Serialización y Filtro por Urgencia en API REST (Backend TDD):** Inclusión de `urgencia` y `urgencia_display` en `BoardExpedienteSerializer` y `ExpedienteListSerializer`. Filtro por urgencia en `ExpedienteFilter`.
- [x] **TS3-07.3 Endpoint PATCH de Actualización de Urgencia (Backend TDD):** `PATCH /api/v1/expedientes/<id>/` con `UpdateUrgenciaExpedienteSerializer` y permiso `IsTribunalOrDirectiva`.
- [x] **TS3-07.4 DTOs, Mapeo y Servicio en Frontend (Angular TDD):** Tipado `NivelUrgencia`, mapeo en `TribunalDataService` y método `actualizarUrgencia()`.
- [x] **TS3-07.5 Indicadores Visuales y Filtro en Tablero Kanban y Tabla (Frontend):** Filtro de urgencia en toolbar, badge semántico con icono, resaltado de borde rojo en tarjetas urgentes (`.kanban-card-urgente`), columna en tabla explorer y selector de urgencia en modal de detalle.
- [x] **TS3-07.6 Verificación Integral, Cobertura y Consistencia con PO:** 9 tests unitarios e integrales backend en verde, 13 tests frontend en Karma pasando en verde y compilación de producción exitosa.

---

## 8. Instrucciones para la Actualización de este Archivo

1. Cuando inicies una tarea del Sprint activo, mantenla visible como tu objetivo único.
2. Al finalizar la tarea y validar que todos sus tests estén en verde, edita este archivo y marca el casillero correspondiente: `- [x] Tn. ...`.
3. Sincroniza simultáneamente el archivo `specs/<spec>/tasks.md`.
4. Al culminar la totalidad de las tareas de una spec, actualiza la tabla del **Roadmap Macro** indicando el estado `Completado` y avanza a la siguiente fase.

