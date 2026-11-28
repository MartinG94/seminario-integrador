# Inventario de Auditoría — Grupo `docs-especificaciones`

> **Fecha de auditoría:** 27/11/2026  
> **Fuente canónica contrastada:** `auditoria/registro-canonico.md` (y verificación puntual de rutas/identificadores en código).  
> **Alcance:** 7 archivos exactos en `docs/especificaciones/`.  
> **Modo:** Solo lectura / relevamiento diagnóstico (sin propuestas de corrección).

---

## Resumen rápido

| # | Ruta | Líneas | Última modificación | Quién lo lee | Qué pasa si desaparece | Clasificación |
|---:|---|---:|:---:|---|---|---|
| 1 | `docs/especificaciones/ERS-SGD-AVEIT.md` | 134 | `2026-10-25` | Equipo / Cátedra | Alguien pregunta | 3. Redundante con `docs/especificaciones/ERS_Especificacion_Requerimientos_Tribunal.md` (ambos desactualizados) e incompleto |
| 2 | `docs/especificaciones/ERS_Especificacion_Requerimientos_Tribunal.md` | 155 | `2026-11-12` | Equipo / Nadie | Alguien pregunta | 3. Redundante con `docs/especificaciones/ERS-SGD-AVEIT.md` (ambos desactualizados) e incompleto |
| 3 | `docs/especificaciones/Escenarios_Calidad_ISO25010_Tribunal.md` | 128 | `2026-09-08` | Cátedra / Equipo | Nada | 3. Incompleto (promete cubrir escenarios y tácticas arquitectónicas reales y quedó desactualizado) |
| 4 | `docs/especificaciones/MODELO_DOMINIO_SGD_AVEIT.md` | 1276 | `2026-11-12` | Cátedra / Equipo | Alguien pregunta | 3. Incompleto (parcialmente actualizado, con contradicciones internas y respecto del registro) |
| 5 | `docs/especificaciones/PLANTILLA_CASO_DE_USO.md` | 108 | `2026-09-08` | Nadie | Nada | 1. Residuo de fabricación |
| 6 | `docs/especificaciones/RBAC-SGD-AVEIT.md` | 86 | `2026-09-19` | Equipo | Alguien se equivoca | 3. Incompleto (congelado en Spec 001; omite el resto de la API y permisos posteriores) |
| 7 | `docs/especificaciones/REDISENIO_EVENTOS_ASISTENCIAS.md` | 118 | `2026-10-15` | Equipo | Nada | 4. Vigente |

---

## 1. `docs/especificaciones/ERS-SGD-AVEIT.md`

- **Ruta:** `docs/especificaciones/ERS-SGD-AVEIT.md`
- **Líneas:** 134
- **Última modificación (`git log`):** `2026-10-25`
- **Tema que cubre:** Especificación de Requerimientos de Software (ERS/SRS) general de SGD-AVEIT con stakeholders, RF-01 a RF-19, RNF-01 a RNF-06, RN-01 a RN-11, supuestos/restricciones/dependencias y matriz de desambiguación.
- **Quién lo lee:** equipo / cátedra (citado en `README.md`, `TASK.md` y `docs/gestion-proyecto/Seguimiento de Proyecto.md`).
- **Qué pasa si desaparece:** alguien pregunta (es referido como base del Product Backlog inicial en `Seguimiento de Proyecto.md` y en el índice de `README.md`).
- **Clasificación:** **3. Redundante con `docs/especificaciones/ERS_Especificacion_Requerimientos_Tribunal.md` (ambos quedan desactualizados frente al código y al registro canónico) e incompleto** (promete ser la ERS completa del sistema pero omite módulos implementados posteriormente y conserva secciones de relevamiento abiertas atribuidas al agente `rawInterviewToRequirementsExtractor`).
- **Contradicciones con el registro:**
  - **Votación nominal individual (`RF-09`, `RN-04`, `STK-01`, `RF-15`, `RF-18`, `SUP-03`):** El documento exige voto nominal individual fundado, quórum `>= 2` votos y mayoría absoluta en sesiones virtuales. El registro (§1.2 #23, §1.3 #24, §1.4 #31, §2 y §3) indica que la votación nominal fue **descartada por el PO el 07/10/2026** y reemplazada por un editor unificado de resolución y firma colegiada de 3 integrantes (4.º, 5.º y 6.º año) en `Resolucion.firmantes`.
  - **Irrecurribilidad absoluta (`RN-04`):** El documento establece `Recurso_Apelacion = PROHIBIDO`. El registro (§1.4 #34 y §2) verifica como implementada la apelación y adecuación del Formulario T01 con plazo parametrizable (`SCRUM-70`, `T01AppealService`, `AdecuacionT01`, `ApelacionT01`).
  - **Nombres de los 6 estados del expediente (`RF-02`, `RF-03`, `RF-06`, `RN-03`):** El documento utiliza denominaciones largas del Reglamento 2026 (`"En período de subida de justificaciones (5 días hábiles)"`, `"Las justificaciones están siendo revisadas"`, `'Justificaciones_En_Revision'`). El registro (§3) fija los 6 estados canónicos del código (`EstadoExpedienteEnum`): `creado` (*"Expediente Creado"*), `justificando` (*"En período de justificaciones"*), `revision_resolucion` (*"Justificaciones en revisión"*), `espera_resolucion` (*"En espera de resolución"*), `pendiente_correos` (*"Pendiente de firma y envío"*) y `emitido` (*"Expedientes ya emitidos"*).
  - **Formularios T02/T03 separados (`RF-04`, `RF-05`):** Describe T02 y T03 como formularios separados. El registro (§3) muestra su modelado unificado bajo `TipoDescargoEnum.T02_CERTIFICADO` (*"Descargo con Causal / Certificado"*) y `TipoDescargoEnum.T03_EXTRAORDINARIO` (*"Descargo - Otros"*).
  - **Firma digital (`RF-10`, `RNF-04`, `AMB-02`):** Menciona sellado criptográfico / cadena de hashes SHA-256 y deja abierta la definición en `AMB-02`. El registro (§1.1 #9 y §2) delimita el alcance a firma electrónica interna colegiada (`Resolucion.firmantes`).
  - **Ambigüedades abiertas ya resueltas en el sistema (`AMB-03`, `AMB-04`):** Mantiene como preguntas abiertas el cómputo matemático del llamado de atención (`AMB-03`) y el calendario de días hábiles (`AMB-04`), cuando el registro (§2) verifica implementadas tanto la regla 3:1 (`AtencionFelicitacion`, `WarningAccumulationService`) como el Calendario Institucional configurable (`Holiday`, `CalendarioVersion`, `FeriadoExcepcion`).
  - **Identificador de socio (`RF-15`):** Refiere a "Número de Legajo UTN/AVEIT"; el registro (§3) distingue `numero_socio` como identificador del sistema y `legajo` en el padrón legado.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - **`RF-16` / `RN-01` / `RN-02` (Alertas automáticas por umbrales -7 y -10):** El registro (§2) marca `SCRUM-62 / US-17` como **parcial** (motor `ThresholdAlertEngine` sin conectar a `LedgerService` / `emitir_resolucion` y sin endpoint/vista).
  - **`RF-17` / `RN-09` (Balance Cuatrimestral Art. 137 exportable en PDF y Excel/CSV):** El registro (§2) marca `SCRUM-63 / SCRUM-124` como **parcial** (falta exportación a **PDF**; solo existe JSON y CSV, y 6 vistas de `reportes_views.py` carecen de permiso de rol).
  - **`RF-19` (Repositorio y motor de búsqueda de antecedentes/jurisprudencia):** El registro (§2) marca `SCRUM-68 / SCRUM-125 / US-19` como **parcial** (solo existe búsqueda de antecedentes dentro de valoraciones T03, sin repositorio dedicado ni exportación).
  - **`RNF-01` (Pruebas de carga k6/JMeter con 50 usuarios concurrentes, P95 <= 500 ms):** El registro (§2) marca `SCRUM-65` (pruebas de carga) como **no implementada**.
  - **`RNF-04` (RBAC estricto en el 100% de operaciones):** El registro (§2) marca RBAC como **parcial** por la brecha de permisos en 6 vistas de `reportes_views.py`.
  - **`RNF-05` / `AMB-05` (Staging, documentación OpenAPI completa, homologación institucional):** El registro (§2 y §6) marca `SCRUM-66` (Staging) y `SCRUM-67` (Homologación) como **No verificable**.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Módulo de Eventos, Reuniones y Asistencia Digital (`SCRUM-50 / SCRUM-86`) y acumulación 3:1 de llamados de atención y felicitaciones (`AtencionFelicitacion`).
  - Apelación y adecuación del Formulario T01 con plazo parametrizable (`SCRUM-70`).
  - Exclusión fundada de involucrados por el TD (`SCRUM-102`) y enmienda trazable de resoluciones con contra-asientos (`SCRUM-103`).
  - Valoración extraordinaria T03 con vinculación de precedentes (`SCRUM-53`) y resolución de causal T02 con puntaje ratificado (`SCRUM-52 / SCRUM-101`).
  - Calendario Institucional (`/calendario-institucional`), ABM de Reglamentos con auditoría inmutable (`/reglamentos`) y Panel de Administración (`/admin/parametros`, `SCRUM-91 / MACRO-03`).
  - Versionado inmutable y retiro lógico de descargos (`DescargoVersion`), censura médica en publicación oficial (`SCRUM-105 / SCRUM-106`) y auditoría de consultas/descargas (`SCRUM-51`).
  - Capa anticorrupción Read-Only sobre tablas legadas MySQL (`backend/padron/`).
- **Referencias rotas:**
  - Citas de trazabilidad no resolubles a archivos del repositorio: `[EstudioInicial:Sec3.5.2/Sec3.7]`, `[EstudioInicial:Sec4.2.6]`, `[Anteproyecto:SecResumen/SecII-B.1]`, `[Anteproyecto:SecV.2]`, `[Anteproyecto:SecVI]`, `[Anteproyecto:SecVIII.2]` (no existe archivo `Anteproyecto` en el repositorio ni rutas enlazadas).

---

## 2. `docs/especificaciones/ERS_Especificacion_Requerimientos_Tribunal.md`

- **Ruta:** `docs/especificaciones/ERS_Especificacion_Requerimientos_Tribunal.md`
- **Líneas:** 155
- **Última modificación (`git log`):** `2026-11-12`
- **Tema que cubre:** ERS específica (v1.1.0, fecha interna `03/09/2026`) del Módulo Unificado de Tribunal de Disciplina y Premiaciones (submódulos, actores, RF-01 a RF-12, RN-01 a RN-16, RNF-01 a RNF-06).
- **Quién lo lee:** equipo / nadie (aparece en el árbol de `README.md`, sin referencias desde código ni desde otros documentos de gestión).
- **Qué pasa si desaparece:** alguien pregunta (por figurar listado en `README.md:213`).
- **Clasificación:** **3. Redundante con `docs/especificaciones/ERS-SGD-AVEIT.md` (ambos desactualizados) e incompleto/inconsistente** (declara `"6 Submódulos Integrados"` en líneas 12 y 21 pero enumera 7 ítems en líneas 23-29; además se contradice en cantidad de estados y votación con el registro).
- **Contradicciones con el registro:**
  - **Ciclo de vida de 5 estados consolidados (líneas 25, 31-37, `RF-03`, `RN-03`):** Afirma que el expediente tiene **5 estados** consolidando revisión y resolución en `"En revisión y resolución"`. El registro (§3) verifica que el código implementa estrictamente **6 estados** (`creado`, `justificando`, `revision_resolucion`, `espera_resolucion`, `pendiente_correos`, `emitido`).
  - **Votación nominal individual (sección 2, `RF-05`, `RN-08`, `RN-09`):** Exige voto nominal fundado y mayoría absoluta `>= 2/3` votos. El registro (§1.3 #24, §2 y §3) confirma que la votación nominal fue **descartada por el PO el 07/10/2026** y reemplazada por editor unificado y firma colegiada de 3 integrantes (4.º, 5.º y 6.º año) en `Resolucion.firmantes`.
  - **Destinatarios de alertas (`RN-13`, `RN-14`):** En `RN-13` dirige la alerta de -7 pts al socio y "a su autoridad de área", y en `RN-14` la alerta roja de -10 pts solo a Comisión Directiva (omitiendo Comisión Fiscalizadora mencionada en la normativa del registro y en `ERS-SGD-AVEIT.md`).
  - **Acceso al ranking (`RF-06`, sección 2):** Asigna `RF-06` (Ranking de Socios) a `"Todos los Actores"` incluyendo Socio Ordinario; el registro (§2 y §3) distingue el portal personal del `SOCIO` ("Mis Expedientes" y saldo propio) del ranking/padrón gestionado por autoridades.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - **`RF-12` (Balance Cuatrimestral exportable en PDF y Excel XLSX):** El registro (§2) marca `SCRUM-63 / SCRUM-124` como **parcial** (no existe exportación PDF ni XLSX; solo JSON y CSV, y faltan permisos de rol en 6 vistas de `reportes_views.py`).
  - **`RN-13` / `RN-14` / sección 2 (Daemon que evalúa automáticamente umbrales -7 y -10 y emite alertas):** El registro (§2) marca `SCRUM-62 / US-17` como **parcial** (motor no conectado al flujo productivo ni expuesto en endpoint/UI).
  - **`RNF-01` (100 usuarios concurrentes simulados, `<= 250 ms`):** El registro (§2) marca `SCRUM-65` (pruebas de carga) como **no implementada**.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Apelación y adecuación del T01 (`SCRUM-70`).
  - Valoración extraordinaria T03 con precedentes (`SCRUM-53`), exclusión fundada de involucrados (`SCRUM-102`) y enmienda de resoluciones con contra-asientos (`SCRUM-103`).
  - Regla 3:1 de llamados de atención y felicitaciones (`AtencionFelicitacion`).
  - Visor Autorizado Unificado con auditoría de consultas (`SCRUM-51`), versionado/retiro lógico de descargos y censura médica (`SCRUM-105 / SCRUM-106`).
  - Calendario Institucional (`/calendario-institucional`), ABM de Reglamentos (`/reglamentos`) y Panel de Administración (`/admin/parametros`).
- **Referencias rotas:**
  - Línea 144: `[DESIGN.md](file:///g:/My%20Drive/Estudios/Seminario/Repositorio/seminario-integrador/DESIGN.md)` — apunta a una ruta local inexistente (`G:\My Drive\...`).

---

## 3. `docs/especificaciones/Escenarios_Calidad_ISO25010_Tribunal.md`

- **Ruta:** `docs/especificaciones/Escenarios_Calidad_ISO25010_Tribunal.md`
- **Líneas:** 128
- **Última modificación (`git log`):** `2026-09-08`
- **Tema que cubre:** Catálogo de 4 Escenarios de Calidad de 6 Partes (ISO/IEC 25010 / SEI) y tácticas arquitectónicas (`ESC-SEG-01`, `ESC-REND-01`, `ESC-USA-01`, `ESC-CONF-01`).
- **Quién lo lee:** cátedra / equipo (listado en `README.md`, sin vínculos desde el código ni otros documentos).
- **Qué pasa si desaparece:** nada (solo figura en el árbol de `README.md:214`).
- **Clasificación:** **3. Incompleto** (promete formalizar los drivers y tácticas arquitectónicas reales de SGD-AVEIT, pero quedó congelado en `03/09/2026` con tácticas y tecnologías que no coinciden con el sistema implementado).
- **Contradicciones con el registro:**
  - **Tailwind CSS (`ESC-USA-01`, línea 77):** Declara `"Maquetación fluida con Tailwind CSS"`. El registro (§3) confirma que el stack real es **Angular 14.2+ + TypeScript + Angular Material** y clasifica la mención de Tailwind CSS como desactualizada.
  - **Estado procesal consolidado (`ESC-CONF-01`, línea 93):** Indica transición al expirar los 5 días hacia `"En revisión y resolución"` (esquema de 5 estados). El registro (§3) establece 6 estados canónicos (`justificando` -> `revision_resolucion` *"Justificaciones en revisión"* -> `espera_resolucion`).
  - **Tácticas de persistencia e integridad (`ESC-SEG-01`, líneas 41-42, 111):** Afirma `"Stored Procedures autorizados"`, `"Triggers MySQL"`, `"particionamiento por año social"` y `"hash SHA-256 de los jueces firmantes"`. El registro (§2) verifica que el libro mayor inmutable se implementa mediante modelos/servicios Django (`AsientoLibroMayor` InsertOnly, `PuntajeAplicado.registrar_movimiento`, `LedgerService`) y firma colegiada en `Resolucion.firmantes`.
  - **Tácticas de rendimiento y móvil (`ESC-REND-01`, `ESC-USA-01`, líneas 57-59, 75, 112, 119):** Describe vista materializada/caché en memoria con invalidación por eventos y compresión de imágenes en cliente. El registro (§2, `SCRUM-87`) verifica que las optimizaciones implementadas son paginación (`backend/core/pagination.py`), `OnPush`, `trackBy` y optimización de consultas ORM.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - **`ESC-REND-01` (150 socios concurrentes, `p95 <= 250 ms`):** El registro (§2) marca `SCRUM-65` (pruebas de carga con 50 usuarios simultáneos, p95) como **no implementada**.
  - **`ESC-SEG-01` (Seguridad integral en backend):** El registro (§2) marca RBAC como **parcial** (6 endpoints de `reportes_views.py` sin permiso de rol específico) y el hardening de seguridad (`SCRUM-65`) como **no implementada**.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Escenario de privacidad/confidencialidad y censura de datos médicos sensibles (`SCRUM-105 / SCRUM-106`, `medical_redaction.py`, auditoría de consultas/descargas `SCRUM-51`).
  - Escenario de interoperabilidad/compatibilidad con el padrón legado MySQL (capa anticorrupción Read-Only `backend/padron/`).
  - Escenario de fiabilidad para notificaciones asíncronas (patrón Outbox `EmailOutbox` con reintentos).
- **Referencias rotas:**
  - Línea 77: `[DESIGN.md](file:///g:/My%20Drive/Estudios/Seminario/Repositorio/seminario-integrador/DESIGN.md)` — apunta a una ruta local inexistente (`G:\My Drive\...`).

---

## 4. `docs/especificaciones/MODELO_DOMINIO_SGD_AVEIT.md`

- **Ruta:** `docs/especificaciones/MODELO_DOMINIO_SGD_AVEIT.md`
- **Líneas:** 1276
- **Última modificación (`git log`):** `2026-11-12`
- **Tema que cubre:** Modelo de Dominio Conceptual (MDD) con patrones ASI, diagramas de clases en Mermaid y PlantUML, diccionario de datos de 24 clases y matriz de trazabilidad con RN-01 a RN-11.
- **Quién lo lee:** cátedra / equipo (citado en `README.md`, `TASK.md` y `docs/gestion-proyecto/Seguimiento de Proyecto.md`).
- **Qué pasa si desaparece:** alguien pregunta (es citado como artefacto de dominio en `Seguimiento de Proyecto.md` y `README.md`; a la vez, en su estado actual contiene contradicciones que pueden inducir a error).
- **Clasificación:** **3. Incompleto** (actualizado parcialmente en noviembre —sección 4.2.1 y ficha 4.15— sin actualizar diagramas, encabezado ni fichas restantes; omite entidades implementadas y conserva elementos descartados).
- **Contradicciones con el registro:**
  - **Modelado de `VotoNominal` y métodos de votación (secciones 1, 2, 3, 4.10, 4.18, 5 y 6):** Los diagramas Mermaid y PlantUML, `ExpedienteDisciplinario` (`tieneQuorumVotacion()`, `calcularMayoriaVotacion()`), la ficha 4.18 (`VotoNominal`) y la trazabilidad de `RN-04` modelan votación nominal individual con quórum `>= 2`. El registro (§1.3 #24, §1.4 #31, §2 y §3) establece que la votación nominal fue **eliminada por el PO el 07/10/2026** y reemplazada por firma colegiada en `Resolucion.firmantes`.
  - **Categorías de socio / Juniors vs Seniors (contradicción interna y con el registro):** La ficha 4.2 (`CategoriaSocio`) y `RN-10` (línea 1259) definen `Pasivo` = años 1-3 y `Activo` = años 4-6 (`"Junior = Pasivo; Senior = Activo"`), coincidiendo con el código (`PASSIVE` 1-3, `ACTIVE` 4-6, registro §3). Sin embargo, la sección 4.2.1 (líneas 809-817) clasifica `Juniors` = 1.º y 2.º año y `Seniors` = 3.º a 6.º año, reproduciendo la divergencia de `Estudio_Inicial.docx` registrada en §3.
  - **Contradicción interna en descargos (`FormularioJustificacion`):** Los diagramas Mermaid (líneas 257-291) y PlantUML (líneas 608-642) modelan subclases separadas `FormularioT02` y `FormularioT03`, mientras que la ficha 4.15 (líneas 1053-1075) ya los unifica en una única clase con `tipoModalidad` (`T02_CERTIFICADO` / `T03_EXTRAORDINARIO`).
  - **Nombres de los 6 estados del expediente (ficha 4.12, línea 1007):** Lista nombres largos reglamentarios (`"En período de subida de justificaciones (5 días hábiles)"`, `"Las justificaciones están siendo revisadas"`) en vez de las denominaciones canónicas del código (`EstadoExpedienteEnum`) documentadas en el registro (§3).
  - **Modelo de Libro Mayor (ficha 4.22):** Modela `MovimientoPuntos` con `saldoAnterior`/`saldoPosterior`; el registro (§2 y §3) verifica en código `AsientoLibroMayor` (`expedientes_asiento_libro_mayor`, InsertOnly) y `PuntajeAplicado` (`tribunal_puntajeaplicado` legado).
  - **Irrecurribilidad absoluta (`RN-04`, línea 1253):** No refleja la apelación y adecuación del T01 (`SCRUM-70`) implementada según el registro (§2).
  - **Metadatos desactualizados:** El encabezado indica `Versión: 1.0.0-final` y `Fecha: 01/09/2026`, aunque el archivo recibió ediciones hasta `2026-11-12`.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - **`BalanceCuatrimestral.exportarInformePDF()` (líneas 369, 718, 1224, 1258):** El registro (§2) marca la exportación a **PDF** del Balance Cuatrimestral (`SCRUM-63 / SCRUM-124`) como **parcial / faltante** (solo existe JSON y CSV).
  - **`Socio.tieneAlertaAmarilla()` / `tieneAlertaRoja()` y cambio automático de estado (`RN-01`, `RN-02`, líneas 56-57, 762-763, 1250-1251):** El registro (§2) marca `SCRUM-62 / US-17` como **parcial** (el motor `ThresholdAlertEngine` no está conectado a `LedgerService` ni a `emitir_resolucion`).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Eventos, Reuniones y Asistencia (`EventoInstitucional`, `EventoConvocado`, `AsistenciaEvento`, `AtencionFelicitacion` y regla 3:1).
  - Composición del Tribunal, apartamiento por conflicto y suplencias (`ComposicionTribunal`, `IntegranteComposicion`, `SCRUM-54`).
  - Apelación y adecuación del Formulario T01 (`PeriodoApelacion`, `ApelacionT01`, `AdecuacionT01`, `ParametroPlazoApelacion`, `SCRUM-70`).
  - Resolución de causal T02 (`DecisionCausalDescargo`), valoración extraordinaria T03 con antecedentes (`ValoracionT03`, `ValoracionT03Antecedente`, `SCRUM-53`), exclusión fundada (`SCRUM-102`) y enmienda de resoluciones (`EnmiendaResolucion`, `SCRUM-103`).
  - Versionado de descargos (`DescargoVersion`) y auditoría de consultas/descargas (`AuditoriaConsultaExpediente`, `AuditoriaDescargaEvidencia`).
  - Calendario Institucional (`Holiday`, `CalendarioVersion`, `FeriadoExcepcion`), ABM de Reglamentos (`ArticuloReglamento`, `AuditoriaArticuloReglamento`), Outbox de emails (`EmailOutbox`) y Parámetros de Administración (`SystemParameterChange`, `TribunalRoleChange`).
- **Referencias rotas:**
  - No presenta enlaces rotos a archivos del repositorio. Presenta fórmulas LaTeX mal formateadas sin delimitadores en líneas 804 y 806 (`\\text{Año Social} = ...`, `\\text{Número de Grupo} = ...`).

---

## 5. `docs/especificaciones/PLANTILLA_CASO_DE_USO.md`

- **Ruta:** `docs/especificaciones/PLANTILLA_CASO_DE_USO.md`
- **Líneas:** 108
- **Última modificación (`git log`):** `2026-09-08`
- **Tema que cubre:** Plantilla genérica vacía (`CU-XX`) para redactar casos de uso con ficha técnica, flujos, reglas de negocio, RNF y mapeo UI/API.
- **Quién lo lee:** nadie (solo figura en `README.md:216,253`; no se instancia desde ningún documento ni código del repositorio).
- **Qué pasa si desaparece:** nada.
- **Clasificación:** **1. Residuo de fabricación** (plantilla genérica de Sprint 0 sin uso posterior; no es arquitectónica, no corresponde al formato ágil de US + UAT exigido por la Guía UTN FRC en el registro §4, ni aporta al código o a los entregables presentables).
- **Contradicciones con el registro:**
  - **Formato de especificación:** Propone Casos de Uso (`CU-XX`), mientras que el registro (§4) indica que la Guía de Documentación UTN FRC para proyectos Ágiles requiere Historias de Usuario (US) + UAT.
  - **Módulos listados (línea 9):** Enumera 5 módulos genéricos (`Tramitación`, `Deliberación`, `Puntos`, `Portal`, `Balances`) que no coinciden con los 9 módulos del menú frontend verificados en el registro (§3).
  - **Descripción en `README.md:253`:** `README.md` afirma que esta plantilla incluye *"criterios de aceptación BDD (Gherkin)"*, pero el archivo no contiene ninguna sección BDD/Gherkin.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - No aplica (plantilla vacía con placeholders).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - No aplica (plantilla genérica vacía).
- **Referencias rotas:**
  - Ninguna (solo contiene placeholders `CU-XX`, `UI-XX`, `POST /api/v1/[recurso]`).

---

## 6. `docs/especificaciones/RBAC-SGD-AVEIT.md`

- **Ruta:** `docs/especificaciones/RBAC-SGD-AVEIT.md`
- **Líneas:** 86
- **Última modificación (`git log`):** `2026-09-19`
- **Tema que cubre:** Esquema RBAC del Walking Skeleton (Spec 001): principios de autorización, 5 roles, equivalencia con permisos legados y cargos estatutarios, 4 endpoints iniciales y cuestiones abiertas al PO.
- **Quién lo lee:** equipo (referenciado directamente desde `backend/README.md:3` y desde el docstring de `backend/socios/models.py:27`).
- **Qué pasa si desaparece:** alguien se equivoca (o alguien pregunta: el código en `backend/socios/models.py` y `backend/README.md` remiten explícitamente a este archivo para comprender el mapeo de `Socio.role` y permisos legados `tribunal_bajo/medio/alto`).
- **Clasificación:** **3. Incompleto** (sus principios, los 5 roles y la tabla de equivalencias legadas siguen vigentes como base en `backend/accounts/permissions.py` y `legacy_rbac.py`, pero quedó congelado en Spec 001: solo documenta 4 endpoints de toda la API y conserva cuestiones abiertas ya superadas).
- **Contradicciones con el registro:**
  - **Cobertura de autorización en endpoints (principios 1 y 4, sección 4):** Afirma privilegio mínimo por defecto en toda ruta protegida y lista solo 4 endpoints (`/api/v1/auth/login/`, `refresh/`, `me/`, `/api/v1/socios/`). El registro (§2) identifica una **brecha RBAC**: 6 vistas en `backend/expedientes/views/reportes_views.py` solo exigen `IsAuthenticated` sin permiso de rol específico.
  - **Cuestión abierta #3 (línea 85):** Declara que la gestión de eventos y asistencias (`tribunal_medio`) *"no tienen módulo equivalente dentro del alcance de Spec 001"*. El registro (§2) verifica que el módulo de Eventos y Asistencia (`SCRUM-50 / SCRUM-86`) está **implementado**.
  - **Cuestión abierta #4 (línea 86):** Declara *"Auditoría sin persistencia"* (solo logger `security`). Aunque `backend/accounts/audit.py` use logger para autenticación, el registro (§2) verifica múltiples tablas persistentes de auditoría en el sistema (`AuditoriaConsultaExpediente`, `AuditoriaDescargaEvidencia`, `AuditoriaArticuloReglamento`, `SystemParameterChange`, `TribunalRoleChange`, `CambioEstadoExpediente`).
  - **Alcance del rol `ADMIN` (líneas 26 y 42):** Describe a `ADMIN` sin atribuciones funcionales operativas, mientras que el registro (§2) verifica el Panel de Administración (`SCRUM-91 / MACRO-03`, `/admin/parametros`) que permite gestionar parámetros del sistema y miembros del TD.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - **Rol `CD` con alertas de 7 y 10 puntos (línea 24):** El registro (§2) marca `SCRUM-62 / US-17` como **parcial** (sin endpoint ni vista de alertas).
  - **Protección RBAC completa (sección 1):** El registro (§2) marca RBAC como **parcial** (brecha en `reportes_views.py`) y `SCRUM-65` (hardening RBAC) como **no implementada**.
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Permisos por rol de todos los módulos posteriores a Spec 001: ranking, legajo integral, solicitudes T01 y competencias (`opening_policy.py`), expedientes y tablero, descargos T02/T03 y evidencias, visor unificado (`SCRUM-51`), valoración T03 (`SCRUM-53`), apelación T01 (`SCRUM-70`), resoluciones/firmas/enmiendas, exclusiones (`SCRUM-102`), eventos y asistencias, calendario institucional, reglamentos, reportes y administración (`/admin/parametros`).
  - Permiso de conflicto de interés `IsNotInvolvedInExpediente` (`backend/expedientes/permissions.py`, `SCRUM-54`, consultado expresamente por la cátedra en el registro §1.4 #32) y el guard frontend (`frontend/src/app/services/tribunal.guard.ts`).
- **Referencias rotas:**
  - Ninguna ruta o símbolo roto: `backend/accounts/permissions.py` (`IsTribunalOrDirectiva`), `backend/accounts/legacy_rbac.py`, `backend/socios/models.py`, `backend/tests/test_rbac.py`, `backend/accounts/audit.py` y `/api/v1/socios/` existen en el repositorio.

---

## 7. `docs/especificaciones/REDISENIO_EVENTOS_ASISTENCIAS.md`

- **Ruta:** `docs/especificaciones/REDISENIO_EVENTOS_ASISTENCIAS.md`
- **Líneas:** 118
- **Última modificación (`git log`):** `2026-10-15`
- **Tema que cubre:** Especificación funcional y técnica del rediseño del módulo de Eventos y Asistencias (`SCRUM-50 / S3-06`): UX en dos pestañas, 6 estados del evento, Reunión vs Actividad, convocatorias y regla 3:1.
- **Quién lo lee:** equipo (especificación puntual de feature; no está referenciada en `README.md`, código ni entregables de cátedra).
- **Qué pasa si desaparece:** nada (el comportamiento ya está implementado y cubierto por código y tests).
- **Clasificación:** **4. Vigente** (coincide con el diseño implementado en `backend/expedientes/models.py` —`CategoriaEventoEnum`, `SubtipoReunionEnum`, `SubtipoActividadEnum`, `ModalidadEventoEnum`, `ModoConvocatoriaEnum`, `EstadoEventoEnum`, `AtencionFelicitacion`— y `notifications_email_outbox`, con desactualizaciones menores de estado y nomenclatura).
- **Contradicciones con el registro:**
  - **Estado del documento (línea 6):** Indica `"Estado: Aprobado / En Implementación"`, cuando el registro (§2) verifica `SCRUM-50 / SCRUM-86` como **implementada**.
  - **Nomenclatura Juniors/Seniors (líneas 105-107):** Define `JUNIORS` = 1.º a 3.º año (pasivos) y `SENIORS` = 4.º a 6.º año (activos). El corte de años coincide con `PASSIVE` (1-3) y `ACTIVE` (4-6) del código en el registro (§3), pero difiere de la definición de `Juniors` (1-2) y `Seniors` (3-6) usada en `Estudio_Inicial.docx` y en `MODELO_DOMINIO_SGD_AVEIT.md §4.2.1`.
- **Afirmaciones sobre funcionalidad que el registro marca como parcial o no implementada:**
  - Ninguna directa: en sección 6 describe la consolidación 3:1 (implementada en `WarningAccumulationService`) y no promete la alerta preventiva previa al llegar a 2 llamados (brecha parcial de `SCRUM-61` en el registro §2).
- **Funcionalidad implementada que el documento debería cubrir y no cubre:**
  - Paginación del listado de eventos incorporada posteriormente en `SCRUM-87` (`test_evento_pagination.py`).
  - Permisos RBAC específicos sobre los endpoints de `backend/expedientes/urls_eventos.py`.
- **Referencias rotas:**
  - No contiene links markdown rotos. Como discrepancia de identificadores técnicos, en línea 115 menciona las tipificaciones `INASISTENCIA_REUNION` e `INCUMPLIMIENTO_ACTIVIDAD`, cadenas que no existen en `backend/expedientes/models.py` ni en `backend/expedientes/services/`. Las tablas/campos `notifications_email_outbox`, `atencionFelicitacion` y `llamadosAtencion` sí existen en el código.

---

## Decisiones pendientes

1. **Coexistencia de dos ERS redundantes y desactualizadas (`ERS-SGD-AVEIT.md` y `ERS_Especificacion_Requerimientos_Tribunal.md`):** Definir cuál será el documento de requerimientos de referencia en `docs/especificaciones/` (si es que alguno debe mantenerse vigente) y cuál pasa a `auditoria/archivados/`, resolviendo la contradicción entre 5 y 6 estados y la eliminación definitiva de la votación nominal exigida por la cátedra (registro §1.3 #24 y §1.4 #31).
2. **Vigencia y alcance de `MODELO_DOMINIO_SGD_AVEIT.md`:** Definir si este archivo se sincroniza completamente con el dominio real (eliminando `VotoNominal`, alineando diagramas Mermaid/PlantUML con `FormularioJustificacion` unificado, resolviendo la contradicción interna Juniors/Seniors vs Pasivos/Activos y agregando los módulos implementados) o si se conserva solo como snapshot histórico archivado frente a la Definición del Producto.
3. **Destino de `Escenarios_Calidad_ISO25010_Tribunal.md`:** Definir si se actualiza para reflejar la arquitectura real (Angular Material, 6 estados, `AsientoLibroMayor` InsertOnly, paginación/ORM, privacidad médica y Outbox) o si se archiva.
4. **Destino de `PLANTILLA_CASO_DE_USO.md`:** Confirmar si se mueve a `auditoria/archivados/` por ser residuo de fabricación sin uso y ajustar la referencia en `README.md`.
5. **Actualización de `RBAC-SGD-AVEIT.md` y cuestiones abiertas al PO:** Definir si se amplía para cubrir todos los endpoints implementados, `IsNotInvolvedInExpediente` (`SCRUM-54`) y la resolución formal de las cuestiones abiertas #1 y #2 (cargos 13, 14 y 15 y rol de Órganos de Fiscalización / Revisores de Cuentas), además de reflejar el estado real de `reportes_views.py`.
6. **Criterio terminológico unificado para Juniors/Seniors vs Pasivos/Activos:** Resolver la divergencia entre el corte 1.º-3.º / 4.º-6.º (`backend/socios/models.py`, `REDISENIO_EVENTOS_ASISTENCIAS.md`, `MODELO_DOMINIO_SGD_AVEIT.md §4.2`) y el corte 1.º-2.º / 3.º-6.º (`MODELO_DOMINIO_SGD_AVEIT.md §4.2.1`, `Estudio_Inicial.docx`).
7. **Conservación o archivo de `REDISENIO_EVENTOS_ASISTENCIAS.md`:** Definir si se mantiene como especificación vigente actualizando su encabezado (`Implementado`) y limpiando los identificadores `INASISTENCIA_REUNION`/`INCUMPLIMIENTO_ACTIVIDAD`, o si se archiva por haber cumplido su ciclo de diseño de Sprint 3.
