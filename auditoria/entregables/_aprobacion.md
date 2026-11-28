# Puerta de Aprobación — Consolidación de los 4 Entregables Formales (`SGD-AVEIT`)

> **Fecha de aprobación:** 28/11/2026  
> **Estado:** **APROBADA** — Todas las decisiones transversales, específicas y los 32 cambios propuestos fueron confirmados por el usuario.  
> **Fuentes:** [`_brief-comun.md`](_brief-comun.md) · [`estudio-inicial-discrepancias.md`](estudio-inicial-discrepancias.md) · [`plan-de-proyecto-discrepancias.md`](plan-de-proyecto-discrepancias.md) · [`seguimiento-discrepancias.md`](seguimiento-discrepancias.md) · [`definicion-producto-discrepancias.md`](definicion-producto-discrepancias.md).

---

## 0. Decisiones Resueltas (Aprobadas el 28/11/2026)

### 0.1 Transversales
- [x] **DEC-T1 — Carátula unificada (todos los entregables):** `N.º de Grupo: 13`, cátedra `Seminario Integrador — Curso 3K2`, nómina docente (`Ing. María Irene Mac William`, `Ing. Silvina Arenas`, tutor `Ing. Fernando Sanabria`), **Fecha de Entrega: `28/11/2026`**, **N.º de Entrega: `Regularidad`**, y **suprimir el campo `Fecha de examen`**.
- [x] **DEC-T2 — Convención única de calendario S3/S4/S5 (Seguimiento + Definición, obs. #26):** Sprint 3 (`07/10–20/10`, aclarando hito PO `07/10` vs tablero Jira `08/10`), Sprint 4 (`21/10–03/11`, aclarando cierre administrativo S3 el `22/10`) y Sprint 5 Consolidado (`04/11–23/11/2026`).
- [x] **DEC-T3 — Unificación de Story Points (Plan + Seguimiento + Definición, obs. #16):** Prevalece **Seguimiento S4** para los 5 ítems con conflicto (`SCRUM-59`: 5, `SCRUM-61`: 2, `SCRUM-64`: 3, `SCRUM-66`: 5, `SCRUM-67`: 5); mantener `116 SP` en Sprint 0 explicando la diferencia `111/116`; reportar los macros ejecutados en Sprint 5 (`SCRUM-86`, `87`, `89`/`101`–`103`, `91`, `93`/`114`–`115`, `129`) por historia/PR **sin inventar SP**.
- [x] **DEC-T4 — Límite temporal de Estudio Inicial y Plan de Proyecto (NO incluyen Sprint 5):** Retirar de `docs/formales/Estudio_Inicial.docx` y `docs/formales/Plan_de_Proyecto.docx` las menciones a Sprint 5/6, tickets `SCRUM-*` y rutas/símbolos internos del repo (`auditoria/...`, `AsientoLibroMayor`), manteniendo solo diseño y arquitectura vigentes.
- [x] **DEC-T5 — Pruebas y capturas (Seguimiento + Definición, obs. #27):** Declarar la **cobertura estática verificada** (`114` archivos `test_*.py` / `55` archivos `*.spec.ts`) y marcar la ejecución viva y capturas nuevas como pendientes de corrida final.

### 0.2 Específicas por Entregable
- [x] **DEC-EI1 (Estudio Inicial — obs. #1 y #4):** **Reubicar** la Matriz TO-BE (§3.7.1) y expectativas tecnológicas al cierre bajo *"Expectativas iniciales del usuario"* y dejar el cuerpo 100% AS-IS + Problemas/Oportunidades.
- [x] **DEC-EI2 (Estudio Inicial — categorías):** Mantener el criterio estatutario (`Juniors 1.º–2.º / Seniors 3.º–6.º`) con una nota única de equivalencia al código (`Pasivo 1.º–3.º / Activo 4.º–6.º`) y eliminar la doble definición de `Socio Pasivo` en el Glosario.
- [x] **DEC-PP1 y DEC-PP2 (Plan de Proyecto — catálogo RF y MoSCoW, obs. #18):** **Agregar nuevos `RF` (`RF-16` en adelante)** para los módulos implementados hoy omitidos y **repriorizar MoSCoW** con entregas tempranas (MVP en Sprint 2 + releases posteriores).
- [x] **DEC-PP3 (Plan de Proyecto — §12 Casos de Uso y §4.1 TGS):** **Eliminar §12** (Casos de Uso/BCE, no exigidos por la Guía para Ágiles) y **retirar §4.1 (TGS)** (vacía) para evitar secciones incompletas.
- [x] **DEC-SG1 (Seguimiento — Retrospectiva S5 y datos faltantes):** Declarar explícitamente como no registrados los datos faltantes (horas reales S1–S5, métricas Jira `Burndown`/`CFD`/`Lead-Cycle Time`, fecha de Review/Retro S5 si no se provee) sin inventar cifras.
- [x] **DEC-DP1 (Definición del Producto — documento maestro único y granularidad):** Consolidar un **único documento maestro en `docs/formales/`** (preservando en historial `v1.0.0` S2 del `08/10` y S4 del `04/11`), **agrupando las US de Sprints 1–5 por Épica/Módulo** (con ficha completa + matriz bidireccional + DER físico/Clases/Estados generados desde el código) y **retirar la sección de Casos de Uso**.

---

## 1. Estudio Inicial *(NO incluye Sprint 5)*

- [x] **EI-01:** Retirar los 3 residuos de votación nominal (§3.9, §3.7 Proceso 3, título de fila §3.7.1) (obs. #23 y #31).
- [x] **EI-02:** Reconstruir §3.5.3 (*Catálogo de Formularios Administrativos Oficiales*) describiendo AS-IS `T01`, `Anexo T01`, `T02` y `T03`.
- [x] **EI-03:** Corregir afirmaciones no verificadas o inexactas (*"hash inalterable"*, *"cron/daemon automatizado"*, *"portal público"*, módulo `"Justificaciones"`, alertas `-7/-10` y balance "con un clic").
- [x] **EI-04:** Aplicar **DEC-T4** retirando menciones a `Sprint 6`, `SCRUM-*` y rutas/símbolos internos del repo.
- [x] **EI-05:** Aplicar **DEC-EI1** y **DEC-EI2** (reubicar TO-BE al cierre bajo *"Expectativas iniciales del usuario"* y conciliar Glosario/`Junior-Senior`).
- [x] **EI-06:** Incorporar al dominio AS-IS los aspectos omitidos (regla 3:1, apartamiento/suplencias TD, apelación/adecuación T01, resguardo médico, calendario institucional, padrón Read-Only, eventos/asistencia, administración de reglamentos).
- [x] **EI-07:** Ajustar §3.5.6 (corregir estilo `Heading 3` y marcar entrevistados/fechas faltantes sin inventar), §3.5.1 (marcar aval institucional faltante si aplica) y agregar nota de no aplicabilidad para *Antecedentes / Competencia* (sistema institucional a medida).
- [x] **EI-08:** Actualizar Carátula (**DEC-T1**), regenerar `ÍNDICE` y consolidar nueva versión (`28/11/2026`, preservando `v1.0.0`–`v1.5.0` inmutables).

---

## 2. Plan de Proyecto *(NO incluye Sprint 5)*

- [x] **PP-01:** Eliminar residuos en `v2.1.0` (votación nominal en §6.1 fila 9 y §8 fila 6; triggers SQL en `RF-12` y `R-03`; `"al menos dos firmas"` en `RNF-03` → **3** firmas activas; *"links directos con token"* en `R-04` → JWT por `numero_socio`).
- [x] **PP-02:** Alinear Matriz RBAC (§6.1) al código (`FISCALIZADORA`, `Pasivo/Activo`, permisos reales de `CD`/`TD` imputados).
- [x] **PP-03:** Alinear `RN-05` a los 6 nombres canónicos del código e incluir Apelación/Adecuación T01 y Enmienda con contra-asientos.
- [x] **PP-04:** Reformular `RNF-01`, `RNF-04`, `RNF-05` y `RES-04`/`R-02` como criterios objetivo pendientes de verificación.
- [x] **PP-05:** Aplicar **DEC-PP1** y **DEC-PP2** en §7 y §8 (nuevos `RF-16+`, trazabilidad normativa completa y repriorización MoSCoW con MVP en Sprint 2).
- [x] **PP-06:** Ampliar §11 (obs. #15: capa Read-Only `backend/padron/`, JWT por `numero_socio`, permisos legados, stack Django 4.2 + Angular 14.2 + Docker Compose).
- [x] **PP-07:** Aplicar **DEC-T4** (retirar reportes de ejecución S5/S6 y rutas internas), **DEC-PP3** (eliminar §12 y §4.1) y limpieza editorial (`Plan de Proyecto` en carátula, `"Provicional"`, eliminar menciones a skills internas de IA).
- [x] **PP-08:** Actualizar Carátula (**DEC-T1**) y consolidar nueva versión (`28/11/2026`, preservando `v1.0.0`, `v1.0.1` y `v2.0.0` inmutables).

---

## 3. Seguimiento del Proyecto *(SÍ incluye Sprint 5)*

- [x] **SG-01:** Restaurar inmutabilidad histórica de `v1.4.0` (`04/11/2026`) y registrar el cierre real del Sprint 5 y traspaso al Sprint 6 en nueva versión (`28/11/2026`).
- [x] **SG-02:** Corregir regresiones de `v1.5.0` (`US-13`, Story Map sin votación nominal, recuperar Retro S4 y tabla S5, corregir numeración e Índice).
- [x] **SG-03:** Corregir cierre real de Sprint 4 (obs. #28 y #29: corte al `03/11` vs `SCRUM-56` el `05/11` y `SCRUM-53` el `12/11`; `SCRUM-63`/`62` parciales).
- [x] **SG-04:** Redactar cierre formal del **Sprint 5 Consolidado (`04/11`–`23/11/2026`)** con los 9 bloques/PRs implementados, los **10 bloques trasladados al Sprint 6** (obs. #30) y Retrospectiva de cierre (**DEC-SG1**).
- [x] **SG-05:** Aplicar observaciones docentes de Sprint 0 (#17, #18, #19, #20: carga promedio planificada, roadmap inicial adaptable, MVP Sprint 2 + Releases, revisión MoSCoW).
- [x] **SG-06:** Aplicar **DEC-T2** (calendario S3/S4/S5) y **DEC-T3** (Story Points).
- [x] **SG-07:** Alinear stack (§2.1.5), rol `FISCALIZADORA` vigente en Sprint 5 (§2.5.2) y DoD (§2.1.1 D).
- [x] **SG-08:** Corregir Carátula (**DEC-T1**) y rotular correctamente `"Legajo UTN"` en la tabla de integrantes.

---

## 4. Definición del Producto / Solución *(SÍ incluye Sprint 5)*

- [x] **DP-01:** Aplicar **DEC-DP1**: consolidar un único documento maestro en `docs/formales/` preservando en historial `v1.0.0` S2 (`08/10`) y S4 (`04/11/2026`).
- [x] **DP-02:** Purgar votación nominal de todo el documento y retirar `+tieneQuorumVotacion()` / `+calcularMayoriaVotacion()` de `docs/especificaciones/MODELO_DOMINIO_SGD_AVEIT.md`.
- [x] **DP-03:** Corregir 6 estados canónicos, resultados T03 (`ACCEPTED`/`REJECTED`), arquitectura real (monolito modular Django/Angular/MySQL en Docker Compose), roles (`TD`, `FISCALIZADORA`), categorías (`PASSIVE`/`ACTIVE`), nombres de tests y diagramas renderizados.
- [x] **DP-04:** Corregir estado real de S4/S5 (`SCRUM-62`/`63` parciales), incorporar todo el incremento del Sprint 5 + módulos omitidos de S2–S4 y listar los **10 ítems trasladados al Sprint 6**.
- [x] **DP-05:** Responder explícitamente a las observaciones docentes #32 (`IsNotInvolvedInExpediente`), #33 (`Resolucion.firmantes` 4.º/5.º/6.º) y #34 (`T01AppealService`/`AdecuacionT01`).
- [x] **DP-06:** Construir matriz bidireccional completa (Sprints 1–5) y aplicar **DEC-T5** (cobertura estática `114`/`55` + ejecución viva/capturas marcadas pendientes).
- [x] **DP-07:** Generar desde el código real: DER físico completo (~30 tablas), Diagrama de Clases y Diagrama de Transición de Estados con US por método.
- [x] **DP-08:** Documentar Arquitectura y Diagrama de Despliegue (Docker Compose local + Staging/Producción AVEIT trasladado al Sprint 6) y unificar Carátula (**DEC-T1**), calendario (**DEC-T2**) y Story Points (**DEC-T3**).
