# Brief Común — Auditoría de los 4 Entregables Formales (SGD-AVEIT)

> **Fecha de elaboración:** 27/11/2026  
> **Orden de autoridad:** `código y tests > auditoria/registro-canonico.md > resto de la documentación` (`AGENTS.md`, Regla 7).  
> **Regla de alcance por entregable:**
> - **Estudio Inicial** y **Plan de Proyecto**: **NO** incluyen la ejecución del Sprint 5.
> - **Seguimiento del Proyecto** y **Definición del Producto / Solución**: **SÍ** incluyen el Sprint 5 efectuado (y marcan lo incompleto como `"trasladada al Sprint 6"`).
> - **Regla de inmutabilidad:** Ninguna fecha ni versión histórica ya presentada ante la cátedra puede modificarse (`AGENTS.md`, Regla 13).

---

## 1. Nombres Canónicos (Módulos, Entidades, Roles, Estados y Sprints)

### 1.1 Identificación Institucional (según `Carátula gral.docx` y código)
- **Universidad / Facultad / Carrera:** Universidad Tecnológica Nacional — Facultad Regional Córdoba — Ingeniería en Sistemas de Información.
- **Cátedra / Curso:** Seminario Integrador — Curso `3K2`.
- **Docentes del Curso:** Ing. María Irene Mac William, Ing. Silvina Arenas · **Docente Tutor:** Ing. Fernando Sanabria.
- **N.º de Grupo:** `13` *(nota: `DEFINICION_DE_PRODUCTO_S4` y el viejo `Plan_de_Proyecto.docx` del repo decían `Grupo 04`; la carátula general vigente fija `13`)*.
- **Sistema / Acrónimo:** `SGD-AVEIT` *(Sistema de Gestión del Tribunal de Disciplina y Premiaciones de A.V.E.I.T.; nunca `SDG-AVEIT`)*.
- **Integrantes (Legajo UTN):** Guillén Lucas Martin (`85194`), Gastiaburu Lucas Nicolas (`74907`), Quiroz Tomas Augusto (`415327`), Rosales Nicolás (`408917`), Sanchez Diego (`87414`), Urviola Luis (`409953`), Villegas Axel Rene (`403655`).
- **Stack Real:** Backend **Python 3.12 + Django 4.2 LTS + DRF** · Frontend **SPA Angular 14.2+ + TypeScript (`strict: true`) + Angular Material / Material Dashboard PRO** (sin Vanilla JS ni Tailwind CSS) · BD **MySQL 8.0** (padrón legado Read-Only + tablas propias) · Orquestación **Docker Compose**.

### 1.2 Roles RBAC y Categorías de Socio
- **Roles vigentes en código (`backend/socios/models.py`):**
  1. `SOCIO` (Socio Ordinario)
  2. `FISCALIZADORA` (Autoridad de Subcomisión / Líder de Equipo — **vigente en Sprint 5 por decisión D-02 del 27/11/2026**; su partición en `AUTORIDAD_SC` + `REVISORES` y vista 403 queda **trasladada al Sprint 6**)
  3. `CD` (Comisión Directiva)
  4. `TD` (Miembro del Tribunal de Disciplina)
  5. `ADMIN` (Administrador de Cómputos)
- **Categorías de Socio en código:** `PASSIVE` (*Pasivo*, años sociales **1.º a 3.º**) y `ACTIVE` (*Activo*, años sociales **4.º a 6.º**).
- **Identificador de Socio:** `numero_socio` (`legajo` únicamente en tabla legada `socio_lista`).

### 1.3 Estados, Formularios, Entidades y Módulos del Menú
- **6 Estados Canónicos (`EstadoExpedienteEnum`):**
  1. `creado` (*Expediente Creado*)
  2. `justificando` (*En período de justificaciones*)
  3. `revision_resolucion` (*Justificaciones en revisión*)
  4. `espera_resolucion` (*En espera de resolución*)
  5. `pendiente_correos` (*Pendiente de firma y envío*; alias UI `pendiente_firma`)
  6. `emitido` (*Expedientes ya emitidos*)
- **Formularios:** `SolicitudT01` (`T01`), `TipoDescargoEnum.T02_CERTIFICADO` (*Descargo con Causal / Certificado*), `TipoDescargoEnum.T03_EXTRAORDINARIO` (*Descargo - Otros*).
- **Decisión colegiada del TD:** Editor unificado de resolución + **firma electrónica colegiada** de 3 integrantes activos (4.º, 5.º y 6.º año) en `Resolucion.firmantes`. **No existe votación nominal** (descartada por el PO el 07/10/2026).
- **Valoración T03 (`ResultadoValoracionT03Enum`):** `ACCEPTED` (*Aprobada*), `REJECTED` (*Desaprobada*).
- **Entidades principales en BD:** `Socio`, `Subcomision`, `Expediente`, `SolicitudT01`, `ExpedienteNumberSequence`, `CambioEstadoExpediente`, `DescargoExpediente`, `DescargoVersion`, `EvidenciaDescargo`, `AuditoriaDescargaEvidencia`, `AuditoriaConsultaExpediente`, `DecisionCausalDescargo`, `ValoracionT03`, `ValoracionT03Antecedente`, `ComposicionTribunal`, `IntegranteComposicion`, `PeriodoApelacion`, `ApelacionT01`, `AdecuacionT01`, `ParametroPlazoApelacion`, `Resolucion`, `EnmiendaResolucion`, `AsientoLibroMayor` (`expedientes_asiento_libro_mayor`, InsertOnly con `REVERSION`), `PuntajeAplicado` (`tribunal_puntajeaplicado` legado), `PuntajeGeneral`, `AtencionFelicitacion`, `EventoInstitucional`, `EventoConvocado`, `AsistenciaEvento`, `Holiday`, `CalendarioVersion`, `FeriadoExcepcion`, `ArticuloReglamento`, `AuditoriaArticuloReglamento`, `EmailOutbox`, `EmailAttachment`, `SystemParameterChange`, `TribunalRoleChange`.
- **9 Módulos del Menú Frontend:** `/mis-expedientes` (*Mis Expedientes*), `/reglamentos` (*Reglamentos*), `/solicitar-puntos` (*Crear Expediente*), `/ranking-socios` (*Ranking de Socios*), `/gestionar-expedientes` (*Gestionar Expedientes*), `/calendario-institucional` (*Calendario Institucional*), `/reportes` (*Reportes & Balance*), `/eventos-asistencia` (*Eventos & Asistencia*), `/admin/parametros` (*Administración*).

### 1.4 Línea Temporal Canónica de Sprints
- **Sprint 0:** Definiciones generales, Working Agreement, Backlog inicial y Story Map (`01/09/2026`–`02/09/2026`).
- **Sprint 1:** Walking Skeleton, Padrón Read-Only, Autenticación JWT, RBAC base y Ranking (`08/09/2026`–`21/09/2026`).
- **Sprint 2:** Apertura T01, Competencias, Ciclo 6 Estados, Outbox y Mis Solicitudes (`SCRUM-75`) (`22/09/2026`–`06/10/2026`).
- **Sprint 3:** Descargos T02/T03, Evidencias Protegidas, Calendario, Urgencia, Eventos/Asistencia 3:1 y adelanto `SCRUM-52` (`07/10` u `08/10` al `20/10/2026`; cierre administrativo `22/10/2026` — *inconsistencia de fecha inicio 07/10 vs 08/10 señalada por docentes*).
- **Sprint 4:** Visor (`SCRUM-51`), Valoración T03 (`SCRUM-53`), Suplencias (`SCRUM-54`), Resolución sin votación (`SCRUM-56`), Apelación T01 (`SCRUM-70`) (`22/10/2026`–`03/11/2026`; *al 03/11 en `main` estaban `SCRUM-70`, `SCRUM-51`, `SCRUM-54` y ABM Reglamentos; `SCRUM-56` se integró el `05/11` y `SCRUM-53` el `12/11`*).
- **Sprint 5 (Consolidado):** Ejecutado entre `04/11/2026` y `23/11/2026` (PRs `#74`–`#79` y commit `6a60167`).
- **Sprint 6:** Traspaso formal de funcionalidades parciales, no implementadas o no verificables del Sprint 5 (`auditoria/traspaso-sprint6.md`).

---

## 2. Estado Real de Funcionalidades (`implementada` / `trasladada al Sprint 6`)

### 2.1 Implementadas (verificadas en código y tests — 114 `test_*.py`, 55 `*.spec.ts`)
- Autenticación JWT por `numero_socio` y elegibilidad; Healthchecks (`/api/health/`, `/api/v1/padron/health/`).
- Capa anticorrupción Padrón Read-Only (`backend/padron/`); Buscador y Legajo Integral; Ranking reconciliado y paginado.
- Solicitudes T01 (borrador, emisión, multi-socio, Anexo, competencias `opening_policy.py`, número canónico, Mis Solicitudes `SCRUM-75`).
- Ciclo procesal de 6 estados, tablero Kanban/Tabla, urgencia (`SCRUM-78`) y concepto/clasificación.
- Notificaciones Outbox (`EmailOutbox`, `EmailAttachment`, reintentos) y `NotificationCenter` UI (10s accesible).
- Calendario Institucional (`Holiday`, `CalendarioVersion`, `FeriadoExcepcion`) y plazos de 5 días hábiles.
- Descargos T02/T03, versionado inmutable (`DescargoVersion`), retiro lógico y evidencia protegida en `BinaryField` con auditoría (`AuditoriaDescargaEvidencia`).
- Visor Autorizado Unificado (`SCRUM-51`, `AuditoriaConsultaExpediente`), Resolución causal T02 con `puntaje_ratificado` (`SCRUM-52`/`101`), Valoración T03 con precedentes (`SCRUM-53`), Composición/Apartamiento/Suplencias (`SCRUM-54`, `IsNotInvolvedInExpediente`), Apelación y Adecuación T01 (`SCRUM-70`).
- Editor unificado de Resolución, preview PDF, firma colegiada 4.º/5.º/6.º (`Resolucion.firmantes`), emisión oficial (`SCRUM-56`/`58`/`89`), Exclusión fundada (`SCRUM-102`), Enmienda trazable con contra-asientos `REVERSION` (`SCRUM-103`).
- Libro Mayor Inmutable (`AsientoLibroMayor` InsertOnly + `PuntajeAplicado` + regla 3:1 `AtencionFelicitacion`, `SCRUM-57`/`59`/`104`).
- Portal "Mis Expedientes", saldo propio y publicación oficial con censura médica (`SCRUM-60`/`105`/`106`, `medical_redaction.py`).
- Eventos, Reuniones y Asistencia Strategy + rediseño UI (`SCRUM-50`/`86`); ABM Reglamentos con auditoría; Panel de Administración (`/admin/parametros`, `SCRUM-91`/`MACRO-03`); Optimización de rendimiento (`SCRUM-87`/`MACRO-06`); Manual de Usuario modular (`SCRUM-129`, 9 capítulos HTML + PDF).
- Reportes analíticos y Balance Art. 137 **solo en JSON y CSV** (4 pestañas UI).

### 2.2 Descartada por PO
- **Votación nominal individual paso a paso:** eliminada el 07/10/2026; reemplazada por editor unificado + firma colegiada en `Resolucion.firmantes`.

### 2.3 Alcance Oficial del Sprint 5 y Traspaso al Sprint 6 (motivo en una línea)

- **Implementado en Sprint 5 (respaldado en código, PRs #74–#79 y `6a60167`):** `SCRUM-57`/`58`/`59`/`60` (`MACRO-01` y `MACRO-02`: Libro Mayor, firma colegiada, exclusión, enmienda, Mis Expedientes, publicación con censura médica), `SCRUM-91` (`MACRO-03`: Panel Admin), `SCRUM-86` (`MACRO-04`: Eventos UI), `SCRUM-93` (`MACRO-05`: N.º socio / ID canónico / celdas atómicas), `SCRUM-87` (`MACRO-06`: Optimización) y `SCRUM-129` (Manual de Usuario).
- **Trasladado al Sprint 6 (ver `auditoria/traspaso-sprint6.md`):**
  1. **Alertas automáticas `-10` y `-7` (`SCRUM-62` / `US-17`):** `ThresholdAlertEngine` no está conectado a `LedgerService`/`emitir_resolucion` ni tiene endpoint/vista.
  2. **Alerta preventiva 3:1 de apercibimientos (`SCRUM-61`):** consolida 3:1 pero falta aviso preventivo a autoridades al llegar a 2 llamados.
  3. **Balance Art. 137 en PDF y blindaje RBAC de Reportes (`SCRUM-63` / `SCRUM-124`):** falta exportación PDF y 6 vistas de `reportes_views.py` solo exigen `IsAuthenticated`.
  4. **Reconciliación bidireccional `PuntajeAplicado` vs `PuntajeGeneral` (`SCRUM-64`):** no existe comando, endpoint ni vista de divergencias.
  5. **Hardening RBAC, 10 disparadores de email y pruebas de carga 50 usuarios (`SCRUM-65` / `SCRUM-92`):** sin scripts/reportes de carga ni suite de los 10 disparadores; persiste brecha RBAC y ruta stub `EnDesarrolloComponent`.
  6. **Partición de rol `FISCALIZADORA` en `AUTORIDAD_SC` + `REVISORES` y vista 403 (`SCRUM-121` / `SCRUM-122`):** por decisión D-02 se mantiene `FISCALIZADORA` vigente en Sprint 5 y se traslada el split al Sprint 6.
  7. **Repositorio dedicado de jurisprudencia (`SCRUM-68` / `SCRUM-125` / `US-19`):** solo existe búsqueda embebida en T03; falta módulo libre y exportación.
  8. **Promoción de Casos Internos a T01 (`PB-01` / `SCRUM-128`):** sin implementación en código ni tests.
  9. **Despliegue en Staging con réplica MySQL legada (`SCRUM-66` / `SCRUM-126`):** no verificable desde el repositorio (sin entorno ni logs de verificación).
  10. **Homologación institucional AVEIT (`SCRUM-67` / `SCRUM-127`):** no verificable (sin actas UAT firmadas por CD, TD y Cómputos).

---

## 3. Fechas y Versiones Ya Presentadas (Inmutables)

| Entregable | Archivo presentado (`Documentación Actual Humana`) | Versiones y fechas inmutables | Estado en repo actual (`regularidadDocs`) |
|---|---|---|---|
| **Estudio Inicial** | `Estudio_Inicial.docx` | `v1.0.0` (15/08), `v1.1.0` (15/08), `v1.2.0` (15/08), `v1.3.0` (16/08), `v1.4.0` (18/08), `v1.5.0` (18/08/2026). Carátula con `xx/xx/2026`. | `docs/formales/Estudio_Inicial.docx` ya actualizado a `v1.6.0` (`27/11/2026`) preservando `v1.0.0`–`v1.5.0`. |
| **Plan de Proyecto** | `Plan_de_Proyecto.docx` | `v1.0.0` (01/09), `v1.0.1` (02/09), `v2.0.0` (03/09/2026). Carátula con `DD/MM/AAAA` y título "Análisis del Sistema". | `docs/formales/Plan_de_Proyecto.docx` ya actualizado a `v2.1.0` (`27/11/2026`) preservando `v1.0.0`–`v2.0.0`. |
| **Seguimiento del Proyecto** | `Seguimiento_de_ProyectoVersionSprint0.pdf`, `...Sprint2.pdf`, `...Sprint4.pdf` | `v1.0.0` (01/09), `v1.1.0` (02/09 — S0), `v1.2.0` (07/10 — S2), `v1.3.0` (22/10 — S3/S4 apertura), `v1.4.0` (04/11/2026 — S4 cierre / S5 apertura). | `docs/gestion-proyecto/Seguimiento de Proyecto.md` tiene `v1.0.0`–`v1.3.0` + `v1.4.0` (04/11) + `v1.5.0` (27/11/2026). |
| **Definición del Producto / Solución** | `Definicion_de_ProductoVersionSprint2.pdf` y `DEFINICION_DE_PRODUCTO_S4_APERTURA_Y_CIERRE.pdf` | S2: `v1.0.0` (`08/10/2026`). S4: sin tabla de revisiones (cubre S4 `21/10`–`03/11/2026`, cierre S3 `22/10`, hito IOC `04/11/2026`). | No existe documento consolidado en `.docx`/`.md` en el repo (hay `ERS-SGD-AVEIT.md`, `MODELO_DOMINIO_SGD_AVEIT.md`, `RBAC-SGD-AVEIT.md` y `specs/`). |

---

## 4. Requisitos por Entregable (Cátedra + Plantilla) y Datos Potencialmente Faltantes

> **Requisitos comunes (`Seminario-Guia de Documentación.pdf` + `Carátula gral.docx`):** Todos los entregables comparten formato de presentación uniforme con **Carátula** (Universidad, Facultad, Carrera, Cátedra, Proyecto, Título del Entregable, Curso `3K2`, N.º de Entrega, Docentes, N.º de Grupo `13`, Integrantes con Legajo, Fecha de Entrega), **Tabla de Contenido / Índice**, **Historial de Cambios / Revisión**, y opcionalmente **Glosario / Diccionario de Datos**. **Extensión (páginas/palabras) y reglas tipográficas:** *No especificadas en la guía*.

### 4.1 Estudio Inicial *(no incluye Sprint 5)*
- **Secciones obligatorias:** Carátula · Índice · Introducción · Propósito · Descripción del Ámbito/Contexto (Presentación, Objetivo, Reseña Histórica, Dimensionamiento, Políticas, Mapa Global de Procesos, Descripción de Procesos AS-IS afectados, Recursos Informáticos Existentes, Lay-Out) · Antecedentes/Competencia (si aplica producto) · Problemas y Oportunidades · Historial de Cambios · *(Glosario)*.
- **Datos exigidos que podrían no existir:** Fecha real de entrega en carátula (`xx/xx/2026`); detalle formal de entrevistados, fechas de entrevistas y técnicas de relevamiento (obs. docente #2); acta o validación institucional explícita de adopción del Reglamento 2026 sobre 2018 (obs. docente #3); plano/lay-out físico depurado (obs. docente #5).

### 4.2 Plan de Proyecto *(no incluye Sprint 5)*
- **Secciones obligatorias:** Carátula · Índice · Propósito · Nombre del producto · Objetivo · Alcances / Requerimientos Funcionales · Requerimientos No Funcionales (arquitectura, implementación, diseño y restricciones normativas/tecnológicas separadas) · Metodología adoptada (Scrumban operativo) · Equipo de trabajo · Historial de Cambios.
- **Datos exigidos que podrían no existir:** Fecha real de entrega / examen en carátula (`DD/MM/AAAA`); versión consolidada definitiva de Casos de Uso (`CU-01..CU-12` citados en `v2.0.0` pero solo `CU-01` está desarrollado); unificación de Story Points (`111` vs `116` en obs. #16).

### 4.3 Seguimiento del Proyecto *(incluye Sprint 5)*
- **Secciones obligatorias:** Carátula · Historia de Revisión · Índice · Propósito · **Sprint 0** (Working Agreement: duración, eventos, capacidad en horas por miembro, roles, herramientas, tecnologías + política IA; Product Backlog inicial; Story Map con corte de MVP) · **Sprint 1 al 5** (Planificación: fecha inicio, SM, Product Backlog actualizado, Sprint Backlog; Resultado Final del Sprint; Retrospectiva del proyecto).
- **Datos exigidos que podrían no existir:** Horas reales dedicadas por integrante en Sprints 4 y 5; burndown/CFD/lead time/cycle time reales de Jira para Sprint 4 y Sprint 5; fechas reales de Sprint Review y Retrospectiva del Sprint 5; criterio final de Story Points consolidados del Sprint 5 (hay divergencias en `SCRUM-59/61/64/66/67` entre Seguimiento S4 y Definición S4); evidencia de aceptación formal por PO/institución al cierre de Sprint 4 (03/11) y Sprint 5.

### 4.4 Definición del Producto / Solución *(incluye Sprint 5)*
- **Secciones obligatorias (proyectos Ágiles):** Carátula · Historia de Revisión · Índice · Propósito · Nombre y Objetivo · Product Backlog · Roles del Sistema · Epics y US asociadas · Por cada US: Descripción + UAT, Diseño de Interfaz, Diseño de Casos de Prueba, Resultados de las Pruebas · Diagrama de Clases · DER completo (PK, FK, longitud, tipo de dato, valores posibles) · Diagramas de Transición de Estados (indicando por método n.º y nombre de US responsable, estado inicial y final/es) · Arquitectura del Software (Ambiente de Implementación, Diagrama de Despliegue indicando US por nodo, Lay-Out de Equipamiento).
- **Datos exigidos que podrían no existir:** Resultados de ejecución viva actualizados de `pytest` y `Karma` (solo existe cobertura estática de 114/55 archivos; obs. docente #27); trazabilidad completa *Normativa → RF → US → Prueba → Resultado real* para todas las US de Sprints 1–5 (obs. #25); diseño de interfaz (capturas actualizadas) y casos de prueba/UAT formales para todas las US de Sprint 5; DER completo con longitud y dominio de valores para las ~30 tablas actuales; Lay-Out de Equipamiento / Diagrama de Despliegue verificado en Staging real (no verificable, trasladado al Sprint 6).
