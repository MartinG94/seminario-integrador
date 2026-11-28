# Auditoría de Discrepancias — Definición del Producto / Solución (`SGD-AVEIT`)

> **Fecha de auditoría:** 27/11/2026  
> **Alcance del entregable:** Especificación técnica del producto — **SÍ incluye la ejecución del Sprint 5**, marcando lo incompleto o no verificable como `"trasladada al Sprint 6"` (`auditoria/entregables/_brief-comun.md`).  
> **Fuentes contrastadas:**
> - Entregables presentados: `C:\Users\terza\Desktop\workshop\Seminario\Documentación Actual Humana\Definicion_de_ProductoVersionSprint2.pdf` (`v1.0.0`, `08/10/2026`, 30 págs., inmutable) y `DEFINICION_DE_PRODUCTO_S4_APERTURA_Y_CIERRE.pdf` (6 págs., sin tabla de revisiones, cierre S4 `03/11`–`04/11/2026`, inmutable).
> - Fuente canónica y código/tests: `auditoria/registro-canonico.md`, `auditoria/traspaso-sprint6.md`, `auditoria/entregables/plan-de-proyecto-discrepancias.md`.
> - Documentos técnicos alineados en el repo: `docs/especificaciones/ERS-SGD-AVEIT.md` (`v1.1.0`), `docs/especificaciones/MODELO_DOMINIO_SGD_AVEIT.md` (`v1.1.0`), `docs/especificaciones/RBAC-SGD-AVEIT.md`.
> - Devoluciones docentes: `Nuevo documento de texto.txt` (Sprint 3) y `retroalimentaciónS4.txt` (Sprint 4).

---

## a) Qué afirma el documento que el sistema no hace o que no está verificado

1. **Votación nominal colegiada inexistente (descartada por el PO el 07/10/2026):**
   - **`Definicion_de_ProductoVersionSprint2.pdf` (S2):** la incluye en la portada (*"Sistema de Gestión Disciplinaria y Votación Colegiada"*), §6 Objetivo (*"votación nominal colegiada del Tribunal de Disciplina"*), §8 Rol `TD` (*"T01, votaciones"*), ficha de US `S4-05: Registrar voto nominal y mayoría absoluta` (pág. 19, CA3 *"puntos/medidas derivan de la votación cerrada"*) y §15.2 Caso de Uso *Votación del Tribunal* (pág. 30). En el sistema real no existe votación nominal; fue reemplazada por editor unificado de resolución + firma electrónica colegiada de 3 activos (`Resolucion.firmantes`).
   - *Residuo en el repo:* `docs/especificaciones/MODELO_DOMINIO_SGD_AVEIT.md` (`v1.1.0`) aún conserva los métodos `+tieneQuorumVotacion()` y `+calcularMayoriaVotacion()` en `ExpedienteDisciplinario` (líns. 197–198 y 528–529).
2. **Nombres de los 6 estados del expediente erróneos en S2 y S4:**
   - **S2 (§13, pág. 29 y §15.2, pág. 30):** afirma el flujo `CREADO -> JUSTIFICANDO -> SUSTANCIANDO -> RESOLVIENDO -> EMITIDO -> CERRADO`.
   - **S4 (CA-RF12.1, CA-RF15.1 y CU-02, págs. 2–3):** usa estados inexistentes `EN_REVISION` y `PARA_RESOLVER` (y `PENDIENTE_VALORACION` para T03).
   - **Código real (`EstadoExpedienteEnum`):** `creado` (*Expediente Creado*), `justificando` (*En período de justificaciones*), `revision_resolucion` (*Justificaciones en revisión*), `espera_resolucion` (*En espera de resolución*), `pendiente_correos` (*Pendiente de firma y envío*, alias UI `pendiente_firma`), `emitido` (*Expedientes ya emitidos*).
3. **Valores de resultado de Valoración T03 erróneos en S4:**
   - **S4 (CA-RF12.1, pág. 2):** afirma que los resultados son `ADMITIDO_TOTAL`, `ADMITIDO_PARCIAL`, `DESESTIMADO`.
   - **Código real (`ResultadoValoracionT03Enum`):** únicamente `ACCEPTED` (*Aprobada*) y `REJECTED` (*Desaprobada*).
4. **`SCRUM-62` y `SCRUM-63` declarados `"100% Completado"` en S4 (§2.2, pág. 4 y §2.5, págs. 5–6):**
   - **`SCRUM-62` (Alertas `-10` y `-7`, PR #72):** en el código es **parcial** (*trasladada al Sprint 6*): `ThresholdAlertEngine` no está conectado a `LedgerService`/`emitir_resolucion` ni tiene endpoint/vista.
   - **`SCRUM-63` (Reportes y Balance Art. 137, PR #70):** en el código es **parcial** (*trasladada al Sprint 6*): falta exportación en **PDF** (solo existe JSON y CSV) y 6 vistas de `reportes_views.py` solo exigen `IsAuthenticated` (brecha RBAC).
5. **Estado de integración en `main` al 03/11/2026 declarado como 100% completado en S4 (§2.2 y §2.5):**
   - S4 §2.2 marca `RF-12` (`SCRUM-53`, PR #71) y `RF-15` (`SCRUM-56`, PR #67) como `"100% Completado"` y §2.5 declara *"100% de los 19 Story Points del Sprint 4 completados y verificados"* al 04/11/2026, contradiciendo su propia tabla §2.3 (pág. 4), donde ambos PRs figuran `"en revisión"`. En git, al `03/11` solo estaban en `main` `SCRUM-70` (25/10), `SCRUM-51` (26/10), `SCRUM-54` (02/11) y ABM Reglamentos (03/11); `SCRUM-56` se integró el `05/11` y `SCRUM-53` el `12/11`.
6. **Declaraciones de pruebas al 100% sin verificación viva y nombres de archivos de test inexactos:**
   - **S2 (§4, pág. 3 y págs. 7–28):** admite verificación parcialmente estática y repite textualmente **33 veces** el mismo bloque genérico (*"206 pasan y 259 fallan por indisponibilidad de conexión MySQL"*), junto con **33 placeholders** `[INSERTAR CAPTURA DE INTERFAZ — ...]`.
   - **S4 (§2.4, pág. 5 y §2.2):** afirma *"más de 1000 pruebas automatizadas en backend (`pytest`) y más de 450 pruebas en frontend (`Karma/Jasmine`) con 0 errores"* (`1097 tests backend passed`), pero no adjunta evidencia de ejecución viva (en esta auditoría solo consta cobertura estática de `114` archivos `test_*.py` y `55` `*.spec.ts`). Además cita nombres de archivos inexistentes en el repo (`test_t03_valoracion_api.py`, `test_resolucion_preview_pdf.py`, `test_resolucion_api.py` en lugar de `test_t03_valuation_api.py`, `test_resolution_preview_api.py`, `test_resolution_api.py`).
7. **Arquitectura declarada como "Microservicios" en S2 (§14.1, pág. 30):**
   - Afirma *"arquitectura por capas basada en Microservicios orquestados mediante Docker"*. El sistema real es un **monolito modular Django 4.2 LTS + DRF**, SPA **Angular 14.2+** y **MySQL 8.0** en Docker Compose.
8. **Errores institucionales, de roles, categorías, fechas, Story Points y maquetación:**
   - **Grupo erróneo:** S4 portada indica `Grupo Nº 04` (el grupo oficial según `Carátula gral.docx` es `Grupo 13`; S2 omite N.º de grupo y docentes).
   - **Cátedra errónea:** S2 indica *"Seminario de Práctica Profesional / Proyecto Final"* (es *Seminario Integrador — Curso 3K2*).
   - **Rol `TRIBUNAL` en S4 (CA-RF11.1, pág. 2):** el rol real en código es `TD`.
   - **Categorías `Junior`/`Senior` en S2 (pág. 8, `S1-04` CA3) y residual en `MODELO_DOMINIO_SGD_AVEIT.md` (lín. 780):** en el código las categorías son `PASSIVE` (1.º–3.º año) y `ACTIVE` (4.º–6.º año).
   - **Inconsistencia de calendario:** S2 tiene fecha `08/10/2026` (inicio S3 `08/10` vs `07/10` en calendario maestro de Seguimiento); S4 fija inicio Sprint 4 el `21/10/2026` y apertura en Jira el `22/10/2026`.
   - **Story Points divergentes en S4 (§2.5, págs. 5–6 vs `Seguimiento S4`):** `SCRUM-59` (3 vs 5 SP), `SCRUM-61` (3 vs 2 SP), `SCRUM-64` (5 vs 3 SP), `SCRUM-66` (3 vs 5 SP), `SCRUM-67` (3 vs 5 SP).
   - **Diagrama sin renderizar en S4 (pág. 5):** el PDF imprime código Mermaid crudo (`flowchart LR ...`).

---

## b) Qué hace el sistema que el documento no dice

1. **Incremento completo del Sprint 5 Consolidado implementado en código (`04/11`–`23/11/2026`, PRs #74–#79 y `6a60167`), totalmente ausente en S2 y S4:**
   - **Libro Mayor Transaccional Inmutable y regla 3:1 (`SCRUM-57` / `SCRUM-59` / `SCRUM-104`, PR #79):** `AsientoLibroMayor` (`expedientes_asiento_libro_mayor`, InsertOnly), `PuntajeAplicado.registrar_movimiento`, `LedgerService`, `AtencionFelicitacion` y `WarningAccumulationService`.
   - **Firma electrónica colegiada de los 3 años activos (4.º, 5.º y 6.º) y emisión oficial (`SCRUM-58` / `SCRUM-89`, PR #77):** `Resolucion.firmantes`, bloqueo definitivo post-emisión y despacho Outbox (`EmailOutbox`, `EmailAttachment`).
   - **Exclusión fundada de involucrados por el TD (`SCRUM-102`, PR #77):** `exclusion_service.py`, `exclusion_views.py`.
   - **Enmienda trazable de resoluciones emitidas con contra-asientos `REVERSION` (`SCRUM-103`, PR #77):** `EnmiendaResolucion`, `enmienda_service.py`, `EnmiendaResolucionView`.
   - **Portal "Mis Expedientes", saldo propio y publicación oficial con censura automática de datos médicos (`SCRUM-60` / `SCRUM-105` / `SCRUM-106`, PR #79):** `publication_views.py`, `publication_service.py`, `medical_redaction.py`.
   - **Panel de Administración (`SCRUM-91` / `MACRO-03`, PR #78):** gestión auditada de parámetros del sistema y miembros TD (`/admin/parametros`, `SystemParameterChange`, `TribunalRoleChange`).
   - **Eventos, Reuniones, Asistencia digital (Strategy) y rediseño UI (`SCRUM-50` / `SCRUM-86` / `MACRO-04`):** `/eventos-asistencia`, `attendance_strategy.py`, `attendance_processing_service.py`.
   - **N.º de socio, ID canónico de expedientes y celdas atómicas (`SCRUM-93` / `MACRO-05`, PRs #74–#75):** `ExpedienteNumberSequence` y rediseño de Gestión.
   - **Optimización de rendimiento (`SCRUM-87` / `MACRO-06`, PR #76):** paginación backend (`core/pagination.py`), `OnPush`, `trackBy` (`track-by.util.ts`) y optimización ORM.
   - **Manual de Usuario modular (`SCRUM-129`, commit `6a60167`):** 9 capítulos HTML + PDF consolidado (32 págs.) en `docs/manual-usuario/`.
2. **Funcionalidades de Sprints 2–4 omitidas o sin especificación completa en S2/S4:**
   - **ABM de Reglamentos con auditoría inmutable** (`ArticuloReglamento`, `AuditoriaArticuloReglamento`, `/reglamentos`, PR #69): ausente en S2 y solo mencionado en 2 líneas en S4.
   - **Resolución causal T02 con `puntaje_ratificado`** (`SCRUM-52` / `SCRUM-101`, `DecisionCausalDescargo`), **versionado inmutable y retiro lógico de descargos** (`DescargoVersion`), **evidencia protegida en `BinaryField`** (`EvidenciaDescargo`), **Calendario Institucional** (`Holiday`, `CalendarioVersion`, `FeriadoExcepcion`, `/calendario-institucional`), **urgencia** (`SCRUM-78`), **Mis Solicitudes** (`SCRUM-75`) y **centro de notificaciones UI** (`NotificationCenter`, 10 s accesible).
3. **Brecha frente al Plan de Proyecto y ausencia de entregable consolidado en el repositorio:**
   - **Contrastando con `auditoria/entregables/plan-de-proyecto-discrepancias.md`:** el Plan (`RF-01..RF-15`) omitía 12 módulos/capacidades construidos (Ranking/Legajo, Calendario, Eventos 3:1, Apelación T01, Apartamiento/Suplencias, Visor/Auditoría, Exclusión/Enmienda, Censura médica, ABM Reglamentos, Panel Admin, Outbox, Capa Read-Only). Por su parte, la Definición del Producto presentada quedó fragmentada en dos PDFs desfasados (S2 y S4) que tampoco incorporan el Sprint 5 ni distinguen formalmente las 10 funcionalidades **trasladadas al Sprint 6** (`auditoria/traspaso-sprint6.md`).
   - **Estado en el repositorio:** no existe un documento consolidado de *Definición del Producto* en `docs/formales/`; solo existen `ERS-SGD-AVEIT.md`, `MODELO_DOMINIO_SGD_AVEIT.md` y `RBAC-SGD-AVEIT.md` (ya alineados al registro canónico el 27/11/2026 salvo los residuos menores señalados en la sección a), pero faltan el catálogo de US/UAT, diseño de interfaz, casos de prueba, DER físico completo, diagrama de transición de estados y arquitectura/despliegue.

---

## c) Correcciones de los profesores sin aplicar (cita breve)

Evaluación de cada observación aplicable de `auditoria/registro-canonico.md` (§1):

| # | Cita textual breve | Estado en S2 / S4 presentados | Estado en repo (`docs/especificaciones` + código) | Qué falta aplicar en el entregable formal |
|---|---|---|---|---|
| **21** | *"La documentación debe ser manejada como el código mismo."* | **Sin aplicar** | **Parcial** | No existe un entregable consolidado versionado de Definición del Producto en el repo sincronizado con el código de Sprint 5. |
| **22** | *"Para la presentación de regularidad el sistema debe estar al día con la documentación... Manual de usuario y toda la documentación presentable."* | **Sin aplicar** | **Parcial** | Manual de Usuario ya existe (`SCRUM-129`, sin carátula/historial formal), pero Definición del Producto sigue partida en S2 (desactualizado) y S4 (6 págs. con Mermaid crudo y sin Sprint 5). |
| **23** | *"Evaluar si la eliminación de la votación nominal corresponde reflejarla en Plan de Proyecto, Estudio Inicial y Definición de Producto."* | **Parcial** | **Parcial** | S4 eliminó votación nominal en el incremento, pero S2 (documento base) nunca se actualizó y `MODELO_DOMINIO_SGD_AVEIT.md` conserva `+tieneQuorumVotacion()` / `+calcularMayoriaVotacion()`. |
| **24** | *"Hay una contradicción funcional importante sobre la votación... No alcanza con incorporarlo en un anexo: debe actualizarse la definición general del producto, las historias afectadas, los casos de uso y los modelos correspondientes."* | **Sin aplicar** | **Parcial** | S4 funcionó justamente como adenda/anexo de 6 págs.; el cuerpo principal (S2: portada, objetivo, roles, `S4-05`, CU 15.2) y el diagrama de clases conceptual nunca se purgaron por completo. |
| **25** | *"La matriz denominada bidireccional vincula principalmente normativa, requerimientos y casos de uso. Debería permitir identificar también la historia implementada, la prueba correspondiente y su resultado."* | **Parcial** | **Sin aplicar** | S4 (§2.3) incorporó historia, suite y resultado **solo para 5 RF del Sprint 4** (con 2 PRs aún en revisión y nombres de archivos inexactos); falta la matriz completa para **todos los Sprints 1–5** con resultados verificados. |
| **26** | *"Hay una inconsistencia en el calendario: Seguimiento presenta inicio del Sprint 3 el 07/10 en el calendario maestro, pero la sección específica y Definición del Producto indican 08/10. También diferencias en inicio del Sprint 4."* | **Sin aplicar** | **Sin aplicar** | Persisten `08/10/2026` en S2 y `21/10/2026` vs `22/10/2026` para inicio de Sprint 4 en S4 sin unificación con Seguimiento. |
| **27** | *"La evidencia de pruebas necesita mayor precisión... Frente a la declaración de cumplimiento del 100%, agregar evidencia actualizada de ejecución satisfactoria, especialmente para permisos, vencimientos y transacciones."* | **Sin aplicar** | **Sin aplicar** | S2 declara 259 fallos por MySQL; S4 declara >1000 / >450 tests con 0 errores sin log ni evidencia reproducible; en auditoría actual no hay ejecución viva de `pytest`/`Karma`. |
| **28** | *"Poner foco en consistencia entre el estado declarado del desarrollo, la integración real, la aceptación institucional y la planificación del cierre."* | **Sin aplicar** | **Parcial** | S4 sobrestima el estado de `SCRUM-62`, `SCRUM-63`, `SCRUM-53` y `SCRUM-56` al 03/11; el entregable formal debe alinear estado declarado, código real y traslados al Sprint 6. |
| **29** | *"¿Cuáles de las historias del Sprint 4 estaban efectivamente integradas en main y aceptadas al 3 de noviembre?"* | **Sin aplicar** | **Aclarado en registro canónico** | Corregir en el entregable el estado real al 03/11: integradas `SCRUM-70`, `SCRUM-51`, `SCRUM-54` y ABM Reglamentos; integradas después `SCRUM-56` (`05/11`) y `SCRUM-53` (`12/11`); sin acta formal de aceptación institucional. |
| **31** | *"¿Qué documentos y modelos generales fueron actualizados para reflejar definitivamente la eliminación de la votación nominal?"* | **Sin aplicar** | **Parcial** | Falta consolidar la actualización definitiva en el documento maestro de Definición del Producto y retirar los 2 métodos residuales de `MODELO_DOMINIO_SGD_AVEIT.md`. |
| **32** | *"¿Cómo garantizan que un miembro del Tribunal involucrado en un expediente no pueda intervenir en su resolución? (Funcional-Seguridad)"* | **Parcial** | **Implementado en código** | S4 describe el requisito (`RF-13`), pero no documenta el mecanismo técnico concreto implementado (`IsNotInvolvedInExpediente` en `backend/expedientes/permissions.py` + `TribunalCompositionService` + bloqueo de transición/firma). |
| **33** | *"¿Cómo se registra y acredita una decisión colegiada sin votación nominal individual?"* | **Parcial** | **Implementado en código** | S4 solo llegaba hasta el borrador PDF (`SCRUM-56`); falta documentar la acreditación implementada en Sprint 5: registro de firma electrónica colegiada de los 3 representantes activos (4.º, 5.º y 6.º año) en `Resolucion.firmantes` (`SCRUM-58`). |
| **34** | *"¿Qué sucede si una apelación modifica los imputados o los puntos de una solicitud que ya tenía descargos presentados?"* | **Parcial** | **Implementado en código** | S4 (`RF-19`/`CA-RF19.1`) describe la adecuación a alto nivel, pero falta especificar en el entregable el comportamiento exacto de `T01AppealService` / `AdecuacionT01` sobre preservación de historial, imputados y reapertura de plazo de descargo. |

---

## d) Datos que la cátedra o la plantilla exigen y no existen en ninguna fuente

1. **Resultados de ejecución viva de las suites de pruebas (`pytest` y `Karma/Jasmine`)** con fecha, conteo real y evidencia en permisos, vencimientos y transacciones (obs. #27; hoy solo existe verificación estática de `114` `test_*.py` y `55` `*.spec.ts`): **`dato faltante`**.
2. **Evidencia UAT formal (aceptación de usuario) y capturas de interfaz actualizadas para todas las US de Sprints 1–5** (S2 contiene 33 placeholders `[INSERTAR CAPTURA...]`; S4 no incluye capturas ni UAT firmado; Sprint 5 carece de fichas US/UAT/capturas): **`dato faltante`**.
3. **Diseño de casos de prueba específicos por US y matriz de trazabilidad completa** (*Normativa → RF → US → Prueba → Resultado real*) para todo el alcance de Sprints 1–5 (S2 usa 33 plantillas genéricas idénticas; S4 solo cubre 5 RF): **`dato faltante`**.
4. **DER físico completo con PK, FK, tipo de dato, longitud y valores posibles** para las ~30 tablas actuales del sistema (S2 solo lista 8 tablas en texto plano sin longitudes/dominios completos; `MODELO_DOMINIO_SGD_AVEIT.md` es conceptual y omite entidades de Sprints 3–5): **`dato faltante`** *(derivable desde los modelos/migraciones Django al redactar el entregable, pero hoy ausente en toda documentación)*.
5. **Diagramas de Transición de Estados formales** indicando por método **n.º y nombre de US responsable**, estado inicial y estado(s) final(es) (S2 solo tiene un listado textual con nombres de estados erróneos y sin US por transición): **`dato faltante`**.
6. **Diagrama de Despliegue verificado (indicando US por nodo) y Lay-Out de Equipamiento** en entorno Staging / Producción real de AVEIT (`SCRUM-66` trasladado al Sprint 6; S2 §14.4 declara explícitamente topología física no definida): **`dato faltante`**.
7. **Datos formales de Carátula y control de versiones para la entrega consolidada** (Fecha real de entrega, N.º de Entrega definitivo e integración en Historial de Revisión de S2 `v1.0.0` y S4 sin versión formal): **`dato faltante`**.
8. **Límites de extensión (páginas/palabras) y reglas tipográficas** (no especificados en `Seminario-Guia de Documentación.pdf`): **`dato faltante`**.

---

## e) Cambios que dependen de una decisión del usuario (alcance, traslados, criterios)

1. **Consolidación en un único documento formal de Definición del Producto:** Confirmar la creación de un documento maestro consolidado en el repositorio (integrando Sprints 1–5 y absorbiendo `ERS-SGD-AVEIT.md`, `MODELO_DOMINIO_SGD_AVEIT.md` y `RBAC-SGD-AVEIT.md`) que preserve en su Historial de Revisión las entregas históricas inmutables (`v1.0.0` del `08/10/2026` — S2, y la entrega S4 del `04/11/2026`) y defina el número de la nueva versión (`v2.0.0` o `v1.1.0`).
2. **Documentación explícita de los 10 ítems trasladados al Sprint 6:** Confirmar que todas las funcionalidades de `auditoria/traspaso-sprint6.md` (`SCRUM-62`, `SCRUM-61`, `SCRUM-63`/`124` PDF y RBAC, `SCRUM-64`, `SCRUM-65`/`92`, partición `FISCALIZADORA` `SCRUM-121`/`122`, `SCRUM-68`/`125`, `PB-01`/`SCRUM-128`, `SCRUM-66` Staging y `SCRUM-67` Homologación) se consignen explícitamente como **"trasladada al Sprint 6"** en Backlog, RF, US y matriz de trazabilidad.
3. **Ejecución viva de pruebas (`pytest` / `Karma`) y capturas de pantalla reales:** Decidir si antes de cerrar el entregable se correrán las suites en entorno local (Docker/MySQL) y se capturarán las pantallas reales del sistema para reemplazar los 33 placeholders y responder a la obs. #27, o si el documento declarará únicamente la cobertura estática (`114` `test_*.py` / `55` `*.spec.ts`) marcando la ejecución viva como pendiente.
4. **Granularidad del catálogo de US (Sprints 1–5) y permanencia de Casos de Uso:** Decidir si cada historia de Sprints 1–5 (incluyendo `MACRO-01..06` y `SCRUM-129`) se detalla con ficha individual completa (Descripción + UAT + UI + Casos de Prueba + Resultado) o agrupada por Épica/Módulo, y si se conserva la sección de Casos de Uso (no exigida por la Guía para proyectos Ágiles, pero usada en la trazabilidad evaluada en obs. #24–#25).
5. **Extracción técnica de DER físico (~30 tablas), Diagrama de Clases y Máquina de Estados desde el código:** Confirmar si se autoriza generar el DER completo (PK, FK, tipos, longitudes, enums), el Diagrama de Clases real (eliminando los métodos residuales de votación en `MODELO_DOMINIO_SGD_AVEIT.md`) y el Diagrama de Transición de Estados con US por método directamente a partir de los modelos y servicios Django vigentes.
6. **Unificación de fechas de calendario y Story Points (obs. #26 y divergencias S4):** Definir (a) las fechas oficiales unificadas de inicio de Sprint 3 (`07/10` vs `08/10`) y Sprint 4 (`21/10` vs `22/10`) consistentes con Seguimiento, y (b) los Story Points definitivos para `SCRUM-59`, `SCRUM-61`, `SCRUM-64`, `SCRUM-66` y `SCRUM-67`.
7. **Alcance del Diagrama de Despliegue y Lay-Out de Equipamiento:** Decidir si se documenta únicamente la arquitectura verificada en Docker Compose local (declarando Staging/Producción AVEIT como trasladado al Sprint 6) o si el usuario aportará especificaciones de infraestructura física/cloud de AVEIT.
8. **Datos formales de Carátula:** Confirmar N.º de Entrega, Fecha real de entrega, unificación en `Grupo 13` (reemplazando `Grupo Nº 04` de S4), cátedra `Seminario Integrador — Curso 3K2` y nómina docente (`Ing. María Irene Mac William`, `Ing. Silvina Arenas`, tutor `Ing. Fernando Sanabria`).
