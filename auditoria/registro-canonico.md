# Registro Canónico — SGD-AVEIT

> **Fecha de relevamiento:** 27/11/2026  
> **Modo de elaboración:** Solo lectura sobre código, tests y fuentes documentales.  
> **Orden de autoridad aplicado:** `código y tests > auditoria/registro-canonico.md > resto de la documentación`.  
> **Fuentes auditadas:**
> - Repositorio local (rama `regularidadDocs`, HEAD `6a60167` del 23/11/2026): `backend/`, `frontend/`, `docs/`, `PLAN_SPRINT_5_CONSOLIDADO.md`.
> - `C:\Users\terza\Desktop\workshop\Seminario\Guias\Seminario-Guia de Documentación.pdf`.
> - `C:\Users\terza\Desktop\workshop\Seminario\Documentacion Extra Contexto\Notas de Profes-Reuniones.docx` y `REPORTES.docx`.
> - `C:\Users\terza\Desktop\workshop\Seminario\Documentación Actual Humana\`: `retroalimentaciónS0.txt`, `Nuevo documento de texto.txt` (retroalimentación Sprint 3), `retroalimentaciónS4.txt`, `Estudio_Inicial.docx`, `Plan_de_Proyecto.docx`, `Seguimiento_de_ProyectoVersionSprint0.pdf`, `Seguimiento_de_ProyectoVersionSprint2.pdf`, `Seguimiento_de_ProyectoVersionSprint4.pdf`, `Definicion_de_ProductoVersionSprint2.pdf`, `DEFINICION_DE_PRODUCTO_S4_APERTURA_Y_CIERRE.pdf`, `Manual_Usuario_SGD_AVEIT_Completo.pdf`.

---

## 1. Correcciones de los Profesores

### 1.1. Retroalimentación Sprint 0 (`retroalimentaciónS0.txt` y `Notas de Profes-Reuniones.docx`, 01-02/09/2026)

| # | Cita breve / Observación docente | Entregable afectado | Alcance (Solo documento / Documento y sistema) |
|---|---|---|---|
| 1 | *"Reformular los procesos afectados describiendo primero el proceso actual (AS-IS), sin SGD-AVEIT."* / *"Hablan de una solución demasiado definida dentro del propio Estudio."* | Estudio Inicial | Solo documento |
| 2 | *"Documentar técnicas y fuentes del relevamiento: entrevistados, roles, documentos y sistemas analizados."* | Estudio Inicial | Solo documento |
| 3 | *"Aclarar quién valida institucionalmente la utilización del procedimiento 2026, dado que el documento indica que 2018 sería el último formalmente aprobado."* | Estudio Inicial | Documento y sistema (regla normativa base del flujo) |
| 4 | *"Separar oportunidades/necesidades de las decisiones de solución tecnológica."* | Estudio Inicial | Solo documento |
| 5 | *"Revisar el nivel de detalle del ámbito físico, conservando solamente aquello relevante para el proyecto."* | Estudio Inicial | Solo documento |
| 6 | *"Completar formalmente el documento: carátula, nombre definitivo, equipo y habilidades."* | Plan de Proyecto | Solo documento |
| 7 | *"Agregar trazabilidad entre reglas del sistema y normativa de AVEIT: formularios, plazos, puntajes, alertas y balances."* | Plan de Proyecto | Documento y sistema |
| 8 | *"Reemplazar expresiones ambiguas como 'cómputo algorítmico' por reglas de negocio más precisas."* | Plan de Proyecto | Solo documento |
| 9 | *"Aclarar qué significa 'firma digital' y no comprometer una solución con validez legal si no es necesaria."* | Plan de Proyecto | Documento y sistema (alcance de firma electrónica interna) |
| 10 | *"Desglosar los requerimientos funcionales globales en funcionalidades detalladas."* | Plan de Proyecto | Solo documento |
| 11 | *"Definir actores, roles y permisos del sistema."* | Plan de Proyecto | Documento y sistema (matriz RBAC) |
| 12 | *"Separar requerimientos no funcionales de restricciones tecnológicas. Ejemplo: Python es restricción."* | Plan de Proyecto | Solo documento |
| 13 | *"Reformular la regla de 'no UPDATE directos' como requisito de integridad, inmutabilidad y trazabilidad del saldo."* | Plan de Proyecto | Documento y sistema |
| 14 | *"Completar cómo aplicarán Scrumban concretamente en el proyecto."* | Plan de Proyecto | Solo documento |
| 15 | *"Explicitar la integración con el sistema existente y restricciones de la BD (repos, uso de BD para consulta, usuarios)."* | Plan de Proyecto | Documento y sistema |
| 16 | *"Revisar Story Points y corregir diferencias entre documentos 111/116."* | Seguimiento de Proyecto / Plan de Proyecto | Solo documento |
| 17 | *"Cambiar 'velocidad proyectada' por carga promedio planificada, hasta que tengan velocidad real."* | Seguimiento de Proyecto | Solo documento |
| 18 | *"Redefinir el Story Map con al menos un corte horizontal de MVP."* / *"Reorganizar las entregas para dar valor antes... no todo Must al final."* | Seguimiento de Proyecto / Plan de Proyecto | Documento y gestión de entregas |
| 19 | *"Convertir el calendario Sprint 1–6 en roadmap inicial adaptable, explícitamente sujeto a velocidad y feedback."* | Seguimiento de Proyecto | Solo documento |

### 1.2. Retroalimentación de Reuniones Intermedias (`Notas de Profes-Reuniones.docx`, 15/09 a 18/11/2026)

| # | Cita breve / Observación docente | Entregable afectado | Alcance |
|---|---|---|---|
| 20 | *"No se llama 'MVP por sprint', sería un release... Apuntar a que el 2do Sprint sea el MVP."* / *"Actualizar el documento de seguimiento con el tema de release."* (15/09/2026) | Seguimiento de Proyecto | Solo documento / gestión |
| 21 | *"La documentación debe ser manejada como el código mismo."* (06/10/2026) | Todos los entregables | Proceso / Documentación |
| 22 | *"Para la presentación de regularidad el sistema debe estar al día con la documentación... Manual de usuario y toda la documentación presentable."* (21/10 y 28/10/2026) | Todos los entregables + Manual de Usuario | Documento y sistema |
| 23 | *"Evaluar si la eliminación de la votación nominal corresponde reflejarla en Plan de Proyecto, Estudio Inicial y Definición de Producto."* (28/10/2026) | Estudio Inicial, Plan de Proyecto, Definición del Producto | Solo documento |

### 1.3. Retroalimentación Sprint 3 (`Nuevo documento de texto.txt`)

| # | Cita breve / Observación docente | Entregable afectado | Alcance |
|---|---|---|---|
| 24 | *"Hay una contradicción funcional importante sobre la votación... No alcanza con incorporarlo en un anexo: debe actualizarse la definición general del producto, las historias afectadas, los casos de uso y los modelos correspondientes."* | Definición del Producto (y consistencia con Plan / Estudio Inicial) | Solo documento (el código ya eliminó la votación nominal) |
| 25 | *"La matriz denominada bidireccional vincula principalmente normativa, requerimientos y casos de uso. Debería permitir identificar también la historia implementada, la prueba correspondiente y su resultado."* | Definición del Producto | Solo documento |
| 26 | *"Hay una inconsistencia en el calendario: Seguimiento presenta inicio del Sprint 3 el 07/10 en el calendario maestro, pero la sección específica y Definición del Producto indican 08/10. También diferencias en inicio del Sprint 4."* | Seguimiento de Proyecto y Definición del Producto | Solo documento |
| 27 | *"La evidencia de pruebas necesita mayor precisión... Frente a la declaración de cumplimiento del 100%, agregar evidencia actualizada de ejecución satisfactoria, especialmente para permisos, vencimientos y transacciones."* | Definición del Producto | Documento y verificación técnica |

### 1.4. Retroalimentación Sprint 4 (`retroalimentaciónS4.txt`)

| # | Cita breve / Observación docente | Entregable afectado | Alcance |
|---|---|---|---|
| 28 | *"Poner foco en consistencia entre el estado declarado del desarrollo, la integración real, la aceptación institucional y la planificación del cierre."* | Seguimiento de Proyecto y Definición del Producto | Documento y proceso |
| 29 | *"¿Cuáles de las historias del Sprint 4 estaban efectivamente integradas en main y aceptadas al 3 de noviembre?"* *(Verificación git: al 03/11 estaban en `main` SCRUM-70 PR#64 [25/10], SCRUM-51 PR#65 [26/10], SCRUM-54 PR#63 [02/11] y ABM Reglamentos PR#69 [03/11]; NO estaban aún en `main` SCRUM-56 PR#67 [05/11] ni SCRUM-53 PR#71 [12/11].)* | Seguimiento de Proyecto y Definición del Producto | Solo documento (corrección de estado declarado) |
| 30 | *"¿Cómo justifican la viabilidad de completar los 36 SP pendientes del Sprint 5 consolidado, incluyendo pruebas y homologación?"* | Seguimiento de Proyecto | Solo documento / planificación |
| 31 | *"¿Qué documentos y modelos generales fueron actualizados para reflejar definitivamente la eliminación de la votación nominal?"* | Estudio Inicial, Plan de Proyecto, Definición del Producto | Solo documento |
| 32 | *"¿Cómo garantizan que un miembro del Tribunal involucrado en un expediente no pueda intervenir en su resolución? (Funcional-Seguridad)"* | Definición del Producto y Sistema | Documento y sistema (`IsNotInvolvedInExpediente` en `backend/expedientes/permissions.py` y `TribunalCompositionService`) |
| 33 | *"¿Cómo se registra y acredita una decisión colegiada sin votación nominal individual?"* | Definición del Producto y Sistema | Documento y sistema (`Resolucion.firmantes` por los 3 años sociales activos 4.º, 5.º y 6.º) |
| 34 | *"¿Qué sucede si una apelación modifica los imputados o los puntos de una solicitud que ya tenía descargos presentados?"* | Definición del Producto y Sistema | Documento y sistema (`T01AppealService` / `AdecuacionT01`) |
| 35 | *"¿Pueden demostrar el recorrido completo de un expediente y su impacto final en el historial de puntajes?"* | Sistema y demostración | Sistema (flujo E2E T01 → Descargo → Valoración/Decisión → Resolución → Firmas → Libro Mayor) |

---

## 2. Estado Funcional Verificado contra el Código

> **Cobertura de archivos de test relevados en el repositorio:** 114 archivos `test_*.py` en `backend/tests/` y 55 archivos `*.spec.ts` en `frontend/src/app/`.  
> **Criterio estricto:** Solo se marca `implementada` cuando existe evidencia directa en código (backend + frontend donde aplica) y tests.

| Funcionalidad | Estado | Evidencia en Código / Tests |
|---|---|---|
| Autenticación JWT (`/api/v1/auth/login/`, `refresh/`, `me/`) por N.º de Socio y elegibilidad | **implementada** | `backend/accounts/views.py`, `backend/accounts/serializers.py`, `frontend/src/app/login/login.component.ts`, `services/auth.service.ts`; tests: `backend/tests/test_auth.py`, `test_login_socios_eligibility.py`, `login.component.spec.ts`, `auth.service.spec.ts`. |
| RBAC y equivalencia de permisos legados (`tribunal_bajo/medio/alto`) | **parcial** | `backend/accounts/permissions.py`, `accounts/legacy_rbac.py`, `expedientes/permissions.py`, `frontend/src/app/services/tribunal.guard.ts`; tests: `backend/tests/test_rbac.py`, `test_opening_permissions.py`. **Brecha:** 6 vistas en `backend/expedientes/views/reportes_views.py` (`ReportesT01View`, `ReportesReunionesView`, `ReportesSubcomisionesListView`, `ReportesSubcomisionView`, `ReportesHistoricoRecordsView`, `ExpedienteClasificacionPatchView`) solo exigen `IsAuthenticated` sin permiso de rol específico. |
| Healthchecks de aplicación y padrón | **implementada** | `backend/core/views.py` (`/api/health/`), `backend/padron/views.py` (`/api/v1/padron/health/`); tests: `backend/tests/test_health.py`, `tests/padron/test_health.py`. |
| Capa anticorrupción Padrón Institucional (Read-Only sobre tablas legadas MySQL) | **implementada** | `backend/padron/models.py` (`ReadOnlyModel`, `Socio`, `Subcomision`, etc.), `padron/adapters.py`, `padron/views.py`, `frontend/src/app/services/padron-api.service.ts`; tests: `backend/tests/padron/test_adapters.py`, `test_adapters_db.py`, `test_api.py`, `test_domain.py`. |
| Buscador de socios, N.º de socio y Legajo Integral | **implementada** | `backend/socios/views.py` (`PadronListView`, `SocioLegajoDetailView`), `frontend/src/app/ranking-socios/socio-legajo-dialog/`, `expedientes-socio-dialog/`; tests: `backend/tests/test_socios.py`, `test_search_legajo.py`, `socio-legajo-dialog.component.spec.ts`. |
| Ranking Oficial de Socios reconciliado y paginado | **implementada** | `backend/ranking/models.py` (`PuntajeGeneral`, `PuntajeAplicado`), `ranking/services.py`, `ranking/views.py`, `frontend/src/app/ranking-socios/ranking-socios.component.ts`; tests: `backend/tests/test_ranking_api.py`, `test_ranking_services.py`, `tests/ranking/test_ranking_pagination.py`, `ranking-socios.component.spec.ts`. |
| Solicitudes T01 (borradores, emisión, multi-socio, Anexo, competencias, número canónico, Mis Solicitudes) | **implementada** | `backend/expedientes/models.py` (`SolicitudT01`, `ExpedienteNumberSequence`), `domain/opening_policy.py`, `views/__init__.py`, `frontend/src/app/solicitar-puntos/`; tests: `backend/tests/expedientes/test_opening_api.py`, `test_opening_policy.py`, `test_mis_solicitudes.py`, `test_canonical_number_migration.py`, `solicitar-puntos.component.spec.ts`. |
| Ciclo procesal de 6 estados, tablero de gestión, urgencia y concepto/clasificación | **implementada** | `backend/expedientes/models.py` (`Expediente`, `EstadoExpedienteEnum`, `CambioEstadoExpediente`), `services/workflow_service.py`, `services/board_service.py`, `frontend/src/app/gestionar-expedientes/gestionar-expedientes.component.ts`; tests: `test_expediente_workflow.py`, `test_board_api.py`, `test_urgencia.py`, `test_concepto_expediente.py`, `gestionar-expedientes.component.spec.ts`. *(Nota: persiste ruta stub `gestionar-expedientes/:id/descargo/:socioId` -> `EnDesarrolloComponent` en `admin-layout.routing.ts:29-38`.)* |
| Notificaciones transaccionales (Outbox de email, reintentos y toasts UI accesibles) | **implementada** | `backend/notifications/models.py` (`EmailOutbox`, `EmailAttachment`), `notifications/services.py`, `management/commands/process_email_queue.py`, `frontend/src/app/components/notification-center/`; tests: `backend/tests/notifications/test_api.py`, `test_services.py`, `test_management_command.py`, `notification-center.component.spec.ts`. *(Nota: no existe `backend/core/services/email_verification_service.py` ni suite universal de los 10 disparadores de `PLAN_SPRINT_5_CONSOLIDADO.md`.)* |
| Calendario Institucional y cálculo de plazos en días hábiles (5 días) | **implementada** | `backend/expedientes/models.py` (`Holiday`, `CalendarioVersion`, `FeriadoExcepcion`), `domain/calendar.py`, `services/deadline_service.py`, `management/commands/close_expired_deadlines.py`, `frontend/src/app/calendario-institucional/`; tests: `test_business_calendar.py`, `test_calendar_api.py`, `test_deadline_enforcement.py`, `calendario-institucional.component.spec.ts`. |
| Descargos T02/T03, versionado inmutable, retiro lógico y evidencia protegida con auditoría | **implementada** | `backend/expedientes/models.py` (`DescargoExpediente`, `DescargoVersion`, `EvidenciaDescargo`, `AuditoriaDescargaEvidencia`), `services/descargo_version_service.py`, `services/evidence_service.py`, `frontend/src/app/mis-expedientes/mis-expedientes.component.ts`; tests: `test_api_descargo.py`, `test_descargo_retiro.py`, `test_descargo_versions_api.py`, `test_evidence_api.py`, `mis-expedientes.component.spec.ts`. |
| Visor Autorizado Unificado de Expediente y auditoría de consultas (`SCRUM-51`) | **implementada** | `backend/expedientes/views/visor_views.py`, `serializers/visor_serializers.py`, `AuditoriaConsultaExpediente`, `frontend/src/app/gestionar-expedientes/visor-expediente/`; tests: `test_visor_expediente.py`, `test_case_detail_api.py`, `visor-expediente.component.spec.ts`. |
| Resolución de causal T02 y persistencia de puntaje final ratificado (`SCRUM-52` / `SCRUM-101`) | **implementada** | `backend/expedientes/models.py` (`DecisionCausalDescargo`, `DescargoExpediente.puntaje_ratificado`), `services/causal_resolution_service.py`, `frontend/src/app/gestionar-expedientes/gestionar-expedientes.component.ts`; tests: `test_causal_resolution_api.py`, `test_causal_resolution_service.py`, `test_decision_causal_api.py`. |
| Valoración extraordinaria T03 con sana crítica y vinculación de precedentes (`SCRUM-53`) | **implementada** | `backend/expedientes/models.py` (`ValoracionT03`, `ValoracionT03Antecedente`), `services/t03_valuation_service.py`, `frontend/src/app/gestionar-expedientes/valoracion-t03-panel/`; tests: `test_t03_valuation_api.py`, `test_t03_antecedent_api.py`, `valoracion-t03-panel.component.spec.ts`. |
| Composición del Tribunal, apartamiento por conflicto y régimen de suplencias (`SCRUM-54`) | **implementada** | `backend/expedientes/models.py` (`ComposicionTribunal`, `IntegranteComposicion`), `services/tribunal_composition_service.py`, `permissions.py` (`IsNotInvolvedInExpediente`), `frontend/src/app/gestionar-expedientes/`; tests: `test_tribunal_composition_api.py`, `test_tribunal_composition_domain.py`, `test_e2e_adhoc_flow.py`. |
| Apelación y adecuación del Formulario T01 con plazo parametrizable (`SCRUM-70`) | **implementada** | `backend/expedientes/models.py` (`ParametroPlazoApelacion`, `AdecuacionT01`, `PeriodoApelacion`, `ApelacionT01`), `services/t01_appeal_service.py`, `frontend/src/app/mis-expedientes/`, `gestionar-expedientes/`, `calendario-institucional/`; tests: `test_t01_appeal_api.py`, `test_t01_appeal_periods.py`, `test_t01_appeal_service.py`. |
| Editor unificado de Resolución, preview PDF, firma colegiada (4.º/5.º/6.º) y emisión oficial (`SCRUM-56`, `SCRUM-58`, `SCRUM-89`) | **implementada** | `backend/expedientes/models.py` (`Resolucion`), `resolution_views.py`, `services/resolution_service.py`, `services/resolution_pdf.py`, `frontend/src/app/gestionar-expedientes/gestionar-expedientes.component.ts`; tests: `test_resolution_api.py`, `test_resolution_preview_api.py`, `test_resolution_service.py`. |
| Exclusión fundada de involucrados por el TD (`SCRUM-102`) | **implementada** | `backend/expedientes/services/exclusion_service.py`, `views/exclusion_views.py`, `frontend/src/app/gestionar-expedientes/gestionar-expedientes.component.ts`; tests: `test_exclusion_api.py`, `test_exclusion_involucrado.py`. |
| Enmienda trazable de resoluciones emitidas con contra-asientos (`SCRUM-103`) | **implementada** | `backend/expedientes/models.py` (`EnmiendaResolucion`), `services/enmienda_service.py`, `resolution_views.py` (`EnmiendaResolucionView`), `frontend/src/app/gestionar-expedientes/`; tests: `test_enmienda_resolucion.py`. |
| Libro Mayor Transaccional Inmutable y regla 3:1 (`SCRUM-57` / `SCRUM-59` / `SCRUM-104`) | **implementada** | `backend/expedientes/models.py` (`AsientoLibroMayor` InsertOnly, `AtencionFelicitacion`), `ranking/models.py` (`PuntajeAplicado.registrar_movimiento`), `services/ledger_service.py`, `services/warning_accumulation_service.py`; tests: `test_ledger_domain.py`, `test_ledger_models.py`, `test_ledger_service.py`, `test_apercibimientos_consolidation.py`. |
| Portal "Mis Expedientes", saldo propio y publicación oficial protegida con censura médica (`SCRUM-60` / `SCRUM-105` / `SCRUM-106`) | **implementada** | `backend/expedientes/publication_views.py`, `services/publication_service.py`, `domain/medical_redaction.py`, `frontend/src/app/mis-expedientes/mis-expedientes.component.ts`; tests: `test_mis_expedientes_publicacion_api.py`, `test_medical_redaction.py`, `mis-expedientes.component.spec.ts`. |
| Eventos, Reuniones, Asistencia (Strategy) y rediseño UI (`SCRUM-50` / `SCRUM-86`) | **implementada** | `backend/expedientes/views/evento_views.py`, `urls_eventos.py`, `services/attendance_processing_service.py`, `attendance_strategy.py`, `frontend/src/app/pages/eventos/asistencia-evento/`; tests: `test_evento_api.py`, `test_evento_services.py`, `test_qa_e2e_eventos_sanciones.py`, `pages/eventos/**/*.spec.ts`. |
| ABM de Reglamentos con auditoría inmutable | **implementada** | `backend/expedientes/models.py` (`ArticuloReglamento`, `AuditoriaArticuloReglamento`), `views/reglamento_views.py`, `frontend/src/app/reglamentos/`; tests: `test_reglamentos_api.py`, `reglamentos.component.spec.ts`. |
| Panel de Administración: parámetros del sistema y gestión de miembros TD (`SCRUM-91` / `MACRO-03`) | **implementada** | `backend/core/models.py` (`SystemParameterChange`, `TribunalRoleChange`), `core/api/views.py`, `core/api/urls.py`, `frontend/src/app/pages/admin/parametros/`; tests: `test_parametros_admin.py`, `test_parametros_consumo.py`, `test_usuarios_td_admin.py`, `admin-parametros.component.spec.ts`. |
| Optimización de rendimiento (paginación, `OnPush`, `trackBy`, consultas ORM) (`SCRUM-87` / `MACRO-06`) | **implementada** | `backend/core/pagination.py`, `frontend/src/app/utils/track-by.util.ts`; tests: `test_pagination.py`, `test_expediente_pagination.py`, `test_evento_pagination.py`, `test_ranking_pagination.py`, `test_orm_performance.py`, `track-by.util.spec.ts`, `lifecycle-memory.spec.ts`. |
| Manual de Usuario modular (9 capítulos HTML + PDFs) (`SCRUM-129`) | **implementada** | `docs/manual-usuario/src/01_*.html`..`09_*.html`, `docs/manual-usuario/pdfs/Manual_Usuario_SGD_AVEIT_Completo.pdf`. |
| Reportes analíticos y Balance Cuatrimestral Art. 137 (`SCRUM-63` / `SCRUM-124`) | **parcial** | `backend/expedientes/views/reportes_views.py`, `services/reportes_service.py`, `frontend/src/app/reportes/reportes.component.ts`; tests: `test_reportes_api.py`, `reportes.component.spec.ts`. **Falta:** exportación a **PDF** del Balance Cuatrimestral Art. 137 (solo existe JSON y CSV) y permisos de rol en 6 vistas de `reportes_views.py`. |
| Alertas automáticas por umbrales críticos `-10` y preventivos `-7` (`SCRUM-62` / `US-17`) | **parcial** | `backend/ranking/domain/threshold_alerts.py` (`ThresholdAlertEngine`), `backend/ranking/services.py` (`evaluate_socio_threshold_crossing`); tests: `backend/tests/test_threshold_alerts.py`. **Falta:** conectar el motor al flujo productivo (`LedgerService` / `emitir_resolucion`) y exponer endpoint/vista de alertas. |
| Alertas automáticas por acumulación de apercibimientos 3:1 (`SCRUM-61`) | **parcial** | `backend/expedientes/services/warning_accumulation_service.py` (consolida 3:1 y abre expediente automático); tests: `test_apercibimientos_consolidation.py`. **Falta:** disparo de aviso/alerta formal a autoridades ante inminencia de descuento `-1 pt` (ej. al llegar a 2 llamados). |
| Repositorio de precedentes y jurisprudencia disciplinaria (`SCRUM-68` / `SCRUM-125` / `US-19`) | **parcial** | Solo existe búsqueda de antecedentes dentro de valoraciones T03 (`AntecedenteT03View` en `/api/v1/expedientes/antecedentes/`, `test_t03_antecedent_api.py`). **Falta:** módulo/vista dedicada de repositorio libre con filtros por artículos/rango temporal y exportación documental. |
| Reconciliación bidireccional y reporte de divergencias `PuntajeAplicado` vs `PuntajeGeneral` (`SCRUM-64`) | **no implementada** | Sin management command, endpoint ni pantalla de reporte de divergencias entre `PuntajeAplicado` y `PuntajeGeneral` (solo existe cálculo en vivo en `ranking/services.py` y comandos de reconciliación de identificadores/números). |
| Hardening de seguridad (revisión completa RBAC) y pruebas de carga (50 usuarios simultáneos, p95) (`SCRUM-65`) | **no implementada** | No existen scripts ni reportes de pruebas de carga/estrés (`locust`, `k6`, `jmeter`) en el repositorio; persisten 6 endpoints de reportes sin permiso de rol específico. |
| Casos Internos y promoción a T01 (`PB-01` / `SCRUM-128`) | **no implementada** | Sin modelos, views, servicios, componentes ni tests en el repositorio. |
| Votación nominal individual paso a paso | **no implementada (descartada por PO)** | Eliminada por directiva PO del 07/10/2026; reemplazada por editor unificado de resolución y firma colegiada en `Resolucion.firmantes`. |
| Despliegue en Staging con datos reales legados (`SCRUM-66`) y Homologación institucional AVEIT (`SCRUM-67`) | **No verificable** | No existe evidencia en el repositorio de entorno Staging activo, acta de homologación firmada ni transferencia operativa formal. |

---

## 3. Terminología y Nombres Canónicos

| Concepto | Valor usado en el CÓDIGO (Fuente práctica) | Variantes encontradas en Documentación |
|---|---|---|
| **Acrónimo del sistema** | `SGD-AVEIT` | `SDG-AVEIT` (error de tipeo en carátula de `Estudio_Inicial.docx` y `Plan_de_Proyecto.docx`) y `SGD-AVEIT` (resto de docs). |
| **N.º de Grupo** | No aplica en código | `Grupo 13` en `Estudio_Inicial.docx` y `Plan_de_Proyecto.docx` vs `Grupo Nº 04` en `DEFINICION_DE_PRODUCTO_S4_APERTURA_Y_CIERRE.pdf`. |
| **Roles RBAC** | `SOCIO`, `FISCALIZADORA` (*"Autoridad de Subcomisión / Líder de Equipo"*), `CD`, `TD`, `ADMIN` (`backend/socios/models.py:26-33`, `frontend/src/app/services/auth.service.ts:8`). *(Por decisión del 27/11/2026, `FISCALIZADORA` se mantiene como rol vigente actual y su partición en `AUTORIDAD_SC` + `REVISORES` queda trasladada al Sprint 6.)* | `Plan_de_Proyecto.docx`: `SOCIO ORDINARIO`, `AUTORIDAD SUBCOMISIÓN`, `COMISIÓN DIRECTIVA (CD)`, `MIEMBRO TRIBUNAL (TD)`, `ADMIN CÓMPUTOS`. `Manual_Usuario`: `SOCIO`, `REVISORES`, `CD`, `TD`, `ADMIN`. `Seguimiento §2.5.2`: afirma renombre de `Fiscalizadora` a `Revisores de Cuentas` en todo el código (no reflejado en el enum del código). `SCRUM-121`/`122` (Jira): proponen split `AUTORIDAD_SC` + `REVISORES`. |
| **Categorías de Socio** | `PASSIVE` (años sociales 1, 2, 3) y `ACTIVE` (años sociales 4, 5, 6) en `backend/socios/models.py:21-23` y `backend/padron/domain.py:17-27`. | `Estudio_Inicial.docx`: `Socios Juniors` (1.º y 2.º año) y `Socios Seniors` (3.º a 6.º año); `Socio Activo (u Ordinario)` vs `Socio Pasivo`. |
| **6 Estados del Expediente** | **Backend (`EstadoExpedienteEnum`, `backend/expedientes/models.py:28-36`):**<br>1. `creado` (*"Expediente Creado"*)<br>2. `justificando` (*"En período de justificaciones"*)<br>3. `revision_resolucion` (*"Justificaciones en revisión"*)<br>4. `espera_resolucion` (*"En espera de resolución"*)<br>5. `pendiente_correos` (*"Pendiente de firma y envío"*)<br>6. `emitido` (*"Expedientes ya emitidos"*)<br>**Frontend (`tribunal-data.service.ts:12-19`):** agrega `'pendiente_firma'` como alias visual junto a `'pendiente_correos'`. | `Definicion_de_ProductoVersionSprint2.pdf`: `CREADO -> JUSTIFICANDO -> SUSTANCIANDO -> RESOLVIENDO -> EMITIDO -> CERRADO`.<br>`DEFINICION_DE_PRODUCTO_S4_APERTURA_Y_CIERRE.pdf`: `EN_REVISION`, `PARA_RESOLVER`.<br>`Estudio_Inicial.docx`: nombres largos reglamentarios del Art. 12 RP 2026. |
| **Formularios** | `SolicitudT01` (`T01`), `TipoDescargoEnum.T02_CERTIFICADO` (*"Descargo con Causal / Certificado"*), `TipoDescargoEnum.T03_EXTRAORDINARIO` (*"Descargo - Otros"*). | `Estudio_Inicial.docx`: `Formulario T01 / Anexo T01`, `Formulario T02 (Justificación)`, `Formulario T03 (Descargo)`. |
| **Decisión colegiada del TD** | **Firma colegiada** de 3 integrantes habilitados representando años sociales 4.º, 5.º y 6.º en `Resolucion.firmantes` (`backend/expedientes/services/resolution_service.py`). No existe modelo de votación nominal. | `Definicion_de_ProductoVersionSprint2.pdf` y `Estudio_Inicial.docx`: mencionan *"Votación nominal colegiada"* / *"Votación del Tribunal"*. `DEFINICION_DE_PRODUCTO_S4`: *"Editor unificado sin votación nominal"*. |
| **Valoración T03 (resultados)** | `ResultadoValoracionT03Enum`: `ACCEPTED` (*"Aprobada"*), `REJECTED` (*"Desaprobada"*). | `DEFINICION_DE_PRODUCTO_S4_APERTURA_Y_CIERRE.pdf` (CA-RF12.1): `ADMITIDO_TOTAL`, `ADMITIDO_PARCIAL`, `DESESTIMADO`. |
| **Modelo de Libro Mayor** | `AsientoLibroMayor` (`expedientes_asiento_libro_mayor`, InsertOnly) + `PuntajeAplicado` (`tribunal_puntajeaplicado` legado). | `PLAN_SPRINT_5_CONSOLIDADO.md`: `TransaccionPuntos` en `ranking/models.py`. |
| **Stack Tecnológico Frontend** | Angular 14.2+ + TypeScript + Angular Material (`frontend/src/app/`). | `Seguimiento de Proyecto` (`§2.1.5`): *"HTML5 semántico, CSS3 modular (`tokens.css`) y Vanilla JavaScript (`view-cd.js`, `view-td.js`, `view-socio.js`)"*. `Plan_de_Proyecto.docx`: menciona Tailwind CSS. |
| **Identificador de Socio** | `numero_socio` (y `legajo` en padrón legado `socio_lista`). | `Seguimiento S0` y `Plan de Proyecto`: *"Legajo"*. `Seguimiento S4` y `Manual_Usuario`: *"Número de Socio"*. |
| **Story Points Sprint 5 Consolidado** | No aplica en código | Discrepancias entre `Seguimiento_de_ProyectoVersionSprint4.pdf` y `DEFINICION_DE_PRODUCTO_S4_APERTURA_Y_CIERRE.pdf`: `SCRUM-59` (5 vs 3 SP), `SCRUM-61` (2 vs 3 SP), `SCRUM-64` (3 vs 5 SP), `SCRUM-66` (5 vs 3 SP), `SCRUM-67` (5 vs 3 SP). |
| **Módulos del Menú (Frontend)** | `/mis-expedientes` (*Mis Expedientes*), `/reglamentos` (*Reglamentos*), `/solicitar-puntos` (*Crear Expediente*), `/ranking-socios` (*Ranking de Socios*), `/gestionar-expedientes` (*Gestionar Expedientes*), `/calendario-institucional` (*Calendario Institucional*), `/reportes` (*Reportes & Balance*), `/eventos-asistencia` (*Eventos & Asistencia*), `/admin/parametros` (*Administración*). | Nombres variados en specs y documentos históricos. |

---

## 4. Lineamientos por Entregable (Cátedra Seminario Integrador — UTN FRC)

> **Fuente:** `C:\Users\terza\Desktop\workshop\Seminario\Guias\Seminario-Guia de Documentación.pdf` (4 páginas).  
> **Requisitos comunes de formato:** *"Todos los documentos deben tener el mismo formato de presentación y contar con: Carátula - Tabla De Contenido o Índice - Historial De Cambios o Tabla De Revisión. En caso de ser necesario agregar GLOSARIO DE TÉRMINOS o DICCIONARIO DE DATOS."*  
> **Extensión (páginas/palabras) y tipografía/márgenes:** **No especificado en la guía** (ver sección 6).

| Entregable | Propósito según Guía | Secciones Obligatorias | Formato y Extensión |
|---|---|---|---|
| **1. Estudio Inicial** | Describe el estado actual del dominio y sus necesidades (AS-IS). | Carátula · Tabla de Contenido (Índice) · Introducción (general del proyecto) · Propósito del documento · Descripción del Ámbito o Contexto de Aplicación (Presentación de la Organización, Objetivo, Reseña Histórica, Dimensionamiento, Políticas, Mapa Global de Procesos, Descripción de Procesos de Negocio afectados, Recursos Informáticos Existentes, Lay-Out de la Organización; o alternativa Ámbito de Aplicación/Nicho) · Antecedentes de Productos Similares / Análisis de Competencia (para Producto) · Problemas y Oportunidades · Historial de Cambios (Historia de Revisión) · *(Opcional: Glosario de Términos)*. | Mismo formato de presentación que el resto de entregables. Extensión: no especificada en la guía. |
| **2. Plan de Proyecto** | Describe la propuesta de solución. | Carátula · Tabla de Contenido (Índice) · Propósito del documento · Nombre del producto de software · Objetivo del producto · Alcances del producto / Requerimientos funcionales · Requerimientos no funcionales (consideraciones de arquitectura, implementación, diseño y restricciones normativas/reglamentarias) · Metodología adoptada (nombre) · Equipo de trabajo · Historial de Cambios (Historia de Revisión). | Mismo formato de presentación. Extensión: no especificada en la guía. |
| **3. Seguimiento del Proyecto** | Describe acuerdos de trabajo y el progreso del proyecto. | Carátula · Historia de Revisión · Tabla de Contenido (Índice) · Propósito del documento · Gestión por Iteración o por Sprint (Ágiles - Scrum):<br>— **Sprint 0:** Working Agreement (Definición de Sprints: duración, eventos — cuáles, duración, cómo, con qué; Capacidad del equipo en hs por miembro; Definición de Roles; Herramientas de Gestión; Tecnologías para el Desarrollo considerando uso y tratamiento de IA), Product Backlog completo inicial, Story Map.<br>— **Sprint 1 al n:** Planificación del Sprint (fecha de inicio, Scrum Master si rotativo, Product Backlog actualizado y priorizado, Sprint Backlog), Resultado Final del Sprint, Resultado de la Retrospectiva (del proyecto). | Mismo formato de presentación. Extensión: no especificada en la guía. |
| **4. Definición del Producto / Solución** *(Ágiles)* | Describe especificaciones técnicas del software. | Carátula · Historia de Revisión · Tabla de Contenido (Índice) · Propósito del documento · Nombre del producto de software · Objetivo del producto · Product Backlog · Roles del Sistema · Epics y USs asociadas · Para cada US: Descripción de US + UAT (criterio de aceptación de usuario), Diseño de Interfaz, Diseño de Casos de Prueba, Resultados de las Pruebas · Diagrama de Clases · DER (indicar PK y FK; para cada atributo definir longitud, tipo de dato y valores posibles) · Diagramas de Transición de Estados (indicar por método n.º y nombre de US responsable del cambio, estado inicial y estado/s final/es) · Definición de la Arquitectura del Software (Ambiente de Implementación, Diagrama de Despliegue indicando US por nodo, Lay-Out de Equipamiento). | Mismo formato de presentación. Extensión: no especificada en la guía. |
| *(Anexo Guía)* **Manual de Usuario** | Guía operativa del sistema (doc., ayuda en línea o video). | Carátula · Historia de Revisión · Tabla de Contenido · Propósito del documento · Configuración · Módulos · Descripción de Funciones (ventanas, botones, etc., ordenado por subsistemas). | Documento, ayuda en línea o video. Extensión: no especificada en la guía. |

---

## 5. Fechas y Versiones Ya Presentadas (Inmutable)

> **Regla:** Las fechas y versiones históricas ya presentadas ante la cátedra **no se modifican nunca**.

### 5.1. Estudio Inicial (`Documentación Actual Humana\Estudio_Inicial.docx`)
- **Fecha en carátula:** `xx/xx/2026` *(placeholder sin completar en el archivo presentado)*.
- **Historial de revisiones existente:**
  - `v1.0.0` — **15/08/2026** — Equipo de Proyecto SGD-AVEIT — Elaboración inicial completa según Guía de Documentación UTN FRC.
  - `v1.1.0` — **15/08/2026** — Equipo de Proyecto SGD-AVEIT — Ajuste de subcomisiones (7), estructura CD (7 miembros), BD MySQL, sanción omisión tareas (-2 pts), reuniones virtuales TD y arquitectura Web Responsive Mobile.
  - `v1.2.0` — **15/08/2026** — Equipo de Proyecto SGD-AVEIT — Análisis comparativo Reglamento Procesal 2018 vs 2026, 6 estados, formularios T01/T02/T03, competencias y firma colegiada.
  - `v1.3.0` — **16/08/2026** — Equipo de Proyecto SGD-AVEIT — Armonización con Estatuto Social 2026 (Juniors 1.º–2.º y Seniors 3.º–6.º).
  - `v1.4.0` — **18/08/2026** — Equipo de Proyecto SGD-AVEIT — Explicitación de fuentes documentales en citas de artículos.
  - `v1.5.0` — **18/08/2026** — Equipo de Proyecto SGD-AVEIT — Formalización del marco metodológico Scrumban.

### 5.2. Plan de Proyecto (`Documentación Actual Humana\Plan_de_Proyecto.docx`)
- **Fecha en carátula:** `DD/MM/AAAA` *(placeholder sin completar; título interno de carátula dice "Análisis del Sistema")*.
- **Historial de revisiones existente:**
  - `v1.0.0` — **01/09/2026** — Equipo de Proyecto SGD-AVEIT — Elaboración inicial del Plan de Proyecto según Guía UTN FRC.
  - `v1.0.1` — **02/09/2026** — *(sin autor)* — Estructuración de formato y presentación según Guía UTN FRC.
  - `v2.0.0` — **03/09/2026** — Equipo de Proyecto SGD-AVEIT — Reestructuración integral ante observaciones de cátedra (carátula, matriz habilidades, taxonomía SI, RF-01 a RF-15, RN-01 a RN-10, separación RNF ISO 25010 vs restricciones, firma electrónica interna, inmutabilidad saldo, Scrumban operativo, CU-01 a CU-12).

### 5.3. Seguimiento de Proyecto (`Seguimiento_de_ProyectoVersionSprint0.pdf`, `...Sprint2.pdf`, `...Sprint4.pdf`)
- **Historial de revisiones acumulado (consolidado en versión Sprint 4):**
  - `v1.0.0` — **01/09/2026** — Equipo de Proyecto SGD-AVEIT — Creación inicial, bosquejo de acuerdos de trabajo, estimación horaria inicial y roles preliminares.
  - `v1.1.0` — **02/09/2026** — Equipo de Proyecto SGD-AVEIT — Formalización integral del Sprint 0 (calendario 14 días, ceremonias, DoD/DoR, capacidad 77 hs/sem, herramientas, tecnologías y gobernanza IA, Product Backlog US-01 a US-19, Story Map, plantillas). *(Presentado en `Seguimiento_de_ProyectoVersionSprint0.pdf`.)*
  - `v1.2.0` — **07/10/2026** — Equipo de Proyecto SGD-AVEIT — Ejecución, métricas, incremento y retrospectiva de Sprint 1 y Sprint 2 + hito PO del 27/09/2026 (`notasPO.md`). *(Presentado en `Seguimiento_de_ProyectoVersionSprint2.pdf`.)*
  - `v1.3.0` — **22/10/2026** — Equipo de Proyecto SGD-AVEIT — Alineación técnica con Cómputos y TD (07/10/2026), cierre Sprint 3 (36/36 SP) y apertura Sprint 4 (19 SP). *(Versión presente en `docs/gestion-proyecto/Seguimiento de Proyecto.md` del repo.)*
  - `v1.4.0` — **04/11/2026** — Equipo de Proyecto SGD-AVEIT — Cierre formal Sprint 4 (19/19 SP declarados) y apertura formal Sprint 5 Consolidado (Fusión Sprint 5 y Sprint 6: 44 SP totales / 8 SP adelantados + 36 SP netos). *(Presentado en `Seguimiento_de_ProyectoVersionSprint4.pdf`.)*

### 5.4. Definición del Producto / Solución
- **`Definicion_de_ProductoVersionSprint2.pdf`:**
  - `v1.0.0` — **08/10/2026** — Equipo Interdisciplinario SGD-AVEIT — Elaboración formal integral del Documento de Definición de Producto (marco conceptual, Product Backlog, 33 US, modelo de dominio, DER, máquina de estados, arquitectura y casos de uso).
- **`DEFINICION_DE_PRODUCTO_S4_APERTURA_Y_CIERRE.pdf`:**
  - Sin tabla formal de historial de revisiones; identifica iteración **Sprint 4 (21/10/2026 al 03/11/2026)**, cierre administrativo Sprint 3 el **22/10/2026**, Hito IOC el **04/11/2026** y transición a Sprint 5 Consolidado desde **04/11/2026**.

### 5.5. Manual de Usuario (`Documentación Actual Humana\Manual_Usuario_SGD_AVEIT_Completo.pdf`)
- **32 páginas** (9 módulos visuales). No incluye carátula formal con fecha ni tabla de historial de revisiones; generado desde `docs/manual-usuario/` (commit `6a60167` del **23/11/2026**).

---

## 6. No Verificable

| Ítem | Motivo |
|---|---|
| **Resultado en ejecución viva de las suites `pytest` y `npm test`** | Este relevamiento se realizó en **MODO SOLO LECTURA**; se verificó la existencia y cobertura estática de los 114 archivos de test backend y 55 specs frontend, pero no se ejecutaron suites contra MySQL/ChromeHeadless. |
| **Estado actual de tickets en Jira** | No se consultó la instancia remota de Jira en esta auditoría; se contrastó únicamente contra los documentos presentados y el código/git del repositorio. |
| **Aceptación formal / actas de homologación institucional de AVEIT (CD, TD, Cómputos)** | No constan actas firmadas ni registros de UAT formal de cierre en el repositorio ni en `C:\Users\terza\Desktop\workshop\Seminario`. |
| **Despliegue real en entorno Staging / Producción con réplica MySQL legada (`SCRUM-66`)** | No existe evidencia verificable en el repositorio de infraestructura Staging desplegada ni logs de verificación sobre base productiva de AVEIT. |
| **Fechas exactas de entrega formal de `Estudio_Inicial.docx` y `Plan_de_Proyecto.docx`** | Sus carátulas conservan placeholders (`xx/xx/2026` y `DD/MM/AAAA`); solo constan las fechas internas de sus tablas de historial de revisiones (`18/08/2026` y `03/09/2026`). |
| **Límites de extensión (páginas/palabras) y reglas tipográficas por entregable** | `Seminario-Guia de Documentación.pdf` no especifica límites de extensión ni formato tipográfico detallado, solo exige uniformidad de presentación y secciones obligatorias. |
| **Fecha exacta de recepción de `retroalimentaciónS0.txt`, `Nuevo documento de texto.txt` (S3) y `retroalimentaciónS4.txt`** | Los archivos `.txt` contienen únicamente el texto de la devolución docente sin encabezado de fecha. |
